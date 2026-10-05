## 5. Pipeline de Escaneo (Core Flow)

El flujo sigue un orden estricto definido por `requires` en los manifests. Esto garantiza composición determinista.

```text
INPUT: mark (image_region | screen_region | text_span | audio_span | file_region)
  │
  ▼
1. mark_parser (pure)
   └─> Normaliza → Mark canónico (modality, bbox, preprocessed_ref...)
  │
  ▼
2. target_classifier (model)
   └─> Propone candidatos (labels) con class_path + discriminadores requeridos
   └─> Calcula ambiguity [0.0 (único) – 1.0 (indistinguible)]
  │
  ▼
3. feature_extractor (model)
   └─> Extrae SOLO discriminadores de taxonomía para cada candidato
   └─> features[disc] = {valor, confianza, ausente}
   └─> completeness = resolved / (resolved + missing)
  │
  ▼
4. specificity_enhancer (model)  [iterativo: máx. 3 pases]
   └─> Prioriza discriminadores faltantes por impacto en especificidad
   └─> Solo acepta valores con evidencia directa (confianza >= 0.70)
   └─> Genera attributes + specificity + blocking_gaps
   └─> Stop reasons: target_reached | no_gain | max_passes
  │
  ▼
5. scan_validator (pure)  ← ÚNICO AUTORIZADO A APROBAR
   └─> Calcula effective_specificity (pesos L1–L5)
   └─> Verifica coherencia taxonómica
   └─> Resultado: accepted (bool) + violations + remediation + specificity_level
```

### Ramas Condicionales (Desambiguación)

| Condición | Rama | Acción |
|---|---|---|
| `feature_extractor.completeness` baja | `reference_lookup` (vía `specificity_agent`/pipeline) | Verifica discriminadores faltantes con fuentes externas. **Única skill con `network_access`**. Opera en `verify_only: true` (no propone nuevos candidatos). |
| `target_classifier.ambiguity` alta (> umbral) | `context_aggregator` (vía `context_agent`) | Desempata candidatos empatados usando señales de sesión/entorno. **Nunca** escribe contexto en `attributes` del objetivo (se registra en `used_signals` para no contaminar la especificidad). |

## 6. Agentes — Responsabilidades

| Agente | Descripción | Skills Requeridas | Permisos |
|---|---|---|---|
| **scan_agent** | Coordina el pipeline completo de escaneo. Solo delega en orden correcto, no interpreta. | `mark_parser`, `target_classifier`, `feature_extractor`, `specificity_enhancer`, `scan_validator` | `memory_read`, `memory_write` |
| **specificity_agent** | Eleva la granularidad hasta la **máxima especificidad alcanzable** con evidencia disponible. Trabaja sobre resultado previo, nunca sobre marca cruda. | `specificity_enhancer`, `scan_validator`, `reference_lookup` | `memory_read`, `network_access` |
| **context_agent** | Agrega contexto para desambiguar cuando evidencia directa no basta. Usa contexto **solo para desempate**, nunca para inventar atributos. | `context_aggregator`, `reference_lookup` | `memory_read`, `memory_write`, `network_access` |

## 7. Skills — Detalle por Componente

| Skill | `determinism` | Propósito | Notas Clave |
|---|---|---|---|
| **mark_parser** | `pure` (`cacheable: true`) | Normaliza cualquier formato de marca a `Mark` canónico. | Única que entiende formatos crudos. Pipeline queda agnóstico a captura. |
| **target_classifier** | `model` | Clasifica jerárquicamente con `multi_label: true`. | Emite `ambiguity`. Reporta `discriminators` por candidato (clave para diferenciación fina). |
| **feature_extractor** | `model` | Extrae **únicamente** discriminadores listados en taxonomía. | **Motor de especificidad**. `measure_only` permite solo reportar ausencias. Prioriza rasgos estructurales (forma/apertura/cuello/stem/pie/proporciones/bezel). |
| **specificity_enhancer** | `model` | Iteración guiada (≤3 pases). Ordena faltantes por impacto. | **Regla dura:** acepta solo con evidencia directa (conf ≥ 0.70). Si ganancia < 0.02 → detiene. Nunca adivina. |
| **scan_validator** | `pure` | Valida coherencia + calcula `effective_specificity`. | **Gate único de aceptación**. Emite `accepted`, `violations`, `remediation`, `specificity_level` (coarse/standard/forensic). |
| **context_aggregator** | `model` | Desempata candidatos empatados. | Separa estrictamente `used_signals` (contexto) de `attributes` (evidencia). Emite `contamination_warning` si aplica. |
| **reference_lookup** | `network` (`rate_limit: 30/min`) | Verifica discriminadores faltantes. | **Solo verifica** (`verify_only: true`). No propone candidatos. Única con permiso de red. |

## 8. Taxonomía y Especificidad Medible

### Niveles y Pesos

| Nivel | ID | Nombre | Peso | Alcance típico |
|---|---|---|---|---|
| L1 | clase_general | Entidad general | 0.15 | `recipiente`, `dispositivo`, `vehículo`... |
| L2 | categoria | Categoría | 0.25 | `botella`, `vaso`, `teléfono`, `tablet`... |
| L3 | subtipo | Subtipo | 0.30 | `botella_de_jugo`, `copa_de_vino`, `taza_vaso`... |
| L4 | variante | Variante | 0.20 | Diferenciadores finos observables |
| L5 | instancia | Instancia | 0.10 | Máxima granularidad alcanzable con evidencia |

**Especificidad efectiva:** `∑ peso_nivel para cada nivel resuelto según atributos verificados`.

**Umbral:** `effective_specificity >= 0.55` → `accepted: true` (configurable vía manifest de `scan_validator`).

### Casos de Diferenciación Fina (Ejemplos)

El diseño resuelve distinciones como las que solicitaste, basándose en **discriminadores estructurales/visuales medibles**:

| Distinción | Discriminadores clave | Explicación |
|---|---|---|
| **Botella vs Vaso** | `neck_present`, `neck_length`, `shoulder_shape`, `opening_type`, `wall_thickness` | Botella: cuello (neck) estrecho + hombros definidos. Vaso: apertura amplia, sin cuello pronunciado. |
| **Vaso vs Copa de Vino** | `stem_present`, `stem_height`, `foot_width`, `bowl_shape`, `rim_shape` | Copa: cáliz (bowl) ensanchado, tallo (stem) + pie (foot). Vaso: base plana, sin stem. |
| **Taza/Vaso con asa vs sin asa** | `handle_present`, `handle_count`, `handle_position` | Diferenciador directo y observable. |
| **Teléfono vs Tablet** | `screen_ratio`, `bezel_type`, `form_factor` | Proporciones pantalla/cuerpo + grosor relativo visible (desde región marcada). |

> Ver detalles completos y reglas para prompts en [`docs/prompt_contracts.md`](docs/prompt_contracts.md). Ver taxonomía extendida en [`config/taxonomy.yaml`](config/taxonomy.yaml).

## 9. Manifiestos y Contratos

Todo agente/skill declara su contrato en `manifest.yaml`. El orquestador lee manifiestos, **no adivina interfaces**.

### Campos Clave

| Entidad | Obligatorios | Destacados |
|---|---|---|
| **Agente** | `name`, `version`, `description`, `skills_required`, `permissions`, `input_schema`, `output_schema` | Composición declarativa. |
| **Skill** | `name`, `version`, `description`, `input_schema`, `output_schema`, `determinism`, `requires` | Define orden del pipeline vía `requires`. |
| **Común (opcional)** | `permissions`, `rate_limit` (network), `cacheable` (solo pure), `privacy_class` | `privacy_class: restricted` bloquea nodos sensibles (ej. `person`). |

**Valores `determinism`:** `pure` | `model` | `network`

**Ver esquema completo:** [`docs/manifest_schema.md`](docs/manifest_schema.md)

## 10. Configuración

| Archivo | Propósito |
|---|---|
| [`config/agents.yaml`](config/agents.yaml) | Lista de agentes activos (`scan_agent`, `specificity_agent`, `context_agent`). |
| [`config/skills.yaml`](config/skills.yaml) | Lista de skills activas en el sistema. |
| [`config/taxonomy.yaml`](config/taxonomy.yaml) | **Fuente de verdad** para jerarquía, `discriminators`, pesos (L1–L5) y `privacy_class`. |
| [`config/environments/dev.yaml`](config/environments/dev.yaml) | Config entorno desarrollo. |
| [`config/environments/prod.yaml`](config/environments/prod.yaml) | Config entorno producción. |

## 11. Herramientas (`tools/`)

| Herramienta | Tipo | Uso |
|---|---|---|
| [`vision_api_client.py`](tools/vision_api_client.py) | Integración pura (tipada) | `detect_objects()`, `segment()`, `ocr()`. Sin lógica de agente/especificidad. Preparado para proveedores de visión. |
| `github_client.py`, `slack_client.py` | Placeholders | Estructura preparada para futuras integraciones. |

## 12. Memoria, Seguridad y Observabilidad

| Componente | Punto Único | Regla |
|---|---|---|
| **Memoria** | `core/memory/memory_manager.py` | **Ningún** agente/skill accede directo a `short_term`/`long_term`. Todo pasa por manager (trazabilidad + composabilidad). |
| **Seguridad** | `core/security/permissions.py` + `guardrails.py` | Permisos por manifiesto (principio mínimo privilegio). Validación de I/O. |
| **Observabilidad** | `core/observability/tracer.py` + `logger.py` | Traza cada decisión del orquestador, pasadas de enhancer, lookups y validaciones. |

## 13. Estado del Proyecto

- **Arquitectura:** Definida y completa.
- **Contratos (manifests):** Completos para agentes y skills.
- **Taxonomía:** Enriquecida para diferenciación fina (recipientes + electrónicos).
- **Implementación lógica (`run()`):** **`NotImplementedError` intencionalmente**. No hay lógica de ejecución aún — solo estructura, contratos y reglas.
- **Interfaces (API/CLI/UI):** Pendientes (no implementadas).
- **Tests/Evaluaciones:** Estructura creada (`evaluations/`), casos a añadir según necesidades.

> Este repositorio es el **esqueleto arquitectónico** sobre el que se alimentará con Skills e implementaciones, siguiendo estrictamente el framework definido.

## 14. Cómo Extender el Proyecto

Para añadir un nuevo caso de escaneo (sin romper invariantes):

1. **Añadir nodo(s) a taxonomía** → [`config/taxonomy.yaml`](config/taxonomy.yaml). Definir `discriminators` que separen clase hermana (medibles, no inferidos).
2. **Crear skill** → `skills/<nombre>/skill.py` (hereda `BaseSkill`) + `manifest.yaml` (`input/output`, `requires`, `determinism`, `permissions` si aplica).
3. **Registrar skill** → Añadir a [`config/skills.yaml`](config/skills.yaml).
4. **Añadir tests** → Casos en [`evaluations/skill_tests/`](evaluations/skill_tests/).
5. **Actualizar docs** (opcional) → Si añade nuevo modo de captura, documentar en `docs/`.

**Regla importante:** No es necesario modificar agentes. El pipeline se compone vía `requires` + registro en config.

## 15. Licencia y Notas

- Proyecto académico/experimental para estructura de agentes con IA.
- Enfoque en **precisión verificable** y **responsabilidad sobre evidencia** (evita alucinaciones mediante "ausente vs adivinado").