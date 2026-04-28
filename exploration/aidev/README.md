# AIDev Exploration

Primer espacio de trabajo para conocer el dataset `hao-li/AIDev` y levantar métricas básicas sin descargar todavía todos los archivos.

## Enfoque recomendado

Para este primer intento conviene usar la API pública del Dataset Viewer de Hugging Face en lugar de bajar todo el dataset de inmediato. Eso permite:

- listar subsets y tamaños;
- inspeccionar columnas y filas de ejemplo;
- calcular métricas rápidas sobre una muestra;
- hacer búsquedas de texto en subsets específicos.

Esto es suficiente para entender la estructura del dataset y decidir después si conviene pasar a un análisis más pesado con `Parquet`, `DuckDB` o notebooks.

## Estructura

- [inspect_aidev.py](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/inspect_aidev.py): CLI para overview, preview, profile y search.
- [pr_activity.py](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/pr_activity.py): helper para cargar URLs Parquet y resumir actividad por PR al cruzar `pull_request`, `pr_commits` y `pr_reviews`.
- [notebooks/2026-04-27-pr-activity-exploration.ipynb](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/notebooks/2026-04-27-pr-activity-exploration.ipynb): notebook inicial con joins y gráficos básicos.
- [requirements-notebook.txt](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/requirements-notebook.txt): dependencias para ejecutar el notebook.
- [tests/test_inspect_aidev.py](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/tests/test_inspect_aidev.py): tests de la lógica de agregación.
- [tests/test_pr_activity.py](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/tests/test_pr_activity.py): tests para el cruce entre PRs, commits y reviews.
- `reports/`: resultados de corridas reales guardadas como referencia.

## Fuentes

- Dataset en Hugging Face: <https://huggingface.co/datasets/hao-li/AIDev>
- Repositorio y notebooks base: <https://github.com/SAILResearch/AI_Teammates_in_SE3/blob/main/README.md>
- Documentación oficial del Dataset Viewer API: <https://huggingface.co/docs/dataset-viewer/quick_start>

## Consultas sugeridas

### 1. Panorama general del dataset

```bash
python3 exploration/aidev/inspect_aidev.py overview
```

Esto muestra:

- si el dataset soporta preview, search y statistics;
- cuántos subsets/configs existen;
- cuántas filas tiene en total;
- tamaño y cantidad de filas por subset.

### 2. Ver columnas y ejemplos del subset principal

```bash
python3 exploration/aidev/inspect_aidev.py preview --config all_pull_request --limit 3
```

Esto sirve para revisar rápidamente la estructura de `all_pull_request`, que incluye campos como `state`, `created_at`, `merged_at`, `repo_id` y `agent`.

### 3. Sacar métricas básicas sobre una muestra

```bash
python3 exploration/aidev/inspect_aidev.py profile --config all_pull_request --limit 500
```

Esto calcula, sobre las primeras `500` filas consultadas:

- conteo de nulos en campos relevantes;
- distribuciones simples de variables categóricas;
- rangos mínimos y máximos de fechas.

Importante: `profile` no resume todo el dataset; resume la muestra indicada por `--limit`.

### 4. Buscar casos puntuales

```bash
python3 exploration/aidev/inspect_aidev.py search --config all_pull_request --query "Generated with"
```

Esto ayuda a revisar patrones textuales en títulos o cuerpos de PRs.

## Siguiente paso sugerido

Si estas consultas iniciales les sirven, el siguiente paso razonable es elegir `2` o `3` subsets centrales para el proyecto, por ejemplo:

- `all_pull_request` o `pull_request`;
- `pr_commits` o `pr_commit_details`;
- `pr_reviews` o `pr_review_comments`.

Después de eso conviene pasar a una segunda etapa con:

1. extracción de una muestra reproducible;
2. unión entre subsets por `id`, `number`, `repo_id` u otras llaves disponibles;
3. métricas ya alineadas con las preguntas de investigación.

## Notebook para cruce inicial

El notebook [2026-04-27-pr-activity-exploration.ipynb](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/notebooks/2026-04-27-pr-activity-exploration.ipynb) está pensado como primer análisis reproducible sobre:

- `pull_request`;
- `pr_commits`;
- `pr_reviews`.

El flujo del notebook es:

1. instalar dependencias si faltan;
2. cargar los tres Parquet oficiales desde Hugging Face;
3. construir una tabla resumen por PR;
4. calcular métricas como merge rate, commits por PR y revisiones humanas/bot;
5. generar gráficos básicos para explorar señales iniciales de intervención.
