# Kiroshi Optics HUD — Next-Gen AI Visual Scanner & Object Identifier

**Kiroshi Optics HUD** es un sistema de visión por computadora y reconocimiento visual avanzado inspirado en la interfaz cibernética de *Cyberpunk 2077*. El proyecto evoluciona el paradigma de detección tradicional hacia la **identificación precisa de productos e investigación contextual en tiempo real**.

---

## Características Principales

* **Detección y Clasificación Primaria (YOLOv8):** Localización en tiempo real de entidades (personas, animales, objetos) en el stream de video.
* **Identificación Fina e Investigación Contextual (AI Vision + Web Search):** 
  * Diferenciación exacta entre productos similares (ej. *Botella de agua vs. Tarro de bloqueador solar*).
  * Extracción de recortes de imagen (*image crops*) para análisis multimodal e identificación precisa estilo Google Lens.
  * Búsqueda e integración de información detallada del objeto en tiempo real para enriquecer los datos presentados en la interfaz.
* **Control por Comandos de Voz:** Conmutación entre **Modo Normal** y **Modo Escaneo** mediante la **Web Speech API** (`"Modo escaneo"` / `"Modo normal"`).
* **Clasificación de Amenazas (Kiroshi Logic):** Categorización dinámica de riesgo, asignando códigos de color, niveles de amenaza e indicadores HUD.
* **Stream de Video de Baja Latencia:** Conexión bidireccional mediante **WebSockets** y procesamiento acelerado por GPU (CUDA / PyTorch).
* **Interfaz Cyberpunk (React + Canvas 2D):** Renderizado de retículas cibernéticas, métricas del sistema y datos extraídos a 30+ FPS.

---

##  Arquitectura y Tecnologías

### Backend (Python)
* **FastAPI:** Servidor WebSocket asíncrono para transmisión continua.
* **Ultralytics YOLOv8:** Detección rápida de regiones de interés (RoI).
* **AI Vision & Search Integration:** Modelos multimodales / APIs de búsqueda visual para reconocimiento fino de productos e investigación web.
* **OpenCV & NumPy:** Procesamiento de cuadros de video y recortes de imagen.
* **PyTorch (CUDA):** Aceleración por hardware.

### Frontend (React / JavaScript)
* **React.js (Vite):** UI reactiva estilo Cyberpunk.
* **HTML5 Canvas 2D:** Renderizado de retículas y capas de información contextual.
* **Web Speech API:** Control por voz nativo desde el navegador.

---
| Miembro | Rol |
|---------|-----|
| **Juan David Casanova** | Líder Técnico, Gestor de producto, QA/Documentación, DevOps|

## Hoja de Ruta (Roadmap)

- [x] Transmisión de video por WebSockets y HUD en React.
- [x] Control por voz para alternar modos de escaneo.
- [x] Intefase básica de detección de objetos con YOLOv8.
- [ ] **Módulo de Reconocimiento Fino:** Extracción de parches de imagen para consulta en modelo multimodal.
- [ ] **Enriquecimiento Web:** Integración de API de búsqueda para desplegar nombre exacto y especificaciones del producto en el HUD.
