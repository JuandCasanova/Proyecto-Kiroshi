# Arquitectura — Kiroshi Optics

## Proposito
Kiroshi Optics escanea **lo que el usuario marco** y devuelve una identificacion
lo mas especifica posible. No crea interfaz ni expone comandos: es el nucleo de
razonamiento y contratos que luego consumira cualquier interfaz.

## Principio rector: especificidad como funcion medible
La especificidad no es una sensacion, es un numero. Se calcula sumando el peso
de cada nivel de la taxonomia que el resultado logra resolver:

    specificity = sum(peso[nivel] para nivel resuelto)

Un escaneo solo se acepta si `specificity >= min_acceptable` (0.55 por defecto,
ver `skills/scan_validator/manifest.yaml`). Esto hace que "especifico" sea
reproducible y auditable entre ejecuciones y entre versiones de prompt.

## Capas

```
interfaces/        Puntos de entrada (api, cli, hud). Todavia no implementados.
      |
core/orchestrator/ router -> planner -> executor
      |             Decide quien atiende, descompone, ejecuta con reintentos.
      |
agents/            scan_agent, specificity_agent, context_agent
      |             Composicion de skills. No interpretan por si mismos.
      |
skills/            Units de trabajo deterministas y verificables.
      |
tools/             Clientes de integracion pura (vision_api_client).
      |
core/               Infraestructura compartida:
      memory/         Contexto de sesion + memoria persistente de escaneos
      llm_gateway/    Abstraccion de proveedor + control de costo
      security/       Permisos y guardrails
      observability/  Trazas y logs de cada decision
```

## Pipeline de escaneo (sendero feliz)

```
mark
 │
 ├─> mark_parser            normaliza cualquier modo de captura a un Mark canonico
 ├─> target_classifier      emite labels con class_path y discriminadores
 ├─> feature_extractor      resuelve solo los discriminadores de la taxonomia
 ├─> specificity_enhancer   itera hasta target, sin_gain o max_passes
 └─> scan_validator         unico autorizado para aprobar o rechazar
```

## Ramas de desambiguacion
- **feature_extractor** reporta `completeness` baja  ->  invoca
  `reference_lookup` (unica skill con `network_access`) para cerrar gaps.
- **target_classifier** devuelve `ambiguity` alta    ->  invoca
  `context_aggregator` via `context_agent`. El contexto se registra aparte y
  nunca se mezcla con los atributos del objetivo, para no inflar la
  especificidad con informacion no verificada.

## Invariantes del diseno
1. **Evidence before inference.** Un atributo ausente se reporta ausente.
   `specificity_enhancer` corre con `strict: true` por defecto.
2. **Solo el validador aprueba.** Ninguna otra skill puede emitir
   `accepted: true`.
3. **Agnosticismo de captura.** Todo el pipeline consume un `Mark` canonico,
   por lo que agregar un modo de captura nuevo no toca skills de analisis.
4. **Trazabilidad total.** Cada pasada del enhancer y cada lookup quedan
   registrados por `core/observability/tracer.py`.
5. **Permisos por manifiesto.** Una skill sin `permissions: [network_access]`
   no puede salir a la red, sin importar lo que el modelo intente.

## Extension: agregar una nueva forma de escaneo
1. Anadir el nodo y sus `discriminators` en `config/taxonomy.yaml`.
2. Crear `skills/<nueva_skill>/` con `skill.py` (hereda `BaseSkill`) y
   `manifest.yaml` con `input_schema`, `output_schema` y `requires`.
3. Registrarla en `config/skills.yaml`.
4. Anadir el caso a `evaluations/skill_tests/`.

No se requiere modificar ningun agente: el pipeline se compone por `requires`.