"""
Recommendation admin
"""
from django.contrib import admin
from .models import Recommendation, RecommendationTemplate, RecommendationFeedback


@admin.register(RecommendationTemplate)
class RecommendationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'recommendation_type', 'priority', 'is_active', 'created_at']
    list_filter = ['recommendation_type', 'priority', 'is_active', 'created_at']
    search_fields = ['name', 'title', 'description']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'recommendation_type', 'priority', 'is_active', 'is_applied', 'created_at']
    list_filter = ['recommendation_type', 'priority', 'is_active', 'is_applied', 'created_at']
    search_fields = ['title', 'employee__email', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['created_at', 'applied_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'recommendation_type', 'priority')
        }),
        ('Relaciones', {
            'fields': ('employee', 'template', 'source_alert')
        }),
        ('Contenido', {
            'fields': ('instructions', 'duration_minutes')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_applied', 'applied_at', 'expires_at')
        }),
        ('Feedback', {
            'fields': ('effectiveness_rating', 'feedback_notes'),
            'classes': ('collapse',)
        }),
        ('Datos Adicionales', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = ['recommendation', 'usefulness_rating', 'effectiveness_rating', 'would_recommend', 'created_at']
    list_filter = ['usefulness_rating', 'effectiveness_rating', 'would_recommend', 'created_at']
    search_fields = ['recommendation__title', 'comments']