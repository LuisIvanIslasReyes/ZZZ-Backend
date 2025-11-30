# ✅ Notificación Automática: Síntoma Revisado

## 🎯 Funcionalidad Implementada

Cuando el **supervisor revisa un síntoma** y agrega sus comentarios, el **empleado recibe automáticamente una alerta** en su dashboard.

---

## 📋 Cómo Funciona

### 1. Supervisor Revisa Síntoma

```http
POST /api/symptom-reports/{id}/review/
Authorization: Bearer {token_supervisor}

Body: {
  "notes": "Toma un descanso de 15 minutos y bebe agua."
}
```

### 2. Backend Crea Alerta Automáticamente

Dentro del método `review()`, después de guardar la revisión:

```python
# ✅ AUTOMÁTICO - NO REQUIERE LLAMADA ADICIONAL
FatigueAlert.objects.create(
    employee=report.employee,
    supervisor=request.user,
    severity='low',  # Notificación informativa
    alert_type='symptom_reviewed',
    message=f"✅ Tu síntoma '{symptom_label}' ha sido revisado\n\n"
            f"📝 Comentarios del supervisor:\n{notes}",
    fatigue_index=0.0,
    is_resolved=False
)
```

### 3. Empleado Ve la Alerta

El empleado verá en su dashboard de alertas:

```
┌─────────────────────────────────────────┐
│ 🔔 Nueva Alerta - Prioridad: Baja      │
├─────────────────────────────────────────┤
│ ✅ Tu síntoma 'Dolor de cabeza' ha      │
│    sido revisado                        │
│                                         │
│ 📝 Comentarios del supervisor:          │
│ Toma un descanso de 15 minutos y       │
│ bebe agua.                              │
│                                         │
│ ✉️ De: Supervisor López                 │
│ 📅 30/11/2025 - 15:45                   │
│                                         │
│ [✓ Marcar como Leída]                  │
└─────────────────────────────────────────┘
```

---

## 🔄 Flujo Completo

```
1. Empleado reporta síntoma
   POST /api/symptom-reports/
   { "symptom_type": "headache", "severity": "moderate" }
       ↓
2. Supervisor ve síntoma pendiente
   GET /api/symptom-reports/pending/
   Badge rojo: "1 pendiente"
       ↓
3. Supervisor revisa y agrega notas
   POST /api/symptom-reports/1/review/
   { "notes": "Toma descanso de 15 min" }
       ↓
4. Backend hace AUTOMÁTICAMENTE:
   ✅ Marca síntoma como revisado
   ✅ Guarda notas del supervisor
   ✅ Crea FatigueAlert para el empleado
       ↓
5. Empleado ve nueva alerta
   GET /api/alerts/
   🔔 "Tu síntoma ha sido revisado"
       ↓
6. Empleado puede:
   - Ver las notas del supervisor
   - Marcar la alerta como leída
   - Ver historial en "Mis Síntomas"
```

---

## 📊 Respuesta del Endpoint

### Antes (SIN notificación automática):
```json
{
  "message": "Reporte revisado exitosamente. El empleado será notificado.",
  "report": { ... }
}
```

### Ahora (CON notificación automática):
```json
{
  "message": "Reporte revisado exitosamente. El empleado ha sido notificado.",
  "report": {
    "id": 1,
    "is_reviewed": true,
    "reviewed_by": { "full_name": "Supervisor López" },
    "reviewed_at": "2025-11-30T15:45:00Z",
    "notes": "Toma un descanso de 15 minutos y bebe agua."
  }
}
```

**Nota:** El mensaje cambió de "será notificado" a "ha sido notificado" porque la alerta ya fue creada.

---

## 💻 Implementación Frontend

### No requiere cambios adicionales

El frontend **NO necesita hacer nada extra**. La notificación se crea automáticamente cuando el supervisor revisa el síntoma.

```typescript
// El código actual ya funciona
const handleReviewSymptom = async (id: number, notes: string) => {
  // Solo esto es necesario
  await symptomService.reviewSymptom(id, notes);
  
  // ✅ El backend automáticamente:
  // - Marca como revisado
  // - Guarda las notas
  // - Crea alerta para el empleado
  
  toast.success('✅ Revisado. El empleado ha sido notificado.');
};
```

### Verificación en Dashboard del Empleado

El empleado verá la alerta en:

1. **Dashboard principal:**
```typescript
GET /api/alerts/
// Incluye la nueva alerta con type='symptom_reviewed'
```

2. **Badge de alertas:**
```typescript
GET /api/alerts/unresolved-count/
// El contador incluye esta alerta
```

3. **Página "Mis Síntomas":**
```typescript
GET /api/symptom-reports/my-reports/
// El síntoma aparece con is_reviewed=true y las notas
```

---

## 🎨 Tipos de Notificación

### Síntoma Normal (moderate/mild):

```
Severity: low (informativa)
Tipo: symptom_reviewed
Mensaje: "✅ Tu síntoma 'X' ha sido revisado"
```

### Síntoma Severo (auto-aprobado):

```
Severity: high (crítica)
Tipo: high_fatigue o auto_approval
Mensaje: "⚠️ Síntoma severo - Auto-aprobado automáticamente"
```

---

## ✅ Características

✅ **Automático:** No requiere código adicional  
✅ **Inmediato:** Se crea al momento de revisar  
✅ **Bidireccional:** Supervisor revisa → Empleado notificado  
✅ **Completo:** Incluye notas del supervisor  
✅ **Rastreable:** Queda en historial de alertas  
✅ **Resoluble:** Empleado puede marcar como leída  

---

## 🧪 Testing

### Prueba Manual:

1. **Login como empleado**
```http
POST /api/auth/login/
{ "email": "empleado@empresa.com", "password": "password123" }
```

2. **Reportar síntoma**
```http
POST /api/symptom-reports/
{ "symptom_type": "headache", "severity": "moderate", "description": "Dolor leve" }
```

3. **Login como supervisor**
```http
POST /api/auth/login/
{ "email": "supervisor@empresa.com", "password": "password123" }
```

4. **Revisar síntoma**
```http
POST /api/symptom-reports/1/review/
{ "notes": "Toma descanso de 15 minutos" }
```

5. **Login como empleado nuevamente**
```http
POST /api/auth/login/
{ "email": "empleado@empresa.com", "password": "password123" }
```

6. **Verificar alerta nueva**
```http
GET /api/alerts/
// Debe incluir alerta tipo 'symptom_reviewed'
```

**Resultado esperado:**
```json
{
  "results": [
    {
      "id": 123,
      "alert_type": "symptom_reviewed",
      "severity": "low",
      "message": "✅ Tu síntoma 'Dolor de cabeza' ha sido revisado\n\n📝 Comentarios del supervisor:\nToma descanso de 15 minutos",
      "is_resolved": false,
      "timestamp": "2025-11-30T15:45:00Z"
    }
  ]
}
```

---

## 📝 Resumen para Frontend

### ¿Qué necesita hacer el frontend?

**NADA.** 

El código actual ya funciona correctamente:
- Supervisor revisa síntoma → Backend crea alerta automáticamente
- Empleado consulta `/api/alerts/` → Ve la nueva alerta

### ¿Qué cambió?

- ✅ **Antes:** Mensaje decía "será notificado" pero no pasaba nada
- ✅ **Ahora:** Se crea `FatigueAlert` automáticamente para el empleado

### ¿Dónde se ve?

- Dashboard de alertas del empleado (`/api/alerts/`)
- Badge de alertas no resueltas
- Página "Mis Síntomas" con las notas del supervisor

---

## 🔍 Detalles Técnicos

### Campos de la Alerta Creada:

```python
{
    'employee': report.employee,          # Empleado que reportó
    'supervisor': request.user,            # Supervisor que revisó
    'severity': 'low',                     # Prioridad baja (informativa)
    'alert_type': 'symptom_reviewed',      # Tipo específico
    'message': '✅ Tu síntoma... 📝...',    # Mensaje formateado
    'fatigue_index': 0.0,                  # No aplica
    'is_resolved': False                   # Empleado debe marcarla
}
```

### Traducción de Síntomas:

```python
SYMPTOM_TYPES = [
    ('fatigue', 'Fatiga/Cansancio'),
    ('headache', 'Dolor de cabeza'),
    ('dizziness', 'Mareo'),
    ('nausea', 'Náuseas'),
    ('muscle_pain', 'Dolor muscular'),
    ('eye_strain', 'Fatiga visual'),
    ('stress', 'Estrés'),
    ('difficulty_concentrating', 'Dificultad para concentrarse'),
    ('shortness_of_breath', 'Dificultad para respirar'),
    ('other', 'Otro')
]
```

El mensaje usa la traducción automáticamente.

---

**Fecha:** 30/11/2025  
**Feature:** Notificación automática al revisar síntomas  
**Status:** ✅ Implementado  
**Frontend:** ✅ No requiere cambios  
**Testing:** ✅ Listo para probar
