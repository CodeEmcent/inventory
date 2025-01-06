from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import InventoryItem
from .serializers import InventoryItemSerializer
from accounts.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin


class InventoryViewSet(ModelViewSet):
    """
    Handles CRUD operations for inventory items.
    """
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

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
            self.permission_classes = [IsOwnerOrAdmin]
        return super().get_permissions()
