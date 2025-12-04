"""
Ejemplo: Python llamando C y C llamando Python
"""

import sensors

# ============================================
# PYTHON LLAMANDO FUNCIONES EN C
# ============================================

def python_calls_c():
    """Ejemplo de Python llamando funciones nativas en C"""
    print("\n=== Python llamando funciones C ===\n")
    
    # Llamar función de log implementada en C
    sensors.log_message("Hola desde Python!")
    
    # Inicializar sensores (implementados en C)
    sensors.xd58c_init()
    sensors.adxl345_init()
    
    # Leer datos (drivers en C)
    adc_value = sensors.xd58c_read()
    voltage_mv = sensors.xd58c_voltage()
    print(f"Datos de C: ADC={adc_value}, Voltaje={voltage_mv}mV")
    
    x, y, z = sensors.adxl345_read()
    print(f"Datos de C: X={x:.3f}g, Y={y:.3f}g, Z={z:.3f}g")

# ============================================
# PYTHON DEFINIENDO FUNCIONES PARA C
# ============================================

def process_sensor_data(adc_value, x, y, z):
    """
    Función Python que procesa datos de sensores
    Esta función puede ser llamada desde C
    """
    # Calcular magnitud de aceleración
    magnitude = (x**2 + y**2 + z**2)**0.5
    
    # Normalizar valor ADC (0-4095 a 0-100%)
    pulse_percent = (adc_value / 4095) * 100
    
    result = {
        'accel_magnitude': magnitude,
        'pulse_percent': pulse_percent,
        'alert': magnitude > 1.5 or adc_value < 500
    }
    
    print(f"Procesamiento Python: {result}")
    return result

# Exponer función para que C la pueda llamar
__all__ = ['process_sensor_data']

# ============================================
# EJECUTAR DEMO
# ============================================

if __name__ == "__main__":
    python_calls_c()
    
    # Simular procesamiento
    import time
    for i in range(5):
        adc = sensors.xd58c_read()
        x, y, z = sensors.adxl345_read()
        
        result = process_sensor_data(adc, x, y, z)
        
        if result['alert']:
            sensors.log_message("¡ALERTA detectada desde Python!")
        
        time.sleep(1)
