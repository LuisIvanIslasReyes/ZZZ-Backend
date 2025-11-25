# API: Exportar Datos del Empleado

## Descripción
Endpoint que permite al empleado autenticado descargar todos sus datos personales, métricas, alertas y recomendaciones en un archivo Excel (.xlsx).

---

## Endpoint

**URL:** `/api/auth/employee/export-my-data/`  
**Método:** `GET`  
**Autenticación:** Requerida (JWT Token)

---

## Cómo consumir desde el frontend

### TypeScript/JavaScript (usando Axios)

```typescript
import axios from 'axios';

const exportMyData = async () => {
  try {
    const response = await axios.get('/auth/employee/export-my-data/', {
      responseType: 'blob', // Importante para archivos binarios
      headers: {
        'Authorization': `Bearer ${token}` // Token JWT del usuario
      }
    });
    
    // Crear un enlace de descarga
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `mis_datos_${Date.now()}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    console.log('✅ Archivo descargado exitosamente');
  } catch (error) {
    console.error('❌ Error al descargar datos:', error);
  }
};
```

### Fetch API

```javascript
const exportMyData = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/auth/employee/export-my-data/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Error al descargar datos');
    }
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mis_datos_${Date.now()}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
    
    console.log('✅ Archivo descargado exitosamente');
  } catch (error) {
    console.error('❌ Error al descargar datos:', error);
  }
};
```

---

## Respuesta

**Tipo de contenido:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`  
**Archivo:** `mis_datos_{user_id}.xlsx`

El archivo Excel contiene **4 hojas**:

### 1. Información Personal
- Nombre completo
- Email
- Teléfono
- Departamento
- Puesto
- Rol
- Empresa
- Supervisor
- Estado (Activo/Inactivo)
- Fecha de registro

### 2. Historial de Métricas
- Fecha y hora
- HR Promedio (BPM)
- HR Máximo (BPM)
- SpO2 Promedio (%)
- HRV RMSSD (ms)
- Índice de Fatiga
- Nivel de Actividad
- Estado

**Nota:** Si no hay métricas, se muestra: *"Sin datos registrados aún"*

### 3. Alertas Recibidas
- Fecha
- Tipo de alerta
- Severidad
- Descripción
- Estado (Resuelta/Pendiente)
- Fecha de resolución

**Nota:** Si no hay alertas, se muestra: *"Sin datos registrados aún"*

### 4. Recomendaciones Aplicadas
- Fecha
- Tipo de recomendación
- Descripción
- Estado
- Aplicada (Sí/No)

**Nota:** Si no hay recomendaciones, se muestra: *"Sin datos registrados aún"*

---

## Errores comunes

### 401 Unauthorized
- **Causa:** Token JWT inválido o no proporcionado
- **Solución:** Verificar que el token esté presente y sea válido

### 404 Not Found
- **Causa:** URL incorrecta
- **Solución:** Asegurarse de usar `/api/auth/employee/export-my-data/`

### 500 Internal Server Error
- **Causa:** Error en el servidor al generar el archivo
- **Solución:** Revisar logs del backend

---

## Implementación en React (ejemplo completo)

```tsx
import React from 'react';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { api } from '@/services/api';

const DownloadMyDataButton: React.FC = () => {
  const [loading, setLoading] = React.useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const response = await api.get('/auth/employee/export-my-data/', {
        responseType: 'blob'
      });

      // Crear enlace de descarga
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `mis_datos_${Date.now()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      alert('✅ Datos descargados exitosamente');
    } catch (error) {
      console.error('Error al descargar datos:', error);
      alert('❌ Error al descargar los datos. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button 
      onClick={handleDownload} 
      disabled={loading}
      className="flex items-center gap-2"
    >
      <Download size={16} />
      {loading ? 'Descargando...' : 'Descargar Mis Datos'}
    </Button>
  );
};

export default DownloadMyDataButton;
```

---

## Seguridad

- ✅ Solo usuarios autenticados pueden acceder
- ✅ Cada usuario solo puede descargar sus propios datos
- ✅ No se requieren permisos especiales (cualquier empleado puede descargar)
- ✅ El backend valida automáticamente el token JWT

---

## Notas adicionales

1. **Límite de métricas:** Por defecto, se exportan las últimas 100 métricas. Si necesitas más, contacta al equipo de desarrollo.

2. **Tamaño del archivo:** El archivo generado tiene un tamaño variable según la cantidad de datos del empleado (típicamente entre 50KB - 500KB).

3. **Compatibilidad:** El archivo Excel es compatible con:
   - Microsoft Excel 2007 o superior
   - Google Sheets
   - LibreOffice Calc
   - Apple Numbers

4. **Formato de fechas:** Todas las fechas se exportan en formato `YYYY-MM-DD HH:MM:SS` (ISO 8601).

---

## Testing

Para probar el endpoint desde el navegador o Postman:

1. Asegúrate de estar autenticado
2. Realiza una petición GET a: `http://localhost:8000/api/auth/employee/export-my-data/`
3. Incluye el header: `Authorization: Bearer {tu_token_jwt}`
4. El navegador debe descargar automáticamente el archivo Excel

---

## Soporte

Si encuentras problemas o necesitas modificaciones en el formato del archivo Excel, contacta al equipo de backend.
