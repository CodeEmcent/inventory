from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryViewSet, ExportInventoryView, ImportInventoryView

# Define the router and register the ViewSet
router = DefaultRouter()
router.register(r'inventory', InventoryViewSet, basename='inventory')

# Include the router-generated URLs
urlpatterns = [
    path('', include(router.urls)),
    path('export/', ExportInventoryView.as_view(), name='export-inventory'),
    path('import/', ImportInventoryView.as_view(), name='import-inventory'),
]
