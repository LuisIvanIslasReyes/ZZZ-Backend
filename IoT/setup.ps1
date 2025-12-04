# Script PowerShell para configuración rápida
# Ejecutar: .\setup.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ESP32 + Sensores - Setup Automático" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar ESP-IDF
Write-Host "Verificando ESP-IDF..." -ForegroundColor Yellow
try {
    $idf_version = idf.py --version 2>&1
    Write-Host "✓ ESP-IDF detectado: $idf_version" -ForegroundColor Green
} catch {
    Write-Host "✗ ESP-IDF no encontrado. Por favor instala ESP-IDF primero." -ForegroundColor Red
    Write-Host "  Descarga: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/" -ForegroundColor Red
    exit 1
}

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
try {
    $python_version = python --version 2>&1
    Write-Host "✓ Python detectado: $python_version" -ForegroundColor Green
} catch {
    Write-Host "✗ Python no encontrado." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configurando proyecto..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configurar target
Write-Host ""
Write-Host "Configurando target ESP32..." -ForegroundColor Yellow
idf.py set-target esp32

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Target configurado correctamente" -ForegroundColor Green
} else {
    Write-Host "✗ Error configurando target" -ForegroundColor Red
    exit 1
}

# Compilar
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Compilando proyecto..." -ForegroundColor Cyan
Write-Host "Esto puede tardar 5-15 minutos la primera vez" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

idf.py build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Compilación exitosa!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Conecta tu ESP32 via USB" -ForegroundColor White
    Write-Host "2. Identifica el puerto COM (generalmente COM3, COM4, etc.)" -ForegroundColor White
    Write-Host "3. Ejecuta:" -ForegroundColor White
    Write-Host "   idf.py -p COMX flash monitor" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ejemplo:" -ForegroundColor White
    Write-Host "   idf.py -p COM3 flash monitor" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para salir del monitor: Ctrl + ]" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ Error en la compilación" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifica los errores arriba y consulta README.md" -ForegroundColor Yellow
    exit 1
}
