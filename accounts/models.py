from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.apps import apps


class Organization(models.Model):
    """
    Represents an organization that users belong to.
    """
    name = models.CharField(max_length=255, unique=True, help_text="The name of the organization.")
    description = models.CharField(max_length=255, unique=True, null=True, help_text="The description of the organization.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CustomUserManager(BaseUserManager):
    VALID_ROLES = ['staff', 'admin', 'super_admin']

    def create_user(self, username: str, email: str = None, password: str = None, role: str = 'staff', **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username: str, email: str = None, password: str = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, role='super_admin', **extra_fields)

class CustomUser(AbstractUser):
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

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.is_superuser:  # Skip validation for superusers
            if self.pk and self.role != 'staff' and self.assigned_offices.exists():
                # Clear assigned offices if role is not 'staff'
                self.assigned_offices.clear()
                # raise ValueError("Only staff users can be assigned offices.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Profile(models.Model):
    """
    Represents a user's profile, including additional information such as bio and profile picture.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Profile of {self.user.username}"
