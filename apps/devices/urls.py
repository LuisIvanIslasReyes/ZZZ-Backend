"""
URLs for devices app
"""
from django.urls import path
from .views import (
    DeviceListCreateView,
    DeviceDetailView,
    BatchSensorDataView,
    EmployeeStressView,
    EmployeeStressSummaryView,
    SupervisorReportsView,
)

app_name = 'devices'

urlpatterns = [
    # Devices
    path('devices/', DeviceListCreateView.as_view(), name='device_list'),
    path('devices/<int:pk>/', DeviceDetailView.as_view(), name='device_detail'),
    
    # Sensor data ingestion
    path('sensor-data/', BatchSensorDataView.as_view(), name='sensor_data_batch'),
    
    # Stress data
    path('employees/<int:employee_id>/stress/', EmployeeStressView.as_view(), name='employee_stress'),
    path('employees/<int:employee_id>/stress/summary/', EmployeeStressSummaryView.as_view(), name='employee_stress_summary'),
    
    # Supervisor reports
    path('supervisor/reports/', SupervisorReportsView.as_view(), name='supervisor_reports'),
]
