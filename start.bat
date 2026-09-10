@echo off
setlocal EnableDelayedExpansion
echo ========================================
echo   KIROSHI OPTICS - SISTEMA DE INICIO
echo ========================================
echo.

echo [0/3] Limpiando procesos zombies en puerto 8000...
set "PORT_PID="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:"LISTENING" ^| findstr ":8000"') do (
    set "PORT_PID=%%a"
)
if defined PORT_PID (
    echo       Cerrando PID !PORT_PID! (backend anterior)...
    taskkill /F /PID !PORT_PID! >nul 2>&1
    timeout /t 2 /nobreak >nul
) else (
    echo       Puerto 8000 libre.
)

echo [1/3] Iniciando backend (FastAPI + YOLOv8 CUDA)...
cd backend
start "Kiroshi-Backend" cmd /k "title KIROSHI BACKEND && .venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/3] Esperando que el backend responda (modelo en GPU)...
set "READY="
for /l %%i in (1,1,12) do (
    curl -s -o nul -w "%%{http_code}" http://localhost:8000/health > "%TEMP%\kiroshi_health.txt" 2>nul
    set /p CODE=<"%TEMP%\kiroshi_health.txt"
    if "!CODE!"=="200" (
        set "READY=1"
        echo       Backend listo en intento %%i.
        goto ready_ok
    )
    timeout /t 3 /nobreak >nul
)
if not defined READY (
    echo.
    echo  [!] El backend no respondio despues de 12 intentos.
    echo      Revisa la ventana "KIROSHI BACKEND" por errores.
    echo      Pista: verifica que la camara este libre y no sea usada
    echo      por otra aplicacion (Zoom, Teams, etc).
    echo.
    goto done
)

:ready_ok
echo [3/3] Iniciando frontend (React + Vite)...
cd ..\frontend
start "Kiroshi-Frontend" cmd /k "title KIROSHI FRONTEND && npm run dev"

echo.
echo ========================================
echo   Backend:  http://localhost:8000/health
echo   Frontend: http://localhost:3000
echo.
echo   Si el HUD muestra SIN SEÑAL:
echo     1. Espera hasta 15s (warmup GPU).
echo     2. Cierra apps que usen la camara.
echo     3. Recarga la pagina (F5).
echo ========================================

:done
pause