# AGENTS.md

## Reglas de Trabajo

- Siempre preguntar si estoy de acuerdo con el mensaje de commit antes de ejecutarlo, este debe ser detallado pero no tan extenso. Preguntar explicitamente si hacer push, rebase o cambios que afecten el repositorio.
- Siempre que hagas cambios en el código o en archivos, actualizar primero el archivo README.md.

## Repo Intent (AIDev / merged-after-rework)

- El foco operativo del proyecto es **solo** la población `merged-after-rework` (PRs mergeados tras señales de retrabajo). No optimizar ni documentar flujos para `rejected` salvo que se pida explícitamente.
- El objetivo de investigación es entender cuándo PRs de agentes IA resultan contraproducentes y **cuánto esfuerzo/tiempo** toma integrarlos (taxonomía + métricas).

## Metodología (en una línea)

- Filtrar casos `merged_after_rework` → muestreo estratificado por `agent` (n=300) → construir tarjetas con evidencia → card sorting manual con 2 evaluadores → agrupar categorías similares → analizar distribución y esfuerzo/tiempo hasta merge.

## Quickstart (Comandos Reales)

- Usar el venv del repo: `.venv/bin/python`.
- Dependencias mínimas para Parquet/AIDev:
  - `.venv/bin/python -m pip install -r exploration/aidev/requirements-notebook.txt`

### 1) Sampling (estratificado por agente)

```bash
.venv/bin/python exploration/aidev/sampling/stratified_sampler.py \
  --source aidev \
  --population-mode merged-after-rework \
  --sample-size 300 \
  --min-per-stratum 3 \
  --seed 20260510 \
  --output-csv exploration/aidev/sampling/outputs/merged_after_rework_sample.csv \
  --summary-json exploration/aidev/sampling/outputs/merged_after_rework_sample_summary.json
```

- Convención: outputs canónicos **sin** sufijos `seed_*`.

### 2) Cards (evidencia textual)

```bash
.venv/bin/python exploration/aidev/preparation/rejection_cards.py \
  --sample-csv exploration/aidev/sampling/outputs/merged_after_rework_sample.csv \
  --output-csv exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510.csv \
  --summary-json exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510_summary.json
```

- El script filtra por defecto a tarjetas con `human_comment_count > 0`.

### 3) Card Sorting (dos vías)

- Taxonomía inicial (manual) versionada aquí:
  - `exploration/aidev/taxonomy/initial/merged_after_rework_manual_categories_template.csv`

- Labeling Machine (web): el adaptador por defecto toma `merged_after_rework_cards_seed_20260510.csv`:

```bash
.venv/bin/python exploration/aidev/labeling_machine/labeling_machine_adapter.py
```

## Tests (rápidos y relevantes)

```bash
.venv/bin/python -m unittest \
  exploration.aidev.tests.test_stratified_sampler \
  exploration.aidev.tests.test_rejection_cards \
  exploration.aidev.tests.test_labeling_machine_adapter
```

## Gotchas

- Si ejecutas scripts con `/usr/bin/python3` puede faltar `pandas`/`pyarrow`. Usa siempre `.venv/bin/python`.
- `--sample-size` debe ser compatible con `--min-per-stratum` y el número de estratos (agente). Si reduces `sample-size`, reduce también `--min-per-stratum`.
- No borrar outputs “históricos” a menos que sean duplicados verificables; los resultados manuales en `exploration/aidev/taxonomy/` no deben tocarse sin pedirlo.
