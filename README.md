# Proyecto Semestral MSR: PRs “No Aceptados Inmediatamente” de Agentes IA (AIDev)

En este repositorio construimos un flujo reproducible para responder:

**¿En qué casos los agentes de IA resultan contraproducentes al abrir PRs y cuánto esfuerzo/iteraciones toma integrarlos efectivamente?**

Usamos como fuente principal el dataset **AIDev** (`hao-li/AIDev`). El núcleo metodológico es construir una **taxonomía inductiva** de motivos de retrabajo mediante **card sorting abierto** sobre una muestra reproducible, y luego analizar distribución y esfuerzo/tiempo de integración asociado.

Referencias clave del diseño:

- Plan metodologico versionado: `docs/plans/plan-metodologico-card-sorting.md`
- Referencia metodológica de card sorting: `docs/card-sorting.pdf`

## Qué buscamos responder y lograr

**Resultado principal del proyecto**

- Una taxonomía jerárquica (2 niveles) de motivos de *retrabajo pre-merge*: `categoria_padre` → `subcategoria`.
- Un mapeo estructurado `pr_id → subcategoria → categoria_padre` para análisis cuantitativo posterior.

**Preguntas de investigación (RQs)**

1. **RQ1**: ¿Qué categorías de motivos de retrabajo (feedback/revisión) emergen del card sorting manual en PRs que no se aceptan de inmediato?
2. **RQ2**: En esos casos, ¿cuánto tiempo pasa hasta el merge final y cuántas intervenciones humanas aparecen en el camino?
3. **RQ3**: ¿Cómo se distribuyen las categorías por agente, lenguaje y tipo de tarea?
4. **RQ4**: ¿Qué relación hay entre la categoría y el esfuerzo/tiempo requerido para llegar a aceptación?

## Definiciones operacionales (cómo se “materializa” el fenómeno en datos)

Trabajamos principalmente con:

1. **Mergeado después de retrabajo** (`merged_after_rework`)
   - PRs con `state = closed` y `merged_at NOT NULL`, con señales de que no fue aceptación inmediata.
   - En el flujo actual se detecta por una combinación de:
     - señales de cambio de código: `commit_count > 1` o `has_post_review_code_change` / `post_review_code_change_count > 0`.
     - señales de feedback/review: conteos en reviews y/o comentarios.

Notas:

- `merged_after_rework` captura casos donde hubo iteración antes de integrarse.
- El análisis de “rechazo definitivo” existe como variante (`rejected`), pero no es el foco operativo principal.

## Metodología: card sorting en tres etapas

Adaptamos la estructura de Zimmermann en `docs/card-sorting.pdf`: **Preparation**, **Execution** y **Analysis**. Usamos primera persona técnica plural para dejar claro qué decisión metodológica tomamos en cada etapa.

### 1) Preparation

- Cargamos el dataset `hao-li/AIDev` y construimos la población operacional `merged_after_rework`.
- Incluimos solo PRs mergeados con retrabajo observable: `merged_at` no nulo, `commit_count > 1` y `human_comment_count > 0`.
- Extraemos una muestra aleatoria estratificada por `agent` y generamos una tarjeta por PR con identificador, contexto mínimo, tiempos de aceptación y evidencia textual humana.

### 2) Execution

- Clasificamos manualmente las tarjetas mediante **card sorting abierto**: no imponemos categorías previas, sino que agrupamos tarjetas por similitud temática.
- Usamos títulos descriptivos para los grupos, separamos tarjetas ambiguas o descartables y calibramos criterios entre evaluadores antes de congelar categorías.
- La tabla de categorización debe ser reducida y trazable: `card_id`, `pr_id`, `agent`, `html_url`, `cita_textual_retrabajo`, `categoria_retrabajo_pre_merge`, `justificacion_breve`.

### 3) Analysis

- Revisamos consistencia dentro de los grupos, consolidamos categorías similares y construimos una taxonomía jerárquica.
- Cruzamos la categoría con métricas de agente, lenguaje, tipo de tarea, comentarios humanos y tiempo hasta aceptación.
- Aplicamos soundness: cada categoría debe responder directamente a la pregunta de investigación y estar respaldada por una cita textual cuando exista evidencia humana.

## Criterios de inclusión y exclusión

Incluimos PRs que cumplen todos estos criterios:

- pertenecen al dataset `hao-li/AIDev`;
- están cerrados y mergeados (`merged_at` no nulo);
- tienen commits adicionales (`commit_count > 1`);
- tienen evidencia textual humana (`human_comment_count > 0`);
- pertenecen al caso operacional `merged_after_rework`.

Excluimos PRs abiertos, PRs cerrados sin merge, PRs mergeados sin commits adicionales, casos sin comentarios humanos observables y casos `rejected`, porque el foco es retrabajo antes del merge, no rechazo definitivo.

## Embudo desde el universo total

Estos totales provienen del resumen canónico de muestreo con seed `20260510`.

| Paso | Total | Retención vs universo | Pérdida vs universo |
|---|---:|---:|---:|
| Universo bruto AIDev | 33.596 | 100,00% | 0,00% |
| PRs mergeados | 24.014 | 71,48% | 28,52% |
| PRs mergeados con commits adicionales | 6.884 | 20,49% | 79,51% |
| Población operacional | 3.166 | 9,42% | 90,58% |
| Muestra estratificada vigente | 300 | 0,89% | 99,11% |

## Muestreo estratificado y error muestral

Usamos asignación proporcional por agente. Para cada estrato `h`:

```text
n_h = round((N_h / N) * n)
```

donde `N_h` es el tamaño del estrato, `N` la población operacional total, `n` el tamaño de muestra objetivo y `n_h` la cuota del agente. Con `N = 3.166` y `n = 300`, las cuotas vigentes son: Copilot 145, Devin 86, OpenAI_Codex 45, Cursor 17 y Claude_Code 7.

Con corrección por población finita, 95% de confianza (`z = 1,96`) y máxima varianza (`p = 0,5`), la muestra vigente `n = 300` produce un error aproximado de ±5,38%. Para cumplir error ≤ 5%, debemos aumentar la muestra a aproximadamente `n = 343`:

```text
n = (N * z^2 * p * (1-p)) / (e^2 * (N-1) + z^2 * p * (1-p))
```

## Plan de mejora metodológica

1. Reescribir notebook y presentación en primera persona técnica.
2. Mostrar la metodología en las tres etapas de Zimmermann: Preparation, Execution y Analysis.
3. Reportar pérdidas porcentuales desde el universo total en cada filtro.
4. Dejar explícitos criterios de inclusión/exclusión y fórmula de estratificación.
5. Ajustar el tamaño muestral a `n ≈ 343` si se exige error ≤ 5% al 95%.
6. Usar una tabla manual reducida con cita textual de retrabajo y justificación breve.
7. Validar soundness: categoría, cita y justificación deben responder la pregunta planteada.
8. Preparar una presentación con problema, dataset, embudo, muestreo, card sorting, soundness y resultados esperados.

La hoja manual de Javier se corrige sin perder categorías ya asignadas: se restauran tiempos con decimales desde la plantilla canónica y se agregan columnas de trazabilidad (`agent`, `cita_textual_retrabajo`, `evidence_source`, `evidence_created_at`, `merged_at`, `justificacion_breve`). La columna `cita_textual_retrabajo` queda vacía para que los evaluadores copien manualmente la cita que sustenta cada categoría; la evidencia sugerida sigue disponible en `cards.csv`.

En el notebook, los criterios de inclusión/exclusión se reportan integrados en la tabla dinámica de embudo junto con los porcentajes de pérdida; esa tabla debe generarse por código, no como texto fijo.

## Flujo del sistema (pipeline reproducible)

El pipeline vive en `exploration/aidev/` y se ejecuta en fases separadas para que el notebook muestre el flujo de datos sin mezclar filtros poblacionales con muestreo:

### 0) Setup

Crear/usar entorno virtual del repo (`.venv`) e instalar dependencias de notebooks/parquet:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r exploration/aidev/requirements-notebook.txt
```

### 1) Filtros poblacionales

Script: `exploration/aidev/sampling/population_filter.py`

Función:

- Construye la población objetivo `merged_after_rework`.
- Aplica el filtro operacional: PR mergeado, `commit_count > 1` y `human_comment_count > 0`.
- Escribe un CSV intermedio con los 3.166 PRs antes de estratificar.

Ejemplo:

```bash
.venv/bin/python exploration/aidev/sampling/population_filter.py
```

Salida:

- `exploration/aidev/sampling/outputs/merged_after_rework_population.csv`
- `exploration/aidev/sampling/outputs/merged_after_rework_population_summary.json`

### 2) Muestreo estratificado por agente

Script: `exploration/aidev/sampling/stratified_sampler.py`

Función:

- Lee la población ya filtrada desde `merged_after_rework_population.csv`.
- Estratifica por `agent` y asigna cuotas proporcionales con un mínimo por estrato.
- Selecciona una muestra aleatoria reproducible con semilla fija.

Ejemplo:

```bash
.venv/bin/python exploration/aidev/sampling/stratified_sampler.py \
  --population-csv exploration/aidev/sampling/outputs/merged_after_rework_population.csv \
  --sample-size 300 \
  --min-per-stratum 3 \
  --seed 20260510 \
  --output-csv exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510.csv \
  --summary-json exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510_summary.json
```

Salida:

- `exploration/aidev/sampling/outputs/*_sample_seed_<seed>.csv`: muestra seleccionada
- `exploration/aidev/sampling/outputs/*_sample_seed_<seed>_summary.json`: resumen de control (seed, tamanos, cuotas, distribuciones)

### 3) Preparación de “tarjetas” (Cards) con evidencia textual

Script: `exploration/aidev/preparation/rejection_cards.py`

Función:

- Carga la muestra (CSV) y cruza evidencia textual desde tablas del dataset (reviews, comments, timeline).
- Selecciona y limpia la evidencia más útil para justificar el motivo de rechazo/feedback.
- Construye una tarjeta por PR con campos estandarizados.
- Filtra por defecto a tarjetas con `human_comment_count > 0` (para asegurar evidencia humana mínima).

Ejemplo:

```bash
.venv/bin/python exploration/aidev/preparation/rejection_cards.py \
  --sample-csv exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510.csv \
  --output-csv exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510.csv \
  --summary-json exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510_summary.json
```

Salida:

- `exploration/aidev/preparation/outputs/*cards*.csv`: tarjetas para clasificar
- `exploration/aidev/preparation/outputs/*summary*.json`: resumen y métricas de control
- Plantilla manual (categorizacion): `exploration/aidev/preparation/outputs/merged_after_rework_manual_categories_template.csv`
- Taxonomia inicial (manual, versionada): `exploration/aidev/taxonomy/initial/`

### 4) Card sorting (manual) y exportación de etiquetas

El card sorting se realiza de forma manual usando CSV:

- Plantilla producida por el flujo: `exploration/aidev/preparation/outputs/merged_after_rework_manual_categories_template.csv`
- Ubicacion recomendada para versionar el trabajo manual inicial:
  - `exploration/aidev/taxonomy/initial/`

Resultado esperado del card sorting:

- Para cada tarjeta/PR: cita textual de retrabajo, categoría, justificación breve y trazabilidad `card_id → pr_id → evidencia → categoría`.
- Luego: agrupar/normalizar categorías similares para llegar a un set estable y reutilizable.

## Dónde está el código

- `exploration/aidev/aidev_data.py`: helpers minimos para acceder a manifests/URLs Parquet.
- `exploration/aidev/sampling/`: filtros poblacionales, muestreo aleatorio estratificado y outputs.
- `exploration/aidev/preparation/`: preparación de tarjetas (evidencia textual, cleaning, calidad).
- `exploration/aidev/notebook_flow.py`: helpers para notebooks del flujo merged-after-rework.

## Tests

No hay suite de tests versionada actualmente. Para validación rápida se usan `compileall`, `--dry-run` en sampling/preparation y ejecución del notebook principal.

Para sesiones OpenCode, las instrucciones operativas compactas viven en `AGENTS.md`.

## Convención de outputs

- Artefactos canónicos de población: `exploration/aidev/sampling/outputs/merged_after_rework_population.csv` y `merged_after_rework_population_summary.json`.
- Artefactos canónicos de sampling: `exploration/aidev/sampling/outputs/*_sample_seed_<seed>.csv` y `*_sample_seed_<seed>_summary.json`.
- Taxonomia inicial (manual): `exploration/aidev/taxonomy/initial/`.
