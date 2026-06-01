# Sampling

`stratified_sampler.py` genera la muestra vigente del proyecto: PRs `merged_after_rework`, es decir, PRs cerrados y mergeados con `commit_count > 1` y `human_comment_count > 0`.

La estratificacion usada es solo por `agent`, con semilla fija `20260510` y tamano por defecto de 300 PRs.

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
