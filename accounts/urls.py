from django.urls import path
from .views import (
    RegisterUserView,
    AllUsersView,
    AssignOfficesView,
    LogoutView
)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('all-staff/', AllUsersView.as_view(), name='all-staff'),
    path('assign-offices/<int:user_id>/', AssignOfficesView.as_view(), name='assign-offices'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
