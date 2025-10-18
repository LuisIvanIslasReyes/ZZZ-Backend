"""
Recommendation views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Recommendation, RecommendationTemplate, RecommendationFeedback
from .serializers import (
    RecommendationSerializer,
    RecommendationCreateSerializer,
    RecommendationApplySerializer,
    RecommendationTemplateSerializer,
    RecommendationFeedbackSerializer,
    RecommendationStatsSerializer
)
from apps.authentication.permissions import IsOwnerOrSupervisor, IsSupervisor

User = get_user_model()


class RecommendationListCreateView(generics.ListCreateAPIView):
    """
    List all recommendations or create a new recommendation
    GET/POST /api/recommendations/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecommendationCreateSerializer
        return RecommendationSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Recommendation.objects.select_related('employee', 'template')
        
        # Filter by user role
        if user.is_admin:
            # Admin can see all recommendations
            pass
        elif user.is_supervisor:
            # Supervisor can see recommendations of supervised employees
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            queryset = queryset.filter(employee__in=supervised_employees)
        else:
            # Employee can only see their own recommendations
            queryset = queryset.filter(employee=user)
        
        # Query parameters
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        is_applied = self.request.query_params.get('is_applied')
        if is_applied is not None:
            queryset = queryset.filter(is_applied=is_applied.lower() == 'true')
        
        recommendation_type = self.request.query_params.get('recommendation_type')
        if recommendation_type:
            queryset = queryset.filter(recommendation_type=recommendation_type)
        
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Exclude expired recommendations unless specifically requested
        include_expired = self.request.query_params.get('include_expired', 'false')
        if include_expired.lower() != 'true':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        return queryset.order_by('-created_at')


class RecommendationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a recommendation
    GET/PUT/DELETE /api/recommendations/<id>/
    """
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Recommendation.objects.select_related('employee', 'template')
        
        if user.is_admin:
            return queryset
        elif user.is_supervisor:
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            return queryset.filter(employee__in=supervised_employees)
        else:
            return queryset.filter(employee=user)


class RecommendationApplyView(APIView):
    """
    Mark a recommendation as applied
    PUT /api/recommendations/<id>/apply/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def put(self, request, pk):
        try:
            recommendation = Recommendation.objects.get(pk=pk)
        except Recommendation.DoesNotExist:
            return Response(
                {'error': 'Recomendación no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if not (user.is_admin or user.is_supervisor or recommendation.employee == user):
            return Response(
                {'error': 'Sin permisos para esta recomendación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if recommendation.is_applied:
            return Response(
                {'error': 'La recomendación ya fue aplicada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if recommendation.is_expired:
            return Response(
                {'error': 'La recomendación ha expirado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RecommendationApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Apply the recommendation
        recommendation.mark_as_applied(
            effectiveness_rating=serializer.validated_data.get('effectiveness_rating'),
            feedback_notes=serializer.validated_data.get('feedback_notes')
        )
        
        return Response({
            'message': 'Recomendación aplicada exitosamente',
            'applied_at': recommendation.applied_at
        })


class EmployeeRecommendationsView(generics.ListAPIView):
    """
    Get recommendations for a specific employee
    GET /api/employees/<employee_id>/recommendations/
    """
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        user = self.request.user
        
        # Check permissions
        if not (user.is_admin or user.is_supervisor or str(user.id) == str(employee_id)):
            return Recommendation.objects.none()
        
        queryset = Recommendation.objects.filter(employee_id=employee_id).select_related('template')
        
        # Exclude expired by default
        include_expired = self.request.query_params.get('include_expired', 'false')
        if include_expired.lower() != 'true':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        return queryset.order_by('-created_at')


class RecommendationStatsView(APIView):
    """
    Get recommendation statistics
    GET /api/recommendations/stats/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request):
        user = request.user
        
        # Base queryset based on permissions
        if user.is_admin:
            queryset = Recommendation.objects.all()
        else:
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            queryset = Recommendation.objects.filter(employee__in=supervised_employees)
        
        # Date filter
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=start_date)
        
        # Calculate stats
        total_recommendations = queryset.count()
        active_recommendations = queryset.filter(is_active=True).count()
        applied_recommendations = queryset.filter(is_applied=True).count()
        pending_recommendations = queryset.filter(is_active=True, is_applied=False).count()
        
        # Average effectiveness rating
        avg_effectiveness = queryset.filter(
            effectiveness_rating__isnull=False
        ).aggregate(avg=Avg('effectiveness_rating'))['avg'] or 0
        
        # Recommendations by type
        recommendations_by_type = dict(
            queryset.values('recommendation_type').annotate(
                count=Count('id')
            ).values_list('recommendation_type', 'count')
        )
        
        # Recommendations by priority
        recommendations_by_priority = dict(
            queryset.values('priority').annotate(
                count=Count('id')
            ).values_list('priority', 'count')
        )
        
        stats = {
            'total_recommendations': total_recommendations,
            'active_recommendations': active_recommendations,
            'applied_recommendations': applied_recommendations,
            'pending_recommendations': pending_recommendations,
            'avg_effectiveness_rating': round(avg_effectiveness, 2),
            'recommendations_by_type': recommendations_by_type,
            'recommendations_by_priority': recommendations_by_priority
        }
        
        serializer = RecommendationStatsSerializer(stats)
        return Response(serializer.data)


# Template Views
class RecommendationTemplateListCreateView(generics.ListCreateAPIView):
    """
    List all recommendation templates or create a new template
    GET/POST /api/recommendations/templates/
    """
    serializer_class = RecommendationTemplateSerializer
    permission_classes = [IsSupervisor]
    queryset = RecommendationTemplate.objects.filter(is_active=True)


class RecommendationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a recommendation template
    GET/PUT/DELETE /api/recommendations/templates/<id>/
    """
    serializer_class = RecommendationTemplateSerializer
    permission_classes = [IsSupervisor]
    queryset = RecommendationTemplate.objects.all()


# Feedback Views
class RecommendationFeedbackListCreateView(generics.ListCreateAPIView):
    """
    List all recommendation feedback or create new feedback
    GET/POST /api/recommendations/feedback/
    """
    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin:
            return RecommendationFeedback.objects.all()
        elif user.is_supervisor:
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            return RecommendationFeedback.objects.filter(
                recommendation__employee__in=supervised_employees
            )
        else:
            return RecommendationFeedback.objects.filter(recommendation__employee=user)


class RecommendationFeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete recommendation feedback
    GET/PUT/DELETE /api/recommendations/feedback/<id>/
    """
    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin:
            return RecommendationFeedback.objects.all()
        elif user.is_supervisor:
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            return RecommendationFeedback.objects.filter(
                recommendation__employee__in=supervised_employees
            )
        else:
            return RecommendationFeedback.objects.filter(recommendation__employee=user)