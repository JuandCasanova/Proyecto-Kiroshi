# Esquema de manifest.yaml — Kiroshi Optics

Todo agente y toda skill declaran su contrato en un `manifest.yaml` al lado de
su codigo. El orquestador lee los manifiestos, no adivina interfaces.

## Campos obligatorios (comunes)
| Campo | Tipo | Descripcion |
|---|---|---|
| `name` | string | Identificador unico, snake_case. Debe coincidir con `name` de la clase y con la carpeta. |
| `version` | semver | Se incrementa al cambiar `input_schema` o `output_schema`. |
| `description` | string | Que hace, en una frase. Sin adjectives. |

## Campos obligatorios (solo agentes)
| Campo | Tipo | Descripcion |
|---|---|---|
| `skills_required` | list[string] | Skills que el agente compone. Deben existir en `config/skills.yaml`. |
| `permissions` | list[enum] | Permisos heredados de sus skills. |
| `input_schema` / `output_schema` | object | Contrato de `run(task) -> result`. |

## Campos obligatorios (solo skills)
| Campo | Tipo | Descripcion |
|---|---|---|
| `input_schema` / `output_schema` | object | Contrato de `run(params) -> result`. |
| `determinism` | enum | `pure` (misma entrada, misma salida), `model` (LLM, no determinista), `network` (fuera de linea). |
| `requires` | list[string] | Skills que deben ejecutarse antes. Define el orden del pipeline. |

## Campos opcionales
| Campo | Tipo | Descripcion |
|---|---|---|
| `permissions` | list[enum] | `network_access`, `memory_read`, `memory_write`, `code_execution`, `db_read`, `face_analysis`. |
| `rate_limit` | string | Ej. `30/min`. Requerido en skills con `determinism: network`. |
| `cacheable` | bool | Solo valido si `determinism: pure`. |
| `privacy_class` | enum | `restricted` bloquea el nodo salvo permiso explicito. |

## Enums de `specificity_level`
- `coarse`: solo clase general (L1).
- `standard`: hasta subtipo (L3).
- `forensic`: hasta variante e instancia (L4-L5). Es el default de Kiroshi.

## Enums de `privacy_class`
- `public`: sin restriccion.
- `restricted`: requiere permiso explicito en el manifiesto del agente.

## Ejemplo minimo
```yaml
name: feature_extractor
version: 0.1.0
description: Extrae los discriminadores taxonomicos del objetivo marcado
input_schema:
  mark: {type: object}
  candidate: {type: object, required: true}
output_schema:
  features: {type: object}
  completeness: {type: number}
requires: [target_classifier]
determinism: model
```