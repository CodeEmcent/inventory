from django.urls import path
from .views import (
    RegisterUserView,
    UserProfileView,
    ProfilePictureUploadView,
    AllUsersView,
    UserDetailView,
    AssignOfficesView,
    RemoveOfficesView,
    StaffAndOfficesView,
    LogoutView,
    UpdateUserView,
    DeleteUserView,
    
)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile-picture/', ProfilePictureUploadView.as_view(), name='profile-picture-upload'),
    path('all-staff/', AllUsersView.as_view(), name='all-staff'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user_detail'),
    path('update/<int:user_id>/', UpdateUserView.as_view(), name='update_user'),
    path('delete/<int:user_id>/', DeleteUserView.as_view(), name='delete_user'),
    path('assign-offices/<int:user_id>/', AssignOfficesView.as_view(), name='get-assigned-offices'),  # GET to get a specific user's assigned offices
    path('remove-office-assignment/', RemoveOfficesView.as_view(), name='remove-office-assignment'),  # GET to get all staff users and their assigned offices
    path('assign-offices/', AssignOfficesView.as_view(), name='get-all-staff-offices'),  # GET to get all staff users and their assigned offices
    path('staff-and-offices/', StaffAndOfficesView.as_view(), name='staff-and-offices'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
