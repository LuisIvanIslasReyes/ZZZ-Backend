"""
API Views para el dashboard de Machine Learning.
Proporciona información sobre el modelo, métricas, re-entrenamiento, etc.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.utils import timezone
from pathlib import Path
import json
import os
from datetime import timedelta

from apps.sensors.models import ProcessedMetrics, SensorData
from apps.analytics.ml_service import ml_service


class MLModelInfoView(APIView):
    """
    Información del modelo ML actual.
    GET /api/ml/model-info/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Devuelve información detallada del modelo ML"""
        try:
            base_dir = Path(settings.BASE_DIR)
            model_path = base_dir / 'ml_models' / 'fatigue_model.pkl'
            metadata_path = base_dir / 'ml_models' / 'model_metadata.json'
            
            # Verificar existencia del modelo
            model_exists = model_path.exists()
            
            # Cargar metadata si existe
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Información del servicio ML
            ml_status = {
                'loaded': ml_service.model_loaded,
                'type': ml_service.model_type,
                'features_count': len(ml_service.selected_features) if ml_service.selected_features else 0,
                'features': ml_service.selected_features if ml_service.selected_features else [],
                'clusters': list(ml_service.cluster_fatigue_map.keys()) if ml_service.cluster_fatigue_map else []
            }
            
            # Tamaño del archivo
            model_size_mb = 0
            if model_exists:
                model_size_mb = model_path.stat().st_size / 1024 / 1024
            
            # Datos de entrenamiento
            training_info = {
                'samples': metadata.get('training_samples', 0),
                'date': metadata.get('training_date', None),
                'clusters': metadata.get('n_clusters', 0),
                'algorithm': metadata.get('algorithm', 'K-Means'),
                'cluster_distribution': metadata.get('cluster_distribution', {}),
                'cluster_fatigue_map': metadata.get('cluster_fatigue_map', {})
            }
            
            # Métricas de calidad (si existen)
            quality_metrics = {
                'silhouette_score': metadata.get('silhouette_score'),
                'davies_bouldin_index': metadata.get('davies_bouldin_index'),
                'calinski_harabasz_index': metadata.get('calinski_harabasz_index')
            }
            
            return Response({
                'model_exists': model_exists,
                'model_size_mb': round(model_size_mb, 2),
                'model_path': str(model_path.name) if model_exists else None,
                'ml_service': ml_status,
                'training': training_info,
                'quality_metrics': quality_metrics,
                'metadata': metadata
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MLStatisticsView(APIView):
    """
    Estadísticas de uso del modelo ML.
    GET /api/ml/statistics/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Devuelve estadísticas de predicciones ML"""
        try:
            # Total de predicciones realizadas
            total_predictions = ProcessedMetrics.objects.count()
            
            # Predicciones últimas 24 horas
            yesterday = timezone.now() - timedelta(days=1)
            predictions_24h = ProcessedMetrics.objects.filter(
                created_at__gte=yesterday
            ).count()
            
            # Predicciones última semana
            last_week = timezone.now() - timedelta(days=7)
            predictions_7d = ProcessedMetrics.objects.filter(
                created_at__gte=last_week
            ).count()
            
            # Distribución de niveles de fatiga
            from django.db.models import Count, Q
            
            fatigue_distribution = {
                'normal': ProcessedMetrics.objects.filter(fatigue_index__lt=55).count(),
                'moderate': ProcessedMetrics.objects.filter(
                    fatigue_index__gte=55,
                    fatigue_index__lt=65
                ).count(),
                'high': ProcessedMetrics.objects.filter(fatigue_index__gte=65).count()
            }
            
            # Promedio de fatiga
            from django.db.models import Avg
            avg_fatigue = ProcessedMetrics.objects.aggregate(
                avg=Avg('fatigue_index')
            )['avg'] or 0
            
            # Datos de sensores disponibles
            total_sensor_data = SensorData.objects.count()
            sensor_data_24h = SensorData.objects.filter(
                timestamp__gte=yesterday
            ).count()
            
            return Response({
                'predictions': {
                    'total': total_predictions,
                    'last_24h': predictions_24h,
                    'last_7d': predictions_7d,
                    'average_fatigue': round(avg_fatigue, 2)
                },
                'fatigue_distribution': fatigue_distribution,
                'sensor_data': {
                    'total': total_sensor_data,
                    'last_24h': sensor_data_24h
                }
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MLRetrainingView(APIView):
    """
    Gestión de re-entrenamiento del modelo.
    GET /api/ml/retraining/ - Ver estado
    POST /api/ml/retraining/ - Iniciar re-entrenamiento
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Devuelve información sobre re-entrenamiento"""
        try:
            base_dir = Path(settings.BASE_DIR)
            metadata_path = base_dir / 'ml_models' / 'model_metadata.json'
            
            # Cargar metadata
            last_training = None
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    last_training = metadata.get('training_date')
            
            # Datos disponibles para re-entrenar
            available_metrics = ProcessedMetrics.objects.count()
            min_required = 100
            
            # Calcular próximo re-entrenamiento (si fue hace menos de 7 días)
            next_training = None
            if last_training:
                from datetime import datetime
                last_date = datetime.fromisoformat(last_training.replace('Z', '+00:00'))
                next_date = last_date + timedelta(days=7)
                next_training = next_date.isoformat()
            
            return Response({
                'last_training': last_training,
                'next_scheduled': next_training,
                'available_metrics': available_metrics,
                'min_required': min_required,
                'can_retrain': available_metrics >= min_required,
                'status': 'ready' if available_metrics >= min_required else 'insufficient_data'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Inicia re-entrenamiento manual del modelo"""
        # Solo admin puede re-entrenar
        if request.user.role not in ['admin', 'supervisor']:
            return Response(
                {'error': 'No tienes permisos para re-entrenar el modelo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            import subprocess
            from django.conf import settings
            
            base_dir = Path(settings.BASE_DIR)
            training_script = base_dir / 'train_simple_model.py'
            
            if not training_script.exists():
                return Response(
                    {'error': 'Script de entrenamiento no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar datos suficientes
            metrics_count = ProcessedMetrics.objects.count()
            force = request.data.get('force', False)
            min_required = 100
            
            if not force and metrics_count < min_required:
                return Response({
                    'error': f'Insuficientes datos: {metrics_count} < {min_required}',
                    'available_metrics': metrics_count,
                    'min_required': min_required,
                    'message': 'Use force=true para entrenar de todas formas'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ejecutar entrenamiento en background
            python_executable = os.path.join(base_dir, 'venv', 'Scripts', 'python.exe')
            if not os.path.exists(python_executable):
                python_executable = 'python'
            
            # Iniciar proceso en background
            subprocess.Popen(
                [python_executable, str(training_script)],
                cwd=str(base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return Response({
                'status': 'started',
                'message': 'Re-entrenamiento iniciado en background',
                'metrics_count': metrics_count,
                'estimated_time': '1-2 minutos'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MLPredictionHistoryView(APIView):
    """
    Histórico de predicciones del modelo.
    GET /api/ml/predictions/history/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Devuelve histórico de predicciones"""
        try:
            # Parámetros de filtrado
            limit = int(request.query_params.get('limit', 50))
            device_id = request.query_params.get('device')
            
            # Query base
            queryset = ProcessedMetrics.objects.select_related(
                'device', 'employee'
            ).order_by('-window_start')
            
            # Filtrar por dispositivo si se especifica
            if device_id:
                queryset = queryset.filter(device_id=device_id)
            
            # Filtrar por permisos
            user = request.user
            if user.role == 'employee':
                queryset = queryset.filter(employee=user)
            elif user.role == 'supervisor':
                queryset = queryset.filter(employee__supervisor=user)
            
            # Limitar resultados
            predictions = queryset[:limit]
            
            # Serializar
            data = []
            for pred in predictions:
                data.append({
                    'id': pred.id,
                    'timestamp': pred.window_start.isoformat(),
                    'device': pred.device.device_identifier,
                    'employee': pred.employee.get_full_name(),
                    'employee_id': pred.employee.id,
                    'fatigue_index': round(pred.fatigue_index, 2),
                    'hr_avg': round(pred.hr_avg, 1),
                    'spo2_avg': round(pred.spo2_avg, 1),
                    'activity_level': round(pred.activity_level, 2),
                    'classification': (
                        'normal' if pred.fatigue_index < 55
                        else 'moderate' if pred.fatigue_index < 65
                        else 'high'
                    )
                })
            
            return Response({
                'count': len(data),
                'predictions': data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
