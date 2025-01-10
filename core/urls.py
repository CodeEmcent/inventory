from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    OfficeViewSet,
    InventoryViewSet,
    TemplateView,
    ImportInventoryView,
    ExportInventoryView,
    BroadsheetView
)

router = DefaultRouter()
router.register(r'offices', OfficeViewSet, basename='offices')
router.register(r'inventory', InventoryViewSet, basename='inventory')

urlpatterns = router.urls + [
    path('template/<int:office_id>/', TemplateView.as_view(), name='download-template'),
    path('import/', ImportInventoryView.as_view(), name='import-inventory'),
    path('export/', ExportInventoryView.as_view(), name='export-inventory'),
    path('broadsheet/', BroadsheetView.as_view(), name='broadsheet'),
]
