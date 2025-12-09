from django.db import models
from django.conf import settings


class FatigueAlert(models.Model):
    """
    Modelo para alertas de fatiga generadas automáticamente.
    Se crean cuando se detectan condiciones peligrosas o niveles altos de fatiga.
    """
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fatigue_alerts',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado al que se le generó la alerta"
    )
    
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supervised_alerts',
        limit_choices_to={'role': 'supervisor'},
        help_text="Supervisor que debe atender la alerta"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Momento en que se generó la alerta"
    )
    
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        db_index=True,
        help_text="Nivel de severidad de la alerta"
    )
    
    alert_type = models.CharField(
        max_length=50,
        help_text="Tipo de alerta (high_fatigue, low_spo2, high_hr, etc.)"
    )
    
    message = models.TextField(
        help_text="Mensaje descriptivo de la alerta"
    )
    
    fatigue_index = models.FloatField(
        help_text="Índice de fatiga en el momento de la alerta"
    )
    
    is_acknowledged = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Si la alerta fue reconocida/vista"
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se reconoció la alerta"
    )
    
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts',
        help_text="Usuario que reconoció la alerta"
    )
    
    is_resolved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Si la alerta fue resuelta"
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se resolvió la alerta"
    )
    
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        help_text="Usuario que resolvió la alerta"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fatigue_alerts'
        ordering = ['-timestamp']
        verbose_name = 'Alerta de Fatiga'
        verbose_name_plural = 'Alertas de Fatiga'
        indexes = [
            models.Index(fields=['employee', 'is_resolved']),
            models.Index(fields=['supervisor', 'is_resolved']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        status = "Resuelta" if self.is_resolved else "Activa"
        return f"{self.get_severity_display()} - {self.employee.get_full_name()} [{status}]"


class RoutineRecommendation(models.Model):
    """
    Modelo para recomendaciones de optimización de rutinas laborales.
    Generadas para supervisores basándose en patrones de fatiga.
    """
    RECOMMENDATION_TYPES = [
        ('break', 'Descanso'),
        ('task_redistribution', 'Redistribución de Tareas'),
        ('shift_rotation', 'Rotación de Turnos'),
    ]
    
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations',
        limit_choices_to={'role': 'supervisor'},
        help_text="Supervisor que recibe la recomendación"
    )
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_recommendations',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado para el cual es la recomendación"
    )
    
    recommendation_type = models.CharField(
        max_length=30,
        choices=RECOMMENDATION_TYPES,
        help_text="Tipo de recomendación"
    )
    
    description = models.TextField(
        help_text="Descripción detallada de la recomendación"
    )
    
    priority = models.IntegerField(
        default=3,
        help_text="Prioridad de 1 (más urgente) a 5 (menos urgente)"
    )
    
    based_on_data = models.JSONField(
        help_text="Métricas y datos que generaron esta recomendación"
    )
    
    is_applied = models.BooleanField(
        default=False,
        help_text="Si la recomendación fue aplicada"
    )
    
    applied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se aplicó la recomendación"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'routine_recommendations'
        ordering = ['priority', '-created_at']
        verbose_name = 'Recomendación de Rutina'
        verbose_name_plural = 'Recomendaciones de Rutinas'
        indexes = [
            models.Index(fields=['supervisor', 'is_applied']),
            models.Index(fields=['employee', 'is_applied']),
            models.Index(fields=['priority', '-created_at']),
        ]
    
    def __str__(self):
        status = "Aplicada" if self.is_applied else "Pendiente"
        return f"{self.get_recommendation_type_display()} - {self.employee.get_full_name()} [{status}]"


class SymptomReport(models.Model):
    """
    Modelo para reportes de síntomas enviados por empleados.
    Permite a los empleados informar cómo se sienten durante su jornada.
    """
    SYMPTOM_TYPES = [
        ('fatigue', 'Fatiga/Cansancio'),
        ('headache', 'Dolor de cabeza'),
        ('dizziness', 'Mareo'),
        ('nausea', 'Náuseas'),
        ('muscle_pain', 'Dolor muscular'),
        ('eye_strain', 'Fatiga visual'),
        ('stress', 'Estrés'),
        ('difficulty_concentrating', 'Dificultad para concentrarse'),
        ('shortness_of_breath', 'Dificultad para respirar'),
        ('other', 'Otro'),
    ]
    
    SEVERITY_CHOICES = [
        ('mild', 'Leve'),
        ('moderate', 'Moderado'),
        ('severe', 'Severo'),
    ]
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='symptom_reports',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado que reporta el síntoma"
    )
    
    symptom_type = models.CharField(
        'Tipo de síntoma',
        max_length=30,
        choices=SYMPTOM_TYPES,
        help_text="Tipo de síntoma reportado"
    )
    
    severity = models.CharField(
        'Severidad',
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='mild',
        help_text="Nivel de severidad del síntoma"
    )
    
    description = models.TextField(
        'Descripción',
        blank=True,
        null=True,
        help_text="Descripción adicional del síntoma (opcional)"
    )
    
    is_reviewed = models.BooleanField(
        'Revisado',
        default=False,
        help_text="Si el reporte fue revisado por el supervisor"
    )
    
    reviewed_at = models.DateTimeField(
        'Fecha de revisión',
        null=True,
        blank=True,
        help_text="Momento en que se revisó el reporte"
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_symptom_reports',
        help_text="Usuario que revisó el reporte"
    )
    
    notes = models.TextField(
        'Notas del supervisor',
        blank=True,
        null=True,
        help_text="Notas o comentarios del supervisor"
    )
    
    created_at = models.DateTimeField('Fecha de reporte', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    
    class Meta:
        db_table = 'symptom_reports'
        ordering = ['-created_at']
        verbose_name = 'Reporte de Síntoma'
        verbose_name_plural = 'Reportes de Síntomas'
        indexes = [
            models.Index(fields=['employee', '-created_at']),
            models.Index(fields=['symptom_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['is_reviewed', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_symptom_type_display()} ({self.get_severity_display()}) - {self.employee.get_full_name()}"


class ScheduledBreak(models.Model):
    """
    Modelo para descansos programados por empleados.
    Permite a los empleados solicitar/programar sus descansos.
    """
    BREAK_TYPES = [
        ('coffee', 'Café/Snack'),
        ('lunch', 'Almuerzo'),
        ('rest', 'Descanso general'),
        ('medical', 'Médico'),
        ('personal', 'Personal'),
        ('stretch', 'Estiramiento/Ejercicio'),
    ]
    
    DURATION_CHOICES = [
        (15, '15 minutos'),
        (30, '30 minutos'),
        (45, '45 minutos'),
        (60, '1 hora'),
        (90, '1 hora 30 minutos'),
        (120, '2 horas'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_breaks',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado que programa el descanso"
    )
    
    break_type = models.CharField(
        'Tipo de descanso',
        max_length=20,
        choices=BREAK_TYPES,
        help_text="Tipo de descanso"
    )
    
    scheduled_date = models.DateField(
        'Fecha programada',
        help_text="Fecha del descanso"
    )
    
    scheduled_time = models.TimeField(
        'Hora programada',
        help_text="Hora de inicio del descanso"
    )
    
    duration_minutes = models.IntegerField(
        'Duración (minutos)',
        choices=DURATION_CHOICES,
        default=30,
        help_text="Duración del descanso en minutos"
    )
    
    reason = models.TextField(
        'Razón',
        blank=True,
        null=True,
        help_text="Razón o motivo del descanso (opcional)"
    )
    
    status = models.CharField(
        'Estado',
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Estado actual del descanso programado"
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_breaks',
        help_text="Supervisor que revisó la solicitud"
    )
    
    reviewed_at = models.DateTimeField(
        'Fecha de revisión',
        null=True,
        blank=True,
        help_text="Momento en que se revisó la solicitud"
    )
    
    reviewer_notes = models.TextField(
        'Notas del supervisor',
        blank=True,
        null=True,
        help_text="Notas o comentarios del supervisor"
    )
    
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    
    class Meta:
        db_table = 'scheduled_breaks'
        ordering = ['scheduled_date', 'scheduled_time']
        verbose_name = 'Descanso Programado'
        verbose_name_plural = 'Descansos Programados'
        indexes = [
            models.Index(fields=['employee', '-scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['scheduled_date', 'scheduled_time']),
        ]
    
    def __str__(self):
        return f"{self.get_break_type_display()} - {self.employee.get_full_name()} ({self.scheduled_date} {self.scheduled_time})"


class Alert(models.Model):
    """
    Modelo para alertas en tiempo real del dispositivo ESP32.
    Almacena alertas como ritmo cardíaco elevado, SpO2 bajo, etc.
    """
    SEVERITY_CHOICES = [
        ('INFO', 'Información'),
        ('WARNING', 'Advertencia'),
        ('CRITICAL', 'Crítica'),
    ]
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_alerts',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado asociado a la alerta"
    )
    
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='alerts',
        help_text="Dispositivo que generó la alerta"
    )
    
    alert_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Tipo de alerta (HIGH_HEART_RATE, LOW_SPO2, etc.)"
    )
    
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='WARNING',
        db_index=True,
        help_text="Severidad de la alerta"
    )
    
    message = models.TextField(
        help_text="Mensaje descriptivo de la alerta"
    )
    
    heart_rate = models.FloatField(
        null=True,
        blank=True,
        help_text="Ritmo cardíaco en el momento de la alerta (BPM)"
    )
    
    spo2 = models.FloatField(
        null=True,
        blank=True,
        help_text="SpO2 en el momento de la alerta (%)"
    )
    
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="Momento en que se generó la alerta"
    )
    
    is_acknowledged = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Si la alerta fue vista/reconocida"
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se reconoció la alerta"
    )
    
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_device_alerts',
        help_text="Usuario que reconoció la alerta"
    )
    
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    
    class Meta:
        db_table = 'device_alerts'
        ordering = ['-timestamp']
        verbose_name = 'Alerta de Dispositivo'
        verbose_name_plural = 'Alertas de Dispositivos'
        indexes = [
            models.Index(fields=['employee', '-timestamp']),
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['alert_type', '-timestamp']),
            models.Index(fields=['is_acknowledged', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.employee.get_full_name()} ({self.timestamp})"
