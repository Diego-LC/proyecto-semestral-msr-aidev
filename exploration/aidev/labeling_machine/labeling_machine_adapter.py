#!/usr/bin/env python3

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from exploration.aidev.preparation.rejection_cards import CARD_FIELDS


DEFAULT_INPUT_CSV = Path(
    "exploration/aidev/preparation/outputs/rejection_cards_seed_20260510.csv"
)
DEFAULT_OUTPUT_CSV = Path(
    "exploration/aidev/labeling_machine/outputs/rejection_cards_for_labeling_machine.csv"
)
DEFAULT_SCHEMA_JSON = Path(
    "exploration/aidev/labeling_machine/outputs/labeling_machine_schema.json"
)
DEFAULT_SUMMARY_JSON = Path(
    "exploration/aidev/labeling_machine/outputs/rejection_cards_for_labeling_machine_summary.json"
)

ARTIFACT_FIELDS = ["artifact_id", *CARD_FIELDS]

LABELING_FIELDS = [
    "category_parent",
    "subcategory",
    "confidence",
    "rationale",
    "needs_discussion",
    "username",
    "duration_sec",
]

EXPORT_FIELDS = ARTIFACT_FIELDS + LABELING_FIELDS
REQUIRED_CARD_FIELDS = [
    "card_id",
    "pr_id",
    "html_url",
    "evidence_text",
    "context_summary",
]


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def normalize_scalar(value) -> str:
    if is_blank(value):
        return ""
    return str(value).strip()


def normalize_boolish(value) -> str:
    value_text = normalize_scalar(value).lower()
    if value_text in {"1", "true", "yes", "y", "si", "sí"}:
        return "true"
    if value_text in {"0", "false", "no", "n"}:
        return "false"
    return ""


def normalize_card_for_labeling(card: Dict, artifact_id: int) -> Dict:
    row = {"artifact_id": str(artifact_id)}
    for field in ARTIFACT_FIELDS:
        if field == "artifact_id":
            continue
        if field == "needs_manual_context_check":
            row[field] = normalize_boolish(card.get(field))
        else:
            row[field] = normalize_scalar(card.get(field))

    for field in LABELING_FIELDS:
        row[field] = ""

    return row


def validate_cards_for_labeling(cards: Sequence[Dict]) -> None:
    errors = []
    seen_card_ids = set()

    for index, card in enumerate(cards, start=1):
        card_id = normalize_scalar(card.get("card_id"))
        if card_id in seen_card_ids:
            errors.append(f"row {index}: duplicated card_id={card_id}")
        if card_id:
            seen_card_ids.add(card_id)

        missing = [
            field for field in REQUIRED_CARD_FIELDS if is_blank(card.get(field))
        ]
        if missing:
            errors.append(f"row {index}: missing {', '.join(missing)}")

    if errors:
        preview = "; ".join(errors[:5])
        suffix = "" if len(errors) <= 5 else f"; and {len(errors) - 5} more"
        raise ValueError(f"Invalid rejection cards for Labeling Machine: {preview}{suffix}")


def build_labeling_schema(row_count: int) -> Dict:
    return {
        "tool": "Labeling Machine",
        "row_count": row_count,
        "artifact_fields": ARTIFACT_FIELDS,
        "labeling_fields": LABELING_FIELDS,
        "artifact_id_policy": (
            "Sequential numeric id used by Labeling Machine routes. "
            "The original PR/card identity is preserved in card_id and pr_id."
        ),
        "label_meaning": {
            "category_parent": "Main rejection reason category created during card sorting.",
            "subcategory": "More specific reason within the main category.",
            "confidence": "Labeler confidence: high, medium, or low.",
            "rationale": "Short explanation of why the case received that label.",
            "needs_discussion": "Whether the case should be discussed by the team.",
        },
        "validation_notes": (
            "After independent labeling, compute agreement between evaluators "
            "with Cohen's kappa for two labelers or Krippendorff's alpha when "
            "there are more labelers or missing labels."
        ),
    }


def load_csv_rows(path: Path) -> List[Dict]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv_rows(path: Path, rows: Sequence[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in EXPORT_FIELDS})


def write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def summarize_rows(rows: Sequence[Dict]) -> Dict:
    return {
        "row_count": len(rows),
        "manual_context_check_count": sum(
            1 for row in rows if row.get("needs_manual_context_check") == "true"
        ),
        "agent_counts": dict(Counter(row.get("agent", "") for row in rows)),
        "language_counts": dict(Counter(row.get("language", "") for row in rows)),
        "complexity_counts": dict(Counter(row.get("complexity_bin", "") for row in rows)),
        "evidence_source_counts": dict(
            Counter(row.get("evidence_source", "") for row in rows)
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare AIDev rejection cards for Labeling Machine."
    )
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT_CSV)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--schema-json", type=Path, default=DEFAULT_SCHEMA_JSON)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cards = load_csv_rows(args.input_csv)
    validate_cards_for_labeling(cards)
    rows = [
        normalize_card_for_labeling(card, artifact_id=index)
        for index, card in enumerate(cards, start=1)
    ]
    schema = build_labeling_schema(row_count=len(rows))
    summary = {
        "input_csv": str(args.input_csv),
        "output_csv": str(args.output_csv),
        "schema_json": str(args.schema_json),
        "summary_json": str(args.summary_json),
        **summarize_rows(rows),
    }

    if args.dry_run:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    write_csv_rows(args.output_csv, rows)
    write_json(args.schema_json, schema)
    write_json(args.summary_json, summary)
    print(
        json.dumps(
            {
                "output_csv": str(args.output_csv),
                "schema_json": str(args.schema_json),
                "summary_json": str(args.summary_json),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
