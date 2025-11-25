"""
Modelos para gestión de sesiones de simuladores ESP32.
"""
from django.db import models
from django.conf import settings


class SimulatorSession(models.Model):
    """
    Sesión de simulador ESP32 para un empleado.
    Permite múltiples simuladores activos simultáneamente.
    """
    STATUS_CHOICES = [
        ('running', 'En Ejecución'),
        ('stopped', 'Detenido'),
        ('error', 'Error'),
    ]
    
    FATIGUE_PROFILES = [
        ('rested', 'Descansado (0-30%)'),
        ('normal', 'Normal (30-50%)'),
        ('tired', 'Cansado (50-70%)'),
        ('fatigued', 'Fatigado (70-85%)'),
        ('critical', 'Crítico (85-100%)'),
    ]
    
    ACTIVITY_MODES = [
        ('resting', 'Reposo'),
        ('light', 'Actividad Ligera'),
        ('moderate', 'Actividad Moderada'),
        ('heavy', 'Actividad Intensa'),
    ]
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='simulator_sessions',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado para el cual se ejecuta el simulador"
    )
    
    device_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="ID del dispositivo ESP32 (ej: ESP32-001)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='running',
        db_index=True,
        help_text="Estado actual del simulador"
    )
    
    fatigue_profile = models.CharField(
        max_length=20,
        choices=FATIGUE_PROFILES,
        default='normal',
        help_text="Perfil de fatiga del empleado simulado"
    )
    
    activity_mode = models.CharField(
        max_length=20,
        choices=ACTIVITY_MODES,
        default='light',
        help_text="Modo de actividad del empleado"
    )
    
    # Configuración de parámetros vitales
    base_heart_rate = models.IntegerField(
        default=70,
        help_text="Ritmo cardíaco base (BPM)"
    )
    
    base_spo2 = models.FloatField(
        default=97.0,
        help_text="Saturación de oxígeno base (%)"
    )
    
    # Configuración de fatiga
    initial_fatigue = models.FloatField(
        default=20.0,
        help_text="Nivel inicial de fatiga (0-100)"
    )
    
    fatigue_rate = models.FloatField(
        default=0.5,
        help_text="Tasa de incremento de fatiga por minuto"
    )
    
    # Configuración MQTT
    mqtt_broker = models.CharField(
        max_length=100,
        default='localhost',
        help_text="Dirección del broker MQTT"
    )
    
    mqtt_port = models.IntegerField(
        default=1883,
        help_text="Puerto del broker MQTT"
    )
    
    publish_interval = models.IntegerField(
        default=5,
        help_text="Intervalo de publicación en segundos"
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento en que se inició el simulador"
    )
    
    stopped_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se detuvo el simulador"
    )
    
    # Estadísticas
    messages_sent = models.IntegerField(
        default=0,
        help_text="Número de mensajes MQTT enviados"
    )
    
    current_fatigue = models.FloatField(
        default=0.0,
        help_text="Nivel actual de fatiga"
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Mensaje de error si el simulador falló"
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_simulator_sessions',
        help_text="Usuario que inició el simulador"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'simulator_sessions'
        ordering = ['-started_at']
        verbose_name = 'Sesión de Simulador'
        verbose_name_plural = 'Sesiones de Simulador'
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['device_id', 'status']),
            models.Index(fields=['-started_at']),
        ]
    
    def __str__(self):
        return f"{self.device_id} - {self.employee.get_full_name()} [{self.get_status_display()}]"
    
    def get_fatigue_range(self):
        """Retorna el rango de fatiga según el perfil."""
        ranges = {
            'rested': (0, 30),
            'normal': (30, 50),
            'tired': (50, 70),
            'fatigued': (70, 85),
            'critical': (85, 100),
        }
        return ranges.get(self.fatigue_profile, (20, 40))
    
    def get_config_dict(self):
        """Retorna la configuración como diccionario."""
        return {
            'device_id': self.device_id,
            'employee_id': self.employee.id,
            'fatigue_profile': self.fatigue_profile,
            'activity_mode': self.activity_mode,
            'base_heart_rate': self.base_heart_rate,
            'base_spo2': self.base_spo2,
            'initial_fatigue': self.initial_fatigue,
            'fatigue_rate': self.fatigue_rate,
            'mqtt_broker': self.mqtt_broker,
            'mqtt_port': self.mqtt_port,
            'publish_interval': self.publish_interval,
        }
