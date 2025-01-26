from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include
from accounts.views import CustomTokenObtainPairView

from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path("admin/", admin.site.urls),
    path("api/users/", include("accounts.urls")),
    path('api/', include('core.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ] 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
