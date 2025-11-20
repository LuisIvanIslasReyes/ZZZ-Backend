from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'contact_email',
        'contact_phone',
        'is_active',
        'employee_count',
        'supervisor_count',
        'subscription_start',
        'subscription_end',
        'created_at'
    ]
    list_filter = ['is_active', 'subscription_start', 'created_at']
    search_fields = ['name', 'contact_email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
