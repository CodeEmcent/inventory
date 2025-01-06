from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryViewSet

# Define the router and register the ViewSet
router = DefaultRouter()
router.register(r'inventory', InventoryViewSet, basename='inventory')

# Include the router-generated URLs
urlpatterns = [
    path('', include(router.urls)),
]
