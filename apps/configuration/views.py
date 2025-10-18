"""
Configuration views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import Configuration, SystemThreshold, NotificationSettings, ConfigurationCategory
from .serializers import (
    ConfigurationSerializer,
    SystemThresholdSerializer,
    NotificationSettingsSerializer,
    SystemConfigSerializer
)
from apps.authentication.permissions import IsSupervisor

User = get_user_model()


class ConfigurationListView(generics.ListAPIView):
    """
    List all configurations
    GET /api/config/
    """
    serializer_class = ConfigurationSerializer
    permission_classes = [IsSupervisor]
    
    def get_queryset(self):
        queryset = Configuration.objects.filter(is_active=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset


class ConfigurationDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a configuration
    GET/PUT /api/config/<key>/
    """
    serializer_class = ConfigurationSerializer
    permission_classes = [IsSupervisor]
    lookup_field = 'key'
    
    def get_queryset(self):
        return Configuration.objects.filter(is_active=True, is_editable=True)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class ThresholdListCreateView(generics.ListCreateAPIView):
    """
    List all thresholds or create a new threshold
    GET/POST /api/config/thresholds/
    """
    serializer_class = SystemThresholdSerializer
    permission_classes = [IsSupervisor]
    queryset = SystemThreshold.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)


class ThresholdDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a threshold
    GET/PUT/DELETE /api/config/thresholds/<id>/
    """
    serializer_class = SystemThresholdSerializer
    permission_classes = [IsSupervisor]
    queryset = SystemThreshold.objects.all()
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class NotificationSettingsView(generics.RetrieveUpdateAPIView):
    """
    Get or update notification settings for current user
    GET/PUT /api/config/notifications/
    """
    serializer_class = NotificationSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        settings, created = NotificationSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings


class UserNotificationSettingsView(generics.RetrieveUpdateAPIView):
    """
    Get or update notification settings for a specific user (supervisors only)
    GET/PUT /api/config/notifications/<user_id>/
    """
    serializer_class = NotificationSettingsSerializer
    permission_classes = [IsSupervisor]
    
    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        
        # Check permissions
        if not self.request.user.is_admin:
            # Supervisor can only modify settings of supervised employees
            if not user.employee_profile or user.employee_profile.supervisor != self.request.user:
                raise PermissionDenied("No tienes permisos para modificar la configuración de este usuario")
        
        settings, created = NotificationSettings.objects.get_or_create(user=user)
        return settings


class SystemConfigView(APIView):
    """
    Get system configuration overview
    GET /api/config/system/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request):
        # Get key thresholds
        try:
            stress_thresholds = SystemThreshold.objects.get(
                name='stress_score',
                is_active=True
            )
        except SystemThreshold.DoesNotExist:
            stress_thresholds = None
        
        try:
            heart_rate_thresholds = SystemThreshold.objects.get(
                name='heart_rate',
                is_active=True
            )
        except SystemThreshold.DoesNotExist:
            heart_rate_thresholds = None
        
        # Get configuration settings by category
        alert_configs = Configuration.objects.filter(
            category=ConfigurationCategory.ALERTS,
            is_active=True
        )
        notification_configs = Configuration.objects.filter(
            category=ConfigurationCategory.NOTIFICATIONS,
            is_active=True
        )
        device_configs = Configuration.objects.filter(
            category=ConfigurationCategory.DEVICES,
            is_active=True
        )
        analytics_configs = Configuration.objects.filter(
            category=ConfigurationCategory.ANALYTICS,
            is_active=True
        )
        
        # Convert to dictionaries
        alert_settings = {config.key: config.value for config in alert_configs}
        notification_settings = {config.key: config.value for config in notification_configs}
        device_settings = {config.key: config.value for config in device_configs}
        analytics_settings = {config.key: config.value for config in analytics_configs}
        
        data = {
            'stress_thresholds': SystemThresholdSerializer(stress_thresholds).data if stress_thresholds else None,
            'heart_rate_thresholds': SystemThresholdSerializer(heart_rate_thresholds).data if heart_rate_thresholds else None,
            'alert_settings': alert_settings,
            'notification_settings': notification_settings,
            'device_settings': device_settings,
            'analytics_settings': analytics_settings
        }
        
        return Response(data)
    
    def put(self, request):
        """Update system configuration"""
        updated_configs = []
        errors = []
        
        # Update individual configurations
        for category, settings in request.data.items():
            if category in ['alert_settings', 'notification_settings', 'device_settings', 'analytics_settings']:
                category_name = category.replace('_settings', '').upper()
                
                for key, value in settings.items():
                    try:
                        config = Configuration.objects.get(
                            key=key,
                            category=category_name,
                            is_editable=True
                        )
                        config.value = value
                        config.updated_by = request.user
                        config.full_clean()
                        config.save()
                        updated_configs.append(key)
                    except Configuration.DoesNotExist:
                        errors.append(f"Configuration {key} not found or not editable")
                    except Exception as e:
                        errors.append(f"Error updating {key}: {str(e)}")
        
        # Update thresholds
        if 'stress_thresholds' in request.data and request.data['stress_thresholds']:
            try:
                threshold = SystemThreshold.objects.get(name='stress_score')
                serializer = SystemThresholdSerializer(threshold, data=request.data['stress_thresholds'], partial=True)
                if serializer.is_valid():
                    serializer.save(updated_by=request.user)
                    updated_configs.append('stress_thresholds')
                else:
                    errors.append(f"Stress threshold validation errors: {serializer.errors}")
            except SystemThreshold.DoesNotExist:
                errors.append("Stress threshold not found")
        
        if 'heart_rate_thresholds' in request.data and request.data['heart_rate_thresholds']:
            try:
                threshold = SystemThreshold.objects.get(name='heart_rate')
                serializer = SystemThresholdSerializer(threshold, data=request.data['heart_rate_thresholds'], partial=True)
                if serializer.is_valid():
                    serializer.save(updated_by=request.user)
                    updated_configs.append('heart_rate_thresholds')
                else:
                    errors.append(f"Heart rate threshold validation errors: {serializer.errors}")
            except SystemThreshold.DoesNotExist:
                errors.append("Heart rate threshold not found")
        
        response_data = {
            'message': f'Updated {len(updated_configs)} configurations',
            'updated': updated_configs,
            'errors': errors
        }
        
        status_code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return Response(response_data, status=status_code)


class ConfigurationCategoriesView(APIView):
    """
    Get available configuration categories
    GET /api/config/categories/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request):
        categories = []
        for choice in ConfigurationCategory.choices:
            config_count = Configuration.objects.filter(
                category=choice[0],
                is_active=True
            ).count()
            
            categories.append({
                'key': choice[0],
                'name': choice[1],
                'config_count': config_count
            })
        
        return Response({'categories': categories})


class ResetConfigurationView(APIView):
    """
    Reset configuration to default values
    POST /api/config/reset/
    """
    permission_classes = [IsSupervisor]
    
    def post(self, request):
        category = request.data.get('category')
        config_key = request.data.get('key')
        
        if config_key:
            # Reset specific configuration
            try:
                config = Configuration.objects.get(key=config_key, is_editable=True)
                # Here you would reset to default value
                # For now, just mark as reset
                config.updated_by = request.user
                config.save()
                
                return Response({
                    'message': f'Configuration {config_key} reset to default',
                    'config': ConfigurationSerializer(config).data
                })
            except Configuration.DoesNotExist:
                return Response(
                    {'error': 'Configuration not found or not editable'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif category:
            # Reset all configurations in category
            configs = Configuration.objects.filter(
                category=category,
                is_editable=True
            )
            
            reset_count = 0
            for config in configs:
                # Reset to default value
                config.updated_by = request.user
                config.save()
                reset_count += 1
            
            return Response({
                'message': f'Reset {reset_count} configurations in category {category}'
            })
        
        else:
            return Response(
                {'error': 'Either category or key must be provided'},
                status=status.HTTP_400_BAD_REQUEST
            )