"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.devices.views import DeviceViewSet
from apps.sensors.views import SensorDataViewSet, ProcessedMetricsViewSet
from apps.analytics.views import FatigueAlertViewSet, RoutineRecommendationViewSet
from apps.analytics.dashboard_views import DashboardViewSet
from apps.analytics.visualization_views import VisualizationViewSet
from apps.analytics.report_views import ReportViewSet
from apps.analytics.reports_views import ReportsViewSet
from apps.users.admin_views import AdminViewSet
from apps.users.views import EmployeeListCreateView, EmployeeDetailView

# Router para ViewSets
router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'sensor-data', SensorDataViewSet, basename='sensordata')
router.register(r'processed-metrics', ProcessedMetricsViewSet, basename='processedmetrics')
router.register(r'alerts', FatigueAlertViewSet, basename='fatiguealert')
router.register(r'recommendations', RoutineRecommendationViewSet, basename='routinerecommendation')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'visualizations', VisualizationViewSet, basename='visualization')
router.register(r'reports', ReportsViewSet, basename='reports')
router.register(r'admin', AdminViewSet, basename='admin')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    # Rutas de administración de empresas
    path('api/admin/', include('apps.companies.urls')),
    # Rutas adicionales para compatibilidad con el frontend
    path('api/supervisor/employees/', EmployeeListCreateView.as_view(), name='employee_list_create_api'),
    path('api/supervisor/employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail_api'),
    path('api/', include(router.urls)),
    
    # OpenAPI/Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
