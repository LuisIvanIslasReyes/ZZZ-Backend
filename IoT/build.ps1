# Script para compilar el proyecto ESP32
# Uso: .\build.ps1

Write-Host "Activando entorno ESP-IDF..." -ForegroundColor Cyan

# Activar entorno ESP-IDF
. C:\Espressif\frameworks\esp-idf-v5.5.1\export.ps1

Write-Host "`nCompilando proyecto..." -ForegroundColor Green

# Compilar
idf.py build

Write-Host "`n✅ Compilación completada" -ForegroundColor Green
Write-Host "`nPara flashear: idf.py -p COMX flash monitor" -ForegroundColor Yellow
Write-Host "(Reemplaza COMX con tu puerto, ej: COM3)" -ForegroundColor Yellow
