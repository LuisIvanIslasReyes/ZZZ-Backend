"""
Configuration URLs
"""
from django.urls import path
from .views import (
    ConfigurationListView,
    ConfigurationDetailView,
    ThresholdListCreateView,
    ThresholdDetailView,
    NotificationSettingsView,
    UserNotificationSettingsView,
    SystemConfigView,
    ConfigurationCategoriesView,
    ResetConfigurationView,
)

app_name = 'configuration'

urlpatterns = [
    # Configurations
    path('', ConfigurationListView.as_view(), name='config_list'),
    path('<str:key>/', ConfigurationDetailView.as_view(), name='config_detail'),
    path('categories/', ConfigurationCategoriesView.as_view(), name='config_categories'),
    path('reset/', ResetConfigurationView.as_view(), name='config_reset'),
    
    # Thresholds
    path('thresholds/', ThresholdListCreateView.as_view(), name='threshold_list'),
    path('thresholds/<int:pk>/', ThresholdDetailView.as_view(), name='threshold_detail'),
    
    # Notification settings
    path('notifications/', NotificationSettingsView.as_view(), name='notification_settings'),
    path('notifications/<int:user_id>/', UserNotificationSettingsView.as_view(), name='user_notification_settings'),
    
    # System configuration
    path('system/', SystemConfigView.as_view(), name='system_config'),
]