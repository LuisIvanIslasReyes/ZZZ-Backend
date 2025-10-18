"""
Analytics views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg, Min, Max
from django.utils import timezone
from datetime import timedelta, datetime
import numpy as np
from collections import defaultdict

from apps.devices.models import StressAggregate, SensorSample
from apps.alerts.models import Alert
from apps.recommendations.models import Recommendation
# from apps.departments.models import Department  # Will be available after migrations
from .serializers import (
    PatternAnalysisSerializer,
    ComparativeAnalysisSerializer,
    TrendAnalysisSerializer,
    HistoricalAnalysisSerializer,
    PredictionAnalysisSerializer,
    DashboardStatsSerializer
)
from apps.authentication.permissions import IsOwnerOrSupervisor, IsSupervisor

User = get_user_model()


class PatternAnalysisView(APIView):
    """
    Analyze patterns for an employee
    GET /api/analytics/patterns/<employee_id>/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get(self, request, employee_id):
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Empleado no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get stress aggregates
        aggregates = StressAggregate.objects.filter(
            employee=employee,
            window_start__gte=start_date
        ).order_by('window_start')
        
        if not aggregates.exists():
            return Response({
                'message': 'No hay datos suficientes para análisis de patrones',
                'employee_id': employee_id,
                'employee_name': employee.get_full_name()
            })
        
        # Analyze patterns
        stress_by_hour = defaultdict(list)
        stress_by_day = defaultdict(list)
        
        for aggregate in aggregates:
            hour = aggregate.window_start.hour
            day = aggregate.window_start.weekday()
            stress_by_hour[hour].append(aggregate.stress_score)
            stress_by_day[day].append(aggregate.stress_score)
        
        # Calculate average stress by hour
        avg_stress_by_hour = {
            hour: sum(scores) / len(scores)
            for hour, scores in stress_by_hour.items()
        }
        
        # Find peak stress hours
        sorted_hours = sorted(avg_stress_by_hour.items(), key=lambda x: x[1], reverse=True)
        peak_stress_hours = [hour for hour, _ in sorted_hours[:3]]
        
        # Determine stress trend
        recent_aggregates = aggregates.filter(
            window_start__gte=timezone.now() - timedelta(days=7)
        )
        older_aggregates = aggregates.filter(
            window_start__lt=timezone.now() - timedelta(days=7)
        )
        
        recent_avg = recent_aggregates.aggregate(avg=Avg('stress_score'))['avg'] or 0
        older_avg = older_aggregates.aggregate(avg=Avg('stress_score'))['avg'] or 0
        
        if recent_avg > older_avg + 5:
            stress_trend = 'increasing'
        elif recent_avg < older_avg - 5:
            stress_trend = 'decreasing'
        else:
            stress_trend = 'stable'
        
        # Fatigue indicators
        high_stress_periods = aggregates.filter(stress_score__gte=70).count()
        total_periods = aggregates.count()
        fatigue_frequency = (high_stress_periods / total_periods * 100) if total_periods > 0 else 0
        
        patterns = {
            'daily_patterns': {day: sum(scores) / len(scores) for day, scores in stress_by_day.items()},
            'weekly_consistency': len(set(stress_by_day.keys())) >= 5,  # Works at least 5 days
            'stress_variability': max(avg_stress_by_hour.values()) - min(avg_stress_by_hour.values()) if avg_stress_by_hour else 0
        }
        
        fatigue_indicators = {
            'high_stress_frequency_percent': round(fatigue_frequency, 2),
            'avg_stress_level': round(recent_avg, 2),
            'stress_spikes_per_week': high_stress_periods,
            'recovery_time_hours': self._calculate_recovery_time(aggregates)
        }
        
        data = {
            'employee_id': employee_id,
            'employee_name': employee.get_full_name(),
            'patterns': patterns,
            'peak_stress_hours': peak_stress_hours,
            'average_stress_by_hour': avg_stress_by_hour,
            'stress_trend': stress_trend,
            'fatigue_indicators': fatigue_indicators
        }
        
        serializer = PatternAnalysisSerializer(data)
        return Response(serializer.data)
    
    def _calculate_recovery_time(self, aggregates):
        """Calculate average recovery time from high stress"""
        recovery_times = []
        high_stress_threshold = 70
        
        stress_scores = list(aggregates.values_list('stress_score', flat=True))
        
        i = 0
        while i < len(stress_scores):
            if stress_scores[i] >= high_stress_threshold:
                # Found high stress, look for recovery
                recovery_start = i + 1
                while recovery_start < len(stress_scores) and stress_scores[recovery_start] >= high_stress_threshold:
                    recovery_start += 1
                
                if recovery_start < len(stress_scores):
                    recovery_times.append(recovery_start - i)
                i = recovery_start
            else:
                i += 1
        
        return sum(recovery_times) / len(recovery_times) if recovery_times else 0


class ComparativeAnalysisView(APIView):
    """
    Comparative analysis between employees, departments, or time periods
    GET /api/analytics/comparatives/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request):
        comparison_type = request.query_params.get('type', 'employees')
        days = int(request.query_params.get('days', 30))
        
        if comparison_type == 'employees':
            return self._compare_employees(request, days)
        elif comparison_type == 'departments':
            return self._compare_departments(request, days)
        elif comparison_type == 'time_periods':
            return self._compare_time_periods(request, days)
        else:
            return Response(
                {'error': 'Tipo de comparación no válido'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _compare_employees(self, request, days):
        user = request.user
        start_date = timezone.now() - timedelta(days=days)
        
        # Get employees based on user permissions
        if user.is_admin:
            employees = User.objects.filter(role=User.Role.EMPLOYEE)
        else:
            employees = User.objects.filter(employee_profile__supervisor=user)
        
        comparison_data = []
        
        for employee in employees:
            aggregates = StressAggregate.objects.filter(
                employee=employee,
                window_start__gte=start_date
            )
            
            if aggregates.exists():
                stats = aggregates.aggregate(
                    avg_stress=Avg('stress_score'),
                    max_stress=Max('stress_score'),
                    min_stress=Min('stress_score')
                )
                
                comparison_data.append({
                    'employee_id': employee.id,
                    'employee_name': employee.get_full_name(),
                    'avg_stress': round(stats['avg_stress'], 2),
                    'max_stress': stats['max_stress'],
                    'min_stress': stats['min_stress'],
                    'data_points': aggregates.count()
                })
        
        # Sort by average stress (highest first)
        comparison_data.sort(key=lambda x: x['avg_stress'], reverse=True)
        
        data = {
            'comparison_type': 'employees',
            'baseline_period': {'days': days, 'start_date': start_date.isoformat()},
            'comparison_period': {'end_date': timezone.now().isoformat()},
            'employees': comparison_data,
            'metrics': {
                'total_employees': len(comparison_data),
                'avg_stress_overall': sum(emp['avg_stress'] for emp in comparison_data) / len(comparison_data) if comparison_data else 0
            },
            'insights': self._generate_employee_insights(comparison_data)
        }
        
        serializer = ComparativeAnalysisSerializer(data)
        return Response(serializer.data)
    
    def _compare_departments(self, request, days):
        # Implementation for department comparison
        start_date = timezone.now() - timedelta(days=days)
        
        departments = Department.objects.all()
        comparison_data = []
        
        for dept in departments:
            employees = dept.employees.all()
            aggregates = StressAggregate.objects.filter(
                employee__in=employees,
                window_start__gte=start_date
            )
            
            if aggregates.exists():
                stats = aggregates.aggregate(
                    avg_stress=Avg('stress_score'),
                    max_stress=Max('stress_score')
                )
                
                comparison_data.append({
                    'department_id': dept.id,
                    'department_name': dept.name,
                    'employee_count': employees.count(),
                    'avg_stress': round(stats['avg_stress'], 2),
                    'max_stress': stats['max_stress'],
                    'data_points': aggregates.count()
                })
        
        data = {
            'comparison_type': 'departments',
            'baseline_period': {'days': days},
            'comparison_period': {'end_date': timezone.now().isoformat()},
            'employees': comparison_data,
            'metrics': {
                'total_departments': len(comparison_data)
            },
            'insights': []
        }
        
        serializer = ComparativeAnalysisSerializer(data)
        return Response(serializer.data)
    
    def _compare_time_periods(self, request, days):
        # Compare current period vs previous period
        current_start = timezone.now() - timedelta(days=days)
        previous_start = timezone.now() - timedelta(days=days*2)
        previous_end = current_start
        
        current_aggregates = StressAggregate.objects.filter(
            window_start__gte=current_start
        )
        previous_aggregates = StressAggregate.objects.filter(
            window_start__gte=previous_start,
            window_start__lt=previous_end
        )
        
        current_stats = current_aggregates.aggregate(
            avg_stress=Avg('stress_score'),
            max_stress=Max('stress_score'),
            count=Count('id')
        )
        
        previous_stats = previous_aggregates.aggregate(
            avg_stress=Avg('stress_score'),
            max_stress=Max('stress_score'),
            count=Count('id')
        )
        
        data = {
            'comparison_type': 'time_periods',
            'baseline_period': {
                'start_date': previous_start.isoformat(),
                'end_date': previous_end.isoformat(),
                'stats': previous_stats
            },
            'comparison_period': {
                'start_date': current_start.isoformat(),
                'end_date': timezone.now().isoformat(),
                'stats': current_stats
            },
            'employees': [],
            'metrics': {
                'stress_change_percent': self._calculate_percentage_change(
                    previous_stats['avg_stress'], current_stats['avg_stress']
                )
            },
            'insights': []
        }
        
        serializer = ComparativeAnalysisSerializer(data)
        return Response(serializer.data)
    
    def _generate_employee_insights(self, comparison_data):
        insights = []
        
        if not comparison_data:
            return insights
        
        # High stress employees
        high_stress_employees = [emp for emp in comparison_data if emp['avg_stress'] > 70]
        if high_stress_employees:
            insights.append(f"{len(high_stress_employees)} empleados con estrés alto (>70)")
        
        # Best performers
        low_stress_employees = [emp for emp in comparison_data if emp['avg_stress'] < 40]
        if low_stress_employees:
            insights.append(f"{len(low_stress_employees)} empleados con estrés bajo (<40)")
        
        return insights
    
    def _calculate_percentage_change(self, old_value, new_value):
        if old_value == 0:
            return 0
        return ((new_value - old_value) / old_value) * 100


class TrendAnalysisView(APIView):
    """
    Trend analysis for departments, shifts, or overall
    GET /api/analytics/trends/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request):
        entity_type = request.query_params.get('entity_type', 'overall')
        entity_id = request.query_params.get('entity_id')
        period = request.query_params.get('period', 'weekly')  # daily, weekly, monthly
        
        # Implementation for trend analysis
        days = {'daily': 7, 'weekly': 30, 'monthly': 90}.get(period, 30)
        start_date = timezone.now() - timedelta(days=days)
        
        # Base queryset
        aggregates = StressAggregate.objects.filter(window_start__gte=start_date)
        
        if entity_type == 'department' and entity_id:
            try:
                department = Department.objects.get(id=entity_id)
                employees = department.employees.all()
                aggregates = aggregates.filter(employee__in=employees)
            except Department.DoesNotExist:
                return Response(
                    {'error': 'Departamento no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Calculate trends
        trends = self._calculate_trends(aggregates, period)
        predictions = self._generate_predictions(trends)
        recommendations = self._generate_trend_recommendations(trends)
        
        data = {
            'period': period,
            'entity_type': entity_type,
            'entity_id': int(entity_id) if entity_id else None,
            'trends': trends,
            'predictions': predictions,
            'recommendations': recommendations
        }
        
        serializer = TrendAnalysisSerializer(data)
        return Response(serializer.data)
    
    def _calculate_trends(self, aggregates, period):
        # Group by time period and calculate averages
        trends = {
            'stress_trend': [],
            'alert_trend': [],
            'productivity_indicators': {}
        }
        
        # Implementation depends on period
        if period == 'daily':
            # Group by day
            pass
        elif period == 'weekly':
            # Group by week
            pass
        elif period == 'monthly':
            # Group by month
            pass
        
        return trends
    
    def _generate_predictions(self, trends):
        # Simple prediction based on trends
        return {
            'next_week_stress_avg': 0,
            'potential_high_risk_days': [],
            'confidence_score': 0.75
        }
    
    def _generate_trend_recommendations(self, trends):
        return [
            'Implementar pausas adicionales en horarios de alto estrés',
            'Revisar carga de trabajo en días de pico',
            'Considerar rotación de turnos'
        ]


class HistoricalAnalysisView(APIView):
    """
    Historical analysis for an employee
    GET /api/analytics/historical/<employee_id>/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get(self, request, employee_id):
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Empleado no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all historical data
        aggregates = StressAggregate.objects.filter(employee=employee).order_by('window_start')
        
        if not aggregates.exists():
            return Response({
                'message': 'No hay datos históricos disponibles',
                'employee_id': employee_id,
                'employee_name': employee.get_full_name()
            })
        
        # Calculate metrics
        time_range = {
            'start_date': aggregates.first().window_start.isoformat(),
            'end_date': aggregates.last().window_start.isoformat(),
            'total_days': (aggregates.last().window_start - aggregates.first().window_start).days
        }
        
        metrics = aggregates.aggregate(
            avg_stress=Avg('stress_score'),
            max_stress=Max('stress_score'),
            min_stress=Min('stress_score')
        )
        
        # Find milestones
        milestones = self._find_milestones(aggregates)
        
        # Calculate progression
        progression = self._calculate_progression(aggregates)
        
        data = {
            'employee_id': employee_id,
            'employee_name': employee.get_full_name(),
            'time_range': time_range,
            'metrics': {
                'total_measurements': aggregates.count(),
                'avg_stress': round(metrics['avg_stress'], 2),
                'max_stress': metrics['max_stress'],
                'min_stress': metrics['min_stress']
            },
            'milestones': milestones,
            'progression': progression
        }
        
        serializer = HistoricalAnalysisSerializer(data)
        return Response(serializer.data)
    
    def _find_milestones(self, aggregates):
        milestones = []
        
        # Find highest stress day
        max_stress = aggregates.order_by('-stress_score').first()
        if max_stress:
            milestones.append({
                'type': 'highest_stress',
                'date': max_stress.window_start.date().isoformat(),
                'value': max_stress.stress_score,
                'description': f'Nivel de estrés más alto: {max_stress.stress_score}'
            })
        
        # Find lowest stress day
        min_stress = aggregates.order_by('stress_score').first()
        if min_stress:
            milestones.append({
                'type': 'lowest_stress',
                'date': min_stress.window_start.date().isoformat(),
                'value': min_stress.stress_score,
                'description': f'Nivel de estrés más bajo: {min_stress.stress_score}'
            })
        
        return milestones
    
    def _calculate_progression(self, aggregates):
        # Calculate monthly averages for progression
        monthly_data = []
        
        # Group by month and calculate averages
        # This is a simplified version
        
        return {
            'monthly_averages': monthly_data,
            'overall_trend': 'stable',  # improving, declining, stable
            'improvement_rate': 0
        }


class PredictionAnalysisView(APIView):
    """
    Prediction analysis for employee fatigue
    GET /api/analytics/predictions/<employee_id>/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get(self, request, employee_id):
        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Empleado no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        prediction_horizon = int(request.query_params.get('hours', 24))
        
        # Get recent data for prediction
        recent_data = StressAggregate.objects.filter(
            employee=employee,
            window_start__gte=timezone.now() - timedelta(days=7)
        ).order_by('window_start')
        
        if recent_data.count() < 10:  # Need minimum data for prediction
            return Response({
                'message': 'Datos insuficientes para predicción',
                'employee_id': employee_id,
                'employee_name': employee.get_full_name()
            })
        
        # Simple prediction model (in production, use ML model)
        predicted_levels = self._predict_stress_levels(recent_data, prediction_horizon)
        risk_assessment = self._assess_risk(predicted_levels)
        recommended_actions = self._recommend_actions(risk_assessment)
        
        data = {
            'employee_id': employee_id,
            'employee_name': employee.get_full_name(),
            'prediction_horizon_hours': prediction_horizon,
            'predicted_stress_levels': predicted_levels,
            'risk_assessment': risk_assessment,
            'recommended_actions': recommended_actions
        }
        
        serializer = PredictionAnalysisSerializer(data)
        return Response(serializer.data)
    
    def _predict_stress_levels(self, recent_data, horizon_hours):
        # Simple linear prediction based on recent trend
        stress_values = list(recent_data.values_list('stress_score', flat=True))
        
        if len(stress_values) < 2:
            return []
        
        # Calculate simple trend
        recent_avg = sum(stress_values[-3:]) / 3 if len(stress_values) >= 3 else stress_values[-1]
        
        predictions = []
        for hour in range(horizon_hours):
            # Simple prediction with some randomness
            predicted_value = max(0, min(100, recent_avg + (hour * 0.5)))
            predictions.append({
                'hour': hour + 1,
                'predicted_stress': round(predicted_value, 2),
                'confidence': max(0.5, 1.0 - (hour * 0.02))  # Decreasing confidence over time
            })
        
        return predictions
    
    def _assess_risk(self, predicted_levels):
        if not predicted_levels:
            return {'risk_level': 'unknown', 'risk_score': 0}
        
        max_predicted = max(pred['predicted_stress'] for pred in predicted_levels)
        avg_predicted = sum(pred['predicted_stress'] for pred in predicted_levels) / len(predicted_levels)
        
        if max_predicted > 80 or avg_predicted > 70:
            risk_level = 'high'
            risk_score = 0.8
        elif max_predicted > 60 or avg_predicted > 50:
            risk_level = 'medium'
            risk_score = 0.5
        else:
            risk_level = 'low'
            risk_score = 0.2
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'max_predicted_stress': max_predicted,
            'avg_predicted_stress': round(avg_predicted, 2)
        }
    
    def _recommend_actions(self, risk_assessment):
        actions = []
        
        if risk_assessment['risk_level'] == 'high':
            actions = [
                'Programar descanso inmediato de 15-20 minutos',
                'Reducir carga de trabajo para las próximas 2 horas',
                'Notificar al supervisor',
                'Realizar ejercicios de respiración'
            ]
        elif risk_assessment['risk_level'] == 'medium':
            actions = [
                'Tomar descanso de 10 minutos cada hora',
                'Hidratarse adecuadamente',
                'Revisar postura de trabajo'
            ]
        else:
            actions = [
                'Mantener rutina actual',
                'Continuar monitoreo regular'
            ]
        
        return actions


class DashboardStatsView(APIView):
    """
    Dashboard statistics and overview
    GET /api/analytics/dashboard/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request):
        user = request.user
        
        # Get employees based on permissions
        if user.is_admin:
            employees = User.objects.filter(role=User.Role.EMPLOYEE)
        else:
            employees = User.objects.filter(employee_profile__supervisor=user)
        
        today = timezone.now().date()
        
        # Basic stats
        total_employees = employees.count()
        active_devices = employees.filter(devices__last_seen__date=today).distinct().count()
        
        # Recent stress data
        recent_aggregates = StressAggregate.objects.filter(
            employee__in=employees,
            window_start__date=today
        )
        
        avg_stress_level = recent_aggregates.aggregate(
            avg=Avg('stress_score')
        )['avg'] or 0
        
        high_risk_employees = recent_aggregates.filter(stress_score__gte=70).values('employee').distinct().count()
        
        # Alerts today
        alerts_today = Alert.objects.filter(
            employee__in=employees,
            created_at__date=today
        ).count()
        
        # Pending recommendations
        recommendations_pending = Recommendation.objects.filter(
            employee__in=employees,
            is_active=True,
            is_applied=False
        ).count()
        
        # Charts data
        stress_distribution = self._get_stress_distribution(recent_aggregates)
        hourly_stress_trend = self._get_hourly_trend(employees, today)
        department_comparison = self._get_department_comparison(employees)
        alert_trends = self._get_alert_trends(employees)
        
        data = {
            'total_employees': total_employees,
            'active_devices': active_devices,
            'avg_stress_level': round(avg_stress_level, 2),
            'high_risk_employees': high_risk_employees,
            'alerts_today': alerts_today,
            'recommendations_pending': recommendations_pending,
            'stress_distribution': stress_distribution,
            'hourly_stress_trend': hourly_stress_trend,
            'department_comparison': department_comparison,
            'alert_trends': alert_trends
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)
    
    def _get_stress_distribution(self, aggregates):
        # Distribution of stress levels
        distribution = {
            'low': aggregates.filter(stress_score__lt=40).count(),
            'medium': aggregates.filter(stress_score__gte=40, stress_score__lt=70).count(),
            'high': aggregates.filter(stress_score__gte=70).count()
        }
        return distribution
    
    def _get_hourly_trend(self, employees, date):
        # Hourly stress trend for today
        hourly_data = []
        
        for hour in range(24):
            hour_aggregates = StressAggregate.objects.filter(
                employee__in=employees,
                window_start__date=date,
                window_start__hour=hour
            )
            
            avg_stress = hour_aggregates.aggregate(avg=Avg('stress_score'))['avg'] or 0
            
            hourly_data.append({
                'hour': hour,
                'avg_stress': round(avg_stress, 2),
                'employee_count': hour_aggregates.values('employee').distinct().count()
            })
        
        return hourly_data
    
    def _get_department_comparison(self, employees):
        # Comparison by department
        departments = Department.objects.filter(employees__in=employees).distinct()
        comparison_data = []
        
        for dept in departments:
            dept_employees = employees.filter(departments=dept)
            dept_aggregates = StressAggregate.objects.filter(
                employee__in=dept_employees,
                window_start__date=timezone.now().date()
            )
            
            avg_stress = dept_aggregates.aggregate(avg=Avg('stress_score'))['avg'] or 0
            
            comparison_data.append({
                'department_name': dept.name,
                'avg_stress': round(avg_stress, 2),
                'employee_count': dept_employees.count()
            })
        
        return comparison_data
    
    def _get_alert_trends(self, employees):
        # Alert trends for the last 7 days
        trends = []
        
        for day in range(7):
            date = timezone.now().date() - timedelta(days=day)
            alert_count = Alert.objects.filter(
                employee__in=employees,
                created_at__date=date
            ).count()
            
            trends.append({
                'date': date.isoformat(),
                'alert_count': alert_count
            })
        
        return list(reversed(trends))