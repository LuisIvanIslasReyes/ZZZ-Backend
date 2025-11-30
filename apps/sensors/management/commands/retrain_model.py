"""
Comando de management para re-entrenar el modelo ML manualmente.
Uso: python manage.py retrain_model [--force]
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.sensors.models import ProcessedMetrics
import os
import subprocess
from pathlib import Path


class Command(BaseCommand):
    help = 'Re-entrena el modelo ML con los datos actuales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar re-entrenamiento aunque no haya suficientes datos',
        )
        parser.add_argument(
            '--min-samples',
            type=int,
            default=100,
            help='Número mínimo de métricas requeridas (default: 100)',
        )

    def handle(self, *args, **options):
        force = options['force']
        min_samples = options['min_samples']
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🤖 RE-ENTRENAMIENTO DEL MODELO ML'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        
        # 1. Verificar datos disponibles
        self.stdout.write('📊 1. Verificando datos disponibles...')
        metrics_count = ProcessedMetrics.objects.count()
        self.stdout.write(f'   Métricas procesadas: {metrics_count}')
        
        if not force and metrics_count < min_samples:
            self.stdout.write(self.style.ERROR(
                f'❌ Insuficientes datos: {metrics_count} < {min_samples}'
            ))
            self.stdout.write(self.style.WARNING(
                f'   Usa --force para entrenar de todas formas'
            ))
            return
        
        self.stdout.write(self.style.SUCCESS('   ✅ Datos suficientes'))
        self.stdout.write('')
        
        # 2. Verificar script de entrenamiento
        self.stdout.write('📁 2. Verificando script de entrenamiento...')
        base_dir = Path(settings.BASE_DIR)
        training_script = base_dir / 'train_simple_model.py'
        
        if not training_script.exists():
            self.stdout.write(self.style.ERROR(
                f'❌ Script no encontrado: {training_script}'
            ))
            return
        
        self.stdout.write(f'   ✅ Script encontrado: {training_script.name}')
        self.stdout.write('')
        
        # 3. Ejecutar entrenamiento
        self.stdout.write('⚙️  3. Ejecutando entrenamiento...')
        self.stdout.write('   (Esto puede tomar 1-2 minutos)')
        self.stdout.write('')
        
        # Usar el Python del virtual environment
        python_executable = os.path.join(base_dir, 'venv', 'Scripts', 'python.exe')
        if not os.path.exists(python_executable):
            python_executable = 'python'
        
        try:
            result = subprocess.run(
                [python_executable, str(training_script)],
                cwd=str(base_dir),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Mostrar salida
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.stdout.write(f'   {line}')
            
            if result.returncode == 0:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Entrenamiento completado exitosamente'))
            else:
                self.stdout.write('')
                self.stdout.write(self.style.ERROR('❌ Error en el entrenamiento:'))
                if result.stderr:
                    for line in result.stderr.split('\n')[:20]:  # Primeras 20 líneas
                        if line.strip():
                            self.stdout.write(f'   {line}')
                return
                
        except subprocess.TimeoutExpired:
            self.stdout.write(self.style.ERROR('❌ Timeout: entrenamiento cancelado (>5 minutos)'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error ejecutando script: {e}'))
            return
        
        # 4. Recargar modelo
        self.stdout.write('')
        self.stdout.write('🔄 4. Recargando modelo en memoria...')
        
        try:
            from apps.analytics.ml_service import ml_service
            
            if ml_service.load_model():
                self.stdout.write(self.style.SUCCESS('   ✅ Modelo recargado exitosamente'))
                self.stdout.write(f'   Tipo: {ml_service.model_type.upper()}')
                self.stdout.write(f'   Features: {len(ml_service.selected_features)}')
                self.stdout.write(f'   Clusters: {list(ml_service.cluster_fatigue_map.keys())}')
            else:
                self.stdout.write(self.style.WARNING('   ⚠️  No se pudo recargar el modelo'))
                self.stdout.write('   Reinicia el servidor para usar el nuevo modelo')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error recargando: {e}'))
            self.stdout.write('   Reinicia el servidor para usar el nuevo modelo')
        
        # 5. Verificar modelo
        self.stdout.write('')
        self.stdout.write('🔍 5. Verificando modelo...')
        
        model_path = base_dir / 'ml_models' / 'fatigue_model.pkl'
        metadata_path = base_dir / 'ml_models' / 'model_metadata.json'
        
        if model_path.exists():
            size_mb = model_path.stat().st_size / 1024 / 1024
            self.stdout.write(f'   ✅ Modelo: {model_path.name} ({size_mb:.2f} MB)')
        else:
            self.stdout.write(self.style.ERROR(f'   ❌ Modelo no encontrado: {model_path}'))
        
        if metadata_path.exists():
            import json
            with open(metadata_path) as f:
                metadata = json.load(f)
            self.stdout.write(f'   ✅ Metadata: {metadata.get("training_samples", "?")} muestras')
        
        # Resumen final
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('✅ RE-ENTRENAMIENTO COMPLETADO'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        self.stdout.write('💡 Próximos pasos:')
        self.stdout.write('   1. Verifica predicciones: python manage.py shell')
        self.stdout.write('      >>> from apps.analytics.ml_service import predict_fatigue')
        self.stdout.write('      >>> predict_fatigue({...})')
        self.stdout.write('')
        self.stdout.write('   2. O ejecuta: python verify_model_usage.py')
        self.stdout.write('')
