# Kiroshi Optics

**Asistencia visual inteligente inspirada en las ópticas Kiroshi de _Cyberpunk 2077_.**

Kiroshi Optics busca llevar al mundo real algunas de las capacidades de las ópticas del videojuego mediante una aplicación que utiliza la cámara del dispositivo donde se ejecuta. El sistema está pensado para reconocer y describir con precisión lo que una persona observa, analizar texto visible y, a futuro, mostrar información contextual superpuesta a la imagen.

La inspiración es conceptual: el proyecto no contempla fabricar implantes oculares. La experiencia se desarrollará como software y podrá evolucionar hacia distintos dispositivos con cámara.

> **Estado actual:** el repositorio define la arquitectura, los agentes, las skills y sus contratos. Es todavía una base de desarrollo: las funciones de agentes y skills, el cliente de visión y las interfaces no están implementados. Por tanto, la captura de cámara, el análisis en vivo, la traducción y las superposiciones son objetivos, no capacidades disponibles hoy.

## Objetivos

- Usar la cámara del dispositivo como fuente de imágenes y, posteriormente, de video en tiempo real.
- Detectar y clasificar objetos, procurando llegar a la identificación más específica que permita la evidencia visual.
- Leer texto de la escena mediante OCR y habilitar su traducción en tiempo real como una capacidad futura.
- Presentar resultados de forma clara y, en una etapa posterior, como elementos flotantes sobre la imagen (HUD o realidad aumentada).
- Mantener resultados verificables: distinguir lo observado de lo inferido, comunicar incertidumbre y no inventar atributos.
- Diseñar componentes modulares para poder cambiar la cámara, la interfaz o el proveedor de visión sin rehacer el núcleo.

## Alcance y etapas previstas

### Base actual

- Arquitectura por capas para interfaces, orquestación, agentes, skills e infraestructura compartida.
- Contratos declarativos para los agentes y las skills.
- Pipeline de análisis de una región marcada (`Mark`) y taxonomía visual inicial.
- Diseños de permisos, trazabilidad, memoria y validación.

### Capacidades por implementar

1. **Captura de cámara:** obtener fotogramas del dispositivo y permitir seleccionar una región u objetivo.
2. **Análisis visual:** integrar detección, segmentación y clasificación mediante un proveedor de visión.
3. **Lectura de texto:** ejecutar OCR sobre texto seleccionado o visible en la escena.
4. **Traducción:** traducir el texto reconocido y asociarlo con su posición en la imagen.
5. **Interfaz visual:** presentar etiquetas, resultados y traducciones como superposiciones; optimizar el procesamiento para una experiencia fluida.
6. **Pruebas y privacidad:** medir precisión y latencia, controlar el uso de datos visuales y validar permisos antes de incorporar nuevas fuentes de contexto.

Las capacidades de cámara, OCR, traducción y HUD requerirán nuevos componentes o la implementación de los adaptadores existentes. No están incluidas entre las skills activas en la configuración actual.

## Cómo funciona el análisis diseñado

El núcleo procesa una región seleccionada, independientemente del dispositivo que la haya capturado. Así se evita acoplar el análisis a una cámara o interfaz específica.

```text
Imagen o región marcada
          │
          ▼
     mark_parser          Normaliza la entrada a un Mark canónico
          │
          ▼
   target_classifier      Propone clases y candidatos posibles
          │
          ▼
   feature_extractor      Busca rasgos discriminadores observables
          │
          ▼
 specificity_enhancer    Refina el resultado con evidencia disponible
          │
          ▼
    scan_validator        Comprueba coherencia y decide si se acepta
          │
          └──────────────► Resultado, evidencia, incertidumbre y faltantes
```

El `context_agent` puede ayudar a resolver empates entre candidatos; el contexto se mantiene separado de los atributos observados. Si falta evidencia que pueda comprobarse externamente, `reference_lookup` puede verificarla con fuentes autorizadas. Es la única skill diseñada con permiso de red.

La captura futura de cámara entregará fotogramas o regiones a este pipeline. De igual manera, el OCR y la traducción deberán añadirse como capacidades explícitas; el flujo actual no los ejecuta.

## Arquitectura

| Capa | Responsabilidad |
|---|---|
| `interfaces/` | Puntos de entrada para API, CLI y futura interfaz visual/cámara. |
| `core/orchestrator/` | Enruta tareas, organiza su ejecución y coordina agentes. |
| `agents/` | Componen skills para realizar un escaneo, elevar especificidad o desambiguar. |
| `skills/` | Unidades con contratos definidos para normalizar, clasificar, extraer rasgos, refinar y validar. |
| `tools/` | Adaptadores puros a servicios externos, como el proveedor de visión. |
| `core/memory/` | Maneja contexto de sesión y memoria de resultados. |
| `core/llm_gateway/` | Abstrae proveedores de modelos y seguimiento de costos. |
| `core/security/` | Aplica permisos y guardrails. |
| `core/observability/` | Registra trazas y eventos para facilitar auditoría y depuración. |
| `config/` | Declara agentes y skills activos, entornos y taxonomía. |
| `evaluations/` | Aloja pruebas de skills y benchmarks de agentes. |

### Agentes

| Agente | Responsabilidad | Skills principales |
|---|---|---|
| `scan_agent` | Coordina el pipeline principal de escaneo. | `mark_parser`, `target_classifier`, `feature_extractor`, `specificity_enhancer`, `scan_validator` |
| `specificity_agent` | Refina un resultado y, si está permitido, verifica faltantes con fuentes externas. | `specificity_enhancer`, `scan_validator`, `reference_lookup` |
| `context_agent` | Desempata candidatos con señales de sesión o entorno, sin mezclarlas con evidencia visual. | `context_aggregator`, `reference_lookup` |

### Skills activas

Las siguientes skills están declaradas en `kiroshi-optics/config/skills.yaml`. Sus implementaciones siguen pendientes.

| Skill | Función |
|---|---|
| `mark_parser` | Normaliza entradas como regiones de imagen, texto o archivos a un formato común. |
| `target_classifier` | Clasifica el objetivo en la jerarquía de la taxonomía y estima ambigüedad. |
| `feature_extractor` | Extrae los rasgos visuales necesarios para diferenciar candidatos. |
| `specificity_enhancer` | Intenta elevar el nivel de detalle sin aceptar atributos carentes de evidencia directa. |
| `scan_validator` | Verifica coherencia taxonómica y es la única skill autorizada para aceptar un escaneo. |
| `context_aggregator` | Usa contexto para ordenar candidatos empatados, separado de los atributos observados. |
| `reference_lookup` | Verifica rasgos faltantes con referencias externas; requiere permiso de red. |

### Taxonomía y aceptación

La taxonomía de `kiroshi-optics/config/taxonomy.yaml` organiza las clases en cinco niveles, de clase general a instancia. Los pesos actuales son L1 `0.15`, L2 `0.25`, L3 `0.30`, L4 `0.20` y L5 `0.10`. El validador usa una especificidad mínima predeterminada de `0.55`, declarada en su manifiesto. Estos valores son parte del diseño actual y podrán ajustarse con evaluaciones.

## Estructura del repositorio

El proyecto de ópticas está en `kiroshi-optics/`. `mi-framework-ia/` es otro directorio del repositorio con un framework de ejemplo; no es el núcleo de Kiroshi.

```text
Proyecto-Kiroshi/
├── README.md
├── crear_estructura_framework.py
├── kiroshi-optics/
│   ├── agents/                 # scan_agent, specificity_agent, context_agent
│   ├── config/                 # agentes, skills, entornos y taxonomía
│   ├── core/
│   │   ├── agent_base/
│   │   ├── llm_gateway/
│   │   ├── memory/
│   │   ├── observability/
│   │   ├── orchestrator/
│   │   ├── security/
│   │   └── skill_base/
│   ├── docs/                   # arquitectura, manifiestos y contratos de prompts
│   ├── evaluations/            # benchmarks y pruebas de skills
│   ├── interfaces/             # API, CLI e interfaz visual por desarrollar
│   ├── skills/                 # skills de escaneo y desambiguación
│   └── tools/                  # integraciones; cliente de visión pendiente
└── mi-framework-ia/            # framework de ejemplo independiente
```

## Principios de diseño

1. **Evidencia antes que inferencia:** si un atributo no es visible o verificable, se reporta como faltante.
2. **Aceptación controlada:** solo `scan_validator` puede aprobar un resultado.
3. **Captura desacoplada:** las skills de análisis reciben un `Mark` normalizado, no dependen de una cámara específica.
4. **Contexto separado:** señales contextuales pueden ayudar a desambiguar, pero no se presentan como rasgos observados.
5. **Permisos explícitos:** el acceso a red y otras capacidades se declaran en los manifiestos.
6. **Trazabilidad:** las decisiones relevantes deben poder revisarse mediante el sistema de observabilidad.
7. **Privacidad:** el tratamiento de imágenes, texto y señales de entorno deberá limitarse a lo necesario para la función solicitada.

## Desarrollo

El repositorio todavía no ofrece un comando para ejecutar una experiencia funcional de Kiroshi: los puntos de entrada y varias implementaciones son esqueletos. Para contribuir, se puede comenzar por implementar una skill según su manifiesto, conectar su integración en `tools/`, y añadir casos de evaluación en `kiroshi-optics/evaluations/`.

Documentación técnica:

- [Arquitectura](kiroshi-optics/docs/architecture.md)
- [Esquema de manifiestos](kiroshi-optics/docs/manifest_schema.md)
- [Contratos de prompts](kiroshi-optics/docs/prompt_contracts.md)
