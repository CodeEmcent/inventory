from django.db import models
from accounts.models import CustomUser

# Create your models here.
class Office(models.Model):
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="inventory_items")
    office = models.ForeignKey(Office, on_delete=models.CASCADE, default='Unknown', related_name="inventory_items")
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'name')  # Prevent duplicates for the same user
        ordering = ['name']  # Default ordering by name

    def __str__(self):
            return self.name

    def save(self, *args, **kwargs):
        # Capitalize the first letter of each word in the name
        self.name = self.name.title() if self.name else self.name
        super().save(*args, **kwargs)