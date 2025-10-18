from django.contrib import admin
from .models import Device, SensorPacket, SensorSample, StressAggregate


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['hardware_id', 'employee', 'device_type', 'is_active', 'last_seen', 'created_at']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['hardware_id', 'employee__email', 'employee__first_name', 'employee__last_name']
    raw_id_fields = ['employee']
    ordering = ['-created_at']


@admin.register(SensorPacket)
class SensorPacketAdmin(admin.ModelAdmin):
    list_display = ['id', 'device', 'packet_timestamp', 'received_at', 'processed']
    list_filter = ['processed', 'received_at']
    search_fields = ['device__hardware_id']
    raw_id_fields = ['device']
    ordering = ['-received_at']


@admin.register(SensorSample)
class SensorSampleAdmin(admin.ModelAdmin):
    list_display = ['id', 'packet', 'sample_time', 'heart_rate', 'spo2', 'steps']
    list_filter = ['sample_time']
    raw_id_fields = ['packet']
    ordering = ['-sample_time']


@admin.register(StressAggregate)
class StressAggregateAdmin(admin.ModelAdmin):
    list_display = ['id', 'employee', 'window_start', 'stress_score', 'confidence', 'sample_count']
    list_filter = ['window_start', 'method_version']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']
    raw_id_fields = ['employee']
    ordering = ['-window_start']
