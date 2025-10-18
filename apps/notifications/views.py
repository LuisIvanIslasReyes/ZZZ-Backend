"""
Notification views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta, datetime

from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationPreference,
    NotificationType,
    NotificationChannel
)
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationTemplateSerializer,
    NotificationPreferenceSerializer,
    NotificationStatsSerializer,
    SendNotificationSerializer
)
from apps.authentication.permissions import IsSupervisor

User = get_user_model()


class NotificationListView(generics.ListAPIView):
    """
    List notifications for current user
    GET /api/notifications/
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Date range filter
        days = self.request.query_params.get('days')
        if days:
            start_date = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(created_at__gte=start_date)
        
        return queryset.select_related('sender', 'recipient').order_by('-created_at')


class NotificationDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific notification
    GET /api/notifications/<id>/
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Automatically mark notification as read when retrieved"""
        instance = self.get_object()
        instance.mark_as_read()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    """
    Mark notification(s) as read
    PUT /api/notifications/<id>/read/ or PUT /api/notifications/mark-read/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, pk=None):
        user = request.user
        
        if pk:
            # Mark single notification as read
            try:
                notification = Notification.objects.get(
                    id=pk,
                    recipient=user
                )
                notification.mark_as_read()
                return Response({'message': 'Notificación marcada como leída'})
            except Notification.DoesNotExist:
                return Response(
                    {'error': 'Notificación no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Mark multiple notifications as read
            notification_ids = request.data.get('notification_ids', [])
            
            if notification_ids:
                # Mark specific notifications
                count = Notification.objects.filter(
                    id__in=notification_ids,
                    recipient=user,
                    is_read=False
                ).update(
                    is_read=True,
                    read_at=timezone.now()
                )
            else:
                # Mark all unread notifications as read
                count = Notification.objects.filter(
                    recipient=user,
                    is_read=False
                ).update(
                    is_read=True,
                    read_at=timezone.now()
                )
            
            return Response({
                'message': f'{count} notificaciones marcadas como leídas'
            })


class NotificationStatsView(APIView):
    """
    Get notification statistics for current user
    GET /api/notifications/stats/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Base queryset
        notifications = Notification.objects.filter(recipient=user)
        
        # Basic stats
        total_notifications = notifications.count()
        unread_notifications = notifications.filter(is_read=False).count()
        notifications_today = notifications.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Notifications by type
        notifications_by_type = dict(
            notifications.values('notification_type').annotate(
                count=Count('id')
            ).values_list('notification_type', 'count')
        )
        
        # Notifications by priority
        notifications_by_priority = dict(
            notifications.values('priority').annotate(
                count=Count('id')
            ).values_list('priority', 'count')
        )
        
        # Delivery success rate (simplified calculation)
        sent_notifications = notifications.exclude(sent_at__isnull=True)
        delivery_success_rate = 100.0
        if sent_notifications.exists():
            # This would be calculated based on actual delivery status
            delivery_success_rate = 95.0  # Placeholder
        
        data = {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'notifications_today': notifications_today,
            'notifications_by_type': notifications_by_type,
            'notifications_by_priority': notifications_by_priority,
            'delivery_success_rate': delivery_success_rate
        }
        
        serializer = NotificationStatsSerializer(data)
        return Response(serializer.data)


class SendNotificationView(APIView):
    """
    Send notification to users (supervisors only)
    POST /api/notifications/send/
    """
    permission_classes = [IsSupervisor]
    
    def post(self, request):
        serializer = SendNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Get recipients
        recipient_ids = data['recipients']
        recipients = User.objects.filter(id__in=recipient_ids)
        
        # Check permissions for recipients
        if not request.user.is_admin:
            # Supervisor can only send to supervised employees
            supervised_employees = User.objects.filter(
                employee_profile__supervisor=request.user
            )
            recipients = recipients.filter(id__in=supervised_employees)
        
        if not recipients.exists():
            return Response(
                {'error': 'No hay destinatarios válidos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create notifications
        notifications_created = []
        for recipient in recipients:
            notification = Notification.objects.create(
                title=data['title'],
                message=data['message'],
                notification_type=data['notification_type'],
                priority=data['priority'],
                recipient=recipient,
                sender=request.user,
                channels=data.get('channels', []),
                data=data.get('data', {}),
                scheduled_for=data.get('scheduled_for')
            )
            notifications_created.append(notification.id)
        
        return Response({
            'message': f'Notificaciones creadas para {len(notifications_created)} usuarios',
            'notification_ids': notifications_created
        }, status=status.HTTP_201_CREATED)


# Notification Templates Views
class NotificationTemplateListCreateView(generics.ListCreateAPIView):
    """
    List all notification templates or create a new template
    GET/POST /api/notifications/templates/
    """
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsSupervisor]
    queryset = NotificationTemplate.objects.filter(is_active=True)


class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a notification template
    GET/PUT/DELETE /api/notifications/templates/<id>/
    """
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsSupervisor]
    queryset = NotificationTemplate.objects.all()


class NotificationTemplateRenderView(APIView):
    """
    Preview notification template with context
    POST /api/notifications/templates/<id>/render/
    """
    permission_classes = [IsSupervisor]
    
    def post(self, request, pk):
        try:
            template = NotificationTemplate.objects.get(id=pk)
        except NotificationTemplate.DoesNotExist:
            return Response(
                {'error': 'Template no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        context = request.data.get('context', {})
        
        try:
            title, message = template.render(context)
            return Response({
                'rendered_title': title,
                'rendered_message': message,
                'available_variables': template.available_variables
            })
        except Exception as e:
            return Response(
                {'error': f'Error al renderizar template: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


# Notification Preferences Views
class NotificationPreferenceListView(generics.ListAPIView):
    """
    List notification preferences for current user
    GET /api/notifications/preferences/
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Create default preferences if they don't exist
        for notification_type in NotificationType.values:
            NotificationPreference.objects.get_or_create(
                user=user,
                notification_type=notification_type
            )
        
        return NotificationPreference.objects.filter(user=user)


class NotificationPreferenceDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a specific notification preference
    GET/PUT /api/notifications/preferences/<id>/
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)


class NotificationPreferenceBulkUpdateView(APIView):
    """
    Bulk update notification preferences
    PUT /api/notifications/preferences/bulk/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request):
        user = request.user
        preferences_data = request.data.get('preferences', [])
        
        updated_count = 0
        errors = []
        
        for pref_data in preferences_data:
            try:
                preference = NotificationPreference.objects.get(
                    user=user,
                    id=pref_data.get('id')
                )
                
                serializer = NotificationPreferenceSerializer(
                    preference,
                    data=pref_data,
                    partial=True
                )
                
                if serializer.is_valid():
                    serializer.save()
                    updated_count += 1
                else:
                    errors.append({
                        'id': pref_data.get('id'),
                        'errors': serializer.errors
                    })
            except NotificationPreference.DoesNotExist:
                errors.append({
                    'id': pref_data.get('id'),
                    'errors': ['Preference not found']
                })
        
        return Response({
            'message': f'Actualizadas {updated_count} preferencias',
            'updated_count': updated_count,
            'errors': errors
        })


class NotificationHistoryView(generics.ListAPIView):
    """
    Get notification history (for supervisors)
    GET /api/notifications/history/
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsSupervisor]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin:
            # Admin can see all notifications
            queryset = Notification.objects.all()
        else:
            # Supervisor can see notifications sent by them or to supervised employees
            supervised_employees = User.objects.filter(
                employee_profile__supervisor=user
            )
            queryset = Notification.objects.filter(
                Q(sender=user) | Q(recipient__in=supervised_employees)
            )
        
        # Filters
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        recipient_id = self.request.query_params.get('recipient_id')
        if recipient_id:
            queryset = queryset.filter(recipient_id=recipient_id)
        
        days = self.request.query_params.get('days', 30)
        start_date = timezone.now() - timedelta(days=int(days))
        queryset = queryset.filter(created_at__gte=start_date)
        
        return queryset.select_related('sender', 'recipient').order_by('-created_at')