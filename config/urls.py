from django.contrib import admin
from django.urls import path, include
from accounts.views import CustomTokenObtainPairView

from django.http import JsonResponse

from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework_simplejwt.views import TokenRefreshView

#Static Configuration
from django.conf.urls.static import static
from django.conf import settings

def welcome(request):
    return JsonResponse(
        {
            "name": "EmcentVault API Documentation",
            "message": "Welcome. To View EmcentVault API Documentation, Click the Link Below.",
            # "url": "",
            "status": 200,
        }
    )

schema_view = get_schema_view(
    openapi.Info(
        title="EmcentVault API Documentation",
        default_version='v1',
        description="This is the documentation to my EmcentVault API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="mcinnobezzy@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
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
