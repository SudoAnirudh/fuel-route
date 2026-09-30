from django.urls import path
from fuel_routes.views import RoutePlanView, HealthCheckView

app_name = 'fuel_routes'

urlpatterns = [
    path('api/v1/routes/plan/', RoutePlanView.as_view(), name='route-plan'),
    path('healthz', HealthCheckView.as_view(), name='health-check'),
]
