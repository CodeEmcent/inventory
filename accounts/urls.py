from django.urls import path
from .views import RegisterUserView
from .views import LogoutView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
