from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import CustomUser, Office
from accounts.models import InventoryItem

class InventoryPermissionsTest(APITestCase):

    def setUp(self):
        # Create offices
        self.office1 = Office.objects.create(name="Office 1")
        self.office2 = Office.objects.create(name="Office 2")

        # Create users
        self.staff_user = CustomUser.objects.create_user(
            username="staff", password="test123", role="staff"
        )
        self.staff_user.assigned_offices.add(self.office1)

        self.admin_user = CustomUser.objects.create_user(
            username="admin", password="test123", role="admin"
        )
        
        self.superadmin_user = CustomUser.objects.create_user(
            username="superadmin", password="test123", role="super_admin"
        )

        # Create inventory items
        self.item1 = InventoryItem.objects.create(
            name="Laptop", quantity=10, user=self.staff_user, office=self.office1
        )
        self.item2 = InventoryItem.objects.create(
            name="Projector", quantity=5, user=self.staff_user, office=self.office2
        )

    def test_staff_access(self):
        self.client.login(username="staff", password="test123")

        # Staff can see items only in assigned offices
        response = self.client.get("/api/inventory/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should see only `item1`

        # Staff cannot delete item outside assigned office
        response = self.client.delete(f"/api/inventory/{self.item2.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access(self):
        self.client.login(username="admin", password="test123")

        # Admin can see all items
        response = self.client.get("/api/inventory/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Admin can delete any item
        response = self.client.delete(f"/api/inventory/{self.item2.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_superadmin_access(self):
        self.client.login(username="superadmin", password="test123")

        # Superadmin can see all items
        response = self.client.get("/api/inventory/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Superadmin can delete any item
        response = self.client.delete(f"/api/inventory/{self.item1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class BroadsheetTest(APITestCase):

    def setUp(self):
        # Reuse setup code from above
        # Add duplicate items for testing aggregation
        InventoryItem.objects.create(name="Laptop", quantity=5, user=self.staff_user, office=self.office2)

    def test_broadsheet_access(self):
        # Test with Admin
        self.client.login(username="admin", password="test123")
        response = self.client.get("/api/inventory/broadsheet/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Validate aggregated data
        expected_data = [
            {"name": "Laptop", "total_quantity": 15},
            {"name": "Projector", "total_quantity": 5},
        ]
        self.assertEqual(response.json(), expected_data)

        # Test with Staff (should be forbidden)
        self.client.login(username="staff", password="test123")
        response = self.client.get("/api/inventory/broadsheet/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TemplateDownloadTest(APITestCase):

    def setUp(self):
        self.staff_user = CustomUser.objects.create_user(
            username="staff", password="test123", role="staff"
        )

    def test_template_download_authenticated(self):
        self.client.login(username="staff", password="test123")
        response = self.client.get("/api/inventory/template/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Disposition"], "attachment; filename=inventory_template.xlsx"
        )

    def test_template_download_unauthenticated(self):
        response = self.client.get("/api/inventory/template/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
