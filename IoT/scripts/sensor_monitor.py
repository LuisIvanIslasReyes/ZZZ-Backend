"""
Script de ejemplo: Lectura de sensores desde Python
Este script demuestra cómo llamar funciones C desde Python
"""

import sensors
import time
import math

def calculate_heart_rate(ir_values, sampling_rate=100):
    """
    Algoritmo simple para detectar picos y estimar frecuencia cardíaca
    """
    if len(ir_values) < 10:
        return 0
    
    # Detectar picos
    peaks = 0
    threshold = sum(ir_values) / len(ir_values) * 1.1
    
    for i in range(1, len(ir_values) - 1):
        if ir_values[i] > threshold and ir_values[i] > ir_values[i-1] and ir_values[i] > ir_values[i+1]:
            peaks += 1
    
    # Calcular BPM
    duration_seconds = len(ir_values) / sampling_rate
    bpm = (peaks / duration_seconds) * 60
    return bpm

def detect_movement(accel_history):
    """
    Detecta movimiento brusco basándose en cambios en aceleración
    """
    if len(accel_history) < 2:
        return False
    
    last = accel_history[-1]
    prev = accel_history[-2]
    
    # Calcular magnitud de cambio
    delta = math.sqrt(
        (last[0] - prev[0])**2 +
        (last[1] - prev[1])**2 +
        (last[2] - prev[2])**2
    )
    
    return delta > 0.5  # Umbral de movimiento

def main():
    """Función principal"""
    sensors.log_message("Iniciando monitoreo de sensores...")
    
    # Inicializar sensores
    print("Inicializando XD58C (sensor analógico)...")
    sensors.xd58c_init()
    
    print("Inicializando ADXL345...")
    sensors.adxl345_init()
    
    print("Calibrando acelerómetro...")
    sensors.adxl345_calibrate()
    
    # Buffers para análisis
    ir_buffer = []
    accel_history = []
    
    print("\n=== Iniciando monitoreo ===\n")
    
    iteration = 0
    
    while True:
        iteration += 1
        
        # Leer sensor de pulso XD58C (analógico)
        adc_value = sensors.xd58c_read()
        ir_buffer.append(adc_value)
        
        # Mantener buffer de últimos 100 valores
        if len(ir_buffer) > 100:
            ir_buffer.pop(0)
        
        # Leer acelerómetro
        x, y, z = sensors.adxl345_read()
        accel_history.append((x, y, z))
        
        if len(accel_history) > 20:
            accel_history.pop(0)
        
        # Calcular métricas cada 10 iteraciones
        if iteration % 10 == 0:
            voltage_mv = sensors.xd58c_voltage()
            hr = calculate_heart_rate(ir_buffer)
            movement = detect_movement(accel_history)
            
            print(f"\n--- Iteración {iteration} ---")
            print(f"XD58C:")
            print(f"  ADC: {adc_value}, Voltaje: {voltage_mv}mV")
            print(f"  Frecuencia cardíaca estimada: {hr:.1f} BPM")
            
            print(f"ADXL345:")
            print(f"  X: {x:.3f}g, Y: {y:.3f}g, Z: {z:.3f}g")
            print(f"  Movimiento detectado: {'SÍ' if movement else 'NO'}")
            
            sensors.log_message(f"Medición completada - HR: {hr:.1f} BPM")
        
        time.sleep(0.1)  # 10Hz de muestreo

if __name__ == "__main__":
    main()
