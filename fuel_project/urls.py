from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from fuel_routes.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('fuel_routes.urls')),
    
    # Root healthz compatibility
    path('healthz', HealthCheckView.as_view(), name='healthz-root'),
    
    # OpenAPI 3.0 / Swagger UI documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
