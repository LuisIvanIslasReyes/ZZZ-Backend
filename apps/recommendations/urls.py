"""
Recommendation URLs
"""
from django.urls import path
from .views import (
    RecommendationListCreateView,
    RecommendationDetailView,
    RecommendationApplyView,
    EmployeeRecommendationsView,
    RecommendationStatsView,
    RecommendationTemplateListCreateView,
    RecommendationTemplateDetailView,
    RecommendationFeedbackListCreateView,
    RecommendationFeedbackDetailView,
)

app_name = 'recommendations'

urlpatterns = [
    # Recommendations
    path('', RecommendationListCreateView.as_view(), name='recommendation_list'),
    path('<int:pk>/', RecommendationDetailView.as_view(), name='recommendation_detail'),
    path('<int:pk>/apply/', RecommendationApplyView.as_view(), name='recommendation_apply'),
    path('stats/', RecommendationStatsView.as_view(), name='recommendation_stats'),
    
    # Employee recommendations
    path('employees/<int:employee_id>/', EmployeeRecommendationsView.as_view(), name='employee_recommendations'),
    
    # Templates
    path('templates/', RecommendationTemplateListCreateView.as_view(), name='recommendation_template_list'),
    path('templates/<int:pk>/', RecommendationTemplateDetailView.as_view(), name='recommendation_template_detail'),
    
    # Feedback
    path('feedback/', RecommendationFeedbackListCreateView.as_view(), name='recommendation_feedback_list'),
    path('feedback/<int:pk>/', RecommendationFeedbackDetailView.as_view(), name='recommendation_feedback_detail'),
]