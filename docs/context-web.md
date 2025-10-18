Preguntas y supuestos
1. ¿Los supervisores verán nombres reales o datos anonimizados/agregados?
2. ¿Se requiere autenticar con SSO corporativo (SAML/Okta) o con sistema propio?
3. ¿Necesitas notificaciones en tiempo real en el dashboard?
4. ¿Qué métricas específicas deben estar en el KPI inicial?

Notas y siguientes pasos
- Crear skeleton en Vite + TypeScript y algunos mocks para los endpoints.

Actualizaciones según tus respuestas
- Autenticación: local (email/contraseña) con roles Admin>Supervisor>Empleado.
- Privacidad: los supervisores verán datos identificables; para la demo escolar podemos usar datos simulados/mocks. Aún así, dejar hooks para anonimizar en producción.
- Tiempo real: no necesario; batch es suficiente. Web puede refrescar datos cada X minutos o usar polling/short-lived websocket para notificaciones.
- Notificaciones: usar FCM para push y también enviar resúmenes por email si se desea.

# Contexto técnico — Web (React)

Resumen rápido
- Stack recomendado: React 18+, Vite (o Create React App), TypeScript, React Query (o SWR) para data fetching, Recharts/Chart.js/D3 para visualizaciones, TailwindCSS o MUI para diseño.
- Propósito: Panel para supervisores, visualizaciones de series temporales, alertas y herramientas para explorar patrones de estrés. Integración con ML para mostrar insights.

Requisitos funcionales clave
- Login/SSO para supervisores
- Dashboard con KPIs (niveles de estrés promedio, tendencias por equipo)
- Visualizaciones: series temporales, histogramas, heatmaps por jornada
- Filtros: por equipo, rango de fechas, empleado
- Página de detalle de empleado con timeline y eventos
- Exportar reportes (CSV, PDF)

Contrato con Backend (consumo de APIs)
- Autenticación: JWT bearer
- Endpoints esperados: /api/supervisor/reports, /api/employees/{id}/stress, /api/events/
- Websockets opcional para notificaciones en tiempo real

Estructura inicial del repo
- src/
  - api/ (clientes de API, react-query hooks)
  - components/ (common UI, charts)
  - features/ (dashboard, employee-detail)
  - pages/ (routes)
  - utils/ (date helpers, metrics)

Consideraciones UX
- Mostrar intervalos de confianza y explicar scores de estrés
- Diseño centrado en privacidad: evitar mostrar PII sin permiso

Preguntas y supuestos
1. ¿Los supervisores verán nombres reales o datos anonimizados/agregados?
2. ¿Se requiere autenticar con SSO corporativo (SAML/Okta) o con sistema propio?
3. ¿Necesitas notificaciones en tiempo real en el dashboard?
4. ¿Qué métricas específicas deben estar en el KPI inicial?

Notas y siguientes pasos
- Crear skeleton en Vite + TypeScript y algunos mocks para los endpoints.
