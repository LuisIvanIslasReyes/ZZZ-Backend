"""
Recommendation serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Recommendation, RecommendationTemplate, RecommendationFeedback

User = get_user_model()


class RecommendationTemplateSerializer(serializers.ModelSerializer):
    """Recommendation template serializer"""
    
    class Meta:
        model = RecommendationTemplate
        fields = [
            'id', 'name', 'title', 'description', 'recommendation_type',
            'priority', 'trigger_conditions', 'instructions', 'duration_minutes',
            'is_active', 'created_at', 'updated_at'
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    """Recommendation serializer"""
    
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'title', 'description', 'recommendation_type', 'priority',
            'employee', 'employee_name', 'template', 'template_name',
            'instructions', 'duration_minutes', 'is_active', 'is_applied',
            'applied_at', 'effectiveness_rating', 'feedback_notes',
            'data', 'source_alert', 'created_at', 'expires_at', 'is_expired'
        ]
        read_only_fields = ['applied_at']


class RecommendationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating recommendations"""
    
    class Meta:
        model = Recommendation
        fields = [
            'title', 'description', 'recommendation_type', 'priority',
            'employee', 'template', 'instructions', 'duration_minutes',
            'data', 'source_alert', 'expires_at'
        ]


class RecommendationApplySerializer(serializers.Serializer):
    """Serializer for applying recommendations"""
    
    effectiveness_rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    feedback_notes = serializers.CharField(max_length=500, required=False, allow_blank=True)


class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    """Recommendation feedback serializer"""
    
    recommendation_title = serializers.CharField(source='recommendation.title', read_only=True)
    
    class Meta:
        model = RecommendationFeedback
        fields = [
            'id', 'recommendation', 'recommendation_title',
            'usefulness_rating', 'ease_of_implementation', 'effectiveness_rating',
            'comments', 'would_recommend', 'implementation_time_minutes',
            'obstacles_encountered', 'created_at'
        ]


class RecommendationStatsSerializer(serializers.Serializer):
    """Serializer for recommendation statistics"""
    
    total_recommendations = serializers.IntegerField()
    active_recommendations = serializers.IntegerField()
    applied_recommendations = serializers.IntegerField()
    pending_recommendations = serializers.IntegerField()
    avg_effectiveness_rating = serializers.FloatField()
    recommendations_by_type = serializers.DictField()
    recommendations_by_priority = serializers.DictField()