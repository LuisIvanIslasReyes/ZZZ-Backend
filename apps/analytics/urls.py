"""
Analytics URLs
"""
from django.urls import path
from .views import (
    PatternAnalysisView,
    ComparativeAnalysisView,
    TrendAnalysisView,
    HistoricalAnalysisView,
    PredictionAnalysisView,
    DashboardStatsView,
)

app_name = 'analytics'

urlpatterns = [
    # Pattern analysis
    path('patterns/<int:employee_id>/', PatternAnalysisView.as_view(), name='pattern_analysis'),
    
    # Comparative analysis
    path('comparatives/', ComparativeAnalysisView.as_view(), name='comparative_analysis'),
    
    # Trend analysis
    path('trends/', TrendAnalysisView.as_view(), name='trend_analysis'),
    
    # Historical analysis
    path('historical/<int:employee_id>/', HistoricalAnalysisView.as_view(), name='historical_analysis'),
    
    # Prediction analysis
    path('predictions/<int:employee_id>/', PredictionAnalysisView.as_view(), name='prediction_analysis'),
    
    # Dashboard stats
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard_stats'),
]