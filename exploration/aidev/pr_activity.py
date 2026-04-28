from datetime import datetime
from statistics import mean
from typing import Dict, Iterable, List, Optional

from exploration.aidev.inspect_aidev import DATASET, api_get


def get_parquet_manifest(dataset: str = DATASET) -> Dict:
    return api_get("parquet", dataset=dataset)


def select_parquet_urls(
    manifest: Dict,
    configs: Iterable[str],
    split: str = "train",
) -> Dict[str, str]:
    requested = set(configs)
    selected: Dict[str, str] = {}

    for entry in manifest.get("parquet_files", []):
        if entry.get("config") in requested and entry.get("split") == split:
            selected[entry["config"]] = entry["url"]

    return selected


def get_parquet_urls(
    configs: Iterable[str],
    dataset: str = DATASET,
    split: str = "train",
) -> Dict[str, str]:
    manifest = get_parquet_manifest(dataset=dataset)
    return select_parquet_urls(manifest, configs=configs, split=split)


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def duration_hours(start: Optional[str], end: Optional[str]) -> Optional[float]:
    start_dt = parse_datetime(start)
    end_dt = parse_datetime(end)
    if start_dt is None or end_dt is None:
        return None
    return (end_dt - start_dt).total_seconds() / 3600.0


def build_pr_activity_records(
    pull_requests: Iterable[Dict],
    commits: Iterable[Dict],
    reviews: Iterable[Dict],
) -> List[Dict]:
    commit_index: Dict[int, List[Dict]] = {}
    review_index: Dict[int, List[Dict]] = {}

    for commit in commits:
        pr_id = commit.get("pr_id")
        if pr_id is not None:
            commit_index.setdefault(pr_id, []).append(commit)

    for review in reviews:
        pr_id = review.get("pr_id")
        if pr_id is not None:
            review_index.setdefault(pr_id, []).append(review)

    records: List[Dict] = []

    for pr in pull_requests:
        pr_id = pr.get("id")
        pr_author = pr.get("user")
        pr_commits = commit_index.get(pr_id, [])
        pr_reviews = review_index.get(pr_id, [])

        commit_authors = {
            commit.get("author")
            for commit in pr_commits
            if commit.get("author") not in (None, "")
        }
        human_reviews = [
            review for review in pr_reviews if str(review.get("user_type", "")).lower() == "user"
        ]
        bot_reviews = [
            review for review in pr_reviews if str(review.get("user_type", "")).lower() == "bot"
        ]
        external_human_reviews = [
            review for review in human_reviews if review.get("user") not in (None, "", pr_author)
        ]

        review_states = [review.get("state") for review in pr_reviews]
        merged = pr.get("merged_at") is not None

        records.append(
            {
                "pr_id": pr_id,
                "number": pr.get("number"),
                "agent": pr.get("agent"),
                "author": pr_author,
                "state": pr.get("state"),
                "merged": merged,
                "repo_id": pr.get("repo_id"),
                "repo_url": pr.get("repo_url"),
                "html_url": pr.get("html_url"),
                "created_at": pr.get("created_at"),
                "closed_at": pr.get("closed_at"),
                "merged_at": pr.get("merged_at"),
                "commit_count": len(pr_commits),
                "unique_commit_authors_count": len(commit_authors),
                "external_commit_author_count": len(
                    [author for author in commit_authors if author != pr_author]
                ),
                "review_count": len(pr_reviews),
                "unique_reviewers_count": len(
                    {
                        review.get("user")
                        for review in pr_reviews
                        if review.get("user") not in (None, "")
                    }
                ),
                "human_review_count": len(human_reviews),
                "bot_review_count": len(bot_reviews),
                "approved_review_count": review_states.count("APPROVED"),
                "changes_requested_review_count": review_states.count("CHANGES_REQUESTED"),
                "commented_review_count": review_states.count("COMMENTED"),
                "has_human_review": len(human_reviews) > 0,
                "has_external_human_review": len(external_human_reviews) > 0,
                "time_to_close_hours": duration_hours(pr.get("created_at"), pr.get("closed_at")),
                "time_to_merge_hours": duration_hours(pr.get("created_at"), pr.get("merged_at")),
            }
        )

    return sorted(records, key=lambda record: (record["pr_id"] is None, record["pr_id"]))


def _mean_or_none(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return mean(clean)


def compute_overview_metrics(records: Iterable[Dict]) -> Dict:
    rows = list(records)
    total_prs = len(rows)
    merged_prs = sum(1 for row in rows if row.get("merged"))
    prs_with_human_reviews = sum(1 for row in rows if row.get("has_human_review"))
    prs_with_external_human_reviews = sum(
        1 for row in rows if row.get("has_external_human_review")
    )
    prs_with_bot_reviews = sum(1 for row in rows if row.get("bot_review_count", 0) > 0)

    return {
        "total_prs": total_prs,
        "merged_prs": merged_prs,
        "merge_rate": (merged_prs / total_prs) if total_prs else None,
        "avg_commits_per_pr": _mean_or_none(row.get("commit_count") for row in rows),
        "avg_reviews_per_pr": _mean_or_none(row.get("review_count") for row in rows),
        "prs_with_human_reviews": prs_with_human_reviews,
        "prs_with_external_human_reviews": prs_with_external_human_reviews,
        "prs_with_bot_reviews": prs_with_bot_reviews,
        "avg_time_to_close_hours": _mean_or_none(
            row.get("time_to_close_hours") for row in rows
        ),
        "avg_time_to_merge_hours": _mean_or_none(
            row.get("time_to_merge_hours") for row in rows
        ),
    }
