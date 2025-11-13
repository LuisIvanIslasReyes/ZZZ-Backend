"""
Script para entrenar el modelo de ML con datos del simulador ESP32.

Pasos:
1. Ejecutar simulador ESP32 para generar datos
2. Procesar datos con notebooks
3. Entrenar modelo de clustering
"""

import os
import sys
import subprocess
import time
from pathlib import Path

print("=" * 80)
print("SCRIPT DE ENTRENAMIENTO - MODELO DE DETECCIÓN DE FATIGA")
print("=" * 80)
print()

# Verificar que estamos en el directorio correcto
if not os.path.exists('manage.py'):
    print("❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto")
    sys.exit(1)

# 1. VERIFICAR DEPENDENCIAS
print("📦 1. VERIFICANDO DEPENDENCIAS...")
print("-" * 80)

required_files = [
    'esp32_simulator.py',
    'notebooks/01_data_exploration.py',
    'notebooks/02_feature_engineering.py',
    'notebooks/03_clustering_model.py'
]

for file in required_files:
    if not os.path.exists(file):
        print(f"❌ Archivo requerido no encontrado: {file}")
        sys.exit(1)
    print(f"✅ {file}")

print()

# 2. EJECUTAR SIMULADOR ESP32
print("🤖 2. GENERANDO DATOS DE PRUEBA CON SIMULADOR ESP32")
print("-" * 80)
print("   Esto generará datos de sensores simulados para entrenamiento...")
print("   Presiona Ctrl+C cuando tengas suficientes datos (recomendado: ~2-5 minutos)")
print()

response = input("¿Deseas ejecutar el simulador ESP32? (s/n): ")
if response.lower() == 's':
    try:
        print("\n⏳ Iniciando simulador ESP32...")
        print("   (Presiona Ctrl+C para detener cuando tengas suficientes datos)")
        print()
        
        # Ejecutar simulador
        process = subprocess.Popen(
            [sys.executable, 'esp32_simulator.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Esperar un tiempo mínimo
        try:
            process.wait(timeout=120)  # 2 minutos mínimo
        except subprocess.TimeoutExpired:
            print("\n✅ Tiempo mínimo alcanzado. Presiona Ctrl+C para continuar...")
            try:
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
                print("\n✅ Simulador detenido por el usuario")
        
    except KeyboardInterrupt:
        print("\n✅ Simulador detenido por el usuario")
    except Exception as e:
        print(f"\n⚠️ Error ejecutando simulador: {e}")
        print("   Puedes ejecutarlo manualmente: python esp32_simulator.py")
else:
    print("⏩ Saltando generación de datos. Asegúrate de tener datos en la BD.")

print()

# 3. PROCESAR DATOS CON NOTEBOOKS
print("📊 3. PROCESANDO DATOS CON NOTEBOOKS")
print("-" * 80)

# 3.1 Data Exploration
print("\n📈 Paso 3.1: Exploración de datos...")
try:
    result = subprocess.run(
        [sys.executable, 'notebooks/01_data_exploration.py'],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode == 0:
        print("✅ Exploración de datos completada")
    else:
        print("⚠️ Advertencia en exploración de datos:")
        print(result.stderr[-500:] if result.stderr else "Error desconocido")
except subprocess.TimeoutExpired:
    print("⚠️ Timeout en exploración de datos (5 min)")
except Exception as e:
    print(f"⚠️ Error: {e}")

# 3.2 Feature Engineering
print("\n🔧 Paso 3.2: Ingeniería de características...")
try:
    result = subprocess.run(
        [sys.executable, 'notebooks/02_feature_engineering.py'],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode == 0:
        print("✅ Ingeniería de características completada")
        
        # Verificar que se crearon los archivos necesarios
        if os.path.exists('notebooks/ml_dataset_scaled.csv'):
            print("   ✓ ml_dataset_scaled.csv creado")
        if os.path.exists('notebooks/scaler_config.pkl'):
            print("   ✓ scaler_config.pkl creado")
    else:
        print("⚠️ Advertencia en feature engineering:")
        print(result.stderr[-500:] if result.stderr else "Error desconocido")
except subprocess.TimeoutExpired:
    print("⚠️ Timeout en feature engineering (5 min)")
except Exception as e:
    print(f"⚠️ Error: {e}")

print()

# 4. ENTRENAR MODELO DE CLUSTERING
print("🤖 4. ENTRENANDO MODELO DE CLUSTERING")
print("-" * 80)

# Verificar archivos previos
if not os.path.exists('notebooks/ml_dataset_scaled.csv'):
    print("❌ Error: No se encontró ml_dataset_scaled.csv")
    print("   Asegúrate de tener datos en la BD y ejecutar los notebooks previos")
    sys.exit(1)

try:
    print("\n⏳ Entrenando modelo K-Means...")
    result = subprocess.run(
        [sys.executable, 'notebooks/03_clustering_model.py'],
        capture_output=True,
        text=True,
        timeout=600
    )
    
    if result.returncode == 0:
        print("✅ Modelo de clustering entrenado exitosamente")
        
        # Mostrar últimas líneas del output
        output_lines = result.stdout.split('\n')
        print("\n" + '\n'.join(output_lines[-30:]))
        
    else:
        print("❌ Error entrenando modelo:")
        print(result.stderr[-1000:] if result.stderr else "Error desconocido")
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("⚠️ Timeout en entrenamiento del modelo (10 min)")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print()

# 5. VERIFICAR ARCHIVOS GENERADOS
print("📁 5. VERIFICANDO ARCHIVOS GENERADOS")
print("-" * 80)

expected_files = [
    'ml_models/fatigue_model.pkl',
    'ml_models/fatigue_model_dbscan.pkl',
    'ml_models/model_metadata.json',
    'notebooks/clustering_analysis.png'
]

all_ok = True
for file in expected_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file} ({size:,} bytes)")
    else:
        print(f"❌ {file} - NO ENCONTRADO")
        all_ok = False

print()

# 6. RESUMEN FINAL
if all_ok:
    print("=" * 80)
    print("✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
    print("=" * 80)
    print()
    print("📊 Modelo de ML listo para usar:")
    print("   - Archivo principal: ml_models/fatigue_model.pkl")
    print("   - Metadata: ml_models/model_metadata.json")
    print("   - Visualizaciones: notebooks/clustering_analysis.png")
    print()
    print("💡 Próximos pasos:")
    print("   1. Revisar visualizaciones: notebooks/clustering_analysis.png")
    print("   2. Verificar metadata del modelo: ml_models/model_metadata.json")
    print("   3. Probar predicciones con el servicio ML")
    print("   4. Ejecutar tests: pytest apps/")
    print()
    print("🚀 El sistema ya puede predecir niveles de fatiga automáticamente!")
    print("=" * 80)
else:
    print("=" * 80)
    print("⚠️ ENTRENAMIENTO COMPLETADO CON ADVERTENCIAS")
    print("=" * 80)
    print()
    print("Algunos archivos no se generaron correctamente.")
    print("Revisa los logs anteriores para identificar problemas.")
    print()
