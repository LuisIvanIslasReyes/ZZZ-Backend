"""
Analytics serializers
"""
from rest_framework import serializers


class PatternAnalysisSerializer(serializers.Serializer):
    """Serializer for pattern analysis results"""
    
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    patterns = serializers.DictField()
    peak_stress_hours = serializers.ListField()
    average_stress_by_hour = serializers.DictField()
    stress_trend = serializers.CharField()
    fatigue_indicators = serializers.DictField()


class ComparativeAnalysisSerializer(serializers.Serializer):
    """Serializer for comparative analysis"""
    
    comparison_type = serializers.CharField()
    baseline_period = serializers.DictField()
    comparison_period = serializers.DictField()
    employees = serializers.ListField()
    metrics = serializers.DictField()
    insights = serializers.ListField()


class TrendAnalysisSerializer(serializers.Serializer):
    """Serializer for trend analysis"""
    
    period = serializers.CharField()
    entity_type = serializers.CharField()  # department, shift, employee
    entity_id = serializers.IntegerField(required=False)
    trends = serializers.DictField()
    predictions = serializers.DictField()
    recommendations = serializers.ListField()


class HistoricalAnalysisSerializer(serializers.Serializer):
    """Serializer for historical analysis"""
    
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    time_range = serializers.DictField()
    metrics = serializers.DictField()
    milestones = serializers.ListField()
    progression = serializers.DictField()


class PredictionAnalysisSerializer(serializers.Serializer):
    """Serializer for prediction analysis"""
    
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    prediction_horizon_hours = serializers.IntegerField()
    predicted_stress_levels = serializers.ListField()
    risk_assessment = serializers.DictField()
    recommended_actions = serializers.ListField()


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    total_employees = serializers.IntegerField()
    active_devices = serializers.IntegerField()
    avg_stress_level = serializers.FloatField()
    high_risk_employees = serializers.IntegerField()
    alerts_today = serializers.IntegerField()
    recommendations_pending = serializers.IntegerField()
    
    # Charts data
    stress_distribution = serializers.DictField()
    hourly_stress_trend = serializers.ListField()
    department_comparison = serializers.ListField()
    alert_trends = serializers.ListField()