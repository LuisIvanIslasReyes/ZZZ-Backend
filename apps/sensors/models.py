from django.db import models
from django.conf import settings
from apps.devices.models import Device


class SensorData(models.Model):
    """
    Modelo para almacenar datos crudos de los sensores del ESP32.
    Frecuencia: cada 5 segundos (12 registros por minuto).
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='sensor_data',
        help_text="Dispositivo que envió los datos"
    )
    
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="Momento exacto de la lectura del sensor"
    )
    
    # Sensor de ritmo cardíaco (PPG/ECG)
    heart_rate = models.FloatField(
        help_text="Ritmo cardíaco en BPM (latidos por minuto)"
    )
    
    # Sensor de oxigenación
    spo2 = models.FloatField(
        help_text="Saturación de oxígeno en sangre (%)"
    )
    
    # Acelerómetro (3 ejes)
    accel_x = models.FloatField(
        help_text="Aceleración en eje X (g)"
    )
    
    accel_y = models.FloatField(
        help_text="Aceleración en eje Y (g)"
    )
    
    accel_z = models.FloatField(
        help_text="Aceleración en eje Z (g)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sensor_data'
        ordering = ['-timestamp']
        verbose_name = 'Dato de Sensor'
        verbose_name_plural = 'Datos de Sensores'
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.device_identifier} - {self.timestamp}"


class ProcessedMetrics(models.Model):
    """
    Modelo para métricas procesadas en ventanas de tiempo (30s - 5min).
    Incluye features calculados y el índice de fatiga del ML.
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='processed_metrics',
        help_text="Dispositivo del cual se procesaron los datos"
    )
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='processed_metrics',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado al que pertenecen las métricas"
    )
    
    window_start = models.DateTimeField(
        db_index=True,
        help_text="Inicio de la ventana de tiempo"
    )
    
    window_end = models.DateTimeField(
        help_text="Fin de la ventana de tiempo"
    )
    
    # === Métricas de Ritmo Cardíaco ===
    hr_avg = models.FloatField(
        help_text="Promedio de ritmo cardíaco en la ventana (BPM)"
    )
    
    hr_max = models.FloatField(
        help_text="Ritmo cardíaco máximo en la ventana (BPM)"
    )
    
    hr_min = models.FloatField(
        help_text="Ritmo cardíaco mínimo en la ventana (BPM)"
    )
    
    hrv_rmssd = models.FloatField(
        null=True,
        blank=True,
        help_text="Variabilidad cardíaca - RMSSD (ms)"
    )
    
    hrv_sdnn = models.FloatField(
        null=True,
        blank=True,
        help_text="Variabilidad cardíaca - SDNN (ms)"
    )
    
    hr_trend = models.CharField(
        max_length=20,
        choices=[
            ('stable', 'Estable'),
            ('increasing', 'Aumentando'),
            ('decreasing', 'Disminuyendo'),
        ],
        default='stable',
        help_text="Tendencia del ritmo cardíaco"
    )
    
    # === Métricas de Oxigenación ===
    spo2_avg = models.FloatField(
        help_text="Promedio de SpO2 en la ventana (%)"
    )
    
    spo2_min = models.FloatField(
        help_text="SpO2 mínimo en la ventana (%)"
    )
    
    spo2_variance = models.FloatField(
        null=True,
        blank=True,
        help_text="Varianza de SpO2"
    )
    
    desaturation_count = models.IntegerField(
        default=0,
        help_text="Número de desaturaciones (caídas >3% o >4%)"
    )
    
    # === Métricas de Movimiento ===
    activity_level = models.FloatField(
        help_text="Nivel de actividad - magnitud RMS del acelerómetro"
    )
    
    movement_variance = models.FloatField(
        null=True,
        blank=True,
        help_text="Varianza del movimiento"
    )
    
    movement_entropy = models.FloatField(
        null=True,
        blank=True,
        help_text="Entropía del movimiento (inactividad o temblores)"
    )
    
    posture_angle = models.FloatField(
        null=True,
        blank=True,
        help_text="Ángulo de postura/inclinación del cuerpo (grados)"
    )
    
    # === Features Combinados ===
    fatigue_index = models.FloatField(
        db_index=True,
        help_text="Índice de fatiga calculado por ML (0-100)"
    )
    
    hr_activity_ratio = models.FloatField(
        null=True,
        blank=True,
        help_text="Ratio HR/Actividad (HR alta + baja actividad = fatiga)"
    )
    
    recovery_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Tiempo de recuperación post-esfuerzo (minutos)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'processed_metrics'
        ordering = ['-window_start']
        verbose_name = 'Métrica Procesada'
        verbose_name_plural = 'Métricas Procesadas'
        indexes = [
            models.Index(fields=['employee', 'window_start']),
            models.Index(fields=['fatigue_index']),
            models.Index(fields=['-window_start']),
            models.Index(fields=['device', 'window_start']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.window_start} (Fatiga: {self.fatigue_index})"
