"""
Alert URLs
"""
from django.urls import path
from .views import (
    AlertListCreateView,
    AlertDetailView,
    AlertAcknowledgeView,
    AlertResolveView,
    AlertActiveView,
    EmployeeAlertsView,
    AlertStatsView,
    AlertRuleListCreateView,
    AlertRuleDetailView,
)

app_name = 'alerts'

urlpatterns = [
    # Alerts
    path('', AlertListCreateView.as_view(), name='alert_list'),
    path('<int:pk>/', AlertDetailView.as_view(), name='alert_detail'),
    path('<int:pk>/acknowledge/', AlertAcknowledgeView.as_view(), name='alert_acknowledge'),
    path('<int:pk>/resolve/', AlertResolveView.as_view(), name='alert_resolve'),
    path('active/', AlertActiveView.as_view(), name='alert_active'),
    path('stats/', AlertStatsView.as_view(), name='alert_stats'),
    
    # Employee alerts
    path('employees/<int:employee_id>/', EmployeeAlertsView.as_view(), name='employee_alerts'),
    
    # Alert rules
    path('rules/', AlertRuleListCreateView.as_view(), name='alert_rule_list'),
    path('rules/<int:pk>/', AlertRuleDetailView.as_view(), name='alert_rule_detail'),
]