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
    name = models.CharField(
        max_length=255,
        help_text="The name of the inventory item."
    )
    quantity = models.PositiveIntegerField(
        default=0,
        help_text="The quantity of this inventory item (must be 1 or greater)."
    )
    description = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Optional description of the inventory item (max 100 characters)."
    )
    remarks = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="Remarks on the item's condition (max 100 characters)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'office', 'name')  # Prevent duplicate items for user-office combinations
        ordering = ['name']  # Default alphabetical order by name
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=1),  # Ensure quantity is at least 1
                name="quantity_gte_1"
            )
        ]

    def __str__(self):
        return f"{self.name} (Office: {self.office.name}, User: {self.user.username})"

    def save(self, *args, **kwargs):
        if self.quantity < 1:
            raise ValueError("Quantity must be at least 1.")
        self.name = self.name.title()  # Capitalize the name
        super().save(*args, **kwargs)