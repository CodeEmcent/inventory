from django.contrib.auth.models import AbstractUser
from django.db import models
# from core.models import Office
from django.apps import apps

class Organization(models.Model):
    """
    Represents an organization that users belong to.
    """
    name = models.CharField(max_length=255, unique=True, help_text="The name of the organization.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """
    Custom user model that extends the default Django User model.
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='staff',
        help_text="The role assigned to the user (e.g., admin, staff)."
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The organization this user belongs to."
    )
    assigned_offices = models.ManyToManyField(
        'core.Office',
        related_name="assigned_users",
        blank=True,
        help_text="The offices assigned to the user."
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        """
        Custom save method to validate role assignments.
        """
        # Check if user has an id (i.e., the user is already saved)
        if self.id and self.role != 'staff' and self.assigned_offices.exists():
            raise ValueError("Only staff users can be assigned offices.")
        super().save(*args, **kwargs)
