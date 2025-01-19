from django.urls import path
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    OfficeViewSet,
    ItemRegistryViewSet,
    RegistryTemplateView, 
    RegistryImportView,
    RegistryDownloadView,
    RegistryView,
    InventoryViewSet,
    TemplateView,
    ImportInventoryView,
    ExportInventoryView,
    BroadsheetView
)

router = DefaultRouter()
router.register(r'offices', OfficeViewSet, basename='offices')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'item-registry', ItemRegistryViewSet, basename='item-registry')

urlpatterns = router.urls + [
    # Item Registry URLs
    path('registry/template/', RegistryTemplateView.as_view(), name='item-registry-template'),
    path('registry/import/', RegistryImportView.as_view(), name='item-registry-import'),
    path('registry/view/', RegistryView.as_view(), name='item-registry-view'),
    path('registry/download/', RegistryDownloadView.as_view(), name='item-registry-download'),
    # Inventory Template URLs
    path('template/<int:office_id>/', TemplateView.as_view(), name='download-template'),
    path('import/', ImportInventoryView.as_view(), name='import-inventory'),
    path('export/', ExportInventoryView.as_view(), name='export-inventory'),
    # Inventory Broadsheet URLs
    path('broadsheet/', BroadsheetView.as_view(), name='broadsheet'),
]