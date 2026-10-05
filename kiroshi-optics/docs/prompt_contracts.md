# Contrato para prompts de Kiroshi Optics

## Principios universales
- Evidence-based: solo responde con lo que puedes ver/leer en la marca. No inventes.
- Specificity-first: tu objetivo es obtener la mayor especificidad medible con evidencia.
- Separar evidencia de contexto: el contexto solo desempata cuando evidencia es insuficiente.
- Estricto por defecto: si no hay evidencia suficiente, responde ausente (null) o missing.
- Canonico: usa la taxonomia activa y sus discriminadores.

## Guias para cada skill

### target_classifier
- Usa solo lo visible en `mark` para proponer candidatos.
- Devuelve `class_path` completo, `class_id` y `discriminators` requeridos.
- Emite `ambiguity` (0.0 unico, 1.0 totalmente ambiguo).
- Prefiere candidatos concretos si hay rasgos distintivos visibles.

### feature_extractor
- Solo extrae discriminadores listados para el candidato.
- Para cada discriminador: valor, confianza (0-1), ausente (bool).
- NO extrapoles: si no puedes medirlo desde la marca, pon `ausente: true`.
- Usa terminologia descriptiva pero precisa (ej: "cilindrico", "tronco-conico", "rectangular_alto").
- Enfocate en formas, proporciones, aperturas, perfiles: estos diferencian vasos vs copas vs botellas.

### specificity_enhancer
- Objetivo: resolver discriminadores faltantes que aumentan especificidad.
- Paso 1: ordena faltantes por peso del nivel al que desbloquean (prioriza los que dan mayor ganancia).
- Paso 2: para cada faltante, pregunta: ¿hay evidencia directa medible en `mark`?
  - Si si: extrae valor con confianza. Solo acepta si confianza >= 0.7.
  - Si no: deja ausente (NO adivinar).
- Paso 3: recalcula especificidad. Si ganancia < 0.02, detente. Si llega a target, detente.
- Max 3 pases. Mantener `strict: true`.
- Nunca uses contexto para inventar atributos del objeto.

### scan_validator
- Calcula especificidad efectiva desde `attributes` + taxonomia.
- Valida que los atributos usados existen para el `class_id` elegido.
- Si `effective_specificity >= min_acceptable` (0.55) y sin violaciones criticas -> accepted=true.
- Si hay gaps pero alcanzable con lookup, sugiere `reference_lookup` en `remediation`.

### context_aggregator
- Solo aplica cuando candidatos empatados (mismo score tras validacion parcial).
- Usa señales de sesion/ambiente solo para desempate justificado.
- Nunca escribe contexto a `attributes` del objetivo. Solo a `used_signals`.

### reference_lookup
- Solo verifica (verify_only=true). No genera nuevos candidatos.
- Busca respaldo para discriminadores faltantes, no descripciones genericas.
- Reporta `confirmed/refuted` y `gap_hits`.

### mark_parser
- Produce Mark canonico y medible (bbox, modality, resolucion si aplica).
- No clasifica. No infiere.

## Notas sobre diferencias finas
- Recipientes: distinguir **botella** (cuello estrecho + hombros) vs **vaso/taza** (abertura amplia, sin cuello).
- Copas de vino: **bowl** mas ancho relativo, **stem** presente, **foot** definido.
- Taza/mug: generalmente **handle** presente.
- Telefonos vs tablets: **screen_ratio** + **bezel_type** + grosor relativo visible.
- Siempre prioriza rasgos **estructurales** (forma, apertura, proporciones) sobre funcion.
- Si dos opciones comparten TODOS los rasgos visibles -> dejar ambiguo, no elegir arbitrariamente.
