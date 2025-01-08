from django.db import models
from accounts.models import CustomUser

# Create your models here.
class InventoryItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="inventory_items")
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'name')  # Prevent duplicates for the same user