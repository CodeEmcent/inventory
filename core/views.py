from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser, FormParser
from openpyxl import load_workbook
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Avg, Count
from .models import Office, InventoryItem
from .serializers import OfficeSerializer, InventoryItemSerializer
from accounts.permissions import (
    IsAdminOrStaffOrReadOnly,
    IsAdminOrSuperAdmin,
    IsOwnerOrAdminOrStaff,
    IsAssignedStaff
)

# --- Office ViewSet ---
class OfficeViewSet(ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data["message"] = "Office created successfully."
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data["message"] = "Office updated successfully."
        return response

    def destroy(self, request, *args, **kwargs):
        office = self.get_object()
        super().destroy(request, *args, **kwargs)
        return Response({"message": f"Office '{office.name}' deleted successfully."}, status=200)

# --- Inventory ViewSet ---
class InventoryViewSet(ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated, IsAdminOrStaffOrReadOnly]

    def get_queryset(self):
        office_id = self.request.query_params.get('office_id')
        if self.request.user.role == 'staff':
            if not office_id:
                return InventoryItem.objects.none()
            office = get_object_or_404(Office, id=office_id)
            if office not in self.request.user.assigned_offices.all():
                return InventoryItem.objects.none()
            return InventoryItem.objects.filter(office=office)
        return InventoryItem.objects.all()

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'destroy']:
            self.permission_classes = [IsOwnerOrAdminOrStaff, IsAssignedStaff]
        elif self.action == 'create':
            self.permission_classes = [IsAuthenticated, IsAssignedStaff]
        else:
            self.permission_classes = [IsAdminOrStaffOrReadOnly]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": f"Item '{instance.name}' successfully deleted."}, status=200)

# --- Template View ---
class TemplateView(APIView):
    permission_classes = [IsAuthenticated, IsAssignedStaff]

    def get(self, request, office_id):
        office = get_object_or_404(Office, id=office_id)
        if office not in request.user.assigned_offices.all():
            return Response({"error": "You do not have permission to download this template."}, status=403)

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = f"Template for {office.name}"

        header_font = Font(bold=True, size=14)
        centered_alignment = Alignment(horizontal="center", vertical="center")

        organization_name = request.user.organization.name if request.user.organization else "Unknown Organization"
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
        sheet.cell(row=1, column=1).value = organization_name
        sheet.cell(row=1, column=1).font = header_font
        sheet.cell(row=1, column=1).alignment = centered_alignment

        sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=5)
        office_description = f"Office: {office.name} | Description: {office.department or 'No Description'}"
        sheet.cell(row=2, column=1).value = office_description
        sheet.cell(row=2, column=1).font = header_font
        sheet.cell(row=2, column=1).alignment = centered_alignment

        headers = ["S/N", "Items", "Qty", "Description (Optional)", "Remarks"]
        for col_num, header in enumerate(headers, start=1):
            cell = sheet.cell(row=3, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        staff_name = request.user.username
        sheet.append([])
        sheet.append([f"Signature: {staff_name}", "This must match the username of the uploader."])
        sheet.merge_cells(start_row=5, start_column=1, end_row=5, end_column=5)
        sheet.cell(row=5, column=1).alignment = centered_alignment

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = f'attachment; filename={office.name}_template.xlsx'
        workbook.save(response)
        return response

# --- Import Inventory View ---
class ImportInventoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('file', None)
        office_id = request.query_params.get('office_id')

        if not file_obj:
            return Response({"error": "No file uploaded."}, status=400)
        if not office_id:
            return Response({"error": "Office ID is required."}, status=400)

        office = get_object_or_404(Office, id=office_id)
        if office not in request.user.assigned_offices.all():
            return Response({"error": "You do not have permission to manage this office."}, status=403)

        workbook = load_workbook(file_obj)
        sheet = workbook.active

        headers = ["S/N", "Items", "Qty", "Description (Optional)", "Remarks"]
        if [cell.value for cell in sheet[3]] != headers:
            return Response({"error": "Invalid template format. Please use the correct template."}, status=400)

        # Process rows excluding the signature row
        imported_items, updated_items = [], []
        for i, row in enumerate(sheet.iter_rows(min_row=4, max_row=sheet.max_row - 1, values_only=True)):
            serial_number, item_name, quantity, description, remarks = row

            if not item_name or not isinstance(quantity, int):
                return Response({"error": f"Invalid data in row {i + 4}."}, status=400)

            item_name = item_name.strip().title()
            description = description[:100] if description else None
            remarks = remarks[:100] if remarks else None

            existing_item = InventoryItem.objects.filter(
                user=request.user, office=office, name=item_name
            ).first()

            if existing_item:
                existing_item.quantity = quantity
                existing_item.description = description
                existing_item.remarks = remarks
                existing_item.save()
                updated_items.append(existing_item.name)
            else:
                imported_items.append(InventoryItem(
                    user=request.user,
                    office=office,
                    name=item_name,
                    quantity=quantity,
                    description=description,
                    remarks=remarks,
                ))

        InventoryItem.objects.bulk_create(imported_items)
        return Response({
            "message": "Inventory imported successfully.",
            "new_items": len(imported_items),
            "updated_items": updated_items
        }, status=201)


# --- Export Inventory View ---
class ExportInventoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        office_id = request.query_params.get('office_id')
        if request.user.role == 'staff':
            if not office_id:
                return Response({"error": "Office ID is required to export inventory."}, status=400)
            inventory_items = InventoryItem.objects.filter(
                user=request.user, office_id=office_id
            )
        else:
            inventory_items = InventoryItem.objects.all()

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Inventory Items"

        organization_name = request.user.organization.name if request.user.organization else "Unknown Organization"
        sheet.append([f"Inventory Export for {organization_name}"])
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)
        sheet.cell(row=1, column=1).font = Font(bold=True, size=14)
        sheet.cell(row=1, column=1).alignment = Alignment(horizontal="center", vertical="center")

        headers = ["ID", "Name", "Quantity", "Office", "Description", "Remarks", "User", "Created At", "Updated At"]
        sheet.append(headers)

        for col_num, header in enumerate(headers, start=1):
            cell = sheet.cell(row=2, column=col_num)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for item in inventory_items:
            sheet.append([
                item.id,
                item.name,
                item.quantity,
                item.office.name,
                item.description or "N/A",
                item.remarks or "N/A",
                item.user.username,
                item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                item.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        column_widths = [10, 20, 10, 15, 30, 30, 15, 20, 20]
        for i, width in enumerate(column_widths, start=1):
            sheet.column_dimensions[chr(64 + i)].width = width

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = 'attachment; filename=inventory_items.xlsx'
        workbook.save(response)
        return response

# --- Broadsheet View ---
class BroadsheetView(APIView):
    """
    API to collate inventory data across all offices and provide analytics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        # Perform data aggregation
        inventory_data = InventoryItem.objects.values(
            'office__name', 'name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_items=Count('id'),
            average_quantity=Avg('quantity')
        ).order_by('office__name', 'name')

        # Office-wise summary
        office_summary = InventoryItem.objects.values('office__name').annotate(
            total_quantity=Sum('quantity'),
            total_items=Count('id'),
            average_quantity=Avg('quantity')
        ).order_by('office__name')

        # Grand totals
        grand_totals = InventoryItem.objects.aggregate(
            total_quantity=Sum('quantity'),
            total_items=Count('id'),
            average_quantity=Avg('quantity')
        )

        # JSON response for the broadsheet
        if format == 'json':
            return Response({
                "inventory_data": list(inventory_data),
                "office_summary": list(office_summary),
                "grand_totals": grand_totals
            })

        # Excel export for the broadsheet
        elif format == 'excel':
            return self.generate_excel(inventory_data, office_summary, grand_totals)

        return Response({"error": "Invalid format. Use 'json' or 'excel'."}, status=400)

    def generate_excel(self, inventory_data, office_summary, grand_totals):
        """
        Generate and return the broadsheet as an Excel file.
        """
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Broadsheet"

        # Add title row
        sheet.append(["Broadsheet Report"])
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)
        sheet.cell(row=1, column=1).font = Font(bold=True, size=14)
        sheet.cell(row=1, column=1).alignment = Alignment(horizontal="center", vertical="center")

        # Add inventory data section
        sheet.append([])  # Blank row
        sheet.append(["Inventory Data"])
        sheet.append(["Office", "Item", "Total Quantity", "Total Items", "Average Quantity"])
        for item in inventory_data:
            sheet.append([
                item['office__name'],
                item['name'],
                item['total_quantity'],
                item['total_items'],
                round(item['average_quantity'], 2) if item['average_quantity'] else 0,
            ])

        # Add office summary section
        sheet.append([])  # Blank row
        sheet.append(["Office Summary"])
        sheet.append(["Office", "Total Quantity", "Total Items", "Average Quantity"])
        for office in office_summary:
            sheet.append([
                office['office__name'],
                office['total_quantity'],
                office['total_items'],
                round(office['average_quantity'], 2) if office['average_quantity'] else 0,
            ])

        # Add grand totals
        sheet.append([])  # Blank row
        sheet.append(["Grand Totals"])
        sheet.append([
            "Total Quantity", grand_totals['total_quantity'],
            "Total Items", grand_totals['total_items'],
            "Average Quantity", round(grand_totals['average_quantity'], 2) if grand_totals['average_quantity'] else 0
        ])

        # Adjust column widths
        for col in range(1, 7):
            sheet.column_dimensions[chr(64 + col)].width = 20

        # Prepare the response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response['Content-Disposition'] = 'attachment; filename=broadsheet.xlsx'
        workbook.save(response)
        return response