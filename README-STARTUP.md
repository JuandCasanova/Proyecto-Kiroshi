# Kiroshi Startup Fixes

Este archivo describe los cambios que se hicieron para corregir el arranque del proyecto y evitar que el archivo `start.bat` falle antes de iniciar el backend.

## Problema encontrado

El archivo `start.bat` se interrumpía al inicio con este tipo de error:

> No se esperaba ... en este momento.

La causa principal estaba en la lógica de comprobación del puerto 8000 y en la validación del health check del backend. En Windows, esas líneas eran demasiado frágiles para ser interpretadas por `cmd.exe`, especialmente cuando combinaban `for /f`, pipes y comandos de red.

## Cambios realizados

### 1) Se eliminó la comprobación problemática del puerto 8000

Se removió la lógica que intentaba detectar procesos activos por medio de `netstat` y `findstr` dentro de un bloque `for /f` que rompía la sintaxis del batch.

Esto evitaba que el script falle antes de llegar a:

- iniciar FastAPI
- revisar si el backend respondió
- lanzar el frontend

### 2) Se simplificó la validación del backend

La verificación del endpoint `/health` se reemplazó por una comprobación más robusta usando PowerShell y `Invoke-WebRequest`, que es más estable en Windows.

Esto permite que el script espere a que el backend esté realmente disponible antes de continuar con el frontend.

### 3) Se agregaron validaciones adicionales de entorno

Ahora el batch comprueba si:

- existe el entorno virtual `.venv`
- existe la carpeta `node_modules`
- se debe instalar dependencias si faltan

Esto hace que el arranque sea más claro y menos propenso a fallos.

### 4) Se mantiene el flujo principal del proyecto

El objetivo principal no cambió: el script sigue iniciando:

1. Backend FastAPI
2. Espera el health check
3. Frontend React/Vite

## Resultado

Tras los cambios, el archivo `start.bat` ya no se corta al inicio y llega correctamente a:

- iniciar el backend en `http://localhost:8000/health`
- iniciar el frontend en `http://localhost:3000`

## Uso

Desde la raíz del proyecto:

```bat
start.bat
```

## Nota

Este documento es solo una guía del cambio operativo del arranque. La explicación general del proyecto sigue en el README principal.
