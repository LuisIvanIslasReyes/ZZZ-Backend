@echo off
cd /d C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
call venv\Scripts\activate.bat
echo.
echo ========================================
echo   SIMULADOR ESP32 - AUTO START
echo ========================================
echo.
echo Device ID: ESP32-001
echo Broker: localhost
echo Puerto: 1883
echo.
echo | set /p="ESP32-001" | python SCRIPTS\esp32_simulator.py
