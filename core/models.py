from django.db import models
from accounts.models import CustomUser

class Office(models.Model):
    """
    Represents an office or department in an organization.
    """
    name = models.CharField(max_length=255, unique=True)  # Unique names for offices
    department = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.department})" if self.department else self.name


class InventoryItem(models.Model):
    """
    Represents an inventory item managed by a user and assigned to an office.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="inventory_items",
        help_text="The user managing this inventory item."
    )
    office = models.ForeignKey(
        Office,
        on_delete=models.CASCADE,
        related_name="inventory_items",
        help_text="The office this inventory item is assigned to."
    )
    name = models.CharField(max_length=255, help_text="The name of the inventory item.")
    quantity = models.PositiveIntegerField(
        default=0, help_text="The quantity of this inventory item (must be non-negative)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'office', 'name')  # Prevent duplicate items per user and office
        ordering = ['name']  # Default alphabetical ordering by name

    def __str__(self):
        return f"{self.name} (Office: {self.office.name}, User: {self.user.username})"

    def save(self, *args, **kwargs):
        """
        Custom save method to enforce capitalization of item names.
        """
        if self.name:
            self.name = self.name.title()
        super().save(*args, **kwargs)
