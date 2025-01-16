from django.urls import path
from .views import (
    RegisterUserView,
    UserProfileView,
    AllUsersView,
    AssignOfficesView,
    LogoutView
)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('all-staff/', AllUsersView.as_view(), name='all-staff'),
    path('assign-offices/<int:user_id>/', AssignOfficesView.as_view(), name='assign-offices'),
    path('logout/', LogoutView.as_view(), name='logout'),
]