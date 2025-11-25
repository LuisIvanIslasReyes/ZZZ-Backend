"""
ML Service - Sistema de Detección de Fatiga
Servicio para cargar y usar el modelo de machine learning.
"""

import os
import joblib
import numpy as np
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

class FatigueMLService:
    """
    Servicio de Machine Learning para predicción de niveles de fatiga.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.selected_features = []
        self.cluster_fatigue_map = {}
        self.model_loaded = False
        self.model_type = 'placeholder'
        
        # NO cargar modelo automáticamente - usar placeholder
        logger.info("✅ Servicio ML inicializado (modo placeholder)")

    
    def load_model(self, model_path=None):
        """
        Carga el modelo de ML desde disco.
        
        Args:
            model_path (str, optional): Ruta al archivo del modelo.
                                       Si es None, usa la ruta por defecto.
        
        Returns:
            bool: True si el modelo se cargó exitosamente, False en caso contrario.
        """
        if model_path is None:
            # Ruta por defecto
            base_dir = Path(settings.BASE_DIR)
            model_path = base_dir / 'ml_models' / 'fatigue_model.pkl'
        
        try:
            if not os.path.exists(model_path):
                print(f"⚠️  Modelo no encontrado en: {model_path}")
                print("   Ejecuta: python notebooks/03_clustering_model.py")
                self.model_loaded = False
                return False
            
            # Cargar modelo
            model_package = joblib.load(model_path)
            
            # Extraer componentes
            self.model = model_package['model']
            self.scaler = model_package['scaler']
            self.selected_features = model_package['selected_features']
            self.model_type = model_package.get('model_type', 'kmeans')
            
            # Para K-Means, cargar el mapeo de clusters a fatiga
            if self.model_type == 'kmeans':
                self.cluster_fatigue_map = model_package['cluster_fatigue_map']
            
            self.model_loaded = True
            print(f"✅ Modelo ML cargado exitosamente desde: {model_path}")
            print(f"   Tipo: {self.model_type.upper()}")
            print(f"   Features: {len(self.selected_features)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar modelo: {str(e)}")
            self.model_loaded = False
            return False
    
    def predict_fatigue_index(self, metrics_dict):
        """
        Predice el índice de fatiga basado en métricas procesadas.
        Usa cálculo basado en heurísticas (placeholder).
        
        Args:
            metrics_dict (dict): Diccionario con las métricas procesadas.
        
        Returns:
            float: Índice de fatiga predicho (0-100).
        """
        # SIEMPRE usar cálculo placeholder hasta que el modelo sea reentrenado
        return self._calculate_placeholder(metrics_dict)
    
    def _calculate_placeholder(self, metrics_dict):
        """
        Cálculo placeholder de fatiga cuando el modelo no está disponible.
        Usa múltiples indicadores para detectar fatiga.
        
        Args:
            metrics_dict (dict): Diccionario con métricas procesadas.
        
        Returns:
            float: Índice de fatiga calculado (0-100).
        """
        fatigue_scores = []
        
        # Indicador 1: Ritmo cardíaco elevado
        hr_avg = metrics_dict.get('hr_avg', 70)
        if hr_avg > 140:
            hr_score = min(100, (hr_avg - 70) * 1.5)
        elif hr_avg > 120:
            hr_score = min(100, (hr_avg - 70) * 1.2)
        elif hr_avg > 100:
            hr_score = min(100, (hr_avg - 70) * 1.0)
        else:
            hr_score = 0
        fatigue_scores.append(hr_score)
        
        # Indicador 2: SpO2 bajo
        spo2_avg = metrics_dict.get('spo2_avg', 98.0)
        if spo2_avg < 92:
            spo2_score = (98 - spo2_avg) * 15  # Muy crítico
        elif spo2_avg < 95:
            spo2_score = (98 - spo2_avg) * 10
        elif spo2_avg < 97:
            spo2_score = (98 - spo2_avg) * 5
        else:
            spo2_score = 0
        fatigue_scores.append(spo2_score)
        
        # Indicador 3: HRV bajo (indica estrés/fatiga)
        hrv_rmssd = metrics_dict.get('hrv_rmssd')
        if hrv_rmssd is not None:
            if hrv_rmssd < 10:
                hrv_score = 80
            elif hrv_rmssd < 20:
                hrv_score = 60
            elif hrv_rmssd < 30:
                hrv_score = 40
            else:
                hrv_score = 0
            fatigue_scores.append(hrv_score)
        
        # Indicador 4: Ratio HR/Actividad (HR alto con poca actividad)
        hr_activity_ratio = metrics_dict.get('hr_activity_ratio', 1.0)
        activity_level = metrics_dict.get('activity_level', 1.0)
        
        # Si hay poca actividad pero HR alto = fatiga
        if activity_level < 0.5 and hr_avg > 90:
            ratio_score = min(100, (hr_avg - 60) * 2)
            fatigue_scores.append(ratio_score)
        elif hr_activity_ratio > 100:
            ratio_score = min(100, (hr_activity_ratio - 50) * 0.8)
            fatigue_scores.append(ratio_score)
        
        # Indicador 5: Desaturaciones
        desaturation_count = metrics_dict.get('desaturation_count', 0)
        if desaturation_count > 0:
            desat_score = min(100, desaturation_count * 30)
            fatigue_scores.append(desat_score)
        
        # Indicador 6: Varianza de SpO2 (inestabilidad)
        spo2_variance = metrics_dict.get('spo2_variance', 0)
        if spo2_variance > 5:
            variance_score = min(100, spo2_variance * 8)
            fatigue_scores.append(variance_score)
        
        # Calcular fatiga final usando el promedio ponderado
        if fatigue_scores:
            # Dar más peso a los scores más altos (indicadores más críticos)
            fatigue_scores_sorted = sorted(fatigue_scores, reverse=True)
            
            # Promedio ponderado: primer score 40%, segundo 30%, resto 30%
            if len(fatigue_scores_sorted) >= 2:
                fatigue_index = (
                    fatigue_scores_sorted[0] * 0.40 +
                    fatigue_scores_sorted[1] * 0.30 +
                    sum(fatigue_scores_sorted[2:]) / max(1, len(fatigue_scores_sorted[2:])) * 0.30
                )
            else:
                fatigue_index = fatigue_scores_sorted[0]
        else:
            fatigue_index = 0
        
        # Asegurar rango 0-100
        fatigue_index = max(0.0, min(100.0, fatigue_index))
        
        logger.debug(f"Cálculo placeholder: HR={hr_avg:.1f}, SpO2={spo2_avg:.1f}, "
                    f"HRV={hrv_rmssd}, Actividad={activity_level:.3f} -> Fatiga={fatigue_index:.1f}")
        
        return fatigue_index
    
    def get_model_info(self):
        """
        Obtiene información sobre el modelo cargado.
        
        Returns:
            dict: Diccionario con información del modelo.
        """
        if not self.model_loaded:
            return {
                'loaded': False,
                'message': 'Modelo no cargado. Usando cálculo placeholder.'
            }
        
        info = {
            'loaded': True,
            'model_type': self.model_type,
            'n_features': len(self.selected_features),
            'features': self.selected_features
        }
        
        if self.model_type == 'kmeans':
            info['n_clusters'] = len(self.cluster_fatigue_map)
            info['cluster_fatigue_map'] = self.cluster_fatigue_map
        
        return info
    
    def reload_model(self):
        """
        Recarga el modelo desde disco.
        Útil después de reentrenar el modelo.
        
        Returns:
            bool: True si se recargó exitosamente, False en caso contrario.
        """
        print("🔄 Recargando modelo ML...")
        self.model = None
        self.scaler = None
        self.selected_features = []
        self.cluster_fatigue_map = {}
        self.model_loaded = False
        
        return self.load_model()


# Instancia global del servicio
ml_service = FatigueMLService()


# Funciones de conveniencia
def predict_fatigue(metrics_dict):
    """
    Función de conveniencia para predecir fatiga.
    
    Args:
        metrics_dict (dict): Diccionario con métricas procesadas.
    
    Returns:
        float: Índice de fatiga predicho (0-100).
    """
    return ml_service.predict_fatigue_index(metrics_dict)


def get_model_status():
    """
    Función de conveniencia para obtener estado del modelo.
    
    Returns:
        dict: Información del modelo.
    """
    return ml_service.get_model_info()


def reload_ml_model():
    """
    Función de conveniencia para recargar el modelo.
    
    Returns:
        bool: True si se recargó exitosamente.
    """
    return ml_service.reload_model()
