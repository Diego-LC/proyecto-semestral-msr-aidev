# Proyecto Semestral MSR: PRs “No Aceptados Inmediatamente” de Agentes IA (AIDev)

Este repositorio implementa el flujo de datos y herramientas para responder:

**¿En qué casos los agentes de IA resultan contraproducentes al abrir PRs y cuánto esfuerzo/iteraciones toma integrarlos efectivamente?**

La fuente principal es el dataset **AIDev** (`hao-li/AIDev`). El núcleo metodológico es construir una **taxonomía inductiva** de motivos de retrabajo mediante **card sorting abierto** sobre una muestra reproducible, y luego analizar distribución y esfuerzo/tiempo de integración asociado.

Referencias clave del diseño:

- Plan metodologico versionado: `docs/plans/plan-metodologico-card-sorting.md`

## Qué se busca responder y lograr

**Resultado principal del proyecto**

- Una taxonomía jerárquica (2 niveles) de motivos de *retrabajo pre-merge*: `categoria_padre` → `subcategoria`.
- Un mapeo estructurado `pr_id → subcategoria → categoria_padre` para análisis cuantitativo posterior.

**Preguntas de investigación (RQs)**

1. **RQ1**: ¿Qué categorías de motivos de retrabajo (feedback/revisión) emergen del card sorting manual en PRs que no se aceptan de inmediato?
2. **RQ2**: En esos casos, ¿cuánto tiempo pasa hasta el merge final y cuántas intervenciones humanas aparecen en el camino?
3. **RQ3**: ¿Cómo se distribuyen las categorías por agente, lenguaje y tipo de tarea?
4. **RQ4**: ¿Qué relación hay entre la categoría y el esfuerzo/tiempo requerido para llegar a aceptación?

## Definiciones operacionales (cómo se “materializa” el fenómeno en datos)

Este repositorio trabaja principalmente con:

1. **Mergeado después de retrabajo** (`merged_after_rework`)
   - PRs con `state = closed` y `merged_at NOT NULL`, con señales de que no fue aceptación inmediata.
   - En el flujo actual se detecta por una combinación de:
     - señales de cambio de código: `commit_count > 1` o `has_post_review_code_change` / `post_review_code_change_count > 0`.
     - señales de feedback/review: conteos en reviews y/o comentarios.

Notas:

- `merged_after_rework` captura casos donde hubo iteración antes de integrarse.
- El análisis de “rechazo definitivo” existe como variante (`rejected`), pero no es el foco operativo principal.

## Metodología (resumen ejecutable)

Basado en `docs/notas.md`.

1. **Fuente de datos**: dataset `hao-li/AIDev`.
2. **Filtro de casos (población)**:
   - PRs mergeados **después** de señales de retrabajo (cambio de código y/o interacción humana), marcados como `population_case_type = merged_after_rework`.
3. **Muestreo**:
   - Muestra aleatoria **estratificada por agente** (tamaño `n=300`, semilla fija para reproducibilidad).
4. **Card sorting manual (2 evaluadores)**:
   - Construir tarjetas con evidencia textual (reviews/comentarios/timeline) para cada PR.
   - Clasificar manualmente para derivar categorías inductivas (taxonomía) y luego agrupar categorías similares.
5. **Resultados a reportar**:
   - Datos crudos y procesados: muestra, tarjetas, taxonomía inicial y taxonomía refinada.
   - Análisis por categoría: distribución por agente/lenguaje/tipo de tarea y métricas de esfuerzo/tiempo hasta merge.

## Flujo del sistema (pipeline reproducible)

El pipeline vive en `exploration/aidev/` y se ejecuta en 3 fases:

### 0) Setup

Crear/usar entorno virtual del repo (`.venv`) e instalar dependencias de notebooks/parquet:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r exploration/aidev/requirements-notebook.txt
```

### 1) Muestreo estratificado por agente (Sampling)

Script: `exploration/aidev/sampling/stratified_sampler.py`

Función:

- Construye la población objetivo (principalmente `merged-after-rework`).
- Estratifica por `agent` (default) y asigna cuotas proporcionales con un mínimo por estrato.
- Selecciona una muestra aleatoria reproducible (semilla fija).

Ejemplo (poblacion `merged-after-rework`, n=300, seed configurable):

```bash
.venv/bin/python exploration/aidev/sampling/stratified_sampler.py \
  --sample-size 300 \
  --min-per-stratum 3 \
  --seed 20260510 \
  --output-csv exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510.csv \
  --summary-json exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510_summary.json
```

Salida:

- `exploration/aidev/sampling/outputs/*_sample_seed_<seed>.csv`: muestra seleccionada
- `exploration/aidev/sampling/outputs/*_sample_seed_<seed>_summary.json`: resumen de control (seed, tamanos, cuotas, distribuciones)

### 2) Preparación de “tarjetas” (Cards) con evidencia textual

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

### 3) Card sorting (manual) y exportación de etiquetas

El card sorting se realiza de forma manual usando CSV:

- Plantilla producida por el flujo: `exploration/aidev/preparation/outputs/merged_after_rework_manual_categories_template.csv`
- Ubicacion recomendada para versionar el trabajo manual inicial:
  - `exploration/aidev/taxonomy/initial/`

Resultado esperado del card sorting:

- Para cada tarjeta/PR: `categoria_padre`, `subcategoria` (y opcionalmente `confidence`, `rationale`, etc.).
- Luego: agrupar/normalizar categorías similares para llegar a un set estable y reutilizable.

## Dónde está el código

- `exploration/aidev/aidev_data.py`: helpers minimos para acceder a manifests/URLs Parquet.
- `exploration/aidev/sampling/`: muestreo aleatorio estratificado y outputs.
- `exploration/aidev/preparation/`: preparación de tarjetas (evidencia textual, cleaning, calidad).
- `exploration/aidev/notebook_flow.py`: helpers para notebooks del flujo merged-after-rework.

## Tests

```bash
.venv/bin/python -m unittest
```

## Convención de outputs

- Artefactos canónicos de sampling: `exploration/aidev/sampling/outputs/*_sample_seed_<seed>.csv` y `*_sample_seed_<seed>_summary.json`.
- Taxonomia inicial (manual): `exploration/aidev/taxonomy/initial/`.
