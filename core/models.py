import uuid
from django.db import models
from accounts.models import CustomUser
from datetime import date

class Office(models.Model):
    """
    Represents an office or department in an organization.
    """
    name = models.CharField(max_length=255, unique=True)  # Unique names for offices
    department = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.department})" if self.department else self.name
    

class ItemRegistry(models.Model):
    """
    Represents a centralized registry of items with unique stock IDs.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="The name of the inventory item."
    )
    stock_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Automatically generated unique identifier for the item."
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional description of the item."
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="The cost per unit of the item."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Automatically generate a stock ID if it doesn't exist.
        """
        if not self.stock_id:
            # Generate a UUID and format it as a short string
            self.stock_id = f"OLASS-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"({self.stock_id})"

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
    item_id = models.ForeignKey(
        ItemRegistry,
        on_delete=models.PROTECT,
        related_name="inventory_items",
        help_text="The standardized item from the registry."
    )
    quantity = models.PositiveIntegerField(
        default=0,
        help_text="The quantity of this inventory item (must be 1 or greater)."
    )
    remarks = models.CharField(
        max_length=100,
        default="Perfect",
        null=False,
        blank=False,
        help_text="Remarks on the item's condition (max 100 characters)."
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The description of the inventory item, pre-filled from ItemRegistry."
    )
    year = models.PositiveIntegerField(
        default=date.today().year,
        help_text="Year of the inventory"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'office', 'item_id', 'year')  # Correct reference to 'item_id'
        ordering = ['item_id__name']  # Correct lookup for 'name' field in ItemRegistry
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=1),  # Ensure quantity is at least 1
                name="quantity_gte_1"
            )
        ]

    def __str__(self):
        return f"{self.item_id.stock_id} - {self.item_id.name} (Office: {self.office.name}, User: {self.user.username})"

    def save(self, *args, **kwargs):
        # Set the description to the item's description from the ItemRegistry
        if not self.description and self.item_id:
            self.description = self.item_id.description
        super().save(*args, **kwargs)  # Call the original save method


