# Desplegar el HUD web

El HUD web es un sitio estatico y funciona en GitHub Pages. La camara, el
escaneo de objetos y el seguimiento de la mano se ejecutan en el navegador con
MediaPipe; no se envian fotogramas a la API. Al activar cada funcion por
primera vez, se descargan sus modelos oficiales y se mantienen en el dispositivo
segun la cache del navegador. Se necesita conexion a internet para esa descarga.

## Publicar solo la interfaz en GitHub Pages

La raiz del repositorio (`index.html`) redirige al HUD web. Configura GitHub
Pages para publicar `main` desde `/(root)` y sube los cambios. Cada visitante
autoriza su propia camara; `E` activa la deteccion local de objetos y `Z` activa
el zoom por gesto de pulgar e indice.

## Probar localmente

Desde `kiroshi-optics` en PowerShell, sirve los archivos estaticos:

```powershell
python -m http.server 8000
```

Abre `http://127.0.0.1:8000/interfaces/hud/web/`. Permite el acceso a la camara
en el navegador. La primera activacion del escaneo o zoom gestual descarga su
modelo de MediaPipe. Usa `Ctrl+C` para detener el servidor.

Para ejecutar la prueba unitaria de validacion JPEG:

```powershell
python -m unittest discover -s tests
```

Tambien puedes crear la imagen Docker:

```powershell
docker build -f kiroshi-optics/Dockerfile -t kiroshi-hud .
docker run --rm -p 8000:8000 kiroshi-hud
```

## API FastAPI en un servicio Docker (opcional)

El HUD web publicado en GitHub Pages no necesita un backend. Si se requiere
desplegar la API incluida por separado, utiliza cualquier plataforma que acepte
contenedores Docker:

1. Usa la raiz del repositorio como contexto de construccion y
   `kiroshi-optics/Dockerfile` como Dockerfile.
2. Expone el puerto `8000`.
3. Configura `/api/health` como ruta de comprobacion de salud, si la plataforma
   ofrece esa opcion.
4. Cuando el servicio esté disponible, verifica que `GET /api/health` responda
   `{"status":"ok"}`.

Esta API es independiente: el frontend actual no le envía fotogramas ni usa sus
resultados. Desplegarla no cambia el funcionamiento del HUD de GitHub Pages.

La API FastAPI incluida es una opcion independiente para despliegues futuros;
la interfaz web actual no depende de ella. El escaneo del navegador usa el
modelo EfficientDet Lite0 y puede variar en velocidad y resultados segun el
dispositivo; no garantiza precision de nivel clinico o de producto.

## Controles

- **Activar camara**: solicita permiso para la camara local del navegador.
- **Escaneo de objetos** o `E`: activa/desactiva detecciones dibujadas sobre la
  vista. El objeto más cercano a la retícula también muestra una descripción
  breve predefinida; el procesamiento se hace localmente en el navegador.
- **Zoom gestual** o `Z`: activa/desactiva el zoom con pulgar e indice; separar
  los dedos acerca la imagen y juntarlos la aleja.
- **Cambiar color** o `C`: alterna cian y rojo.
- **Glitch** o `G`: activa o desactiva el efecto visual.
- **Zoom**: tambien puede ajustarse manualmente; `Q` desconecta la camara.

El escaneo facial solo cuenta rostros y no identifica personas. La consulta
opcional a Gemini del HUD de escritorio no se ejecuta en esta version web.
