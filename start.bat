@echo off
setlocal

echo ========================================
echo   KIROSHI OPTICS - SISTEMA DE INICIO
echo ========================================
echo.

echo [1/3] Iniciando backend (FastAPI + YOLOv8 CUDA)...
cd backend
if not exist ".venv\Scripts\python.exe" (
    echo [!] No se encontro el entorno virtual .venv
    echo     Ejecuta primero:
    echo       cd backend
    echo       python -m venv .venv
    echo       .venv\Scripts\pip install -r requirements.txt
    goto done
)

start "Kiroshi-Backend" cmd /k "title KIROSHI BACKEND && .venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/3] Esperando que el backend responda...
set "READY="
for /l %%i in (1,1,20) do (
    powershell -NoProfile -Command "$r = try { [int](Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>nul
    if not errorlevel 1 (
        set "READY=1"
        echo       Backend listo en intento %%i.
        goto ready_ok
    )
    timeout /t 2 /nobreak >nul
)

if not defined READY (
    echo.
    echo  [!] El backend no respondio despues de 20 intentos.
    echo      Revisa la ventana "KIROSHI BACKEND" por errores.
    echo.
    goto done
)

:ready_ok
echo [3/3] Iniciando frontend (React + Vite)...
cd ..\frontend
if not exist "node_modules" (
    echo       Instalando dependencias de frontend...
    call npm install
)
start "Kiroshi-Frontend" cmd /k "title KIROSHI FRONTEND && npm run dev"

echo.
echo ========================================
echo   Backend:  http://localhost:8000/health
echo   Frontend: http://localhost:3000
echo ========================================

echo   Si el HUD muestra SIN SEÑAL:
    echo     1. Espera hasta 15s (warmup GPU).
    echo     2. Cierra apps que usen la camara.
    echo     3. Recarga la pagina (F5).

echo ========================================

:done
pause