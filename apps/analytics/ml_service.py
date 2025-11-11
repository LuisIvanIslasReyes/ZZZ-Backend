"""
ML Service - Sistema de Detección de Fatiga
Servicio para cargar y usar el modelo de machine learning.
"""

import os
import joblib
import numpy as np
from pathlib import Path
from django.conf import settings

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
        self.model_type = 'kmeans'
        
        # Intentar cargar el modelo al inicializar
        self.load_model()
    
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
        
        Args:
            metrics_dict (dict): Diccionario con las métricas procesadas.
                                Debe incluir todos los features seleccionados.
        
        Returns:
            float: Índice de fatiga predicho (0-100).
                   Si el modelo no está cargado, usa el cálculo placeholder.
        """
        if not self.model_loaded:
            # Fallback al cálculo placeholder
            return self._calculate_placeholder(metrics_dict)
        
        try:
            # Extraer features en el orden correcto
            feature_values = []
            for feature in self.selected_features:
                value = metrics_dict.get(feature, 0)
                # Manejar valores None
                if value is None:
                    value = 0
                feature_values.append(value)
            
            # Normalizar usando el scaler entrenado
            X = np.array([feature_values])
            X_scaled = self.scaler.transform(X)
            
            # Predecir cluster
            cluster = self.model.predict(X_scaled)[0]
            
            # Mapear cluster a nivel de fatiga
            if self.model_type == 'kmeans':
                fatigue_index = self.cluster_fatigue_map.get(cluster, 50.0)
            else:
                # Para DBSCAN u otros modelos, usar cálculo básico
                fatigue_index = self._calculate_placeholder(metrics_dict)
            
            # Asegurar que esté en rango 0-100
            fatigue_index = max(0.0, min(100.0, fatigue_index))
            
            return fatigue_index
            
        except Exception as e:
            print(f"⚠️  Error en predicción ML: {str(e)}")
            # Fallback al cálculo placeholder
            return self._calculate_placeholder(metrics_dict)
    
    def _calculate_placeholder(self, metrics_dict):
        """
        Cálculo placeholder de fatiga cuando el modelo no está disponible.
        Usa el mismo algoritmo que processors.py para compatibilidad.
        
        Args:
            metrics_dict (dict): Diccionario con métricas procesadas.
        
        Returns:
            float: Índice de fatiga calculado (0-100).
        """
        # Pesos para cada componente
        WEIGHT_HR_ACTIVITY = 0.40
        WEIGHT_SPO2 = 0.30
        WEIGHT_HRV = 0.20
        WEIGHT_DESATURATION = 0.10
        
        # Componente 1: Ratio HR/Actividad (40%)
        hr_activity_ratio = metrics_dict.get('hr_activity_ratio', 1.0)
        if hr_activity_ratio > 1.2:  # HR muy alto para la actividad
            hr_activity_score = min(100, (hr_activity_ratio - 1.0) * 100)
        else:
            hr_activity_score = 0
        
        # Componente 2: SpO2 (30%)
        spo2_avg = metrics_dict.get('spo2_avg', 98.0)
        if spo2_avg < 95:
            spo2_score = (95 - spo2_avg) * 20  # 1% menos = +20 puntos
        else:
            spo2_score = 0
        
        # Componente 3: HRV (20%)
        hrv_rmssd = metrics_dict.get('hrv_rmssd', 50.0)
        if hrv_rmssd < 30:  # HRV bajo indica estrés
            hrv_score = (30 - hrv_rmssd) * 2
        else:
            hrv_score = 0
        
        # Componente 4: Desaturaciones (10%)
        desaturation_count = metrics_dict.get('desaturation_count', 0)
        desaturation_score = min(100, desaturation_count * 25)  # Cada desaturación = +25 puntos
        
        # Calcular índice final
        fatigue_index = (
            hr_activity_score * WEIGHT_HR_ACTIVITY +
            spo2_score * WEIGHT_SPO2 +
            hrv_score * WEIGHT_HRV +
            desaturation_score * WEIGHT_DESATURATION
        )
        
        # Asegurar rango 0-100
        fatigue_index = max(0.0, min(100.0, fatigue_index))
        
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
