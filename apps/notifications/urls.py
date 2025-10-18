"""
Notification URLs
"""
from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    NotificationMarkReadView,
    NotificationStatsView,
    SendNotificationView,
    NotificationTemplateListCreateView,
    NotificationTemplateDetailView,
    NotificationTemplateRenderView,
    NotificationPreferenceListView,
    NotificationPreferenceDetailView,
    NotificationPreferenceBulkUpdateView,
    NotificationHistoryView,
)

app_name = 'notifications'

urlpatterns = [
    # Notifications
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification_detail'),
    path('<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('mark-read/', NotificationMarkReadView.as_view(), name='notification_bulk_mark_read'),
    path('stats/', NotificationStatsView.as_view(), name='notification_stats'),
    path('send/', SendNotificationView.as_view(), name='send_notification'),
    path('history/', NotificationHistoryView.as_view(), name='notification_history'),
    
    # Templates
    path('templates/', NotificationTemplateListCreateView.as_view(), name='notification_template_list'),
    path('templates/<int:pk>/', NotificationTemplateDetailView.as_view(), name='notification_template_detail'),
    path('templates/<int:pk>/render/', NotificationTemplateRenderView.as_view(), name='notification_template_render'),
    
    # Preferences
    path('preferences/', NotificationPreferenceListView.as_view(), name='notification_preference_list'),
    path('preferences/<int:pk>/', NotificationPreferenceDetailView.as_view(), name='notification_preference_detail'),
    path('preferences/bulk/', NotificationPreferenceBulkUpdateView.as_view(), name='notification_preference_bulk'),
]