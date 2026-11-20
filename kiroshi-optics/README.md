# Kiroshi Optics

Nucleo de escaneo de precision. Identifica **lo que el usuario marca** con la
mayor especificidad posible, sin adivinar y sin perder trazabilidad.

Inspirado en las opticas Kiroshi de Cyberpunk 2077: apuntas, escaneas, el
sistema te dice exactamente que estas mirando.

## Estado actual
El nucleo define la arquitectura y los contratos; los `run()` de agentes y
skills siguen deliberadamente sin implementar. El HUD de escritorio usa la
camara local, MediaPipe y YOLO. El HUD web muestra la camara en el navegador y
ejecuta localmente la deteccion de objetos y el zoom gestual; no envia los
fotogramas a la API FastAPI.

## Estructura
```
kiroshi-optics/
|-- agents/          scan_agent, specificity_agent, context_agent
|-- skills/          mark_parser, target_classifier, feature_extractor,
|                    specificity_enhancer, scan_validator,
|                    context_aggregator, reference_lookup
|-- core/            orchestrator, agent_base, skill_base, memory,
|                    llm_gateway, security, observability
|-- tools/           vision_api_client
|-- config/          agents.yaml, skills.yaml, taxonomy.yaml, environments/
|-- interfaces/      api, cli, chat_ui, hud (escritorio y navegador)
|-- evaluations/     agent_benchmarks, skill_tests
`-- docs/            documento_tecnico.md, manifest_schema.md, prompt_contracts.md
```

## Como funciona
```
mark -> mark_parser -> target_classifier -> feature_extractor
     -> specificity_enhancer -> scan_validator
```
La especificidad se calcula con los pesos de `config/taxonomy.yaml` y debe
superar `min_acceptable` (0.55) para que el escaneo sea aceptado.
Detalle de componentes, alcance y diagramas en
[`docs/documento_tecnico.md`](docs/documento_tecnico.md).

## Reglas del proyecto
1. Evidencia antes que inferencia. Ausente se reporta ausente.
2. Solo `scan_validator` aprueba un escaneo.
3. Una skill sin `network_access` no accede a la red.
4. Toda decision queda trazado en `core/observability/tracer.py`.

## Documentacion
- [`docs/documento_tecnico.md`](docs/documento_tecnico.md) — descripcion del
  sistema, objetivos, estado funcional y diagramas UML.
- `docs/manifest_schema.md` — contrato obligatorio de agentes y skills.

## HUD web

La interfaz web esta en `interfaces/hud/web` y puede publicarse como sitio
estatico; la pagina principal del repositorio redirige a ella. La deteccion de
objetos con la tecla `E` y el zoom por gesto con `Z` se ejecutan localmente con
MediaPipe; no transmiten fotogramas a la API. GitHub Pages entrega la interfaz
y los modelos se descargan desde CDN al activarlos por primera vez. Para
publicar la interfaz o desplegar la API independiente, sigue
[`DEPLOY_WEB.md`](DEPLOY_WEB.md).

## HUD de webcam

Requiere Python 3.10 o superior. Desde la carpeta `kiroshi-optics`, instala
las dependencias y ejecuta:

```powershell
python -m pip install -r requirements.txt
python -m interfaces.hud
```

En Windows con una GPU NVIDIA, instala despues la compilacion CUDA de PyTorch
para que YOLO pueda usarla:

```powershell
python -m pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu130
```

Este indice requiere un controlador NVIDIA compatible con CUDA 13.0 y ruedas
disponibles para tu version de Python. Si no es compatible, conserva PyTorch
CPU; el escaner seguira funcionando con el procesador.

Por defecto, el HUD abre la camara local `0`. Para usar el telefono como
camara IP, conecta ambos dispositivos a la misma red Wi-Fi, inicia en el
telefono una aplicacion que publique un flujo compatible con OpenCV (MJPEG,
HTTP o RTSP) y pasa su URL con `--camera`:

```powershell
python -m interfaces.hud --camera "http://192.168.1.50:8080/video"
```

Reemplaza esa URL de ejemplo por la direccion exacta que muestre la aplicacion
del telefono. Tambien puedes elegir otra camara local indicando su indice, por
ejemplo `python -m interfaces.hud --camera 1`. Si la URL no abre, confirma que
el flujo funcione en el PC, que los dos dispositivos esten en la misma red y
que el firewall permita la conexion.

El HUD detecta rostros localmente con MediaPipe y aplica una gradacion cian o
roja, distorsion de lente, scanlines y elementos de interfaz. En el primer
inicio descarga el modelo oficial de MediaPipe y lo guarda en
`~/.cache/kiroshi-optics`.

El escaner de objetos usa YOLO11n-seg para segmentacion de instancias y puede
marcar personas, botellas, tazas/pocillos, laptops, mouse, teclados, sillas,
pantallas/TV, perros, gatos y peluches. «JUGUETE/PELUCHE» corresponde a la clase
`teddy bear` del modelo; no representa una categoria universal para cualquier
juguete. El HUD muestra una descripcion local y breve del objeto mas cercano a
la reticula. El objetivo detectado se marca con un cuadro amarillo pequeño en
el centro, sin recubrirlo. `e` activa o desactiva el escaneo; el modelo se descarga
al activar el escaneo por primera vez y se guarda en `~/.cache/kiroshi-optics`.
Usa CUDA automaticamente si PyTorch detecta una GPU NVIDIA compatible; si no,
usa CPU. El HUD muestra el dispositivo activo. Para CUDA se necesita una
instalacion de PyTorch compatible con la version del controlador NVIDIA; si
CUDA no esta disponible, el programa sigue funcionando en CPU. La inferencia
se ejecuta en un hilo separado y se limita para evitar acumular fotogramas.
Es una linea base de categorias generales, no un reconocedor entrenado para
cada modelo de producto: no confirma el contenido de una botella, no detecta
de forma fiable torres de PC ni permite diferenciar un todo-en-uno de un
monitor externo por la presencia de un teclado. Cuando ve pantalla y teclado
cercanos, los informa como componentes, sin inferir que la torre o el
ordenador integrado fueron detectados. El detector no procesa objetos cuando
el modo de escaneo esta apagado.
En personas solo se marca la clase general «persona»; el HUD no infiere
genero a partir de cabello, cuerpo o rostro.

### Verificacion visual en la web

Opcionalmente, Kiroshi puede contrastar el objetivo seleccionado con Gemini 4
Carbon y Google Search. Configura `GEMINI_API_KEY` en el entorno de Windows
antes de iniciar el HUD:

```powershell
$env:GEMINI_API_KEY = "TU_CLAVE_DE_GEMINI"
.\.venv\Scripts\python.exe -m interfaces.hud
```

Al activar el escaneo con `e`, se envía una sola imagen recortada del objetivo
seleccionado (no el video ni fotogramas continuos) para generar una respuesta
con búsquedas y fuentes citadas. La consulta se ejecuta en segundo plano.
Objetivos clasificados como personas no se envían. La solicitud usa
almacenamiento desactivado (`store: false`); aun así, el procesamiento de la
imagen está sujeto a las condiciones del proveedor. Sin `GEMINI_API_KEY`, la
detección local funciona y el HUD muestra el error de configuración de la
búsqueda web.

La traduccion y el OCR se han pausado por ahora; no forman parte de esta
version del HUD. Se podran reincorporar mas adelante con una solucion mas
ligera y rapida. El HUD local no requiere Tesseract, Argos Translate ni
Transformers. PyTorch se utiliza para el modelo de objetos.

Pulsa `e` para activar o desactivar el escaneo de objetos. Pulsa `z` en
cualquier momento para activar o desactivar el zoom manual por gestos,
independiente del escaneo. MediaPipe detecta la punta
del indice y del pulgar. El zoom cambia de forma continua mientras mueves los
dedos: juntarlos disminuye el zoom y separarlos lo aumenta. El zoom digital va
de 0.7x a 3.0x sin confirmaciones temporales ni pausas entre movimientos. Al
activar el zoom por primera vez se descarga el modelo de manos de MediaPipe y se guarda en
`~/.cache/kiroshi-optics`; requiere conexion a Internet solo esa vez.

La deteccion facial se mantiene local y muestra el conteo y etiquetas anonimas
en un panel lateral, sin dibujar cuadros sobre rostros ni identificar personas.
Pulsa `c` para cambiar el modo de color, `g` para activar o desactivar
glitch/scanlines y `q` para salir.