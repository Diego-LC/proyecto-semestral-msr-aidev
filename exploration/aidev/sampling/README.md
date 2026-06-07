# Sampling

El flujo de sampling queda separado en dos pasos ejecutables e importables:

1. `population_filter.py`: construye la poblacion operacional `merged_after_rework`.
2. `stratified_sampler.py`: lee esa poblacion y genera la muestra estratificada.

## Paso 0: poblacion operacional

`population_filter.py` filtra PRs cerrados y mergeados con `commit_count > 1` y `human_comment_count > 0`. También calcula las métricas que se auditan antes del muestreo: conteos de reviews/comentarios humanos y bot, bins de complejidad del cambio, popularidad del repositorio, periodo de creación y tipo de tarea.

```bash
.venv/bin/python exploration/aidev/sampling/population_filter.py
```

Salidas:

- `outputs/merged_after_rework_population.csv`
- `outputs/merged_after_rework_population_summary.json`

Para revisar el resumen sin escribir archivos:

```bash
.venv/bin/python exploration/aidev/sampling/population_filter.py --dry-run
```

## Paso 1: muestra estratificada

La estratificacion usada es solo por `agent`, con semilla fija `20260510` y tamano por defecto de 300 PRs.
Este paso no descarga Parquets ni recalcula filtros poblacionales; consume el CSV producido por `population_filter.py`.

```bash
.venv/bin/python exploration/aidev/sampling/stratified_sampler.py
```

Salidas:

- `outputs/merged_after_rework_sample_seed_20260510.csv`
- `outputs/merged_after_rework_sample_seed_20260510_summary.json`

Para revisar el resumen sin escribir archivos:

```bash
.venv/bin/python exploration/aidev/sampling/stratified_sampler.py --dry-run
```
