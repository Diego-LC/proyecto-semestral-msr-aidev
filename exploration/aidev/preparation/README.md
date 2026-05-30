# AIDev Cards Preparation

Esta carpeta implementa la fase de preparación de datos para el análisis manual de PRs de AIDev.

Entrada principal:

- `exploration/aidev/sampling/outputs/merged_after_rework_sample.csv`

Salida principal:

- `exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510.csv`
- `exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510_summary.json`

Taxonomía (manual, inicial):

- `exploration/aidev/taxonomy/initial/merged_after_rework_manual_categories_template.csv`

## Qué hace

El script [rejection_cards.py](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/preparation/rejection_cards.py):

- carga la muestra estratificada de PRs;
- carga evidencia textual desde `pr_reviews`, `pr_review_comments`, `pr_comments` y `pr_timeline`;
- selecciona la evidencia más útil para explicar el rechazo;
- construye una fila tipo tarjeta por PR;
- filtra la salida final a tarjetas con `human_comment_count > 0`;
- agrega columnas con señales de revisión, comentarios y calidad de evidencia;
- marca casos que requieren revisión manual de contexto o descarte.

## Prioridad de evidencia

Para cada PR se busca evidencia en este orden:

1. Reviews con `CHANGES_REQUESTED`.
2. Comentarios inline humanos en el diff.
3. Comentarios generales humanos del PR.
4. Reviews o comentarios de bots.
5. Mensajes de timeline.
6. Título y descripción del PR como respaldo.

Si solo existe título/descripción, la tarjeta queda con `needs_manual_context_check = true`, porque no hay una explicación explícita de rechazo.

## Campos de salida

El CSV `rejection_cards` contiene los campos definidos en el plan:

```text
card_id
pr_id
population_case_type
pr_state
merged
repo_id
repo_full_name
html_url
agent
pr_author
language
task_type
task_confidence
created_at
closed_at
merged_at
time_to_close_hours
time_to_merge_hours
complexity_bin
repo_popularity_bin
stars
forks
commit_count
file_count
total_changes
review_state
evidence_text
evidence_raw_text
evidence_source
evidence_path
evidence_diff_hunk
context_summary
pr_title
pr_body_text
needs_manual_context_check
evidence_quality_score
discard_candidate_reason
```

También incluye campos auxiliares para trazabilidad y filtrado:

```text
review_count
human_review_count
bot_review_count
approved_review_count
changes_requested_review_count
commented_review_count
review_comment_count
pr_comment_count
timeline_event_count
human_comment_count
bot_comment_count
textual_evidence_count
non_pr_textual_evidence_count
all_evidence_text
changes_requested_text
review_comment_text
pr_comment_text
timeline_text
evidence_sources
evidence_states
evidence_users
first_evidence_created_at
last_evidence_created_at
evidence_user
evidence_user_type
evidence_created_at
evidence_id
evidence_count
```

Para depurar la muestra inicial de 300 casos, revisar primero `discard_candidate_reason`, `evidence_quality_score`, `needs_manual_context_check` y `non_pr_textual_evidence_count`.

La salida escrita por defecto conserva solo filas con `human_comment_count > 0`, porque esas tarjetas tienen al menos un comentario humano asociado al PR.

## Taxonomía inicial (manual)

Para una primera pasada rápida (antes o en paralelo a la herramienta web), se mantiene una
plantilla CSV con una columna manual `categoria_retrabajo_pre_merge`.

La convención del repo es guardar este trabajo en:

- `exploration/aidev/taxonomy/initial/`

## Uso

Para ejecutar la preparación usando la muestra por defecto ya generada:

```bash
python3 exploration/aidev/preparation/rejection_cards.py
```

Para probar sin escribir archivos:

```bash
python3 exploration/aidev/preparation/rejection_cards.py --dry-run
```

Para usar otra muestra:

```bash
python3 exploration/aidev/preparation/rejection_cards.py \
  --sample-csv path/to/rejection_sample.csv \
  --output-csv path/to/rejection_cards.csv \
  --summary-json path/to/rejection_cards_summary.json
```

## Verificación

Tests asociados:

```bash
python3 -m unittest exploration.aidev.tests.test_rejection_cards
```
