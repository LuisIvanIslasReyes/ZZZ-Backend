"""
Procesador de ventanas de tiempo para calcular métricas.
Este script lee datos de SensorData y genera ProcessedMetrics.
"""

from django.utils import timezone
from django.db.models import Avg, Max, Min, Count, StdDev
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.devices.models import Device
from apps.analytics.ml_service import predict_fatigue
import numpy as np
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class MetricsProcessor:
    """
    Procesa datos de sensores en ventanas de tiempo y calcula métricas.
    """
    
    def __init__(self, window_minutes=1):
        """
        Args:
            window_minutes: Tamaño de la ventana en minutos (default: 1 minuto)
        """
        self.window_minutes = window_minutes
    
    def calculate_hrv_rmssd(self, heart_rates):
        """
        Calcula HRV (Heart Rate Variability) usando RMSSD.
        RMSSD = raíz cuadrada de la media de las diferencias al cuadrado.
        """
        if len(heart_rates) < 2:
            return None
        
        # Calcular diferencias sucesivas
        diffs = np.diff(heart_rates)
        
        # Calcular RMSSD
        rmssd = np.sqrt(np.mean(diffs ** 2))
        
        return round(float(rmssd), 2)
    
    def calculate_hrv_sdnn(self, heart_rates):
        """
        Calcula HRV usando SDNN (Standard Deviation of NN intervals).
        """
        if len(heart_rates) < 2:
            return None
        
        sdnn = np.std(heart_rates)
        return round(float(sdnn), 2)
    
    def detect_hr_trend(self, heart_rates):
        """
        Detecta tendencia del ritmo cardíaco: stable, increasing, decreasing.
        """
        if len(heart_rates) < 5:
            return 'stable'
        
        # Calcular pendiente usando regresión lineal simple
        x = np.arange(len(heart_rates))
        slope = np.polyfit(x, heart_rates, 1)[0]
        
        # Clasificar tendencia
        if slope > 1.0:
            return 'increasing'
        elif slope < -1.0:
            return 'decreasing'
        else:
            return 'stable'
    
    def count_desaturations(self, spo2_values, threshold=3):
        """
        Cuenta desaturaciones (caídas de SpO2 > threshold%).
        """
        if len(spo2_values) < 2:
            return 0
        
        count = 0
        for i in range(1, len(spo2_values)):
            drop = spo2_values[i-1] - spo2_values[i]
            if drop >= threshold:
                count += 1
        
        return count
    
    def calculate_activity_level(self, accel_x_list, accel_y_list, accel_z_list):
        """
        Calcula nivel de actividad usando magnitud RMS del acelerómetro.
        RMS = raíz cuadrada de la media de (x² + y² + z²)
        """
        if not accel_x_list or not accel_y_list or not accel_z_list:
            return 0.0
        
        # Calcular magnitud para cada muestra
        magnitudes = []
        for x, y, z in zip(accel_x_list, accel_y_list, accel_z_list):
            # Restar gravedad del eje z
            z_adj = z - 9.81
            magnitude = np.sqrt(x**2 + y**2 + z_adj**2)
            magnitudes.append(magnitude)
        
        # Calcular RMS
        rms = np.sqrt(np.mean(np.array(magnitudes) ** 2))
        
        return round(float(rms), 3)
    
    def calculate_movement_entropy(self, accel_values):
        """
        Calcula entropía del movimiento (simplicidad del patrón).
        Alta entropía = movimiento irregular
        Baja entropía = movimiento repetitivo o inactividad
        """
        if len(accel_values) < 5:
            return None
        
        # Discretizar valores en bins
        hist, _ = np.histogram(accel_values, bins=10)
        
        # Calcular probabilidades
        probs = hist / len(accel_values)
        probs = probs[probs > 0]  # Eliminar ceros
        
        # Calcular entropía de Shannon
        entropy = -np.sum(probs * np.log2(probs))
        
        return round(float(entropy), 3)
    
    def calculate_fatigue_index_placeholder(self, metrics):
        """
        Placeholder para el índice de fatiga.
        TODO: Reemplazar con modelo ML entrenado.
        
        Por ahora usa heurísticas simples:
        - HR alto + actividad baja = fatiga
        - SpO2 bajo = fatiga
        - HRV bajo = fatiga/estrés
        """
        fatigue = 0.0
        
        # Factor 1: Ratio HR/Actividad (40% del índice)
        hr_ratio = metrics.get('hr_activity_ratio', 0)
        if hr_ratio > 100:  # HR muy alto para poca actividad
            fatigue += 40
        elif hr_ratio > 50:
            fatigue += 25
        elif hr_ratio > 30:
            fatigue += 15
        
        # Factor 2: SpO2 bajo (30% del índice)
        spo2 = metrics.get('spo2_avg', 98)
        if spo2 < 92:
            fatigue += 30
        elif spo2 < 95:
            fatigue += 20
        elif spo2 < 97:
            fatigue += 10
        
        # Factor 3: HRV bajo (20% del índice)
        hrv_rmssd = metrics.get('hrv_rmssd', 0)
        if hrv_rmssd and hrv_rmssd < 10:
            fatigue += 20
        elif hrv_rmssd and hrv_rmssd < 20:
            fatigue += 10
        
        # Factor 4: Desaturaciones (10% del índice)
        desat = metrics.get('desaturation_count', 0)
        if desat > 3:
            fatigue += 10
        elif desat > 0:
            fatigue += 5
        
        return min(100, fatigue)  # Limitar a 100
    
    def process_device_window(self, device, window_start, window_end):
        """
        Procesa una ventana de tiempo para un dispositivo específico.
        """
        # Obtener datos de sensores en la ventana
        sensor_data = SensorData.objects.filter(
            device=device,
            timestamp__gte=window_start,
            timestamp__lt=window_end
        ).order_by('timestamp')
        
        if not sensor_data.exists():
            logger.debug(f"No hay datos para {device.device_identifier} en ventana {window_start}")
            return None
        
        # Extraer listas de valores
        hr_list = list(sensor_data.values_list('heart_rate', flat=True))
        spo2_list = list(sensor_data.values_list('spo2', flat=True))
        accel_x_list = list(sensor_data.values_list('accel_x', flat=True))
        accel_y_list = list(sensor_data.values_list('accel_y', flat=True))
        accel_z_list = list(sensor_data.values_list('accel_z', flat=True))
        
        # Calcular métricas de HR
        hr_avg = float(np.mean(hr_list))
        hr_max = float(np.max(hr_list))
        hr_min = float(np.min(hr_list))
        hrv_rmssd = self.calculate_hrv_rmssd(hr_list)
        hrv_sdnn = self.calculate_hrv_sdnn(hr_list)
        hr_trend = self.detect_hr_trend(hr_list)
        
        # Calcular métricas de SpO2
        spo2_avg = float(np.mean(spo2_list))
        spo2_min = float(np.min(spo2_list))
        spo2_variance = float(np.var(spo2_list))
        desaturation_count = self.count_desaturations(spo2_list)
        
        # Calcular métricas de movimiento
        activity_level = self.calculate_activity_level(accel_x_list, accel_y_list, accel_z_list)
        movement_variance = float(np.var(accel_x_list + accel_y_list + accel_z_list))
        movement_entropy = self.calculate_movement_entropy(accel_x_list + accel_y_list)
        
        # Calcular features combinados
        hr_activity_ratio = (hr_avg / activity_level) if activity_level > 0 else hr_avg
        
        # Preparar diccionario de métricas para ML
        metrics = {
            'hr_avg': hr_avg,
            'hr_max': hr_max,
            'hr_min': hr_min,
            'hrv_rmssd': hrv_rmssd,
            'hrv_sdnn': hrv_sdnn,
            'spo2_avg': spo2_avg,
            'spo2_min': spo2_min,
            'spo2_variance': spo2_variance,
            'desaturation_count': desaturation_count,
            'activity_level': activity_level,
            'movement_variance': movement_variance,
            'movement_entropy': movement_entropy,
            'hr_activity_ratio': hr_activity_ratio,
            'hr_range': hr_max - hr_min,
            'recovery_index': spo2_avg / (hr_avg / 100) if hr_avg > 0 else 0,
            'hrv_ratio': hrv_rmssd / (hrv_sdnn + 1) if hrv_sdnn is not None else 0,
            'stress_index': hr_avg / (hrv_rmssd + 1) if hrv_rmssd is not None else 0,
            'activity_normalized': activity_level / (hr_avg / 100) if hr_avg > 0 else 0,
        }
        
        # Calcular índice de fatiga usando ML service
        # Si el modelo no está disponible, usa el cálculo placeholder automáticamente
        fatigue_index = predict_fatigue(metrics)
        
        # Crear registro de ProcessedMetrics
        processed = ProcessedMetrics.objects.create(
            device=device,
            employee=device.employee,
            window_start=window_start,
            window_end=window_end,
            hr_avg=hr_avg,
            hr_max=hr_max,
            hr_min=hr_min,
            hrv_rmssd=hrv_rmssd,
            hrv_sdnn=hrv_sdnn,
            hr_trend=hr_trend,
            spo2_avg=spo2_avg,
            spo2_min=spo2_min,
            spo2_variance=spo2_variance,
            desaturation_count=desaturation_count,
            activity_level=activity_level,
            movement_variance=movement_variance,
            movement_entropy=movement_entropy,
            fatigue_index=fatigue_index,
            hr_activity_ratio=hr_activity_ratio,
        )
        
        logger.info(f"✅ Métricas procesadas: {device.device_identifier} | "
                   f"Fatiga: {fatigue_index:.1f} | HR: {hr_avg:.1f} | SpO2: {spo2_avg:.1f}")
        
        return processed
    
    def process_latest_windows(self):
        """
        Procesa las ventanas más recientes de todos los dispositivos activos.
        """
        now = timezone.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        active_devices = Device.objects.filter(is_active=True)
        
        logger.info(f"🔄 Procesando ventanas de {active_devices.count()} dispositivos...")
        
        processed_count = 0
        for device in active_devices:
            result = self.process_device_window(device, window_start, now)
            if result:
                processed_count += 1
        
        logger.info(f"✅ Procesadas {processed_count} ventanas")
        
        return processed_count


# Instancia global del procesador
metrics_processor = MetricsProcessor(window_minutes=1)
