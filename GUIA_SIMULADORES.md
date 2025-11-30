# 📊 GUÍA DE USO - SIMULADORES ESP32

## ✅ Problemas Resueltos

### 1. WARNING del Scheduler ✅
**Problema**: `WARNING Job 'process_metrics_auto' no longer exists!`

**Causa**: El scheduler usaba `DjangoJobStore` que persiste jobs en BD, causando warnings al reiniciar.

**Solución**: Cambiado a `MemoryJobStore` para jobs en memoria.

**Resultado**: Ya no aparecen warnings molestos.

---

### 2. Simuladores se Pierden al Reiniciar ✅
**Problema**: Simuladores en estado 'running' desaparecen de memoria cuando el servidor se reinicia.

**Solución**: Agregado método `_recover_running_simulators()` que:
- Se ejecuta automáticamente al iniciar `SimulatorManager`
- Busca sesiones con status='running' en BD
- Reinicia cada simulador en memoria
- Log detallado del proceso de recuperación

**Resultado**: Los simuladores se recuperan automáticamente al reiniciar.

---

## 🎯 Cómo Funcionan los Simuladores

### Intervalos de Tiempo
- **Actualización interna**: Cada **5 segundos** (por defecto)
- **Publicación MQTT**: Cada **5 segundos** (si MQTT disponible)
- **Actualización BD**: Cada ciclo actualiza fatiga, actividad, mensajes
- **Cambio automático de actividad**: Cada **2 minutos**

### Flujo de Datos

```
┌─────────────────────────────────────────┐
│   Frontend (React)                      │
│   - Crear simulador                     │
│   - Ver estado en tiempo real           │
│   - Detener/Reiniciar                   │
│   - Actualizar configuración            │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│   Django Backend                        │
│   /api/v1/simulators/                   │
│   - POST /        → Crear               │
│   - POST /{id}/stop/     → Detener      │
│   - POST /{id}/restart/  → Reiniciar    │
│   - POST /{id}/update_config/ → Config  │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│   SimulatorManager (Python)             │
│   - Gestiona múltiples simuladores      │
│   - Singleton en memoria                │
│   - Recuperación automática             │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│   ESP32SimulatorThread                  │
│   - Thread independiente por simulador  │
│   - Genera datos realistas:             │
│     • Heart Rate (HR)                   │
│     • SpO2                              │
│     • Aceleración 3 ejes (X,Y,Z)        │
│     • Nivel de fatiga                   │
│   - Modo local (sin MQTT)               │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│   Base de Datos (PostgreSQL)            │
│   - SimulatorSession (sesiones)         │
│   - Estado: running/stopped/error       │
│   - Fatiga actual                       │
│   - Actividad                           │
│   - Mensajes enviados                   │
└─────────────────────────────────────────┘
```

---

## 🔍 Cómo Verificar que un Simulador Funciona

### Opción 1: Monitor en Tiempo Real (Recomendado)
```bash
cd c:\xampp2\htdocs\UTT4B\ZZZ-Backend
.\venv\Scripts\python.exe monitor_simulator_live.py
```

**Verás**:
- 💓 Fatiga actual (0-100%)
- 🏃 Modo de actividad (resting/light/moderate/heavy)
- 📤 Mensajes enviados (incrementa cada 5 segundos)
- Stats en tiempo real (HR, SpO2, Fatiga)

### Opción 2: Verificación Rápida
```bash
.\venv\Scripts\python.exe check_simulators.py
```

**Muestra**:
- Simuladores en BD (running/stopped/error)
- Simuladores en memoria (activos)
- Comparación BD vs Memoria

### Opción 3: Frontend
- Ve a **Gestión de Simuladores**
- Los simuladores ACTIVOS muestran:
  - Badge verde "ACTIVO"
  - Fatiga actual actualizándose
  - Actividad actual
  - Duración transcurrida

---

## 📊 Estados de los Datos del Simulador

### Nivel de Fatiga (0-100%)
- **0-30%**: Descansado (Verde)
- **30-50%**: Normal (Azul)
- **50-70%**: Cansado (Amarillo)
- **70-85%**: Fatigado (Naranja)
- **85-100%**: Crítico (Rojo)

### Modos de Actividad
1. **resting (reposo)**
   - HR: ~65-75 bpm
   - SpO2: ~98-100%
   - Fatiga: Disminuye (-0.3/min)
   - Aceleración: Mínima (0.1g)

2. **light (ligera)**
   - HR: ~80-95 bpm
   - SpO2: ~96-99%
   - Fatiga: Aumenta lento (+0.1/min)
   - Aceleración: Baja (0.5g)

3. **moderate (moderada)**
   - HR: ~95-120 bpm
   - SpO2: ~94-97%
   - Fatiga: Aumenta medio (+0.3/min)
   - Aceleración: Media (1.2g)

4. **heavy (intensa)**
   - HR: ~120-140 bpm
   - SpO2: ~90-95%
   - Fatiga: Aumenta rápido (+0.8/min)
   - Aceleración: Alta (2.0g)

---

## 🎮 Controles Disponibles

### Desde el Frontend

1. **Crear Simulador**
   - Selecciona empleado
   - Configura parámetros iniciales
   - Auto-inicia en modo local

2. **Detener Simulador**
   - Estado → 'stopped'
   - Se guarda progreso
   - Puede reiniciarse después

3. **Reiniciar Simulador**
   - Solo para stopped/error
   - Resetea contadores
   - Inicia nuevo ciclo

4. **Actualizar Configuración** (en tiempo real)
   - `fatigue_level`: 0-100
   - `activity_mode`: reposo/ligera/moderada/intensa
   - `fatigue_rate`: 0-10 (velocidad de cambio)

5. **Detener Todos**
   - Detiene todos los simuladores activos
   - Útil para emergencias

---

## 🔧 Configuración Avanzada

### Parámetros Configurables en `simulator_manager.py`

```python
# Línea ~43: Intervalo de publicación
self.publish_interval = config.get('publish_interval', 5)  # segundos

# Línea ~234: Velocidad de cambio de fatiga
fatigue_changes = {
    'resting': -0.3,    # Recuperación
    'light': 0.1,       # Incremento lento
    'moderate': 0.3,    # Incremento medio
    'heavy': 0.8        # Incremento rápido
}

# Línea ~247: Frecuencia de cambio automático de actividad
if self.time_offset % (120 // self.publish_interval) == 0:  # 2 minutos
```

---

## 🐛 Troubleshooting

### El simulador no aparece en "Activos"
**Solución**: 
1. Verifica que esté en 'running' en BD
2. Reinicia el servidor (se recuperará automáticamente)
3. Revisa logs del servidor

### Mensajes no incrementan
**Causa**: MQTT no disponible (esperado)
**Solución**: 
- En modo local, los mensajes NO se publican a MQTT
- Los datos se actualizan internamente en BD
- Para ver MQTT funcionando, inicia Mosquitto:
  ```bash
  docker-compose up mosquitto
  ```

### Simulador en estado 'error'
**Solución**:
```bash
# Limpiar errores
.\venv\Scripts\python.exe clean_error_simulators.py

# Reiniciar simulador
# Desde frontend: botón "Reiniciar"
```

### Warning del Scheduler
**Ya Resuelto**: El warning ya no aparece después del cambio a MemoryJobStore

---

## 📈 Monitoreo de Performance

### Recursos por Simulador
- **Memoria**: ~2-5 MB por simulador
- **CPU**: <1% por simulador (idle la mayoría del tiempo)
- **Threads**: 1 thread por simulador
- **BD Queries**: ~1 query cada 5 segundos

### Límite Recomendado
- **Desarrollo**: 10-20 simuladores simultáneos
- **Producción**: 50-100 simuladores (depende del servidor)

---

## 🎯 Casos de Uso

### 1. Desarrollo y Testing
```bash
# Crear 3 simuladores de prueba
# Frontend → Nuevo Simulador (x3)

# Monitorear en tiempo real
.\venv\Scripts\python.exe monitor_simulator_live.py
```

### 2. Demo para Cliente
- Crear 5-10 simuladores con diferentes perfiles
- Mostrar dashboard en tiempo real
- Actualizar configuraciones en vivo
- Detener/reiniciar para mostrar controles

### 3. Testing de Carga
- Crear 20-50 simuladores
- Verificar performance del sistema
- Monitorear uso de recursos
- Validar alertas y recomendaciones ML

---

## 📝 Logs Importantes

### Al Iniciar Servidor
```
INFO ✅ SimulatorManager inicializado
INFO 🔄 Recuperando 3 simuladores...
INFO ✅ Simulador recuperado: ESP32-003
INFO ✅ Simulador recuperado: ESP32-004
INFO ✅ Simulador recuperado: ESP32-005
INFO ✅ Recuperación completa: 3 simuladores activos
```

### Durante Ejecución
```
INFO [ESP32-003] Conectando a localhost:1883
WARNING ⚠️  [ESP32-003] MQTT no disponible - Modo local
INFO 🔄 [ESP32-003] Iniciando loop de simulación...
INFO 🔄 [ESP32-003] Actividad: moderate, Fatiga: 45.2%
```

### Al Detener
```
INFO 🛑 [ESP32-003] Deteniendo simulador...
INFO ✅ [ESP32-003] Simulador detenido
INFO 🛑 Simulador detenido por admin@example.com: ESP32-003
```

---

## ✅ Checklist de Verificación

- [ ] Servidor Django corriendo sin warnings
- [ ] Al menos 1 simulador en estado 'running'
- [ ] Monitor en vivo muestra datos actualizándose
- [ ] Frontend muestra badge "ACTIVO" verde
- [ ] Fatiga cambia con el tiempo
- [ ] Actividad cambia automáticamente
- [ ] Se puede actualizar configuración
- [ ] Se puede detener/reiniciar
- [ ] Los logs no muestran errores críticos

---

**Última actualización**: 29 de Noviembre, 2025
**Versión Backend**: Django 4.2.7
**Estado**: ✅ Totalmente funcional en modo local (sin MQTT)
