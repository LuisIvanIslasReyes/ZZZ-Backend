# Script para flashear y monitorear el ESP32
# Uso: .\flash.ps1 COM3 (reemplaza COM3 con tu puerto)

param(
    [string]$Port = "COM4"
)

Write-Host "Activando entorno ESP-IDF..." -ForegroundColor Cyan

# Activar entorno ESP-IDF
. C:\Espressif\frameworks\esp-idf-v5.5.1\export.ps1

Write-Host "`nFlasheando a puerto $Port..." -ForegroundColor Green

# Flashear y monitorear
idf.py -p $Port flash monitor

Write-Host "`nPara salir del monitor: Ctrl + ]" -ForegroundColor Yellow
