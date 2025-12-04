"""
Script simple: Prueba básica de sensores
"""

import sensors
import time

def test_basic():
    """Prueba básica de lectura de sensores"""
    
    print("=== PRUEBA BÁSICA DE SENSORES ===\n")
    
    # Inicializar
    sensors.xd58c_init()
    sensors.adxl345_init()
    
    for i in range(10):
        print(f"\n--- Lectura {i+1} ---")
        
        # XD58C (analógico)
        adc = sensors.xd58c_read()
        voltage = sensors.xd58c_voltage()
        print(f"Sensor de Pulso XD58C -> ADC: {adc}, Voltaje: {voltage}mV")
        
        # ADXL345
        x, y, z = sensors.adxl345_read()
        print(f"Acelerómetro -> X: {x:.3f}g, Y: {y:.3f}g, Z: {z:.3f}g")
        
        time.sleep(1)
    
    print("\n=== PRUEBA COMPLETADA ===")
    sensors.log_message("Prueba básica finalizada")

test_basic()
