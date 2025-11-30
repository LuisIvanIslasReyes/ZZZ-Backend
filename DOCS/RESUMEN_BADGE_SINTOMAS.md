# 🔥 RESUMEN: Badge Dinámico de Síntomas

## ❌ Problema Actual
El badge rojo en "Síntomas del Equipo" está **hardcodeado** en el frontend. Siempre aparece aunque no haya síntomas pendientes.

## ✅ Solución (Backend ya listo)

### 🚀 Nuevo Endpoint Creado
```http
GET /api/symptom-reports/pending-count/
```

**Respuesta:**
```json
{
  "count": 5,
  "by_severity": {
    "severe": 2,
    "moderate": 2,
    "mild": 1
  }
}
```

---

## 📝 Tareas Frontend (5 pasos)

### 1️⃣ MainLayout.tsx - Agregar Estado
```typescript
const [pendingSymptomsCount, setPendingSymptomsCount] = useState(0);
```

### 2️⃣ MainLayout.tsx - Cargar Datos con Polling
```typescript
useEffect(() => {
  const loadCount = async () => {
    const data = await symptomService.getPendingCount();
    setPendingSymptomsCount(data.count);
  };
  
  loadCount(); // Inicial
  const interval = setInterval(loadCount, 30000); // Cada 30s
  
  window.addEventListener('symptoms-updated', loadCount); // Evento
  
  return () => {
    clearInterval(interval);
    window.removeEventListener('symptoms-updated', loadCount);
  };
}, []);
```

### 3️⃣ MainLayout.tsx - Badge Dinámico
```typescript
{
  label: 'Síntomas del Equipo',
  badge: pendingSymptomsCount > 0 ? {
    color: 'red',
    count: pendingSymptomsCount
  } : undefined
}
```

### 4️⃣ TeamSymptomsPage.tsx - Emitir Evento
```typescript
const handleReview = async (id, comment) => {
  await symptomService.reviewSymptom(id, comment);
  
  // ✅ Emitir evento
  window.dispatchEvent(new CustomEvent('symptoms-updated'));
  
  toast.success('Revisado');
};
```

### 5️⃣ symptomService.ts - Agregar Método
```typescript
export const symptomService = {
  getPendingCount: async () => {
    const { data } = await axios.get(
      '/api/symptom-reports/pending-count/',
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return data;
  }
};
```

---

## 🎨 Resultado

**Antes:**
- Badge siempre visible ❌
- Número fijo/hardcodeado ❌
- No se actualiza ❌

**Después:**
- Badge solo si hay pendientes ✅
- Número real (ej: "5") ✅
- Auto-actualiza cada 30s ✅
- Actualiza al revisar ✅
- Badge rojo pulsante ✅

---

## 📦 Archivo de Referencia
Ver documentación completa en: **`DOCS/API_SINTOMAS.md`**

Incluye:
- ✅ Todos los endpoints de síntomas
- ✅ Código TypeScript completo
- ✅ CSS para badges
- ✅ Badge amarillo opcional para empleados
- ✅ Tabla de síntomas completa

---

**Backend:** ✅ Listo y probado  
**Frontend:** 5 cambios simples  
**Tiempo estimado:** 30 minutos
