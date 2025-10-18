"""
Analytics admin
"""
from django.contrib import admin
from .models import AnalyticsReport


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'employee', 'department', 'generated_by', 'created_at']
    list_filter = ['report_type', 'created_at']
    search_fields = ['name', 'employee__email', 'department__name']
    readonly_fields = ['created_at']