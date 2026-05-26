#!/usr/bin/env python3

import argparse
import csv
import json
import math
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from exploration.aidev.pr_activity import get_parquet_urls


DEFAULT_SEED = 20260510
DEFAULT_SAMPLE_SIZE = 300
DEFAULT_MIN_PER_STRATUM = 3
DEFAULT_STRATA_FIELDS = ["agent"]
DEFAULT_FALLBACK_STRATA_FIELDS = ["agent"]
DEFAULT_MAX_LANGUAGE_VALUES = 8
POPULATION_REJECTED = "rejected"
POPULATION_REJECTED_OR_REWORKED_MERGED = "rejected-or-reworked-merged"
POPULATION_MERGED_AFTER_REWORK = "merged-after-rework"
POPULATION_NOT_IMMEDIATELY_ACCEPTED = "not-immediately-accepted"
DEFAULT_POPULATION_MODE = POPULATION_MERGED_AFTER_REWORK
DEFAULT_OUTPUT_CSV = Path(
    "exploration/aidev/sampling/outputs/merged_after_rework_sample.csv"
)
DEFAULT_SUMMARY_JSON = Path(
    "exploration/aidev/sampling/outputs/merged_after_rework_sample_summary.json"
)
UNKNOWN_VALUE = "unknown"
OTHER_VALUE = "other"


@dataclass
class SamplingResult:
    rows: List[Dict]
    quotas: Dict[str, int]
    stratum_sizes: Dict[str, int]
    strata_fields: List[str]
    seed: int


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


def filter_rejected_prs(rows: Iterable[Dict]) -> List[Dict]:
    return [
        dict(row)
        for row in rows
        if is_rejected_pr(row)
    ]


def is_rejected_pr(row: Dict) -> bool:
    return (
        normalize_value(row.get("state")).lower() == "closed"
        and is_missing(row.get("merged_at"))
    )


def boolish(value) -> bool:
    return normalize_value(value).lower() in {"1", "true", "yes", "y", "si", "sí"}


def to_int(value, default: int = 0) -> int:
    if is_missing(value):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def is_reworked_merged_pr(row: Dict) -> bool:
    if normalize_value(row.get("state")).lower() != "closed":
        return False
    if is_missing(row.get("merged_at")):
        return False

    post_review_code_change = (
        boolish(row.get("has_post_review_code_change"))
        or to_int(row.get("post_review_code_change_count")) > 0
    )
    multiple_commits = to_int(row.get("commit_count")) > 1
    code_change_signal = post_review_code_change or multiple_commits

    review_or_feedback_signal = any(
        to_int(row.get(field)) > 0
        for field in (
            "changes_requested_review_count",
            "human_review_count",
            "review_count",
            "review_comment_count",
            "pr_comment_count",
        )
    )

    return code_change_signal and review_or_feedback_signal


def population_mode_includes_rejected(population_mode: str) -> bool:
    return population_mode in {
        POPULATION_REJECTED,
        POPULATION_REJECTED_OR_REWORKED_MERGED,
    }


def population_mode_includes_reworked_merged(population_mode: str) -> bool:
    return population_mode in {
        POPULATION_REJECTED_OR_REWORKED_MERGED,
        POPULATION_MERGED_AFTER_REWORK,
        POPULATION_NOT_IMMEDIATELY_ACCEPTED,
    }


def classify_population_case(row: Dict, population_mode: str) -> str:
    if population_mode_includes_rejected(population_mode) and is_rejected_pr(row):
        return "rejected"
    if (
        population_mode_includes_reworked_merged(population_mode)
        and is_reworked_merged_pr(row)
    ):
        return "merged_after_rework"
    return ""


def filter_population_prs(
    rows: Iterable[Dict],
    population_mode: str = DEFAULT_POPULATION_MODE,
) -> List[Dict]:
    population = []
    for row in rows:
        case_type = classify_population_case(row, population_mode)
        if not case_type:
            continue
        enriched = dict(row)
        enriched["population_case_type"] = case_type
        enriched["merged"] = "false" if is_missing(row.get("merged_at")) else "true"
        population.append(enriched)
    return population


def build_stratum_key(row: Dict, fields: Sequence[str]) -> str:
    return "|".join(normalize_value(row.get(field)) for field in fields)


def group_by_stratum(rows: Iterable[Dict], strata_fields: Sequence[str]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        groups[build_stratum_key(row, strata_fields)].append(row)
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
        raise ValueError(
            "The requested minimum per stratum is impossible for this sample size. "
            "Use fewer strata, lower min_per_stratum, or increase target_size."
        )

    raw_quotas = {
        key: (target * size / population_size) for key, size in clean_sizes.items()
    }
    quotas = {
        key: min(size, max(minimums[key], int(math.floor(raw_quotas[key] + 0.5))))
        for key, size in clean_sizes.items()
    }

    while sum(quotas.values()) > target:
        reducible = [
            key for key, quota in quotas.items() if quota > minimums[key]
        ]
        if not reducible:
            break
        key = max(
            reducible,
            key=lambda item: (quotas[item] - raw_quotas[item], quotas[item], item),
        )
        quotas[key] -= 1

    while sum(quotas.values()) < target:
        expandable = [
            key for key, quota in quotas.items() if quota < clean_sizes[key]
        ]
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
    strata_fields: Sequence[str],
    target_size: int = DEFAULT_SAMPLE_SIZE,
    min_per_stratum: int = DEFAULT_MIN_PER_STRATUM,
    seed: int = DEFAULT_SEED,
) -> SamplingResult:
    source_rows = [dict(row) for row in rows]
    groups = group_by_stratum(source_rows, strata_fields)
    stratum_sizes = {key: len(value) for key, value in groups.items()}
    quotas = allocate_stratified_quotas(
        stratum_sizes,
        target_size=target_size,
        min_per_stratum=min_per_stratum,
    )
    rng = random.Random(seed)
    sampled_rows: List[Dict] = []

    for stratum_key, quota in sorted(quotas.items()):
        group_rows = sorted(groups[stratum_key], key=stable_row_id)
        selected = rng.sample(group_rows, quota)
        for row in selected:
            enriched = dict(row)
            enriched["_stratum_key"] = stratum_key
            enriched["_sample_seed"] = seed
            sampled_rows.append(enriched)

    sampled_rows.sort(key=lambda row: (row["_stratum_key"], stable_row_id(row)))
    return SamplingResult(
        rows=sampled_rows,
        quotas=quotas,
        stratum_sizes=dict(sorted(stratum_sizes.items())),
        strata_fields=list(strata_fields),
        seed=seed,
    )


def choose_supported_strata_fields(
    rows: Iterable[Dict],
    candidates: Sequence[Sequence[str]],
    target_size: int,
    min_per_stratum: int,
) -> List[str]:
    source_rows = [dict(row) for row in rows]
    target = min(target_size, len(source_rows))
    for fields in candidates:
        groups = group_by_stratum(source_rows, fields)
        minimum_required = len(groups) * min_per_stratum
        if minimum_required <= target:
            return list(fields)
    raise ValueError("No candidate strata configuration fits the requested sample size")


def has_field_in_candidates(candidates: Sequence[Sequence[str]], field: str) -> bool:
    return any(field in candidate for candidate in candidates)


def unique_candidates(candidates: Sequence[Sequence[str]]) -> List[List[str]]:
    seen = set()
    unique = []
    for candidate in candidates:
        key = tuple(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(list(candidate))
    return unique


def to_float(value) -> Optional[float]:
    if is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def assign_created_period_bins(rows: Iterable[Dict]) -> List[Dict]:
    return assign_quantile_bins(
        rows,
        source_field="_created_at_rank",
        target_field="created_period",
        labels=("old", "middle", "recent"),
    )


def add_created_at_rank(rows: Iterable[Dict]) -> List[Dict]:
    enriched = [dict(row) for row in rows]
    dated = [
        (idx, normalize_value(row.get("created_at")))
        for idx, row in enumerate(enriched)
        if not is_missing(row.get("created_at"))
    ]
    dated.sort(key=lambda item: (item[1], item[0]))
    for rank, (idx, _) in enumerate(dated):
        enriched[idx]["_created_at_rank"] = rank
    return enriched


def prepare_rows_for_sampling(rows: Iterable[Dict]) -> List[Dict]:
    prepared = [dict(row) for row in rows]

    if any("commit_count" in row for row in prepared) and not all(
        not is_missing(row.get("change_complexity_bin")) for row in prepared
    ):
        prepared = assign_quantile_bins(
            prepared,
            source_field="commit_count",
            target_field="change_complexity_bin",
        )

    if any("stars" in row for row in prepared) and not all(
        not is_missing(row.get("repo_popularity_bin")) for row in prepared
    ):
        prepared = assign_quantile_bins(
            prepared,
            source_field="stars",
            target_field="repo_popularity_bin",
        )

    if any("created_at" in row for row in prepared) and not all(
        not is_missing(row.get("created_period")) for row in prepared
    ):
        prepared = add_created_at_rank(prepared)
        prepared = assign_created_period_bins(prepared)

    for row in prepared:
        row.setdefault("change_complexity_bin", UNKNOWN_VALUE)
        row.setdefault("repo_popularity_bin", UNKNOWN_VALUE)
        row.setdefault("created_period", UNKNOWN_VALUE)
        row.setdefault("task_type", UNKNOWN_VALUE)

    return prepared


def collapse_rare_values(
    rows: Iterable[Dict],
    field: str,
    max_values: int,
    other_value: str = OTHER_VALUE,
) -> List[Dict]:
    if max_values <= 0:
        return [dict(row) for row in rows]

    enriched = [dict(row) for row in rows]
    counts = Counter(normalize_value(row.get(field)) for row in enriched)
    counts.pop(UNKNOWN_VALUE, None)
    kept_values = {
        value
        for value, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[
            :max_values
        ]
    }

    for row in enriched:
        value = normalize_value(row.get(field))
        if value == UNKNOWN_VALUE:
            row[field] = UNKNOWN_VALUE
        elif value not in kept_values:
            row[field] = other_value
        else:
            row[field] = value

    return enriched


def load_csv_rows(path: Path) -> List[Dict]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv_rows(path: Path, rows: Sequence[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({field for row in rows for field in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _merge_count_summary(df, target_df, left_key: str, right_key: str, fill_columns: Sequence[str]):
    if df is None or df.empty:
        for column in fill_columns:
            target_df[column] = 0
        return target_df
    merged = target_df.merge(df, left_on=left_key, right_on=right_key, how="left")
    if right_key != left_key and right_key in merged.columns:
        merged = merged.drop(columns=[right_key])
    for column in fill_columns:
        merged[column] = merged[column].fillna(0).astype(int)
    return merged


def summarize_pr_reviews_pd(reviews_df):
    import pandas as pd

    if reviews_df.empty:
        return pd.DataFrame(columns=["pr_id"])

    reviews = reviews_df.copy()
    if "user_type" in reviews.columns:
        reviews["_user_type"] = reviews["user_type"].fillna("").astype(str).str.lower()
    else:
        reviews["_user_type"] = ""
    if "state" in reviews.columns:
        reviews["_state"] = reviews["state"].fillna("").astype(str)
    else:
        reviews["_state"] = ""
    grouped = reviews.groupby("pr_id")
    summary = grouped.size().reset_index(name="review_count")

    if "user" in reviews.columns:
        unique_reviewers = (
            grouped["user"].nunique(dropna=True).reset_index(name="unique_reviewers_count")
        )
        summary = summary.merge(unique_reviewers, on="pr_id", how="left")
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

    state_map = {
        "APPROVED": "approved_review_count",
        "CHANGES_REQUESTED": "changes_requested_review_count",
        "COMMENTED": "commented_review_count",
    }
    for state, column in state_map.items():
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
        first_human_review = (
            reviews[reviews["_user_type"].eq("user")]
            .groupby("pr_id")["_submitted_at_dt"]
            .min()
            .reset_index(name="first_human_review_at")
        )
        first_approval = (
            reviews[reviews["_state"].eq("APPROVED")]
            .groupby("pr_id")["_submitted_at_dt"]
            .min()
            .reset_index(name="first_approval_at")
        )
        summary = summary.merge(first_human_review, on="pr_id", how="left")
        summary = summary.merge(first_approval, on="pr_id", how="left")

    return summary


def summarize_pr_timeline_pd(timeline_df, review_summary_df):
    import pandas as pd

    if timeline_df.empty or "event" not in timeline_df.columns:
        return pd.DataFrame(columns=["pr_id"])

    timeline = timeline_df.copy()
    timeline["_event"] = timeline["event"].fillna("").astype(str)
    code_events = timeline[
        timeline["_event"].isin(["committed", "head_ref_force_pushed"])
    ].copy()
    if code_events.empty:
        return pd.DataFrame(columns=["pr_id"])

    summary = code_events.groupby("pr_id").size().reset_index(
        name="timeline_code_change_count"
    )
    force_push_count = (
        code_events[code_events["_event"].eq("head_ref_force_pushed")]
        .groupby("pr_id")
        .size()
        .reset_index(name="force_push_count")
    )
    summary = summary.merge(force_push_count, on="pr_id", how="left")
    summary["force_push_count"] = summary["force_push_count"].fillna(0).astype(int)

    if (
        "created_at" not in code_events.columns
        or "first_human_review_at" not in review_summary_df.columns
    ):
        summary["post_review_code_change_count"] = 0
        summary["pre_approval_code_change_count"] = 0
        summary["has_post_review_code_change"] = False
        return summary

    code_events["_created_at_dt"] = pd.to_datetime(
        code_events["created_at"], utc=True, errors="coerce"
    )
    review_times = review_summary_df[
        ["pr_id", "first_human_review_at", "first_approval_at"]
    ].copy()
    joined = code_events.merge(review_times, on="pr_id", how="left")
    post_review = joined[
        joined["first_human_review_at"].notna()
        & joined["_created_at_dt"].notna()
        & (joined["_created_at_dt"] > joined["first_human_review_at"])
    ].copy()
    post_review_count = (
        post_review.groupby("pr_id").size().reset_index(name="post_review_code_change_count")
    )
    summary = summary.merge(post_review_count, on="pr_id", how="left")
    summary["post_review_code_change_count"] = (
        summary["post_review_code_change_count"].fillna(0).astype(int)
    )

    pre_approval = post_review[
        post_review["first_approval_at"].isna()
        | (post_review["_created_at_dt"] < post_review["first_approval_at"])
    ]
    pre_approval_count = (
        pre_approval.groupby("pr_id")
        .size()
        .reset_index(name="pre_approval_code_change_count")
    )
    summary = summary.merge(pre_approval_count, on="pr_id", how="left")
    summary["pre_approval_code_change_count"] = (
        summary["pre_approval_code_change_count"].fillna(0).astype(int)
    )
    summary["has_post_review_code_change"] = (
        summary["post_review_code_change_count"] > 0
    )
    return summary


def load_pr_population_from_aidev(
    include_commit_details: bool = False,
    population_mode: str = DEFAULT_POPULATION_MODE,
) -> List[Dict]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas and pyarrow are required to load AIDev parquet files. "
            "Install exploration/aidev/requirements-notebook.txt first."
        ) from exc

    configs = ["pull_request", "repository", "pr_commits", "pr_reviews", "pr_task_type"]
    if population_mode_includes_reworked_merged(population_mode):
        configs.append("pr_timeline")
    if include_commit_details:
        configs.append("pr_commit_details")

    urls = get_parquet_urls(configs)
    missing = [config for config in configs if config not in urls]
    if missing:
        raise RuntimeError(f"Missing parquet URLs for configs: {', '.join(missing)}")

    pr_df = pd.read_parquet(urls["pull_request"]).copy()

    repo_df = pd.read_parquet(urls["repository"])[
        ["id", "language", "stars", "forks", "full_name"]
    ].rename(columns={"id": "repo_id"})
    pr_df = pr_df.merge(repo_df, on="repo_id", how="left")

    commits_df = pd.read_parquet(urls["pr_commits"])
    commit_summary = commits_df.groupby("pr_id").size().reset_index(name="commit_count")
    if "author" in commits_df.columns:
        commit_summary = commit_summary.merge(
            commits_df.groupby("pr_id")["author"]
            .nunique(dropna=True)
            .reset_index(name="unique_commit_authors_count"),
            on="pr_id",
            how="left",
        )
    else:
        commit_summary["unique_commit_authors_count"] = 0
    pr_df = _merge_count_summary(
        commit_summary,
        pr_df,
        left_key="id",
        right_key="pr_id",
        fill_columns=["commit_count", "unique_commit_authors_count"],
    )

    reviews_df = pd.read_parquet(urls["pr_reviews"])
    review_summary = summarize_pr_reviews_pd(reviews_df)
    review_count_columns = [
        "review_count",
        "unique_reviewers_count",
        "human_review_count",
        "bot_review_count",
        "approved_review_count",
        "changes_requested_review_count",
        "commented_review_count",
    ]
    pr_df = _merge_count_summary(
        review_summary,
        pr_df,
        left_key="id",
        right_key="pr_id",
        fill_columns=review_count_columns,
    )

    if "pr_timeline" in urls:
        timeline_summary = summarize_pr_timeline_pd(
            pd.read_parquet(urls["pr_timeline"]),
            review_summary,
        )
        timeline_count_columns = [
            "timeline_code_change_count",
            "force_push_count",
            "post_review_code_change_count",
            "pre_approval_code_change_count",
        ]
        pr_df = pr_df.merge(timeline_summary, left_on="id", right_on="pr_id", how="left")
        if "pr_id" in pr_df.columns:
            pr_df = pr_df.drop(columns=["pr_id"])
        for column in timeline_count_columns:
            pr_df[column] = pr_df[column].fillna(0).astype(int)
        pr_df["has_post_review_code_change"] = (
            pr_df["has_post_review_code_change"].apply(
                lambda value: False if pd.isna(value) else bool(value)
            )
            if "has_post_review_code_change" in pr_df.columns
            else False
        )

    task_df = pd.read_parquet(urls["pr_task_type"])[
        ["id", "type", "confidence"]
    ].rename(columns={"type": "task_type", "confidence": "task_confidence"})
    pr_df = pr_df.merge(task_df, on="id", how="left")

    if include_commit_details:
        details_df = pd.read_parquet(urls["pr_commit_details"])
        detail_summary = (
            details_df.groupby("pr_id")
            .agg(file_count=("filename", "nunique"), total_changes=("changes", "sum"))
            .reset_index()
        )
        pr_df = pr_df.merge(
            detail_summary,
            left_on="id",
            right_on="pr_id",
            how="left",
        )
        if "pr_id" in pr_df.columns:
            pr_df = pr_df.drop(columns=["pr_id"])
        pr_df["file_count"] = pr_df["file_count"].fillna(0).astype(int)
        pr_df["total_changes"] = pr_df["total_changes"].fillna(0)

    rows = filter_population_prs(
        pr_df.to_dict("records"),
        population_mode=population_mode,
    )
    rows = prepare_rows_for_sampling(rows)
    for row in rows:
        row["pr_id"] = row.get("id")
    return rows


def load_rejected_prs_from_aidev(include_commit_details: bool = False) -> List[Dict]:
    return load_pr_population_from_aidev(
        include_commit_details=include_commit_details,
        population_mode=POPULATION_REJECTED,
    )


def value_counts(rows: Iterable[Dict], field: str) -> Dict[str, int]:
    counter = Counter(normalize_value(row.get(field)) for row in rows)
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def summarize_result(
    population_rows: Sequence[Dict],
    result: SamplingResult,
    requested_strata_fields: Sequence[str],
    control_fields: Sequence[str],
    population_mode: str = DEFAULT_POPULATION_MODE,
) -> Dict:
    return {
        "seed": result.seed,
        "population_mode": population_mode,
        "population_size": len(population_rows),
        "sample_size": len(result.rows),
        "requested_strata_fields": list(requested_strata_fields),
        "used_strata_fields": result.strata_fields,
        "stratum_count": len(result.stratum_sizes),
        "stratum_sizes": result.stratum_sizes,
        "quotas": result.quotas,
        "population_distributions": {
            field: value_counts(population_rows, field) for field in control_fields
        },
        "sample_distributions": {
            field: value_counts(result.rows, field) for field in control_fields
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a reproducible stratified random sample of AIDev PRs."
    )
    parser.add_argument("--source", choices=["aidev", "csv"], default="aidev")
    parser.add_argument("--input-csv", type=Path)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=DEFAULT_OUTPUT_CSV,
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=DEFAULT_SUMMARY_JSON,
    )
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--min-per-stratum", type=int, default=DEFAULT_MIN_PER_STRATUM)
    parser.add_argument("--strata", nargs="+", default=DEFAULT_STRATA_FIELDS)
    parser.add_argument("--fallback-strata", nargs="+", default=DEFAULT_FALLBACK_STRATA_FIELDS)
    parser.add_argument(
        "--population-mode",
        choices=[
            POPULATION_REJECTED,
            POPULATION_REJECTED_OR_REWORKED_MERGED,
            POPULATION_MERGED_AFTER_REWORK,
            POPULATION_NOT_IMMEDIATELY_ACCEPTED,
        ],
        default=DEFAULT_POPULATION_MODE,
        help=(
            "Use closed non-merged PRs, merged PRs with review/rework signals, "
            "or both."
        ),
    )
    parser.add_argument(
        "--max-language-values",
        type=int,
        default=DEFAULT_MAX_LANGUAGE_VALUES,
        help="Keep only the top N languages and group the rest as 'other'. Use 0 to disable.",
    )
    parser.add_argument("--no-auto-fallback", action="store_true")
    parser.add_argument("--include-commit-details", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.source == "csv":
        if not args.input_csv:
            raise SystemExit("--input-csv is required when --source csv is used")
        rows = prepare_rows_for_sampling(
            filter_population_prs(
                load_csv_rows(args.input_csv),
                population_mode=args.population_mode,
            )
        )
    else:
        rows = load_pr_population_from_aidev(
            include_commit_details=args.include_commit_details,
            population_mode=args.population_mode,
        )

    candidates = [args.strata]
    if not args.no_auto_fallback:
        candidates.extend([args.fallback_strata, ["agent"]])
    candidates = unique_candidates(candidates)

    if has_field_in_candidates(candidates, "language"):
        rows = collapse_rare_values(
            rows,
            field="language",
            max_values=args.max_language_values,
        )

    strata_fields = choose_supported_strata_fields(
        rows,
        candidates=candidates,
        target_size=args.sample_size,
        min_per_stratum=args.min_per_stratum,
    )
    result = stratified_sample(
        rows,
        strata_fields=strata_fields,
        target_size=args.sample_size,
        min_per_stratum=args.min_per_stratum,
        seed=args.seed,
    )
    summary = summarize_result(
        population_rows=rows,
        result=result,
        requested_strata_fields=args.strata,
        population_mode=args.population_mode,
        control_fields=[
            "population_case_type",
            "agent",
            "language",
            "change_complexity_bin",
            "repo_popularity_bin",
            "created_period",
            "task_type",
        ],
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
    print(json.dumps({"output_csv": str(args.output_csv), "summary_json": str(args.summary_json)}))


if __name__ == "__main__":
    main()
