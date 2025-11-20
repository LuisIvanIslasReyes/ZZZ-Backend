# Script para iniciar Django con auto-inicio del cliente MQTT
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host "INICIANDO SERVIDOR DJANGO CON MQTT"
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host ""

Set-Location "C:\Users\bauti\Downloads\respaldos\ZZZ-Backend"

Write-Host "Activando entorno virtual..."
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Iniciando servidor Django..."
Write-Host "El cliente MQTT se iniciará automáticamente"
Write-Host ""
Write-Host "Presiona Ctrl+C para detener"
Write-Host ""

python manage.py runserver
