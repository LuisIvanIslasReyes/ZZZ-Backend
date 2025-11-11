from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import pytest
from unittest.mock import patch, MagicMock

from apps.users.models import CustomUser
from apps.devices.models import Device
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.sensors.processors import SensorDataProcessor


@pytest.mark.django_db
class TestSensorDataModel:
    """Tests para el modelo SensorData."""

    def setup_method(self):
        """Configuración inicial."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123',
            role='employee'
        )
        
        self.device = Device.objects.create(
            user=self.user,
            device_id='ESP32-TEST',
            device_type='esp32',
            is_active=True
        )

    def test_create_sensor_data(self):
        """Test: crear datos de sensor."""
        data = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=75.0,
            spo2=98.0,
            temperature=36.8,
            steps=100,
            battery_level=85.0
        )
        
        assert data.id is not None
        assert data.user == self.user
        assert data.heart_rate == 75.0
        assert data.is_processed is False

    def test_sensor_data_validation(self):
        """Test: validación de rangos de datos de sensor."""
        # Datos válidos
        valid_data = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=75.0,
            spo2=98.0,
            temperature=36.8,
            steps=100
        )
        assert valid_data.id is not None

    def test_sensor_data_ordering(self):
        """Test: orden de datos por timestamp."""
        now = timezone.now()
        
        data1 = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=75.0,
            timestamp=now - timedelta(hours=2)
        )
        
        data2 = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=80.0,
            timestamp=now - timedelta(hours=1)
        )
        
        # Obtener todos ordenados (más reciente primero)
        all_data = SensorData.objects.all()
        assert all_data[0].id == data2.id
        assert all_data[1].id == data1.id


@pytest.mark.django_db
class TestProcessedMetrics:
    """Tests para el modelo ProcessedMetrics."""

    def setup_method(self):
        """Configuración inicial."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123',
            role='employee'
        )
        
        self.device = Device.objects.create(
            user=self.user,
            device_id='ESP32-TEST',
            device_type='esp32',
            is_active=True
        )

    def test_create_processed_metrics(self):
        """Test: crear métricas procesadas."""
        metrics = ProcessedMetrics.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=75.0,
            spo2=98.0,
            temperature=36.8,
            steps=1000,
            calories=250.0,
            distance=5.0,
            activity_level='moderate',
            fatigue_index=45.0,
            stress_level=35.0,
            recovery_score=75.0
        )
        
        assert metrics.id is not None
        assert metrics.fatigue_index == 45.0
        assert metrics.activity_level == 'moderate'

    def test_fatigue_index_range(self):
        """Test: índice de fatiga debe estar en rango 0-100."""
        metrics = ProcessedMetrics.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=75.0,
            fatigue_index=95.0
        )
        
        assert 0 <= metrics.fatigue_index <= 100

    def test_get_by_date_range(self):
        """Test: obtener métricas por rango de fechas."""
        now = timezone.now()
        
        # Crear métricas en diferentes fechas
        for i in range(5):
            ProcessedMetrics.objects.create(
                user=self.user,
                device=self.device,
                timestamp=now - timedelta(days=i),
                heart_rate=75.0,
                fatigue_index=50.0
            )
        
        # Obtener últimas 3 días
        start_date = now - timedelta(days=2)
        recent_metrics = ProcessedMetrics.objects.filter(
            user=self.user,
            timestamp__gte=start_date
        )
        
        assert recent_metrics.count() == 3


@pytest.mark.django_db
class TestSensorDataProcessor:
    """Tests para el procesador de datos de sensores."""

    def setup_method(self):
        """Configuración inicial."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123',
            role='employee'
        )
        
        self.device = Device.objects.create(
            user=self.user,
            device_id='ESP32-TEST',
            device_type='esp32',
            is_active=True
        )
        
        self.processor = SensorDataProcessor()

    @patch('apps.sensors.processors.MLService')
    def test_process_single_sensor_data(self, mock_ml_service):
        """Test: procesar un único registro de sensor."""
        # Configurar mock del servicio ML
        mock_ml_service.return_value.predict_fatigue.return_value = 55.0
        
        # Crear datos de sensor sin procesar
        sensor_data = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=80.0,
            spo2=96.0,
            temperature=37.0,
            steps=500,
            is_processed=False
        )
        
        # Procesar
        processed = self.processor.process_sensor_data(sensor_data.id)
        
        # Verificar que se creó métrica procesada
        assert processed is not None
        assert processed.user == self.user
        assert processed.heart_rate == 80.0
        
        # Verificar que el dato original se marcó como procesado
        sensor_data.refresh_from_db()
        assert sensor_data.is_processed is True

    @patch('apps.sensors.processors.MLService')
    def test_calculate_fatigue_without_ml_model(self, mock_ml_service):
        """Test: cálculo de fatiga sin modelo ML (fallback)."""
        # Simular que no hay modelo ML disponible
        mock_ml_service.return_value.predict_fatigue.side_effect = Exception("No model")
        
        sensor_data = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=95.0,  # Alta
            spo2=92.0,        # Baja
            temperature=37.5,
            steps=100,
            is_processed=False
        )
        
        # Procesar (debería usar método de fallback)
        processed = self.processor.process_sensor_data(sensor_data.id)
        
        # Verificar que se calculó fatiga (aunque sea con heurística)
        assert processed is not None
        assert processed.fatigue_index >= 0
        assert processed.fatigue_index <= 100

    def test_calculate_activity_metrics(self):
        """Test: cálculo de métricas de actividad."""
        sensor_data = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=75.0,
            steps=5000,  # Muchos pasos
            is_processed=False
        )
        
        # Procesar
        with patch('apps.sensors.processors.MLService') as mock_ml:
            mock_ml.return_value.predict_fatigue.return_value = 50.0
            processed = self.processor.process_sensor_data(sensor_data.id)
        
        # Verificar que se calcularon calorías y distancia
        assert processed.calories > 0
        assert processed.distance > 0

    def test_determine_activity_level(self):
        """Test: determinación del nivel de actividad."""
        # Actividad baja
        low_data = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=70.0,
            steps=500,
            is_processed=False
        )
        
        with patch('apps.sensors.processors.MLService') as mock_ml:
            mock_ml.return_value.predict_fatigue.return_value = 30.0
            processed_low = self.processor.process_sensor_data(low_data.id)
        
        assert processed_low.activity_level in ['sedentary', 'low']
        
        # Actividad alta
        high_data = SensorData.objects.create(
            user=self.user,
            device=self.device,
            heart_rate=120.0,
            steps=8000,
            is_processed=False
        )
        
        with patch('apps.sensors.processors.MLService') as mock_ml:
            mock_ml.return_value.predict_fatigue.return_value = 70.0
            processed_high = self.processor.process_sensor_data(high_data.id)
        
        assert processed_high.activity_level in ['moderate', 'high', 'vigorous']


@pytest.mark.integration
@pytest.mark.django_db
class TestSensorDataWorkflow:
    """Tests de integración del flujo completo de datos de sensores."""

    def setup_method(self):
        """Configuración inicial."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123',
            role='employee'
        )
        
        self.device = Device.objects.create(
            user=self.user,
            device_id='ESP32-TEST',
            device_type='esp32',
            is_active=True
        )
        
        self.processor = SensorDataProcessor()

    @patch('apps.sensors.processors.MLService')
    def test_complete_sensor_workflow(self, mock_ml_service):
        """Test: flujo completo desde datos raw hasta métricas procesadas."""
        # Configurar mock
        mock_ml_service.return_value.predict_fatigue.return_value = 65.0
        
        # 1. Crear múltiples datos de sensor
        sensor_data_list = []
        for i in range(5):
            data = SensorData.objects.create(
                user=self.user,
                device=self.device,
                heart_rate=75.0 + i,
                spo2=96.0,
                temperature=36.8,
                steps=1000 * (i + 1),
                is_processed=False
            )
            sensor_data_list.append(data)
        
        # 2. Procesar todos los datos
        processed_metrics = []
        for sensor_data in sensor_data_list:
            processed = self.processor.process_sensor_data(sensor_data.id)
            processed_metrics.append(processed)
        
        # 3. Verificar que todos se procesaron correctamente
        assert len(processed_metrics) == 5
        
        # 4. Verificar que todos los datos originales están marcados como procesados
        for sensor_data in sensor_data_list:
            sensor_data.refresh_from_db()
            assert sensor_data.is_processed is True
        
        # 5. Verificar que se pueden consultar las métricas procesadas
        all_metrics = ProcessedMetrics.objects.filter(user=self.user)
        assert all_metrics.count() == 5

    @patch('apps.sensors.processors.MLService')
    def test_batch_processing(self, mock_ml_service):
        """Test: procesamiento en lote de datos pendientes."""
        mock_ml_service.return_value.predict_fatigue.return_value = 55.0
        
        # Crear 10 datos sin procesar
        for i in range(10):
            SensorData.objects.create(
                user=self.user,
                device=self.device,
                heart_rate=75.0,
                is_processed=False
            )
        
        # Obtener todos los pendientes
        pending = SensorData.objects.filter(is_processed=False)
        assert pending.count() == 10
        
        # Procesar todos
        for data in pending:
            self.processor.process_sensor_data(data.id)
        
        # Verificar que no quedan pendientes
        still_pending = SensorData.objects.filter(is_processed=False)
        assert still_pending.count() == 0
        
        # Verificar que se crearon 10 métricas procesadas
        assert ProcessedMetrics.objects.filter(user=self.user).count() == 10

