"""
Department admin
"""
from django.contrib import admin
from .models import Department, DepartmentMembership, WorkShift, ShiftAssignment


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'manager', 'parent_department', 'employee_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'parent_department']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at', 'employee_count']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'code')
        }),
        ('Jerarquía', {
            'fields': ('parent_department', 'manager')
        }),
        ('Contacto', {
            'fields': ('location', 'email', 'phone')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DepartmentMembership)
class DepartmentMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'position', 'is_primary', 'joined_at', 'left_at']
    list_filter = ['is_primary', 'joined_at', 'left_at', 'department']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'department__name']
    readonly_fields = ['joined_at']


@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'start_time', 'end_time', 'duration_hours', 'is_active', 'created_at']
    list_filter = ['is_active', 'department', 'created_at']
    search_fields = ['name', 'description', 'department__name']
    readonly_fields = ['created_at', 'updated_at', 'duration_hours']


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'work_shift', 'start_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['is_active', 'start_date', 'end_date', 'work_shift__department']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'work_shift__name']
    readonly_fields = ['created_at']