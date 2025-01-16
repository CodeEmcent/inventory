from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from accounts.serializers import CustomTokenObtainPairView

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path("admin/", admin.site.urls),
    path("api/users/", include("accounts.urls")),
    path('api/', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
