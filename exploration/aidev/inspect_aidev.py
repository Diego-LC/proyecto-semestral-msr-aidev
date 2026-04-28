#!/usr/bin/env python3

import argparse
import json
from collections import Counter
from typing import Dict, Iterable, List
from urllib.parse import urlencode
from urllib.request import urlopen


DATASET = "hao-li/AIDev"
DATASET_SERVER = "https://datasets-server.huggingface.co"
MAX_PAGE_SIZE = 100
PREFERRED_TRACKED_FIELDS = [
    "state",
    "agent",
    "user",
    "created_at",
    "closed_at",
    "merged_at",
    "repo_id",
    "repo_url",
    "user_id",
    "review_state",
    "event",
]
PREFERRED_CATEGORICAL_FIELDS = [
    "state",
    "agent",
    "user",
    "repo_id",
    "repo_url",
    "user_id",
    "review_state",
    "event",
]


def api_get(path: str, **params) -> Dict:
    query = urlencode(params)
    url = f"{DATASET_SERVER}/{path}?{query}"
    with urlopen(url) as response:
        return json.load(response)


def pick_default_fields(columns: Iterable[str]) -> Dict[str, List[str]]:
    columns = list(columns)
    tracked_fields: List[str] = []
    date_fields: List[str] = []
    categorical_fields: List[str] = []

    for field in PREFERRED_TRACKED_FIELDS:
        if field in columns:
            tracked_fields.append(field)

    for field in columns:
        if field.endswith("_at") and field not in tracked_fields:
            tracked_fields.append(field)

    for field in columns:
        if field.endswith("_at") and field not in date_fields:
            date_fields.append(field)

    for field in PREFERRED_CATEGORICAL_FIELDS:
        if field in columns:
            categorical_fields.append(field)

    if not tracked_fields:
        tracked_fields = columns[: min(6, len(columns))]

    return {
        "tracked_fields": tracked_fields,
        "categorical_fields": categorical_fields,
        "date_fields": date_fields,
    }


def summarize_rows(
    rows: Iterable[Dict],
    tracked_fields: List[str],
    categorical_fields: List[str],
    date_fields: List[str],
    top_k: int = 10,
) -> Dict:
    null_counts = {field: 0 for field in tracked_fields}
    counters = {field: Counter() for field in categorical_fields}
    date_ranges = {field: {"min": None, "max": None} for field in date_fields}
    rows_seen = 0

    for row in rows:
        rows_seen += 1
        for field in tracked_fields:
            value = row.get(field)
            if value is None or value == "":
                null_counts[field] += 1

        for field in categorical_fields:
            value = row.get(field)
            if value is not None and value != "":
                counters[field][str(value)] += 1

        for field in date_fields:
            value = row.get(field)
            if value is None or value == "":
                continue
            current = date_ranges[field]
            if current["min"] is None or value < current["min"]:
                current["min"] = value
            if current["max"] is None or value > current["max"]:
                current["max"] = value

    value_counts = {}
    for field, counter in counters.items():
        sorted_items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        value_counts[field] = dict(sorted_items[:top_k])

    return {
        "rows_seen": rows_seen,
        "null_counts": null_counts,
        "value_counts": value_counts,
        "date_ranges": date_ranges,
    }


def feature_names(features: List[Dict]) -> List[str]:
    return [feature["name"] for feature in features]


def compact_row(row: Dict, max_text_length: int = 160) -> Dict:
    compact = {}
    for key, value in row.items():
        if isinstance(value, str) and len(value) > max_text_length:
            compact[key] = value[: max_text_length - 3] + "..."
        else:
            compact[key] = value
    return compact


def overview(dataset: str) -> Dict:
    validity = api_get("is-valid", dataset=dataset)
    splits = api_get("splits", dataset=dataset)
    size = api_get("size", dataset=dataset)

    configs = sorted(
        size["size"]["configs"],
        key=lambda item: item["num_rows"],
        reverse=True,
    )

    return {
        "dataset": dataset,
        "capabilities": validity,
        "config_count": len(splits["splits"]),
        "total_rows": size["size"]["dataset"]["num_rows"],
        "total_parquet_bytes": size["size"]["dataset"]["num_bytes_parquet_files"],
        "configs": configs,
    }


def preview(dataset: str, config: str, split: str, limit: int) -> Dict:
    data = api_get("first-rows", dataset=dataset, config=config, split=split)
    rows = [compact_row(item["row"]) for item in data["rows"][:limit]]
    return {
        "dataset": dataset,
        "config": config,
        "split": split,
        "features": feature_names(data["features"]),
        "rows": rows,
    }


def profile(dataset: str, config: str, split: str, limit: int, top_k: int) -> Dict:
    rows_to_fetch = max(0, limit)
    if rows_to_fetch == 0:
        data = api_get("rows", dataset=dataset, config=config, split=split, offset=0, length=1)
        fields = pick_default_fields(feature_names(data["features"]))
        summary = summarize_rows([], **fields, top_k=top_k)
        return {
            "dataset": dataset,
            "config": config,
            "split": split,
            "available_rows": data["num_rows_total"],
            "requested_rows": 0,
            "tracked_fields": fields["tracked_fields"],
            "categorical_fields": fields["categorical_fields"],
            "date_fields": fields["date_fields"],
            "summary": summary,
        }

    first_batch_size = min(MAX_PAGE_SIZE, rows_to_fetch)
    page = api_get(
        "rows",
        dataset=dataset,
        config=config,
        split=split,
        offset=0,
        length=first_batch_size,
    )
    features = feature_names(page["features"])
    fields = pick_default_fields(features)
    collected_rows = [item["row"] for item in page["rows"]]
    total_rows = min(page["num_rows_total"], rows_to_fetch)
    offset = len(collected_rows)

    while offset < total_rows:
        batch_size = min(MAX_PAGE_SIZE, total_rows - offset)
        page = api_get(
            "rows",
            dataset=dataset,
            config=config,
            split=split,
            offset=offset,
            length=batch_size,
        )
        collected_rows.extend(item["row"] for item in page["rows"])
        offset += len(page["rows"])

    summary = summarize_rows(
        collected_rows,
        tracked_fields=fields["tracked_fields"],
        categorical_fields=fields["categorical_fields"],
        date_fields=fields["date_fields"],
        top_k=top_k,
    )

    return {
        "dataset": dataset,
        "config": config,
        "split": split,
        "available_rows": page["num_rows_total"],
        "requested_rows": total_rows,
        "tracked_fields": fields["tracked_fields"],
        "categorical_fields": fields["categorical_fields"],
        "date_fields": fields["date_fields"],
        "summary": summary,
    }


def search(dataset: str, config: str, split: str, query: str, limit: int) -> Dict:
    data = api_get(
        "search",
        dataset=dataset,
        config=config,
        split=split,
        query=query,
        offset=0,
        length=min(limit, MAX_PAGE_SIZE),
    )
    return {
        "dataset": dataset,
        "config": config,
        "split": split,
        "query": query,
        "matches_total": data["num_rows_total"],
        "rows": [compact_row(item["row"]) for item in data["rows"]],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="First-pass explorer for the AIDev dataset.")
    parser.add_argument("--dataset", default=DATASET, help="Dataset name in Hugging Face.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("overview", help="List dataset-wide metadata and config sizes.")

    preview_parser = subparsers.add_parser("preview", help="Show compact first rows for a config.")
    preview_parser.add_argument("--config", required=True, help="Dataset config/subset name.")
    preview_parser.add_argument("--split", default="train", help="Split name.")
    preview_parser.add_argument("--limit", type=int, default=5, help="Number of preview rows.")

    profile_parser = subparsers.add_parser("profile", help="Compute basic metrics from sampled rows.")
    profile_parser.add_argument("--config", required=True, help="Dataset config/subset name.")
    profile_parser.add_argument("--split", default="train", help="Split name.")
    profile_parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="How many rows to scan using the dataset viewer API.",
    )
    profile_parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Top values to keep for categorical distributions.",
    )

    search_parser = subparsers.add_parser("search", help="Search text within a config.")
    search_parser.add_argument("--config", required=True, help="Dataset config/subset name.")
    search_parser.add_argument("--split", default="train", help="Split name.")
    search_parser.add_argument("--query", required=True, help="Search query.")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum rows to show.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "overview":
        result = overview(args.dataset)
    elif args.command == "preview":
        result = preview(args.dataset, args.config, args.split, args.limit)
    elif args.command == "profile":
        result = profile(args.dataset, args.config, args.split, args.limit, args.top_k)
    elif args.command == "search":
        result = search(args.dataset, args.config, args.split, args.query, args.limit)
    else:
        raise ValueError(f"Unsupported command: {args.command}")

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
