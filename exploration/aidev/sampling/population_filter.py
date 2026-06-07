#!/usr/bin/env python3
"""Build the merged-after-rework population used before stratified sampling."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from exploration.aidev.aidev_data import get_parquet_urls


POPULATION_MODE = "merged-after-rework"
POPULATION_CASE_TYPE = "merged_after_rework"
UNKNOWN_VALUE = "unknown"

DEFAULT_POPULATION_CSV = Path(
    "exploration/aidev/sampling/outputs/merged_after_rework_population.csv"
)
DEFAULT_SUMMARY_JSON = Path(
    "exploration/aidev/sampling/outputs/merged_after_rework_population_summary.json"
)
DEFAULT_POPULATION_SUMMARY_JSON = DEFAULT_SUMMARY_JSON

CONTROL_FIELDS = [
    "population_case_type",
    "agent",
    "language",
    "change_complexity_bin",
    "repo_popularity_bin",
    "created_period",
    "task_type",
]


def is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() == ""


def normalize_value(value) -> str:
    if is_missing(value):
        return UNKNOWN_VALUE
    return str(value).strip()


def to_int(value, default: int = 0) -> int:
    if is_missing(value):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def to_float(value) -> Optional[float]:
    if is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_parquet(url: str, columns: Optional[Sequence[str]] = None):
    import pandas as pd

    try:
        return pd.read_parquet(url, columns=list(columns) if columns else None)
    except Exception:
        if columns is None:
            raise
        return pd.read_parquet(url)


def require_urls(configs: Sequence[str]) -> Dict[str, str]:
    urls = get_parquet_urls(configs)
    missing = [config for config in configs if config not in urls]
    if missing:
        raise RuntimeError(f"Missing parquet URLs for configs: {', '.join(missing)}")
    return urls


def _merge_count_summary(
    target_df,
    summary_df,
    left_key: str,
    right_key: str,
    count_columns: Sequence[str],
):
    if summary_df.empty:
        for column in count_columns:
            target_df[column] = 0
        return target_df

    merged = target_df.merge(summary_df, left_on=left_key, right_on=right_key, how="left")
    if right_key != left_key and right_key in merged.columns:
        merged = merged.drop(columns=[right_key])
    for column in count_columns:
        merged[column] = merged[column].fillna(0).astype(int)
    return merged


def summarize_pr_reviews(reviews_df):
    import pandas as pd

    columns = [
        "pr_id",
        "review_count",
        "unique_reviewers_count",
        "human_review_count",
        "bot_review_count",
        "approved_review_count",
        "changes_requested_review_count",
        "commented_review_count",
        "first_human_review_at",
        "first_approval_at",
    ]
    if reviews_df.empty:
        return pd.DataFrame(columns=columns)

    reviews = reviews_df.copy()
    reviews["_user_type"] = reviews.get("user_type", "").fillna("").astype(str).str.lower()
    reviews["_state"] = reviews.get("state", "").fillna("").astype(str)
    grouped = reviews.groupby("pr_id")
    summary = grouped.size().reset_index(name="review_count")

    if "user" in reviews.columns:
        summary = summary.merge(
            grouped["user"].nunique(dropna=True).reset_index(name="unique_reviewers_count"),
            on="pr_id",
            how="left",
        )
    else:
        summary["unique_reviewers_count"] = 0

    summary["human_review_count"] = (
        reviews[reviews["_user_type"].eq("user")]
        .groupby("pr_id")
        .size()
        .reindex(summary["pr_id"], fill_value=0)
        .to_numpy()
    )
    summary["bot_review_count"] = (
        reviews[reviews["_user_type"].eq("bot")]
        .groupby("pr_id")
        .size()
        .reindex(summary["pr_id"], fill_value=0)
        .to_numpy()
    )

    for state, column in {
        "APPROVED": "approved_review_count",
        "CHANGES_REQUESTED": "changes_requested_review_count",
        "COMMENTED": "commented_review_count",
    }.items():
        summary[column] = (
            reviews[reviews["_state"].eq(state)]
            .groupby("pr_id")
            .size()
            .reindex(summary["pr_id"], fill_value=0)
            .to_numpy()
        )

    if "submitted_at" in reviews.columns:
        reviews["_submitted_at_dt"] = pd.to_datetime(
            reviews["submitted_at"], utc=True, errors="coerce"
        )
        summary = summary.merge(
            reviews[reviews["_user_type"].eq("user")]
            .groupby("pr_id")["_submitted_at_dt"]
            .min()
            .reset_index(name="first_human_review_at"),
            on="pr_id",
            how="left",
        )
        summary = summary.merge(
            reviews[reviews["_state"].eq("APPROVED")]
            .groupby("pr_id")["_submitted_at_dt"]
            .min()
            .reset_index(name="first_approval_at"),
            on="pr_id",
            how="left",
        )
    else:
        summary["first_human_review_at"] = None
        summary["first_approval_at"] = None

    return summary


def summarize_pr_comments(comments_df):
    import pandas as pd

    if comments_df.empty:
        return pd.DataFrame(
            columns=["pr_id", "pr_comment_count", "human_pr_comment_count", "bot_pr_comment_count"]
        )

    comments = comments_df.copy()
    comments["_user_type"] = comments.get("user_type", "").fillna("").astype(str).str.lower()
    summary = comments.groupby("pr_id").size().reset_index(name="pr_comment_count")
    summary["human_pr_comment_count"] = (
        comments[comments["_user_type"].eq("user")]
        .groupby("pr_id")
        .size()
        .reindex(summary["pr_id"], fill_value=0)
        .to_numpy()
    )
    summary["bot_pr_comment_count"] = (
        comments[comments["_user_type"].eq("bot")]
        .groupby("pr_id")
        .size()
        .reindex(summary["pr_id"], fill_value=0)
        .to_numpy()
    )
    return summary


def summarize_review_comments(review_comments_df):
    import pandas as pd

    if review_comments_df.empty:
        return pd.DataFrame(
            columns=[
                "pull_request_url",
                "review_comment_count",
                "human_review_comment_count",
                "bot_review_comment_count",
            ]
        )

    comments = review_comments_df.copy()
    dedupe_fields = [
        field for field in ("id", "pull_request_url", "path", "body") if field in comments.columns
    ]
    if dedupe_fields:
        comments = comments.drop_duplicates(subset=dedupe_fields)

    comments["_user_type"] = comments.get("user_type", "").fillna("").astype(str).str.lower()
    summary = comments.groupby("pull_request_url").size().reset_index(name="review_comment_count")
    summary["human_review_comment_count"] = (
        comments[comments["_user_type"].eq("user")]
        .groupby("pull_request_url")
        .size()
        .reindex(summary["pull_request_url"], fill_value=0)
        .to_numpy()
    )
    summary["bot_review_comment_count"] = (
        comments[comments["_user_type"].eq("bot")]
        .groupby("pull_request_url")
        .size()
        .reindex(summary["pull_request_url"], fill_value=0)
        .to_numpy()
    )
    return summary


def add_repository_fields(pr_df, repo_df):
    repo_columns = ["id", "language", "stars", "forks", "full_name"]
    available = [column for column in repo_columns if column in repo_df.columns]
    repo = repo_df[available].rename(columns={"id": "repo_id"})
    return pr_df.merge(repo, on="repo_id", how="left")


def add_task_type_fields(pr_df, task_df):
    available = [column for column in ["id", "type", "confidence"] if column in task_df.columns]
    if not {"id", "type"}.issubset(available):
        pr_df["task_type"] = UNKNOWN_VALUE
        pr_df["task_confidence"] = ""
        return pr_df
    task = task_df[available].rename(
        columns={"type": "task_type", "confidence": "task_confidence"}
    )
    return pr_df.merge(task, on="id", how="left")


def build_api_pull_urls(pr_df):
    return pr_df.apply(
        lambda row: (
            f"{row.get('repo_url')}/pulls/{int(row.get('number'))}"
            if not is_missing(row.get("repo_url")) and not is_missing(row.get("number"))
            else ""
        ),
        axis=1,
    )


def load_pull_request_population():
    import pandas as pd

    configs = [
        "pull_request",
        "repository",
        "pr_commits",
        "pr_reviews",
        "pr_comments",
        "pr_review_comments",
        "pr_review_comments_v2",
        "pr_task_type",
    ]
    urls = require_urls(configs)

    pr_df = read_parquet(urls["pull_request"]).copy()
    pr_df = add_repository_fields(pr_df, read_parquet(urls["repository"]))

    commits = read_parquet(urls["pr_commits"], columns=["pr_id", "author"])
    commit_summary = commits.groupby("pr_id").size().reset_index(name="commit_count")
    if "author" in commits.columns:
        commit_summary = commit_summary.merge(
            commits.groupby("pr_id")["author"]
            .nunique(dropna=True)
            .reset_index(name="unique_commit_authors_count"),
            on="pr_id",
            how="left",
        )
    else:
        commit_summary["unique_commit_authors_count"] = 0
    pr_df = _merge_count_summary(
        pr_df,
        commit_summary,
        left_key="id",
        right_key="pr_id",
        count_columns=["commit_count", "unique_commit_authors_count"],
    )

    review_summary = summarize_pr_reviews(
        read_parquet(
            urls["pr_reviews"],
            columns=["id", "pr_id", "state", "user", "user_type", "submitted_at"],
        )
    )
    pr_df = _merge_count_summary(
        pr_df,
        review_summary,
        left_key="id",
        right_key="pr_id",
        count_columns=[
            "review_count",
            "unique_reviewers_count",
            "human_review_count",
            "bot_review_count",
            "approved_review_count",
            "changes_requested_review_count",
            "commented_review_count",
        ],
    )

    comment_summary = summarize_pr_comments(
        read_parquet(urls["pr_comments"], columns=["pr_id", "user_type"])
    )
    pr_df = _merge_count_summary(
        pr_df,
        comment_summary,
        left_key="id",
        right_key="pr_id",
        count_columns=[
            "pr_comment_count",
            "human_pr_comment_count",
            "bot_pr_comment_count",
        ],
    )

    review_comment_frames = [
        read_parquet(
            urls[config],
            columns=["id", "pull_request_url", "user_type", "body", "path"],
        )
        for config in ("pr_review_comments_v2", "pr_review_comments")
    ]
    review_comment_summary = summarize_review_comments(
        pd.concat(review_comment_frames, ignore_index=True)
    )
    pr_df["_api_pull_url"] = build_api_pull_urls(pr_df)
    pr_df = pr_df.merge(
        review_comment_summary,
        left_on="_api_pull_url",
        right_on="pull_request_url",
        how="left",
    ).drop(columns=["_api_pull_url"])
    if "pull_request_url" in pr_df.columns:
        pr_df = pr_df.drop(columns=["pull_request_url"])
    for column in [
        "review_comment_count",
        "human_review_comment_count",
        "bot_review_comment_count",
    ]:
        pr_df[column] = pr_df[column].fillna(0).astype(int)

    pr_df["human_comment_count"] = (
        pr_df["human_pr_comment_count"] + pr_df["human_review_comment_count"]
    )
    pr_df["bot_comment_count"] = pr_df["bot_pr_comment_count"] + pr_df["bot_review_comment_count"]
    pr_df = add_task_type_fields(pr_df, read_parquet(urls["pr_task_type"]))
    return pr_df


def is_closed(row: Dict) -> bool:
    return normalize_value(row.get("state")).lower() == "closed"


def is_merged(row: Dict) -> bool:
    return is_closed(row) and not is_missing(row.get("merged_at"))


def is_closed_unmerged(row: Dict) -> bool:
    return is_closed(row) and is_missing(row.get("merged_at"))


def summarize_population_filters(rows: Sequence[Dict]) -> Dict[str, int]:
    return {
        "all_pull_request": len(rows),
        "closed": sum(1 for row in rows if is_closed(row)),
        "merged": sum(1 for row in rows if is_merged(row)),
        "closed_unmerged": sum(1 for row in rows if is_closed_unmerged(row)),
        "merged_with_additional_commits": sum(
            1 for row in rows if is_merged(row) and to_int(row.get("commit_count")) > 1
        ),
        "merged_with_additional_commits_and_human_comments": sum(
            1
            for row in rows
            if is_merged(row)
            and to_int(row.get("commit_count")) > 1
            and to_int(row.get("human_comment_count")) > 0
        ),
    }


def assign_quantile_bins(
    rows: Iterable[Dict],
    source_field: str,
    target_field: str,
    labels: Sequence[str] = ("low", "medium", "high"),
) -> List[Dict]:
    enriched = [dict(row) for row in rows]
    numeric_pairs = [
        (idx, to_float(row.get(source_field)))
        for idx, row in enumerate(enriched)
        if to_float(row.get(source_field)) is not None
    ]
    if not numeric_pairs:
        for row in enriched:
            row[target_field] = UNKNOWN_VALUE
        return enriched

    numeric_pairs.sort(key=lambda item: (item[1], item[0]))
    total = len(numeric_pairs)
    for rank, (idx, _) in enumerate(numeric_pairs):
        label_index = min(len(labels) - 1, int(rank * len(labels) / total))
        enriched[idx][target_field] = labels[label_index]
    for row in enriched:
        if is_missing(row.get(target_field)):
            row[target_field] = UNKNOWN_VALUE
    return enriched


def add_created_period(rows: Iterable[Dict]) -> List[Dict]:
    enriched = [dict(row) for row in rows]
    dated = [
        (idx, normalize_value(row.get("created_at")))
        for idx, row in enumerate(enriched)
        if not is_missing(row.get("created_at"))
    ]
    dated.sort(key=lambda item: (item[1], item[0]))
    for rank, (idx, _) in enumerate(dated):
        enriched[idx]["_created_at_rank"] = rank
    return assign_quantile_bins(
        enriched,
        source_field="_created_at_rank",
        target_field="created_period",
        labels=("old", "middle", "recent"),
    )


def prepare_population_rows(rows: Iterable[Dict]) -> List[Dict]:
    population = []
    for row in rows:
        if not (
            is_merged(row)
            and to_int(row.get("commit_count")) > 1
            and to_int(row.get("human_comment_count")) > 0
        ):
            continue
        enriched = dict(row)
        enriched["pr_id"] = enriched.get("id")
        enriched["merged"] = "true"
        enriched["population_case_type"] = POPULATION_CASE_TYPE
        population.append(enriched)

    population = assign_quantile_bins(
        population,
        source_field="commit_count",
        target_field="change_complexity_bin",
    )
    population = assign_quantile_bins(
        population,
        source_field="stars",
        target_field="repo_popularity_bin",
    )
    population = add_created_period(population)

    for row in population:
        if is_missing(row.get("task_type")):
            row["task_type"] = UNKNOWN_VALUE
        if is_missing(row.get("language")):
            row["language"] = UNKNOWN_VALUE
        row.pop("_created_at_rank", None)
    return population


def validate_population_rows(population_rows: Sequence[Dict]) -> None:
    if not population_rows:
        raise ValueError("Population is empty after applying merged-after-rework filters")

    required_fields = [
        "pr_id",
        "agent",
        "state",
        "merged_at",
        "commit_count",
        "human_comment_count",
        *CONTROL_FIELDS,
    ]
    missing_fields = sorted(
        {
            field
            for field in required_fields
            if any(field not in row for row in population_rows)
        }
    )
    if missing_fields:
        raise ValueError(f"Population rows are missing fields: {', '.join(missing_fields)}")

    duplicate_pr_ids = [
        pr_id
        for pr_id, count in Counter(normalize_value(row.get("pr_id")) for row in population_rows).items()
        if pr_id != UNKNOWN_VALUE and count > 1
    ]
    if duplicate_pr_ids:
        raise ValueError(f"Population has duplicated pr_id values: {duplicate_pr_ids[:5]}")

    invalid_rows = [
        row.get("pr_id")
        for row in population_rows
        if not (
            is_merged(row)
            and to_int(row.get("commit_count")) > 1
            and to_int(row.get("human_comment_count")) > 0
            and normalize_value(row.get("population_case_type")) == POPULATION_CASE_TYPE
        )
    ]
    if invalid_rows:
        raise ValueError(
            "Population contains rows outside merged-after-rework definition; "
            f"examples: {invalid_rows[:5]}"
        )


def value_counts(rows: Iterable[Dict], field: str) -> Dict[str, int]:
    counter = Counter(normalize_value(row.get(field)) for row in rows)
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def build_population_summary(
    source_rows: Sequence[Dict],
    population_rows: Sequence[Dict],
    filter_counts: Dict[str, int],
    output_csv: Path,
) -> Dict:
    return {
        "population_mode": POPULATION_MODE,
        "population_case_type": POPULATION_CASE_TYPE,
        "population_csv": str(output_csv),
        "source_pull_request_count": len(source_rows),
        "population_size": len(population_rows),
        "control_fields": CONTROL_FIELDS,
        "population_distributions": {
            field: value_counts(population_rows, field) for field in CONTROL_FIELDS
        },
        "population_filter_counts": filter_counts,
    }


def write_csv_rows(path: Path, rows: Sequence[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({field for row in rows for field in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the merged-after-rework AIDev population CSV."
    )
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_POPULATION_CSV)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_rows = load_pull_request_population().to_dict("records")
    filter_counts = summarize_population_filters(source_rows)
    population_rows = prepare_population_rows(source_rows)
    validate_population_rows(population_rows)
    summary = build_population_summary(
        source_rows,
        population_rows,
        filter_counts,
        args.output_csv,
    )

    if args.dry_run:
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
        return

    write_csv_rows(args.output_csv, population_rows)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "population_csv": str(args.output_csv),
                "summary_json": str(args.summary_json),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
