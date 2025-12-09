# Script para limpiar y recompilar el proyecto ESP32
# Uso: .\rebuild.ps1

Write-Host "Activando entorno ESP-IDF..." -ForegroundColor Cyan
. C:\Espressif\frameworks\esp-idf-v5.5.1\export.ps1

Write-Host "`nLimpiando proyecto..." -ForegroundColor Yellow
idf.py fullclean

Write-Host "`nCompilando proyecto desde cero..." -ForegroundColor Green
idf.py build

Write-Host "`n✅ Compilación completada" -ForegroundColor Green
Write-Host "`nPara flashear: .\flash.ps1" -ForegroundColor Yellow
