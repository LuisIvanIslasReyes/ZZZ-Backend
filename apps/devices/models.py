"""
Device and Sensor models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Device(models.Model):
    """
    Wearable device registered to an employee
    """
    class DeviceType(models.TextChoices):
        WATCH = 'WATCH', 'Smartwatch'
        BAND = 'BAND', 'Smart Band'
        OTHER = 'OTHER', 'Otro'
    
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name='Empleado'
    )
    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.WATCH,
        verbose_name='Tipo de dispositivo'
    )
    hardware_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='ID de hardware',
        help_text='Identificador único del dispositivo (MAC, IMEI, etc.)'
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Modelo'
    )
    firmware_version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Versión de firmware'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última conexión'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.hardware_id} - {self.employee.get_full_name()}"


class SensorPacket(models.Model):
    """
    Raw packet of sensor data received from device
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='sensor_packets',
        verbose_name='Dispositivo'
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Recibido en'
    )
    packet_timestamp = models.DateTimeField(
        verbose_name='Timestamp del paquete',
        help_text='Timestamp original del dispositivo'
    )
    raw_payload = models.JSONField(
        verbose_name='Payload crudo',
        help_text='Datos crudos del sensor en formato JSON'
    )
    processed = models.BooleanField(
        default=False,
        verbose_name='Procesado'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Procesado en'
    )
    
    class Meta:
        verbose_name = 'Paquete de sensores'
        verbose_name_plural = 'Paquetes de sensores'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['device', '-received_at']),
            models.Index(fields=['processed', '-received_at']),
        ]
    
    def __str__(self):
        return f"Packet {self.id} - {self.device.hardware_id} - {self.packet_timestamp}"


class SensorSample(models.Model):
    """
    Individual sensor sample extracted from packet
    """
    packet = models.ForeignKey(
        SensorPacket,
        on_delete=models.CASCADE,
        related_name='samples',
        verbose_name='Paquete'
    )
    sample_time = models.DateTimeField(
        verbose_name='Tiempo de muestra',
        db_index=True
    )
    
    # Heart rate sensor
    heart_rate = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)],
        verbose_name='Frecuencia cardíaca (bpm)'
    )
    
    # SpO2 sensor
    spo2 = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Saturación de oxígeno (%)'
    )
    
    # Accelerometer (3 axes)
    accel_x = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Acelerómetro X'
    )
    accel_y = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Acelerómetro Y'
    )
    accel_z = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Acelerómetro Z'
    )
    
    # Steps counter
    steps = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Pasos'
    )
    
    # Battery level
    battery_level = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Nivel de batería (%)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Muestra de sensor'
        verbose_name_plural = 'Muestras de sensores'
        ordering = ['-sample_time']
        indexes = [
            models.Index(fields=['packet', 'sample_time']),
        ]
    
    def __str__(self):
        return f"Sample {self.id} - {self.sample_time}"


class StressAggregate(models.Model):
    """
    Aggregated stress score for a time window
    """
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stress_aggregates',
        verbose_name='Empleado'
    )
    window_start = models.DateTimeField(
        verbose_name='Inicio de ventana',
        db_index=True
    )
    window_end = models.DateTimeField(
        verbose_name='Fin de ventana',
        db_index=True
    )
    
    # Stress metrics
    stress_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Puntuación de estrés',
        help_text='Score de 0-100, donde 100 es máximo estrés'
    )
    confidence = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=1.0,
        verbose_name='Confianza',
        help_text='Nivel de confianza del cálculo (0-1)'
    )
    
    # Aggregate features used for calculation
    avg_heart_rate = models.FloatField(
        null=True,
        blank=True,
        verbose_name='HR promedio'
    )
    heart_rate_variability = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Variabilidad de HR'
    )
    movement_intensity = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Intensidad de movimiento'
    )
    
    # Metadata
    sample_count = models.IntegerField(
        default=0,
        verbose_name='Cantidad de muestras'
    )
    method_version = models.CharField(
        max_length=20,
        default='v1.0',
        verbose_name='Versión del método'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Agregado de estrés'
        verbose_name_plural = 'Agregados de estrés'
        ordering = ['-window_start']
        indexes = [
            models.Index(fields=['employee', '-window_start']),
        ]
        unique_together = ['employee', 'window_start', 'window_end']
    
    def __str__(self):
        return f"Stress {self.stress_score:.1f} - {self.employee.get_full_name()} - {self.window_start}"
