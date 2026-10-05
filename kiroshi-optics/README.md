# Kiroshi Optics

Nucleo de escaneo de precision. Identifica **lo que el usuario marca** con la
mayor especificidad posible, sin adivinar y sin perder trazabilidad.

Inspirado en las opticas Kiroshi de Cyberpunk 2077: apuntas, escaneas, el
sistema te dice exactamente que estas mirando.

## Estado actual
Arquitectura y contratos definidos. **Sin interfaz y sin funciones
implementadas**: los `run()` de agentes y skills son deliberadamente
`NotImplementedError`. Este repo es el esqueleto sobre el que se iterara.

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
|-- interfaces/      api, cli, chat_ui (pendientes)
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