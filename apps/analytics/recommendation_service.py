"""
Servicio de Generación Automática de Recomendaciones de Rutinas.
Analiza patrones históricos de fatiga y genera recomendaciones para optimizar rutinas laborales.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Max, Min, Count, Q, StdDev, F
from django.db.models.functions import ExtractHour, ExtractWeekDay
from django.contrib.auth import get_user_model

from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import RoutineRecommendation, FatigueAlert
from apps.devices.models import Device

User = get_user_model()
logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Servicio para generar recomendaciones automáticas de optimización de rutinas.
    """
    
    # Umbrales de fatiga
    FATIGUE_HIGH = 70
    FATIGUE_MEDIUM = 50
    FATIGUE_LOW = 30
    
    # Umbrales de tiempo
    ANALYSIS_DAYS = 7  # Analizar últimos 7 días
    MIN_DATA_POINTS = 20  # Mínimo de métricas para análisis confiable
    
    def __init__(self, supervisor=None):
        """
        Inicializa el servicio.
        
        Args:
            supervisor: Usuario supervisor para el cual generar recomendaciones.
                       Si es None, genera para todos los supervisores.
        """
        self.supervisor = supervisor
    
    def generate_all_recommendations(self):
        """
        Genera todas las recomendaciones para el supervisor o todos los supervisores.
        
        Returns:
            dict: Resumen de recomendaciones generadas
        """
        logger.info("🔄 Iniciando generación de recomendaciones...")
        
        if self.supervisor:
            supervisors = [self.supervisor]
        else:
            supervisors = User.objects.filter(role='supervisor', is_active=True)
        
        total_recommendations = 0
        recommendations_by_type = {
            'break': 0,
            'task_redistribution': 0,
            'shift_rotation': 0,
        }
        
        for supervisor in supervisors:
            logger.info(f"   Analizando supervisor: {supervisor.get_full_name()}")
            
            # Obtener empleados del supervisor
            employees = User.objects.filter(
                role='employee',
                supervisor=supervisor,
                is_active=True
            )
            
            if not employees.exists():
                logger.info(f"   ⚠️  Sin empleados activos")
                continue
            
            # Generar cada tipo de recomendación
            breaks = self._generate_break_recommendations(supervisor, employees)
            redistributions = self._generate_task_redistribution_recommendations(supervisor, employees)
            rotations = self._generate_shift_rotation_recommendations(supervisor, employees)
            
            # Contar
            total_recommendations += len(breaks) + len(redistributions) + len(rotations)
            recommendations_by_type['break'] += len(breaks)
            recommendations_by_type['task_redistribution'] += len(redistributions)
            recommendations_by_type['shift_rotation'] += len(rotations)
            
            logger.info(f"   ✅ Generadas: {len(breaks)} descansos, {len(redistributions)} redistribuciones, {len(rotations)} rotaciones")
        
        logger.info(f"✅ Generación completada: {total_recommendations} recomendaciones totales")
        
        return {
            'total': total_recommendations,
            'by_type': recommendations_by_type,
            'supervisors_analyzed': len(supervisors)
        }
    
    def _generate_break_recommendations(self, supervisor, employees):
        """
        Genera recomendaciones de descansos programados.
        
        Detecta:
        - Empleados con fatiga alta sostenida
        - Patrones de fatiga en horarios específicos
        - Necesidad de descansos preventivos
        """
        recommendations = []
        cutoff_date = timezone.now() - timedelta(days=self.ANALYSIS_DAYS)
        
        for employee in employees:
            # Analizar métricas recientes
            metrics = ProcessedMetrics.objects.filter(
                employee=employee,
                window_start__gte=cutoff_date
            ).order_by('-window_start')
            
            if metrics.count() < self.MIN_DATA_POINTS:
                continue
            
            # Calcular estadísticas
            stats = metrics.aggregate(
                avg_fatigue=Avg('fatigue_index'),
                max_fatigue=Max('fatigue_index'),
                high_fatigue_count=Count('id', filter=Q(fatigue_index__gte=self.FATIGUE_HIGH))
            )
            
            avg_fatigue = stats['avg_fatigue'] or 0
            max_fatigue = stats['max_fatigue'] or 0
            high_fatigue_count = stats['high_fatigue_count'] or 0
            
            # Detectar necesidad de descansos
            needs_break = False
            priority = 3
            reason = ""
            
            # Caso 1: Fatiga promedio alta
            if avg_fatigue >= self.FATIGUE_MEDIUM:
                needs_break = True
                priority = 4 if avg_fatigue >= self.FATIGUE_HIGH else 3
                reason = f"Fatiga promedio elevada ({avg_fatigue:.1f}/100) en los últimos {self.ANALYSIS_DAYS} días"
            
            # Caso 2: Muchos episodios de fatiga alta
            elif high_fatigue_count > 5:
                needs_break = True
                priority = 3
                reason = f"{high_fatigue_count} episodios de fatiga alta en los últimos {self.ANALYSIS_DAYS} días"
            
            # Caso 3: Pico de fatiga muy alto
            elif max_fatigue >= 85:
                needs_break = True
                priority = 4
                reason = f"Pico de fatiga crítico ({max_fatigue:.1f}/100) detectado"
            
            if needs_break:
                # Analizar horarios de pico de fatiga
                peak_hours = self._analyze_fatigue_peak_hours(employee, cutoff_date)
                
                description = f"**Empleado:** {employee.get_full_name()}\n\n"
                description += f"**Razón:** {reason}\n\n"
                description += f"**Recomendación:**\n"
                description += f"- Programar descansos preventivos de 15-20 minutos\n"
                
                if peak_hours:
                    hours_str = ", ".join([f"{h}:00" for h in peak_hours[:3]])
                    description += f"- Horarios sugeridos para descansos: {hours_str}\n"
                
                description += f"\n**Estadísticas ({self.ANALYSIS_DAYS} días):**\n"
                description += f"- Fatiga promedio: {avg_fatigue:.1f}/100\n"
                description += f"- Fatiga máxima: {max_fatigue:.1f}/100\n"
                description += f"- Episodios de fatiga alta: {high_fatigue_count}\n"
                
                # Crear o actualizar recomendación
                recommendation = self._create_or_update_recommendation(
                    supervisor=supervisor,
                    employee=employee,
                    recommendation_type='break',
                    description=description,
                    priority=priority,
                    based_on_data={
                        'avg_fatigue': round(avg_fatigue, 2),
                        'max_fatigue': round(max_fatigue, 2),
                        'high_fatigue_count': high_fatigue_count,
                        'peak_hours': peak_hours,
                        'analysis_days': self.ANALYSIS_DAYS
                    }
                )
                
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_task_redistribution_recommendations(self, supervisor, employees):
        """
        Genera recomendaciones de redistribución de tareas.
        
        Detecta:
        - Empleados sobrecargados vs empleados con menor carga
        - Desbalance en niveles de fatiga
        - Oportunidades de redistribución
        """
        recommendations = []
        cutoff_date = timezone.now() - timedelta(days=self.ANALYSIS_DAYS)
        
        # Analizar todos los empleados del supervisor
        employee_stats = []
        for employee in employees:
            metrics = ProcessedMetrics.objects.filter(
                employee=employee,
                window_start__gte=cutoff_date
            )
            
            if metrics.count() < self.MIN_DATA_POINTS:
                continue
            
            stats = metrics.aggregate(
                avg_fatigue=Avg('fatigue_index'),
                max_fatigue=Max('fatigue_index'),
                std_fatigue=StdDev('fatigue_index')
            )
            
            employee_stats.append({
                'employee': employee,
                'avg_fatigue': stats['avg_fatigue'] or 0,
                'max_fatigue': stats['max_fatigue'] or 0,
                'std_fatigue': stats['std_fatigue'] or 0,
                'metrics_count': metrics.count()
            })
        
        if len(employee_stats) < 2:
            return recommendations
        
        # Ordenar por fatiga promedio
        employee_stats.sort(key=lambda x: x['avg_fatigue'], reverse=True)
        
        # Analizar desbalance
        highest = employee_stats[0]
        lowest = employee_stats[-1]
        avg_team_fatigue = sum(e['avg_fatigue'] for e in employee_stats) / len(employee_stats)
        
        fatigue_difference = highest['avg_fatigue'] - lowest['avg_fatigue']
        
        # Si hay desbalance significativo (>20 puntos de diferencia)
        if fatigue_difference > 20:
            overloaded = [e for e in employee_stats if e['avg_fatigue'] > avg_team_fatigue + 10]
            underloaded = [e for e in employee_stats if e['avg_fatigue'] < avg_team_fatigue - 10]
            
            if overloaded and underloaded:
                description = f"**Desbalance de carga detectado en el equipo**\n\n"
                description += f"**Empleados sobrecargados:**\n"
                for e in overloaded:
                    description += f"- {e['employee'].get_full_name()}: Fatiga promedio {e['avg_fatigue']:.1f}/100\n"
                
                description += f"\n**Empleados con menor carga:**\n"
                for e in underloaded[:3]:
                    description += f"- {e['employee'].get_full_name()}: Fatiga promedio {e['avg_fatigue']:.1f}/100\n"
                
                description += f"\n**Recomendación:**\n"
                description += f"- Redistribuir tareas desde empleados sobrecargados a los de menor carga\n"
                description += f"- Fatiga promedio del equipo: {avg_team_fatigue:.1f}/100\n"
                description += f"- Diferencia máxima: {fatigue_difference:.1f} puntos\n"
                description += f"\n**Beneficio esperado:**\n"
                description += f"- Equilibrar carga de trabajo\n"
                description += f"- Reducir fatiga en empleados sobrecargados\n"
                description += f"- Mejorar eficiencia general del equipo\n"
                
                # Prioridad alta si la diferencia es muy grande
                priority = 5 if fatigue_difference > 30 else 4
                
                # Crear recomendación general para el supervisor
                recommendation = self._create_or_update_recommendation(
                    supervisor=supervisor,
                    employee=None,  # Es para el equipo en general
                    recommendation_type='task_redistribution',
                    description=description,
                    priority=priority,
                    based_on_data={
                        'avg_team_fatigue': round(avg_team_fatigue, 2),
                        'fatigue_difference': round(fatigue_difference, 2),
                        'overloaded_count': len(overloaded),
                        'underloaded_count': len(underloaded),
                        'employee_stats': [
                            {
                                'employee_id': e['employee'].id,
                                'employee_name': e['employee'].get_full_name(),
                                'avg_fatigue': round(e['avg_fatigue'], 2)
                            }
                            for e in employee_stats
                        ]
                    }
                )
                
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_shift_rotation_recommendations(self, supervisor, employees):
        """
        Genera recomendaciones de rotación de turnos.
        
        Detecta:
        - Empleados con fatiga crónica en ciertos horarios
        - Patrones de fatiga por día de la semana
        - Oportunidades de cambio de turno
        """
        recommendations = []
        cutoff_date = timezone.now() - timedelta(days=self.ANALYSIS_DAYS)
        
        for employee in employees:
            metrics = ProcessedMetrics.objects.filter(
                employee=employee,
                window_start__gte=cutoff_date
            ).annotate(
                hour=ExtractHour('window_start'),
                weekday=ExtractWeekDay('window_start')
            )
            
            if metrics.count() < self.MIN_DATA_POINTS:
                continue
            
            # Analizar fatiga por hora del día
            hourly_fatigue = metrics.values('hour').annotate(
                avg_fatigue=Avg('fatigue_index'),
                count=Count('id')
            ).filter(count__gte=3).order_by('-avg_fatigue')
            
            # Analizar fatiga por día de la semana
            daily_fatigue = metrics.values('weekday').annotate(
                avg_fatigue=Avg('fatigue_index'),
                count=Count('id')
            ).filter(count__gte=3).order_by('-avg_fatigue')
            
            # Detectar horarios problemáticos
            problematic_hours = [h for h in hourly_fatigue if h['avg_fatigue'] > self.FATIGUE_HIGH]
            problematic_days = [d for d in daily_fatigue if d['avg_fatigue'] > self.FATIGUE_MEDIUM]
            
            if problematic_hours or problematic_days:
                needs_rotation = False
                priority = 3
                reason_parts = []
                
                if problematic_hours:
                    hours_str = ", ".join([f"{h['hour']}:00" for h in problematic_hours[:3]])
                    reason_parts.append(f"Fatiga alta en horarios: {hours_str}")
                    needs_rotation = True
                
                if problematic_days and len(problematic_days) >= 2:
                    days_map = {1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles', 
                               5: 'Jueves', 6: 'Viernes', 7: 'Sábado'}
                    days_str = ", ".join([days_map.get(d['weekday'], str(d['weekday'])) 
                                         for d in problematic_days[:3]])
                    reason_parts.append(f"Fatiga elevada en días: {days_str}")
                    needs_rotation = True
                    priority = 4
                
                if needs_rotation:
                    description = f"**Empleado:** {employee.get_full_name()}\n\n"
                    description += f"**Patrones detectados:**\n"
                    for reason in reason_parts:
                        description += f"- {reason}\n"
                    
                    description += f"\n**Recomendación:**\n"
                    description += f"- Considerar rotación de turno para este empleado\n"
                    
                    if problematic_hours:
                        best_hours = [h for h in hourly_fatigue.reverse()[:3]]
                        if best_hours:
                            hours_str = ", ".join([f"{h['hour']}:00" for h in best_hours])
                            description += f"- Horarios con mejor desempeño: {hours_str}\n"
                    
                    if problematic_days:
                        best_days = [d for d in daily_fatigue.reverse()[:3]]
                        if best_days:
                            days_map = {1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles', 
                                       5: 'Jueves', 6: 'Viernes', 7: 'Sábado'}
                            days_str = ", ".join([days_map.get(d['weekday'], str(d['weekday'])) 
                                                 for d in best_days])
                            description += f"- Días con mejor desempeño: {days_str}\n"
                    
                    description += f"\n**Beneficio esperado:**\n"
                    description += f"- Reducir fatiga crónica\n"
                    description += f"- Mejorar bienestar del empleado\n"
                    description += f"- Optimizar rendimiento en horarios de menor fatiga\n"
                    
                    # Crear recomendación
                    recommendation = self._create_or_update_recommendation(
                        supervisor=supervisor,
                        employee=employee,
                        recommendation_type='shift_rotation',
                        description=description,
                        priority=priority,
                        based_on_data={
                            'problematic_hours': [
                                {'hour': h['hour'], 'avg_fatigue': round(h['avg_fatigue'], 2)}
                                for h in problematic_hours
                            ],
                            'problematic_days': [
                                {'weekday': d['weekday'], 'avg_fatigue': round(d['avg_fatigue'], 2)}
                                for d in problematic_days
                            ],
                            'analysis_days': self.ANALYSIS_DAYS
                        }
                    )
                    
                    if recommendation:
                        recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_fatigue_peak_hours(self, employee, cutoff_date):
        """
        Analiza las horas del día con mayor fatiga para un empleado.
        
        Returns:
            list: Horas con mayor fatiga promedio (ordenadas de mayor a menor)
        """
        metrics = ProcessedMetrics.objects.filter(
            employee=employee,
            window_start__gte=cutoff_date
        ).annotate(
            hour=ExtractHour('window_start')
        )
        
        hourly_stats = metrics.values('hour').annotate(
            avg_fatigue=Avg('fatigue_index'),
            count=Count('id')
        ).filter(count__gte=3).order_by('-avg_fatigue')
        
        # Retornar las 3 horas con mayor fatiga
        peak_hours = [h['hour'] for h in hourly_stats[:3]]
        return peak_hours
    
    def _create_or_update_recommendation(self, supervisor, employee, recommendation_type, 
                                        description, priority, based_on_data):
        """
        Crea una nueva recomendación o actualiza una existente si ya existe una similar pendiente.
        
        Returns:
            RoutineRecommendation: La recomendación creada o actualizada, o None si ya existe
        """
        # Buscar recomendación similar pendiente
        existing = RoutineRecommendation.objects.filter(
            supervisor=supervisor,
            employee=employee,
            recommendation_type=recommendation_type,
            is_applied=False
        ).first()
        
        if existing:
            # Actualizar recomendación existente
            existing.description = description
            existing.priority = priority
            existing.based_on_data = based_on_data
            existing.created_at = timezone.now()  # Actualizar timestamp
            existing.save()
            logger.debug(f"   ♻️  Actualizada recomendación existente: {recommendation_type}")
            return existing
        else:
            # Crear nueva recomendación
            recommendation = RoutineRecommendation.objects.create(
                supervisor=supervisor,
                employee=employee,
                recommendation_type=recommendation_type,
                description=description,
                priority=priority,
                based_on_data=based_on_data
            )
            logger.debug(f"   ✨ Nueva recomendación: {recommendation_type}")
            return recommendation
    
    def get_recommendation_summary(self, supervisor=None):
        """
        Obtiene un resumen de las recomendaciones actuales.
        
        Args:
            supervisor: Filtrar por supervisor (opcional)
        
        Returns:
            dict: Resumen de recomendaciones
        """
        query = RoutineRecommendation.objects.all()
        
        if supervisor:
            query = query.filter(supervisor=supervisor)
        
        total = query.count()
        pending = query.filter(is_applied=False).count()
        applied = query.filter(is_applied=True).count()
        
        by_type = query.filter(is_applied=False).values('recommendation_type').annotate(
            count=Count('id')
        )
        
        by_priority = query.filter(is_applied=False).values('priority').annotate(
            count=Count('id')
        ).order_by('-priority')
        
        return {
            'total': total,
            'pending': pending,
            'applied': applied,
            'by_type': {item['recommendation_type']: item['count'] for item in by_type},
            'by_priority': {item['priority']: item['count'] for item in by_priority}
        }
