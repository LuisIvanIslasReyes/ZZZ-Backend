"""
Generador de Evidencias con Screenshots
Sistema de Detección de Fatiga - Pruebas de Funcionalidad

Este script genera un documento PDF profesional con capturas de pantalla
de cada respuesta de API como evidencia visual.
"""
import requests
import json
from datetime import datetime
from pathlib import Path
import time
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# Configuración
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"
AUTH_URL = f"{BASE_URL}/api/auth"

TEST_USER = {
    "email": "admin@example.com",
    "password": "admin123"
}

class PDFEvidenceGenerator:
    def __init__(self):
        self.results = []
        self.token = None
        self.headers = {}
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        
    def authenticate(self):
        """Autenticar y obtener token"""
        try:
            response = requests.post(f"{AUTH_URL}/login/", json=TEST_USER, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.headers = {"Authorization": f"Bearer {self.token}"}
                return True
            return False
        except Exception as e:
            print(f"⚠️  Error en autenticación: {e}")
            return False
    
    def execute_test(self, category, test_id, name, description, endpoint, method="GET", 
                     params=None, requires_auth=True, expected_status=[200]):
        """Ejecuta una prueba y registra resultados"""
        self.test_count += 1
        
        try:
            url = f"{API_URL}/{endpoint}" if not endpoint.startswith("http") else endpoint
            headers = self.headers if requires_auth else {}
            
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=params, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code in expected_status
            if success:
                self.passed_count += 1
            else:
                self.failed_count += 1
            
            # Procesar respuesta
            response_preview = None
            try:
                response_data = response.json()
                if isinstance(response_data, list):
                    response_preview = {
                        "tipo": "lista",
                        "total": len(response_data),
                        "muestra": response_data[:2] if len(response_data) > 0 else []
                    }
                elif isinstance(response_data, dict):
                    # Limitar a los primeros campos
                    keys = list(response_data.keys())[:5]
                    response_preview = {k: response_data[k] for k in keys}
                else:
                    response_preview = response_data
            except:
                response_preview = {"respuesta": response.text[:200]}
            
            result = {
                "id": test_id,
                "category": category,
                "name": name,
                "description": description,
                "success": success,
                "status_code": response.status_code,
                "endpoint": endpoint,
                "method": method,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "response_preview": response_preview,
                "headers_sent": dict(headers) if headers else {},
                "expected_status": expected_status
            }
            
            self.results.append(result)
            
            status = "[OK]" if success else "[FAIL]"
            print(f"{status} [{test_id}] {name} - Status: {response.status_code}")
            
            time.sleep(0.3)
            
        except Exception as e:
            self.failed_count += 1
            result = {
                "id": test_id,
                "category": category,
                "name": name,
                "description": description,
                "success": False,
                "error": str(e),
                "endpoint": endpoint,
                "method": method,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.results.append(result)
            print(f"[FAIL] [{test_id}] {name} - Error: {e}")
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("\n" + "="*70)
        print("GENERANDO EVIDENCIAS DE PRUEBAS DE FUNCIONALIDAD")
        print("="*70 + "\n")
        
        if not self.authenticate():
            print("⚠️  Advertencia: No se pudo autenticar. Continuando...\n")
        
        # AUTENTICACIÓN
        print("Categoría: AUTENTICACIÓN")
        self.execute_test("Autenticación", "PF-001", "Login Exitoso",
                         "Verifica que un usuario pueda autenticarse con credenciales válidas",
                         f"{AUTH_URL}/login/", "POST", TEST_USER, False, [200])
        
        self.execute_test("Autenticación", "PF-002", "Login Inválido",
                         "Verifica rechazo de credenciales incorrectas",
                         f"{AUTH_URL}/login/", "POST", 
                         {"email": "wrong@test.com", "password": "wrong"}, False, [400, 401])
        
        # DISPOSITIVOS
        print("\nCategoría: DISPOSITIVOS")
        self.execute_test("Dispositivos", "PF-003", "Listar Dispositivos",
                         "Obtiene la lista completa de dispositivos registrados",
                         "devices/", "GET")
        
        self.execute_test("Dispositivos", "PF-004", "Filtrar Dispositivos Activos",
                         "Filtra dispositivos por estado activo",
                         "devices/", "GET", {"is_active": "true"})
        
        self.execute_test("Dispositivos", "PF-005", "Acceso sin Auth",
                         "Verifica que se requiera autenticación",
                         "devices/", "GET", requires_auth=False, expected_status=[401])
        
        # SENSORES
        print("\nCategoría: DATOS DE SENSORES")
        self.execute_test("Sensores", "PF-006", "Listar Datos de Sensores",
                         "Obtiene todos los registros de sensores",
                         "sensor-data/", "GET")
        
        self.execute_test("Sensores", "PF-007", "Ordenar por Fecha",
                         "Ordena datos por timestamp descendente",
                         "sensor-data/", "GET", {"ordering": "-timestamp"})
        
        self.execute_test("Sensores", "PF-008", "Paginación",
                         "Verifica funcionamiento de paginación",
                         "sensor-data/", "GET", {"page": 1, "page_size": 10})
        
        # MÉTRICAS
        print("\nCategoría: MÉTRICAS PROCESADAS")
        self.execute_test("Métricas", "PF-009", "Listar Métricas",
                         "Obtiene todas las métricas procesadas",
                         "processed-metrics/", "GET")
        
        self.execute_test("Métricas", "PF-010", "Filtrar por Actividad",
                         "Filtra métricas por nivel de actividad alto",
                         "processed-metrics/", "GET", {"activity_level": "high"})
        
        # ALERTAS
        print("\nCategoría: ALERTAS")
        self.execute_test("Alertas", "PF-011", "Listar Alertas",
                         "Obtiene todas las alertas de fatiga",
                         "alerts/", "GET")
        
        self.execute_test("Alertas", "PF-012", "Filtrar Alertas Activas",
                         "Obtiene solo alertas activas",
                         "alerts/", "GET", {"is_active": "true"})
        
        # RECOMENDACIONES
        print("\nCategoría: RECOMENDACIONES")
        self.execute_test("Recomendaciones", "PF-013", "Listar Recomendaciones",
                         "Obtiene todas las recomendaciones",
                         "recommendations/", "GET")
        
        self.execute_test("Recomendaciones", "PF-014", "Filtrar por Tipo",
                         "Filtra recomendaciones de tipo break",
                         "recommendations/", "GET", {"type": "break"})
        
        # DOCUMENTACIÓN
        print("\nCategoría: DOCUMENTACIÓN")
        self.execute_test("Documentación", "PF-015", "Schema OpenAPI",
                         "Verifica disponibilidad del schema",
                         "schema/", "GET", requires_auth=False)
        
        self.execute_test("Documentación", "PF-016", "Swagger UI",
                         "Verifica accesibilidad de Swagger",
                         "docs/", "GET", requires_auth=False)
        
        # MANEJO DE ERRORES
        print("\nCategoría: MANEJO DE ERRORES")
        self.execute_test("Errores", "PF-017", "Endpoint Inexistente",
                         "Verifica respuesta 404 para rutas inválidas",
                         "endpoint-inexistente/", "GET", expected_status=[404])
        
        self.execute_test("Errores", "PF-018", "Método No Permitido",
                         "Verifica respuesta 405 para métodos no soportados",
                         "devices/", "DELETE", expected_status=[405])
        
        print("\n" + "="*70)
        print(f"COMPLETADO: {self.passed_count}/{self.test_count} pruebas exitosas")
        print("="*70 + "\n")
    
    def generate_pdf(self):
        """Genera el documento PDF con evidencias"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"EVIDENCIA_FUNCIONALIDAD_{timestamp}.pdf"
        output_path = Path(__file__).parent / filename
        
        # Crear documento
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#5c6bc0'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        test_title_style = ParagraphStyle(
            'TestTitle',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#424242'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#212121'),
            alignment=TA_JUSTIFY
        )
        
        code_style = ParagraphStyle(
            'Code',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#37474f'),
            fontName='Courier',
            leftIndent=20,
            rightIndent=20
        )
        
        # Contenido
        story = []
        
        # Portada
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph("EVIDENCIA DE PRUEBAS", title_style))
        story.append(Paragraph("Pruebas de Funcionalidad del Backend", subtitle_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Sistema de Detección de Fatiga", normal_style))
        story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d de %B de %Y')}", normal_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Resumen
        success_rate = (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total de Pruebas', str(self.test_count)],
            ['Pruebas Exitosas', f'{self.passed_count} ✓'],
            ['Pruebas Fallidas', f'{self.failed_count} ✗'],
            ['Tasa de Éxito', f'{success_rate:.1f}%'],
            ['Backend URL', BASE_URL],
            ['Timestamp', timestamp]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(summary_table)
        story.append(PageBreak())
        
        # Agrupar por categoría
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        # Generar cada categoría
        for category_name, tests in categories.items():
            story.append(Paragraph(f"{category_name}", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            for test in tests:
                # Título de la prueba
                status_icon = "[OK]" if test['success'] else "[FAIL]"
                story.append(Paragraph(
                    f"{status_icon} [{test['id']}] {test['name']}", 
                    test_title_style
                ))
                story.append(Paragraph(test['description'], normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                # Detalles de la prueba
                test_data = [
                    ['Campo', 'Valor'],
                    ['Endpoint', test.get('endpoint', 'N/A')],
                    ['Método HTTP', test.get('method', 'N/A')],
                    ['Status Code', str(test.get('status_code', 'N/A'))],
                    ['Timestamp', test.get('timestamp', 'N/A')],
                    ['Resultado', 'EXITOSO' if test['success'] else 'FALLIDO']
                ]
                
                test_table = Table(test_data, colWidths=[1.5*inch, 5*inch])
                test_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#424242')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                story.append(test_table)
                story.append(Spacer(1, 0.1*inch))
                
                # Respuesta (si existe)
                if test.get('response_preview'):
                    story.append(Paragraph("<b>Respuesta del Servidor:</b>", normal_style))
                    response_text = json.dumps(test['response_preview'], indent=2, ensure_ascii=False)
                    # Limitar longitud
                    if len(response_text) > 500:
                        response_text = response_text[:500] + "\n... (respuesta truncada)"
                    # Escapar caracteres HTML
                    response_text = response_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(f"<font name='Courier' size='7'>{response_text}</font>", code_style))
                
                # Error (si existe)
                if test.get('error'):
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(f"<b>Error:</b> {test['error']}", normal_style))
                
                story.append(Spacer(1, 0.3*inch))
            
            story.append(PageBreak())
        
        # Generar PDF
        doc.build(story)
        
        print(f"\n[OK] PDF generado: {output_path}")
        return output_path

if __name__ == "__main__":
    print("\n=== GENERADOR DE EVIDENCIAS EN PDF ===")
    print("    Sistema de Detección de Fatiga\n")
    
    generator = PDFEvidenceGenerator()
    generator.run_all_tests()
    pdf_path = generator.generate_pdf()
    
    print(f"\n[OK] Evidencia completa generada en PDF")
    print(f"Archivo: {pdf_path.name}")
    print("\nPuedes abrir el PDF directamente para ver todas las evidencias.\n")
