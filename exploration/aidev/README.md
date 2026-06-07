# AIDev merged-after-rework flow

Este directorio contiene el flujo reproducible usado para analizar PRs de AIDev que fueron aceptados despues de retrabajo: PRs mergeados con commits adicionales y comentarios humanos.

## Entorno

Desde la raiz del repositorio:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r exploration/aidev/requirements-notebook.txt
```

## Ejecucion

Construir la poblacion operacional antes de estratificar:

```bash
.venv/bin/python exploration/aidev/sampling/population_filter.py
```

Generar la muestra estratificada por agente desde el CSV poblacional:

```bash
.venv/bin/python exploration/aidev/sampling/stratified_sampler.py
```

Generar tarjetas con evidencia y plantilla manual:

```bash
.venv/bin/python exploration/aidev/preparation/rejection_cards.py
```

Validar sin escribir archivos:

```bash
.venv/bin/python exploration/aidev/sampling/population_filter.py --dry-run
.venv/bin/python exploration/aidev/sampling/stratified_sampler.py --dry-run
.venv/bin/python exploration/aidev/preparation/rejection_cards.py --dry-run
```

## Artefactos vigentes

- `sampling/outputs/merged_after_rework_population.csv`
- `sampling/outputs/merged_after_rework_population_summary.json`
- `sampling/outputs/merged_after_rework_sample_seed_20260510.csv`
- `sampling/outputs/merged_after_rework_sample_seed_20260510_summary.json`
- `preparation/outputs/merged_after_rework_cards_seed_20260510.csv`
- `preparation/outputs/merged_after_rework_cards_seed_20260510_summary.json`
- `preparation/outputs/merged_after_rework_manual_categories_template.csv`
- `notebooks/2026-05-26-merged-after-rework-flow.ipynb`

## Flujo

1. `sampling/population_filter.py` descarga los Parquet oficiales desde Hugging Face, calcula métricas de reviews/comentarios y controles, aplica filtros y escribe la poblacion `merged_after_rework`.
2. `sampling/stratified_sampler.py` carga `merged_after_rework_population.csv` y extrae una muestra de 300 PRs estratificada por `agent`, sin reconstruir la poblacion.
3. `preparation/rejection_cards.py` carga la muestra, recupera evidencia desde reviews, comentarios y timeline, y produce una tarjeta por PR.
4. El notebook principal documenta el embudo, las distribuciones y las validaciones importando helpers de los scripts del flujo.
