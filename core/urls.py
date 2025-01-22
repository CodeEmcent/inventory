from django.urls import path
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    OfficeViewSet,
    ItemRegisterViewSet,
    RegisterTemplateView, 
    RegisterImportView,
    RegisterDownloadView,
    InventoryViewSet,
    TemplateView,
    ImportInventoryView,
    ExportInventoryView,
    BroadsheetView
)

router = DefaultRouter()
router.register(r'offices', OfficeViewSet, basename='offices')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'item-register', ItemRegisterViewSet, basename='item-register')

urlpatterns = router.urls + [
    # Item Register URLs
    path('register/template/', RegisterTemplateView.as_view(), name='item-regisery-template'),
    path('register/import/', RegisterImportView.as_view(), name='item-register-import'),
    path('register/download/', RegisterDownloadView.as_view(), name='item-register-download'),
    # Inventory Template URLs
    path('template/<int:office_id>/', TemplateView.as_view(), name='download-template'),
    path('import/', ImportInventoryView.as_view(), name='import-inventory'),
    path('export/', ExportInventoryView.as_view(), name='export-inventory'),
    # Inventory Broadsheet URLs
    path('broadsheet/', BroadsheetView.as_view(), name='broadsheet'),
]
