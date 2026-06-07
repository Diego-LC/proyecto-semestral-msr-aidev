#!/usr/bin/env python3
"""Create the reproducible stratified sample from the prepared population CSV."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from exploration.aidev.sampling.population_filter import (
    CONTROL_FIELDS,
    DEFAULT_POPULATION_CSV,
    DEFAULT_SUMMARY_JSON as DEFAULT_POPULATION_SUMMARY_JSON,
    POPULATION_MODE,
    is_missing,
    normalize_value,
    value_counts,
    write_csv_rows,
)


DEFAULT_SEED = 20260510
DEFAULT_SAMPLE_SIZE = 300
DEFAULT_MIN_PER_STRATUM = 3
STRATA_FIELDS = ["agent"]

DEFAULT_OUTPUT_CSV = Path(
    "exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510.csv"
)
DEFAULT_SUMMARY_JSON = Path(
    "exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510_summary.json"
)


@dataclass
class SamplingResult:
    rows: List[Dict]
    quotas: Dict[str, int]
    stratum_sizes: Dict[str, int]
    seed: int


def load_csv_rows(path: Path) -> List[Dict]:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(
            f"Population CSV not found or empty: {path}. Run population_filter.py first."
        )
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def read_json_optional(path: Path) -> Dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def validate_population_input(rows: Sequence[Dict], population_summary: Dict) -> None:
    if not rows:
        raise ValueError("Population CSV is empty; run population_filter.py first")

    missing_strata_fields = [
        field for field in STRATA_FIELDS if any(field not in row for row in rows)
    ]
    if missing_strata_fields:
        raise ValueError(
            f"Population CSV is missing strata fields: {', '.join(missing_strata_fields)}"
        )

    if population_summary:
        expected_size = population_summary.get("population_size")
        if expected_size is not None and int(expected_size) != len(rows):
            raise ValueError(
                "Population summary size does not match CSV rows: "
                f"summary={expected_size}, csv={len(rows)}"
            )

    pr_ids = [normalize_value(row.get("pr_id")) for row in rows if not is_missing(row.get("pr_id"))]
    if len(pr_ids) != len(set(pr_ids)):
        raise ValueError("Population CSV contains duplicated pr_id values")


def build_stratum_key(row: Dict) -> str:
    return "|".join(normalize_value(row.get(field)) for field in STRATA_FIELDS)


def group_by_stratum(rows: Iterable[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        groups[build_stratum_key(row)].append(row)
    return dict(groups)


def allocate_stratified_quotas(
    stratum_sizes: Dict[str, int],
    target_size: int,
    min_per_stratum: int = DEFAULT_MIN_PER_STRATUM,
) -> Dict[str, int]:
    clean_sizes = {key: size for key, size in stratum_sizes.items() if size > 0}
    if target_size <= 0:
        raise ValueError("target_size must be greater than zero")
    if not clean_sizes:
        return {}

    population_size = sum(clean_sizes.values())
    target = min(target_size, population_size)
    minimums = {key: min(min_per_stratum, size) for key, size in clean_sizes.items()}
    if sum(minimums.values()) > target:
        raise ValueError("min_per_stratum is too high for the requested sample size")

    raw_quotas = {key: (target * size / population_size) for key, size in clean_sizes.items()}
    quotas = {
        key: min(size, max(minimums[key], int(math.floor(raw_quotas[key] + 0.5))))
        for key, size in clean_sizes.items()
    }

    while sum(quotas.values()) > target:
        key = max(
            [item for item in quotas if quotas[item] > minimums[item]],
            key=lambda item: (quotas[item] - raw_quotas[item], quotas[item], item),
        )
        quotas[key] -= 1

    while sum(quotas.values()) < target:
        expandable = [item for item in quotas if quotas[item] < clean_sizes[item]]
        if not expandable:
            break
        key = max(
            expandable,
            key=lambda item: (
                raw_quotas[item] - math.floor(raw_quotas[item]),
                clean_sizes[item] - quotas[item],
                item,
            ),
        )
        quotas[key] += 1

    return dict(sorted(quotas.items()))


def stable_row_id(row: Dict) -> str:
    for field in ("card_id", "pr_id", "id", "html_url"):
        if field in row and not is_missing(row.get(field)):
            return normalize_value(row.get(field))
    return json.dumps(row, sort_keys=True, default=str)


def stratified_sample(
    rows: Iterable[Dict],
    target_size: int = DEFAULT_SAMPLE_SIZE,
    min_per_stratum: int = DEFAULT_MIN_PER_STRATUM,
    seed: int = DEFAULT_SEED,
) -> SamplingResult:
    groups = group_by_stratum(rows)
    stratum_sizes = {key: len(value) for key, value in groups.items()}
    quotas = allocate_stratified_quotas(stratum_sizes, target_size, min_per_stratum)
    rng = random.Random(seed)
    sampled_rows: List[Dict] = []

    for stratum_key, quota in sorted(quotas.items()):
        selected = rng.sample(sorted(groups[stratum_key], key=stable_row_id), quota)
        for row in selected:
            enriched = dict(row)
            enriched["_stratum_key"] = stratum_key
            enriched["_sample_seed"] = seed
            sampled_rows.append(enriched)

    sampled_ids = [
        normalize_value(row.get("pr_id"))
        for row in sampled_rows
        if not is_missing(row.get("pr_id"))
    ]
    if len(sampled_ids) != len(set(sampled_ids)):
        raise ValueError("Sample contains duplicated pr_id values")

    sampled_rows.sort(key=lambda row: (row["_stratum_key"], stable_row_id(row)))
    return SamplingResult(
        rows=sampled_rows,
        quotas=quotas,
        stratum_sizes=dict(sorted(stratum_sizes.items())),
        seed=seed,
    )


def summarize_result(
    population_rows: Sequence[Dict],
    result: SamplingResult,
    population_csv: Path,
    population_summary_json: Path,
    population_summary: Dict,
) -> Dict:
    return {
        "seed": result.seed,
        "population_mode": POPULATION_MODE,
        "population_csv": str(population_csv),
        "population_summary_json": str(population_summary_json),
        "population_size": len(population_rows),
        "sample_size": len(result.rows),
        "requested_strata_fields": STRATA_FIELDS,
        "used_strata_fields": STRATA_FIELDS,
        "stratum_count": len(result.stratum_sizes),
        "stratum_sizes": result.stratum_sizes,
        "quotas": result.quotas,
        "population_distributions": population_summary.get(
            "population_distributions",
            {field: value_counts(population_rows, field) for field in CONTROL_FIELDS},
        ),
        "sample_distributions": {
            field: value_counts(result.rows, field) for field in CONTROL_FIELDS
        },
        "population_filter_counts": population_summary.get("population_filter_counts", {}),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the merged-after-rework stratified AIDev sample."
    )
    parser.add_argument("--population-csv", type=Path, default=DEFAULT_POPULATION_CSV)
    parser.add_argument(
        "--population-summary-json",
        type=Path,
        default=DEFAULT_POPULATION_SUMMARY_JSON,
    )
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--min-per-stratum", type=int, default=DEFAULT_MIN_PER_STRATUM)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    population_rows = load_csv_rows(args.population_csv)
    population_summary = read_json_optional(args.population_summary_json)
    validate_population_input(population_rows, population_summary)
    result = stratified_sample(
        population_rows,
        target_size=args.sample_size,
        min_per_stratum=args.min_per_stratum,
        seed=args.seed,
    )
    summary = summarize_result(
        population_rows,
        result,
        args.population_csv,
        args.population_summary_json,
        population_summary,
    )

    if args.dry_run:
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
        return

    write_csv_rows(args.output_csv, result.rows)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "population_csv": str(args.population_csv),
                "output_csv": str(args.output_csv),
                "summary_json": str(args.summary_json),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
