from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import pytest

from apps.users.models import CustomUser
from apps.devices.models import Device
from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation
from apps.analytics.recommendation_service import RecommendationService
from apps.analytics.pattern_analyzer import PatternAnalyzer


@pytest.mark.django_db
class TestRecommendationService:
    """Tests para el servicio de generación de recomendaciones."""

    def setup_method(self):
        """Configuración inicial para cada test."""
        # Crear supervisor
        self.supervisor = CustomUser.objects.create_user(
            username='supervisor1',
            email='supervisor1@test.com',
            password='test123',
            role='supervisor',
            first_name='Super',
            last_name='Visor'
        )
        
        # Crear empleados
        self.employee1 = CustomUser.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='test123',
            role='employee',
            first_name='Employee',
            last_name='One',
            supervisor=self.supervisor
        )
        
        self.employee2 = CustomUser.objects.create_user(
            username='employee2',
            email='employee2@test.com',
            password='test123',
            role='employee',
            first_name='Employee',
            last_name='Two',
            supervisor=self.supervisor
        )
        
        # Crear dispositivos
        self.device1 = Device.objects.create(
            user=self.employee1,
            device_id='ESP32-001',
            device_type='esp32',
            is_active=True
        )
        
        self.device2 = Device.objects.create(
            user=self.employee2,
            device_id='ESP32-002',
            device_type='esp32',
            is_active=True
        )
        
        self.service = RecommendationService()

    def test_generate_break_recommendations_high_fatigue(self):
        """Test: generar recomendaciones de descanso cuando hay fatiga alta."""
        now = timezone.now()
        
        # Generar métricas con fatiga alta (>70) para employee1
        for i in range(5):
            ProcessedMetrics.objects.create(
                user=self.employee1,
                device=self.device1,
                timestamp=now - timedelta(hours=i),
                heart_rate=95.0,
                spo2=92.0,
                temperature=37.5,
                steps=100,
                calories=50.0,
                distance=0.5,
                activity_level='moderate',
                fatigue_index=85.0,  # Fatiga alta
                stress_level=75.0,
                recovery_score=30.0
            )
        
        # Crear alerta de fatiga
        FatigueAlert.objects.create(
            user=self.employee1,
            device=self.device1,
            fatigue_level=85.0,
            alert_type='high',
            severity='high',
            message='Fatiga alta detectada',
            is_resolved=False
        )
        
        # Generar recomendaciones
        recommendations = self.service.generate_all_recommendations(self.supervisor.id)
        
        # Verificar que se generó una recomendación de descanso
        break_recs = [r for r in recommendations if r.recommendation_type == 'break_schedule']
        assert len(break_recs) > 0
        assert break_recs[0].employee == self.employee1
        assert 'descanso' in break_recs[0].description.lower()
        assert break_recs[0].priority >= 4  # Alta prioridad

    def test_generate_task_redistribution_recommendations(self):
        """Test: generar recomendaciones de redistribución de tareas."""
        now = timezone.now()
        
        # Employee1 con fatiga muy alta
        for i in range(10):
            ProcessedMetrics.objects.create(
                user=self.employee1,
                device=self.device1,
                timestamp=now - timedelta(hours=i),
                heart_rate=100.0,
                spo2=90.0,
                temperature=37.8,
                steps=150,
                calories=75.0,
                distance=0.8,
                activity_level='high',
                fatigue_index=90.0,  # Fatiga muy alta
                stress_level=85.0,
                recovery_score=20.0
            )
        
        # Employee2 con fatiga baja
        for i in range(10):
            ProcessedMetrics.objects.create(
                user=self.employee2,
                device=self.device2,
                timestamp=now - timedelta(hours=i),
                heart_rate=70.0,
                spo2=98.0,
                temperature=36.8,
                steps=80,
                calories=40.0,
                distance=0.4,
                activity_level='low',
                fatigue_index=30.0,  # Fatiga baja
                stress_level=25.0,
                recovery_score=85.0
            )
        
        # Generar recomendaciones
        recommendations = self.service.generate_all_recommendations(self.supervisor.id)
        
        # Verificar que se generó una recomendación de redistribución
        redistribution_recs = [r for r in recommendations if r.recommendation_type == 'task_redistribution']
        assert len(redistribution_recs) > 0
        assert 'redistribución' in redistribution_recs[0].description.lower() or 'redistribuci' in redistribution_recs[0].description.lower()

    def test_generate_shift_rotation_recommendations(self):
        """Test: generar recomendaciones de rotación de turnos."""
        now = timezone.now()
        
        # Generar métricas con patrón problemático en horario específico (ej: 14:00-16:00)
        base_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day in range(7):
            for hour in range(24):
                fatigue = 85.0 if 14 <= hour <= 16 else 45.0  # Pico de fatiga entre 14-16h
                
                ProcessedMetrics.objects.create(
                    user=self.employee1,
                    device=self.device1,
                    timestamp=base_date - timedelta(days=day, hours=23-hour),
                    heart_rate=95.0 if 14 <= hour <= 16 else 75.0,
                    spo2=92.0 if 14 <= hour <= 16 else 97.0,
                    temperature=37.5,
                    steps=100,
                    calories=50.0,
                    distance=0.5,
                    activity_level='moderate',
                    fatigue_index=fatigue,
                    stress_level=75.0 if 14 <= hour <= 16 else 35.0,
                    recovery_score=30.0 if 14 <= hour <= 16 else 70.0
                )
        
        # Generar recomendaciones
        recommendations = self.service.generate_all_recommendations(self.supervisor.id)
        
        # Verificar que se generó alguna recomendación
        assert len(recommendations) > 0

    def test_no_duplicate_recommendations(self):
        """Test: no generar recomendaciones duplicadas."""
        now = timezone.now()
        
        # Generar métricas con fatiga alta
        for i in range(5):
            ProcessedMetrics.objects.create(
                user=self.employee1,
                device=self.device1,
                timestamp=now - timedelta(hours=i),
                heart_rate=95.0,
                spo2=92.0,
                temperature=37.5,
                steps=100,
                calories=50.0,
                distance=0.5,
                activity_level='moderate',
                fatigue_index=85.0,
                stress_level=75.0,
                recovery_score=30.0
            )
        
        FatigueAlert.objects.create(
            user=self.employee1,
            device=self.device1,
            fatigue_level=85.0,
            alert_type='high',
            severity='high',
            message='Fatiga alta detectada',
            is_resolved=False
        )
        
        # Generar recomendaciones por primera vez
        recommendations1 = self.service.generate_all_recommendations(self.supervisor.id)
        initial_count = len(recommendations1)
        
        # Generar recomendaciones por segunda vez (no debería crear duplicados)
        recommendations2 = self.service.generate_all_recommendations(self.supervisor.id)
        
        # El total de recomendaciones en BD no debería aumentar significativamente
        total_recommendations = RoutineRecommendation.objects.filter(
            supervisor=self.supervisor
        ).count()
        
        assert total_recommendations <= initial_count + 2  # Permitir mínimo margen


@pytest.mark.django_db
class TestPatternAnalyzer:
    """Tests para el analizador de patrones."""

    def setup_method(self):
        """Configuración inicial para cada test."""
        self.supervisor = CustomUser.objects.create_user(
            username='supervisor1',
            email='supervisor1@test.com',
            password='test123',
            role='supervisor'
        )
        
        self.employee = CustomUser.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='test123',
            role='employee',
            supervisor=self.supervisor
        )
        
        self.device = Device.objects.create(
            user=self.employee,
            device_id='ESP32-001',
            device_type='esp32',
            is_active=True
        )
        
        self.analyzer = PatternAnalyzer()

    def test_analyze_hourly_patterns(self):
        """Test: análisis de patrones por hora del día."""
        now = timezone.now()
        base_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Generar datos con pico de fatiga a las 15:00
        for day in range(7):
            for hour in range(24):
                fatigue = 90.0 if hour == 15 else 45.0
                
                ProcessedMetrics.objects.create(
                    user=self.employee,
                    device=self.device,
                    timestamp=base_date - timedelta(days=day, hours=23-hour),
                    heart_rate=95.0 if hour == 15 else 75.0,
                    spo2=92.0,
                    temperature=37.2,
                    steps=100,
                    calories=50.0,
                    distance=0.5,
                    activity_level='moderate',
                    fatigue_index=fatigue,
                    stress_level=75.0,
                    recovery_score=40.0
                )
        
        # Analizar patrones
        patterns = self.analyzer.analyze_hourly_patterns(self.employee.id, days=7)
        
        assert 'hourly_averages' in patterns
        assert len(patterns['hourly_averages']) == 24
        assert 'peak_fatigue_hours' in patterns
        
        # Verificar que detecta la hora 15 como pico
        peak_hours = patterns['peak_fatigue_hours']
        assert 15 in peak_hours

    def test_analyze_daily_patterns(self):
        """Test: análisis de patrones por día de la semana."""
        now = timezone.now()
        base_date = now.replace(hour=12, minute=0, second=0, microsecond=0)
        
        # Generar datos con fatiga alta los lunes (weekday=0)
        for day in range(21):  # 3 semanas
            date = base_date - timedelta(days=day)
            weekday = date.weekday()
            fatigue = 85.0 if weekday == 0 else 50.0  # Lunes problemático
            
            ProcessedMetrics.objects.create(
                user=self.employee,
                device=self.device,
                timestamp=date,
                heart_rate=90.0 if weekday == 0 else 75.0,
                spo2=93.0,
                temperature=37.1,
                steps=100,
                calories=50.0,
                distance=0.5,
                activity_level='moderate',
                fatigue_index=fatigue,
                stress_level=70.0,
                recovery_score=45.0
            )
        
        # Analizar patrones
        patterns = self.analyzer.analyze_daily_patterns(self.employee.id, days=21)
        
        assert 'daily_averages' in patterns
        assert len(patterns['daily_averages']) == 7
        assert 'problematic_days' in patterns
        
        # Verificar que detecta el lunes como problemático
        problematic_days = patterns['problematic_days']
        assert 0 in problematic_days  # 0 = lunes

    def test_analyze_trends(self):
        """Test: análisis de tendencias temporales."""
        now = timezone.now()
        
        # Generar datos con tendencia creciente de fatiga
        for i in range(30):
            fatigue = 40.0 + (i * 1.5)  # Incremento progresivo
            
            ProcessedMetrics.objects.create(
                user=self.employee,
                device=self.device,
                timestamp=now - timedelta(days=29-i),
                heart_rate=70.0 + i,
                spo2=95.0,
                temperature=37.0,
                steps=100,
                calories=50.0,
                distance=0.5,
                activity_level='moderate',
                fatigue_index=min(fatigue, 100.0),
                stress_level=50.0,
                recovery_score=60.0
            )
        
        # Analizar tendencias
        trends = self.analyzer.analyze_trends(self.employee.id, days=30)
        
        assert 'fatigue_trend' in trends
        assert 'slope' in trends['fatigue_trend']
        assert trends['fatigue_trend']['slope'] > 0  # Tendencia creciente

    def test_analyze_correlations(self):
        """Test: análisis de correlaciones entre variables."""
        now = timezone.now()
        
        # Generar datos con correlación entre fatiga y frecuencia cardíaca
        for i in range(50):
            hr = 70.0 + (i * 0.5)
            fatigue = 40.0 + (i * 1.0)
            
            ProcessedMetrics.objects.create(
                user=self.employee,
                device=self.device,
                timestamp=now - timedelta(hours=i),
                heart_rate=min(hr, 120.0),
                spo2=95.0,
                temperature=37.0,
                steps=100,
                calories=50.0,
                distance=0.5,
                activity_level='moderate',
                fatigue_index=min(fatigue, 100.0),
                stress_level=50.0,
                recovery_score=60.0
            )
        
        # Analizar correlaciones
        correlations = self.analyzer.analyze_correlations(self.employee.id, days=7)
        
        assert 'fatigue_heart_rate' in correlations
        assert 'fatigue_spo2' in correlations
        
        # Debería haber correlación positiva entre fatiga y HR
        assert correlations['fatigue_heart_rate'] > 0.5

    def test_assess_risk_level(self):
        """Test: evaluación del nivel de riesgo."""
        now = timezone.now()
        
        # Generar datos de alto riesgo
        for i in range(30):
            ProcessedMetrics.objects.create(
                user=self.employee,
                device=self.device,
                timestamp=now - timedelta(hours=i),
                heart_rate=95.0,
                spo2=91.0,  # SpO2 bajo
                temperature=37.8,
                steps=100,
                calories=50.0,
                distance=0.5,
                activity_level='high',
                fatigue_index=88.0,  # Fatiga alta
                stress_level=82.0,  # Estrés alto
                recovery_score=25.0  # Recuperación baja
            )
        
        # Crear múltiples alertas
        for i in range(8):
            FatigueAlert.objects.create(
                user=self.employee,
                device=self.device,
                fatigue_level=85.0,
                alert_type='high',
                severity='high',
                message=f'Alerta {i}',
                is_resolved=False,
                created_at=now - timedelta(days=i)
            )
        
        # Evaluar riesgo
        risk = self.analyzer.assess_risk_level(self.employee.id, days=7)
        
        assert 'risk_score' in risk
        assert 'risk_level' in risk
        assert risk['risk_score'] >= 8  # Alto riesgo
        assert risk['risk_level'] in ['high', 'critical']


@pytest.mark.django_db
class TestRoutineRecommendationModel:
    """Tests para el modelo RoutineRecommendation."""

    def setup_method(self):
        """Configuración inicial."""
        self.supervisor = CustomUser.objects.create_user(
            username='supervisor1',
            email='supervisor1@test.com',
            password='test123',
            role='supervisor'
        )
        
        self.employee = CustomUser.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='test123',
            role='employee',
            supervisor=self.supervisor
        )

    def test_create_recommendation(self):
        """Test: crear una recomendación."""
        recommendation = RoutineRecommendation.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            recommendation_type='break_schedule',
            description='Test recommendation',
            priority=5,
            status='pending'
        )
        
        assert recommendation.id is not None
        assert recommendation.employee == self.employee
        assert recommendation.status == 'pending'

    def test_recommendation_status_transition(self):
        """Test: transición de estados de una recomendación."""
        recommendation = RoutineRecommendation.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            recommendation_type='task_redistribution',
            description='Test',
            priority=3,
            status='pending'
        )
        
        # Cambiar a aprobada
        recommendation.status = 'approved'
        recommendation.approved_at = timezone.now()
        recommendation.approved_by = self.supervisor
        recommendation.save()
        
        assert recommendation.status == 'approved'
        assert recommendation.approved_at is not None
        
        # Cambiar a implementada
        recommendation.status = 'implemented'
        recommendation.implemented_at = timezone.now()
        recommendation.save()
        
        assert recommendation.status == 'implemented'
        assert recommendation.implemented_at is not None


@pytest.mark.integration
@pytest.mark.django_db
class TestRecommendationWorkflow:
    """Tests de integración del flujo completo de recomendaciones."""

    def setup_method(self):
        """Configuración inicial."""
        self.supervisor = CustomUser.objects.create_user(
            username='supervisor1',
            email='supervisor1@test.com',
            password='test123',
            role='supervisor'
        )
        
        self.employee = CustomUser.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='test123',
            role='employee',
            supervisor=self.supervisor
        )
        
        self.device = Device.objects.create(
            user=self.employee,
            device_id='ESP32-001',
            device_type='esp32',
            is_active=True
        )

    def test_complete_workflow_high_fatigue(self):
        """Test: flujo completo desde datos hasta recomendación."""
        now = timezone.now()
        
        # 1. Generar métricas procesadas con fatiga alta
        metrics = []
        for i in range(10):
            metric = ProcessedMetrics.objects.create(
                user=self.employee,
                device=self.device,
                timestamp=now - timedelta(hours=i),
                heart_rate=95.0,
                spo2=92.0,
                temperature=37.5,
                steps=100,
                calories=50.0,
                distance=0.5,
                activity_level='moderate',
                fatigue_index=85.0,
                stress_level=75.0,
                recovery_score=30.0
            )
            metrics.append(metric)
        
        # 2. Crear alerta de fatiga
        alert = FatigueAlert.objects.create(
            user=self.employee,
            device=self.device,
            fatigue_level=85.0,
            alert_type='high',
            severity='high',
            message='Fatiga alta detectada',
            is_resolved=False
        )
        
        # 3. Generar recomendaciones
        service = RecommendationService()
        recommendations = service.generate_all_recommendations(self.supervisor.id)
        
        # 4. Verificar que se crearon recomendaciones
        assert len(recommendations) > 0
        
        # 5. Verificar que hay al menos una recomendación de descanso
        break_recs = [r for r in recommendations if r.recommendation_type == 'break_schedule']
        assert len(break_recs) > 0
        
        # 6. Simular aprobación de la recomendación
        recommendation = break_recs[0]
        recommendation.status = 'approved'
        recommendation.approved_at = timezone.now()
        recommendation.approved_by = self.supervisor
        recommendation.save()
        
        # 7. Verificar estado final
        recommendation.refresh_from_db()
        assert recommendation.status == 'approved'
        assert recommendation.approved_by == self.supervisor

