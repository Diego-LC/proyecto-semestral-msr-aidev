# AGENTS.md

## Reglas de trabajo

- Antes de cualquier cambio en código o archivos, actualiza primero `README.md`.
- Pregunta antes de `git commit`, `git push`, `git rebase` o cambios que afecten ramas/remotos. Propón el comando exacto.
- Commits en español, Conventional Commits y con cuerpo breve; ver `.agents/workflows/commits.md`.

## Foco del repo

- El flujo operativo es `merged_after_rework`: PRs AIDev mergeados tras retrabajo. No revivas ni optimices flujos `rejected` salvo pedido explícito.
- Pregunta principal de investigación: qué motivos de retrabajo humano emergen en PRs de agentes IA antes de su integración.
- Pregunta complementaria: cómo se relacionan esos motivos con el esfuerzo y el tiempo requeridos hasta el merge.
- Pipeline: población `merged_after_rework` → muestra estratificada por `agent` (n=300, seed `20260510`) → tarjetas con evidencia → card sorting manual → taxonomía + métricas.

## Entorno y comandos reales

- Usa siempre `.venv/bin/python`; con `/usr/bin/python3` pueden faltar `pandas`/`pyarrow`.
- Instalar dependencias mínimas:
  ```bash
  .venv/bin/python -m pip install -r exploration/aidev/requirements-notebook.txt
  ```
- Muestreo canónico:
  ```bash
  .venv/bin/python exploration/aidev/sampling/stratified_sampler.py \
    --sample-size 300 \
    --min-per-stratum 3 \
    --seed 20260510 \
    --output-csv exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510.csv \
    --summary-json exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510_summary.json
  ```
- Tarjetas canónicas:
  ```bash
  .venv/bin/python exploration/aidev/preparation/rejection_cards.py \
    --sample-csv exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510.csv \
    --output-csv exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510.csv \
    --summary-json exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510_summary.json
  ```
- Validación sin escribir archivos: agrega `--dry-run` a cualquiera de esos dos scripts.

## Estructura que importa

- `exploration/aidev/aidev_data.py`: resuelve URLs Parquet del dataset `hao-li/AIDev` vía Hugging Face.
- `exploration/aidev/sampling/stratified_sampler.py`: arma la población y muestra; los outputs canónicos llevan `seed_<seed>`.
- `exploration/aidev/preparation/rejection_cards.py`: cruza muestra con reviews/comentarios/timeline; filtra por defecto tarjetas con `human_comment_count > 0` y escribe también la plantilla manual.
- `exploration/aidev/notebook_flow.py`: helpers del notebook principal `notebooks/2026-05-26-merged-after-rework-flow.ipynb`.
- Taxonomía manual versionada: `exploration/aidev/taxonomy/initial/`. No tocar resultados manuales sin confirmación.

## Verificación y gotchas

- No hay CI ni suite de tests versionada actualmente; `exploration/aidev/tests/` no contiene tests. Usa `--dry-run` como verificación rápida del pipeline.
- `--sample-size` debe ser compatible con `--min-per-stratum` y la cantidad de agentes; si bajas el tamaño de muestra, baja también el mínimo por estrato.
- No borres outputs históricos salvo que confirmes que son duplicados verificables.
- `.gitignore` ignora borradores locales `exploration/aidev/preparation/outputs/*manual_categories.csv`, pero no la plantilla canónica `*_manual_categories_template.csv`.
