from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models  # Import models for aggregation
from django.shortcuts import get_object_or_404
from .models import Office, InventoryItem
from .serializers import OfficeSerializer, InventoryItemSerializer
from accounts.permissions import *
from rest_framework.views import APIView
from openpyxl import Workbook
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser, FormParser
from openpyxl import load_workbook
from accounts.permissions import IsAdminOrSuperAdmin
from accounts.permissions import IsAssignedStaff
from accounts.models import CustomUser
from core.models import Office

class InventoryViewSet(ModelViewSet):
    """
    Handles CRUD operations for inventory items.
    """
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated, IsAdminOrStaffOrReadOnly]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_items(self, request):
        """
        Custom action to retrieve inventory items owned by the requesting user.
        """
        queryset = self.get_queryset().filter(user=request.user)  # Ensure consistent filtering
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrSuperAdmin])
    def broadsheet(self, request):
        """
        Aggregated inventory data for the entire organization.
        """
        data = InventoryItem.objects.values('name').annotate(
            total_quantity=models.Sum('quantity')
        )
        return Response(data)

    def get_queryset(self):
        # Restrict staff to only see items for their assigned offices
        if self.request.user.role == 'staff':
            return InventoryItem.objects.filter(office__in=self.request.user.assigned_offices.all())
        # Admins and superadmins can view all inventory
        return InventoryItem.objects.all()
    
    def get_permissions(self):
        """
        Apply specific permissions for retrieve and destroy actions.
        """
        if self.action in ['retrieve', 'update', 'destroy']:
            self.permission_classes = [IsOwnerOrAdminOrStaff, IsAssignedStaff]
        else:
            self.permission_classes = [IsAdminOrSuperAdmin]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        """
        Override the destroy method to add a custom success message.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Item successfully deleted."}, status=200)


class TemplateView(APIView):
    """
    Endpoint to download an Excel template for inventory import.
    Staff members can only download templates for their assigned offices.
    """
    permission_classes = [IsAuthenticated, IsAssignedStaff]

    def get(self, request, office_id):
        try:
            # Validate the office
            office = Office.objects.get(id=office_id)
            if office not in request.user.assigned_offices.all():
                return Response({"error": "You do not have permission to download this template."}, status=403)

            # Create the workbook and sheet
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = f"Template for {office.name}"

            # Add the header rows
            organization_name = request.user.organization.name if request.user.organization else "Unknown Organization"
            sheet.append([organization_name])  # Row 1: Organization Name
            sheet.append([f"Office: {office.name}", f"Description: {office.department}"])  # Row 2: Office Name and Description

            # Add the column headers
            headers = ["S/N", "Items", "Qty", "Description", "Remarks"]
            sheet.append(headers)

            # Add a footer with staff information
            staff_name = request.user.username
            sheet.append([])  # Leave a blank row
            sheet.append([f"Staff Name:", f"{staff_name}"])

            # Prepare the response
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response['Content-Disposition'] = f'attachment; filename={office.name}_template.xlsx'
            workbook.save(response)
            return response

        except Office.DoesNotExist:
            return Response({"error": "Office not found."}, status=404)



class ExportInventoryView(APIView):
    """
    View to export all inventory items to an Excel file.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Query all inventory items
        inventory_items = InventoryItem.objects.filter(user=request.user)

        # Create a workbook and worksheet
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Inventory Items"

        # Add header row
        headers = ["ID", "Name", "Quantity", "Created At", "Updated At"]
        sheet.append(headers)

        # Add data rows
        for item in inventory_items:
            sheet.append([
                item.id,
                item.name,
                item.quantity,
                item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                item.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        # Prepare the response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response['Content-Disposition'] = 'attachment; filename=inventory_items.xlsx'
        workbook.save(response)
        return response


class ImportInventoryView(APIView):
    """
    View to handle importing inventory items from an Excel file, replacing quantities for duplicates.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # Check if file is in the request
        file_obj = request.FILES.get('file', None)
        if not file_obj:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            # Load the workbook
            workbook = load_workbook(file_obj)
            sheet = workbook.active  # Get the first sheet

            # Extract and validate data
            imported_items = []
            updated_items = []
            errors = []  # Track row-specific errors
            for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True)):  # Skip header
                name, quantity = row
                if not name or not isinstance(quantity, (int, float)):
                    errors.append({"row": i + 2, "error": "Invalid data."})
                    continue

                # Normalize the name to handle duplicates (case and whitespace)
                normalized_name = name.strip().lower()

                # Check if the item already exists
                existing_item = InventoryItem.objects.filter(user=request.user, name__iexact=normalized_name).first()
                if existing_item:
                    # Replace the existing item's quantity
                    existing_item.quantity = int(quantity)
                    existing_item.save()
                    updated_items.append(existing_item.name)
                else:
                    # Create a new item
                    imported_items.append(InventoryItem(user=request.user, name=normalized_name, quantity=int(quantity)))

            # Save new items in bulk
            InventoryItem.objects.bulk_create(imported_items)

            # Prepare the response
            message = {
                "new_items_added": len(imported_items),
                "updated_items": len(updated_items),
                "updated_item_names": updated_items,
                "errors": errors
            }
            return Response(message, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class OfficeViewSet(ModelViewSet):
    """
    Handles CRUD operations for offices. Restricted to admins and superadmins.
    """
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def create(self, request, *args, **kwargs):
        """
        Create an office and return a success message.
        """
        response = super().create(request, *args, **kwargs)
        response.data["message"] = "Office created successfully."
        return response

    def update(self, request, *args, **kwargs):
        """
        Update an office and return a success message.
        """
        response = super().update(request, *args, **kwargs)
        response.data["message"] = "Office updated successfully."
        return response

    def destroy(self, request, *args, **kwargs):
        """
        Delete an office and return a success message.
        """
        office = self.get_object()
        super().destroy(request, *args, **kwargs)
        return Response({"message": f"Office '{office.name}' deleted successfully."}, status=200)
