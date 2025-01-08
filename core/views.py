from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import InventoryItem
from .serializers import InventoryItemSerializer
from accounts.permissions import *
from rest_framework.views import APIView
from openpyxl import Workbook
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser, FormParser
from openpyxl import load_workbook


class InventoryViewSet(ModelViewSet):
    """
    Handles CRUD operations for inventory items.
    """
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated, IsAdminOrStaffOrReadOnly]

    # Example of adding a custom action
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_items(self, request):
        """
        Custom action to retrieve inventory items owned by the requesting user.
        """
        user_items = InventoryItem.objects.filter(user=request.user)
        serializer = self.get_serializer(user_items, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        """
        Apply specific permissions for retrieve and destroy actions.
        """
        if self.action in ['retrieve', 'destroy']:
            self.permission_classes = [IsOwnerOrAdminOrStaff]
        return super().get_permissions()


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
            for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True)):  # Skip header
                name, quantity = row
                if not name or not isinstance(quantity, (int, float)):
                    return Response({"error": f"Invalid data in row {i + 2}."}, status=400)

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
            }
            return Response(message, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
