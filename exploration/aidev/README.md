# AIDev merged-after-rework flow

Este directorio contiene el flujo reproducible usado para analizar PRs de AIDev que fueron aceptados despues de retrabajo: PRs mergeados con commits adicionales y comentarios humanos.

## Entorno

Desde la raiz del repositorio:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r exploration/aidev/requirements-notebook.txt
```

## Ejecucion

Generar la muestra estratificada por agente:

```powershell
python exploration/aidev/sampling/stratified_sampler.py
```

Generar tarjetas con evidencia y plantilla manual:

```powershell
python exploration/aidev/preparation/rejection_cards.py
```

Validar sin escribir archivos:

```powershell
python exploration/aidev/sampling/stratified_sampler.py --dry-run
python exploration/aidev/preparation/rejection_cards.py --dry-run
```

## Artefactos vigentes

- `sampling/outputs/merged_after_rework_sample_seed_20260510.csv`
- `sampling/outputs/merged_after_rework_sample_seed_20260510_summary.json`
- `preparation/outputs/merged_after_rework_cards_seed_20260510.csv`
- `preparation/outputs/merged_after_rework_cards_seed_20260510_summary.json`
- `preparation/outputs/merged_after_rework_manual_categories_template.csv`
- `notebooks/2026-05-26-merged-after-rework-flow.ipynb`

## Flujo

1. `sampling/stratified_sampler.py` descarga los Parquet oficiales desde Hugging Face, construye la poblacion `merged_after_rework` y extrae una muestra de 300 PRs estratificada por `agent`.
2. `preparation/rejection_cards.py` carga la muestra, recupera evidencia desde reviews, comentarios y timeline, y produce una tarjeta por PR.
3. El notebook principal documenta el embudo, las distribuciones y las validaciones importando helpers de los scripts del flujo.
