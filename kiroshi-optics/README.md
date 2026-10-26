# Kiroshi Optics

Nucleo de escaneo de precision. Identifica **lo que el usuario marca** con la
mayor especificidad posible, sin adivinar y sin perder trazabilidad.

Inspirado en las opticas Kiroshi de Cyberpunk 2077: apuntas, escaneas, el
sistema te dice exactamente que estas mirando.

## Estado actual
El nucleo define la arquitectura y los contratos; los `run()` de agentes y
skills siguen deliberadamente sin implementar. La interfaz local de webcam
`interfaces/hud` ya ofrece una simulacion visual de las opticas Kiroshi.

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
|-- interfaces/      api, cli, chat_ui, hud (webcam local)
|-- evaluations/     agent_benchmarks, skill_tests
`-- docs/            architecture.md, manifest_schema.md
```

## Como funciona
```
mark -> mark_parser -> target_classifier -> feature_extractor
     -> specificity_enhancer -> scan_validator
```
La especificidad se calcula con los pesos de `config/taxonomy.yaml` y debe
superar `min_acceptable` (0.55) para que el escaneo sea aceptado.
Detalle completo en `docs/architecture.md`.

## Reglas del proyecto
1. Evidencia antes que inferencia. Ausente se reporta ausente.
2. Solo `scan_validator` aprueba un escaneo.
3. Una skill sin `network_access` no accede a la red.
4. Toda decision queda trazado en `core/observability/tracer.py`.

## Documentacion
- `docs/architecture.md` — capas, pipeline, invariantes, como extender.
- `docs/manifest_schema.md` — contrato obligatorio de agentes y skills.

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
marcar personas, botellas, tazas/pocillos, laptops, teclados, pantallas/TV,
perros, gatos y peluches. «JUGUETE (PELUCHE)» corresponde a la clase `teddy
bear` del modelo; no representa una categoria universal para cualquier
juguete. El HUD dibuja el contorno de la mascara de cada instancia, no una caja
rectangular. El modelo se descarga al activar el escaneo por primera vez y se
guarda en `~/.cache/kiroshi-optics`.
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

La traduccion y el OCR se han pausado por ahora; no forman parte de esta
version del HUD. Se podran reincorporar mas adelante con una solucion mas
ligera y rapida. El HUD no requiere Tesseract, Argos Translate, Transformers
ni servicios de Google Cloud. PyTorch se utiliza para el modelo de
segmentacion.

Pulsa `e` para activar o desactivar el modo de escaneo de objetos. El modelo
de objetos solo procesa y dibuja detecciones mientras este modo esta activo.
Dentro del escaneo, pulsa `z` para activar o desactivar el zoom manual por
gestos; fuera del escaneo `z` no tiene efecto. MediaPipe detecta la punta del
indice y del pulgar: mantenlos separados y luego juntalos durante un segundo
para alejar el zoom; mantenlos juntos y separalos durante un segundo para
acercarlo. El zoom digital va de 0.7x a 3.0x. Despues de cada accion hay una
pausa de 1.5 segundos para recolocar los dedos; la posicion detectada al
terminar la pausa se toma como nuevo punto de inicio. Al activar el zoom por
primera vez se descarga el modelo de manos de MediaPipe y se guarda en
`~/.cache/kiroshi-optics`; requiere conexion a Internet solo esa vez.

El panel facial muestra la etiqueta «PERSONA», la afiliacion fija
«UNIMINUTO» y una recompensa ficticia; no son inferencias ni identificaciones
de las personas captadas por la camara. Pulsa `c` para cambiar el modo de
color, `g` para activar o desactivar glitch/scanlines y `q` para salir.