# Preparation

`rejection_cards.py` prepara las tarjetas para card sorting a partir de la muestra `merged_after_rework`.

Entrada por defecto:

- `../sampling/outputs/merged_after_rework_sample_seed_20260510.csv`

Salidas:

- `outputs/merged_after_rework_cards_seed_20260510.csv`
- `outputs/merged_after_rework_cards_seed_20260510_summary.json`
- `outputs/merged_after_rework_manual_categories_template.csv`

Ejecucion:

```powershell
python exploration/aidev/preparation/rejection_cards.py
```

Validacion sin escribir archivos:

```powershell
python exploration/aidev/preparation/rejection_cards.py --dry-run
```

La preparacion conserva una tarjeta por PR de la muestra y usa `human_comment_count > 0` como guardia de calidad. La evidencia se prioriza desde reviews con cambios solicitados, comentarios inline, comentarios generales, eventos de timeline y, como respaldo, titulo y descripcion del PR.

El CSV final conserva columnas de lectura rapida, como `evidence_text`, `review_comment_text` y `pr_comment_text`, y tambien columnas JSON estructuradas para trazabilidad: `all_evidence_json`, `pr_reviews_json`, `pr_review_comments_json` y `pr_comments_json`.
