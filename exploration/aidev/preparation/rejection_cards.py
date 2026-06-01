#!/usr/bin/env python3

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from exploration.aidev.aidev_data import get_parquet_urls


DEFAULT_SAMPLE_CSV = Path(
    "exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510.csv"
)
DEFAULT_OUTPUT_CSV = Path(
    "exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510.csv"
)
DEFAULT_SUMMARY_JSON = Path(
    "exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510_summary.json"
)
DEFAULT_TEMPLATE_CSV = Path(
    "exploration/aidev/preparation/outputs/merged_after_rework_manual_categories_template.csv"
)
MANUAL_TEMPLATE_FIELDS = [
    "card_id",
    "pr_id",
    "population_case_type",
    "pr_state",
    "merged",
    "repo_id",
    "html_url",
    "resumen_justificacion_categoria",
    "horas_creacion_a_primera_aprobacion",
    "horas_creacion_a_merge",
    "horas_creacion_a_aceptacion",
    "fuente_tiempo_aceptacion",
    "categoria_retrabajo_pre_merge",
]
CARD_FIELDS = [
    "card_id",
    "pr_id",
    "population_case_type",
    "pr_state",
    "merged",
    "repo_id",
    "repo_full_name",
    "html_url",
    "agent",
    "pr_author",
    "language",
    "task_type",
    "task_confidence",
    "created_at",
    "closed_at",
    "merged_at",
    "time_to_close_hours",
    "time_to_merge_hours",
    "complexity_bin",
    "repo_popularity_bin",
    "stars",
    "forks",
    "commit_count",
    "file_count",
    "total_changes",
    "review_count",
    "human_review_count",
    "bot_review_count",
    "approved_review_count",
    "changes_requested_review_count",
    "commented_review_count",
    "review_comment_count",
    "pr_comment_count",
    "timeline_event_count",
    "human_comment_count",
    "bot_comment_count",
    "textual_evidence_count",
    "non_pr_textual_evidence_count",
    "review_state",
    "evidence_text",
    "evidence_raw_text",
    "evidence_source",
    "evidence_path",
    "evidence_diff_hunk",
    "context_summary",
    "pr_title",
    "pr_body_text",
    "all_evidence_text",
    "all_evidence_json",
    "pr_reviews_json",
    "pr_review_comments_json",
    "pr_comments_json",
    "changes_requested_text",
    "review_comment_text",
    "pr_comment_text",
    "timeline_text",
    "evidence_sources",
    "evidence_states",
    "evidence_users",
    "first_evidence_created_at",
    "last_evidence_created_at",
    "needs_manual_context_check",
    "evidence_quality_score",
    "discard_candidate_reason",
    "evidence_user",
    "evidence_user_type",
    "evidence_created_at",
    "evidence_id",
    "evidence_count",
]


def is_missing(value) -> bool:
    if value is None:
        return True
    return str(value).strip() == ""


def normalize_scalar(value) -> str:
    if is_missing(value):
        return ""
    return str(value).strip()


def clean_evidence_text(text: Optional[str], max_length: int = 1200) -> str:
    if is_missing(text):
        return ""

    cleaned = str(text)
    cleaned = re.sub(r"<!--.*?-->", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"```.*?```", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<details>.*?</details>", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("`", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max(0, max_length - 3)].rstrip() + "..."


def parse_github_datetime(value) -> Optional[datetime]:
    if is_missing(value):
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def duration_hours(start, end) -> str:
    start_dt = parse_github_datetime(start)
    end_dt = parse_github_datetime(end)
    if start_dt is None or end_dt is None:
        return ""
    return f"{(end_dt - start_dt).total_seconds() / 3600.0:.3f}"


def duration_hours_between(start_dt: Optional[datetime], end_dt: Optional[datetime]) -> str:
    if start_dt is None or end_dt is None:
        return ""
    return f"{(end_dt - start_dt).total_seconds() / 3600.0:.3f}"


def to_int(value, default: int = 0) -> int:
    if is_missing(value):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def boolish_text(value) -> str:
    if normalize_scalar(value).lower() in {"1", "true", "yes", "y", "si", "sí"}:
        return "true"
    if normalize_scalar(value).lower() in {"0", "false", "no", "n"}:
        return "false"
    return ""


def join_limited(values: Iterable[str], separator: str = " | ", max_length: int = 3000) -> str:
    pieces = [value for value in values if not is_missing(value)]
    joined = separator.join(pieces)
    if len(joined) <= max_length:
        return joined
    return joined[: max_length - 3].rstrip() + "..."


def unique_join(values: Iterable[str], max_items: int = 20) -> str:
    seen = []
    for value in values:
        normalized = normalize_scalar(value)
        if not normalized or normalized in seen:
            continue
        seen.append(normalized)
        if len(seen) >= max_items:
            break
    return "|".join(seen)


def source_counts_text(evidences: Sequence[Dict], field: str) -> str:
    counter = Counter(
        normalize_scalar(evidence.get(field))
        for evidence in evidences
        if normalize_scalar(evidence.get(field))
    )
    return "|".join(f"{key}:{counter[key]}" for key in sorted(counter))


def evidence_texts_for(
    evidences: Sequence[Dict],
    source: Optional[str] = None,
    state: Optional[str] = None,
    max_length: int = 2000,
) -> str:
    texts = []
    for evidence in evidences:
        if source and evidence.get("source") != source:
            continue
        if state and evidence.get("state") != state:
            continue
        text = clean_evidence_text(evidence.get("body"))
        if text:
            texts.append(text)
    return join_limited(texts, max_length=max_length)


def evidences_json_for(
    evidences: Sequence[Dict],
    source: Optional[str] = None,
    max_text_length: int = 2000,
) -> str:
    records = []
    for evidence in sorted(
        evidences,
        key=lambda item: (
            to_int(item.get("source_rank"), default=999),
            normalize_scalar(item.get("created_at")),
            normalize_scalar(item.get("id")),
        ),
    ):
        if source and evidence.get("source") != source:
            continue
        text = clean_evidence_text(evidence.get("body"), max_length=max_text_length)
        records.append(
            {
                "source": normalize_scalar(evidence.get("source")),
                "source_rank": to_int(evidence.get("source_rank"), default=999),
                "state": normalize_scalar(evidence.get("state")),
                "user": normalize_scalar(evidence.get("user")),
                "user_type": normalize_scalar(evidence.get("user_type")),
                "created_at": normalize_scalar(evidence.get("created_at")),
                "id": normalize_scalar(evidence.get("id")),
                "path": normalize_scalar(evidence.get("path")),
                "diff_hunk": clean_evidence_text(
                    evidence.get("diff_hunk"),
                    max_length=800,
                ),
                "text": text,
                "has_text": bool(text),
            }
        )
    return json.dumps(records, ensure_ascii=False)


def count_evidences(evidences: Sequence[Dict], **criteria) -> int:
    count = 0
    for evidence in evidences:
        if all(evidence.get(key) == value for key, value in criteria.items()):
            count += 1
    return count


def count_human_comment_evidences(evidences: Sequence[Dict]) -> int:
    return sum(
        1
        for evidence in evidences
        if evidence.get("source") in {"pr_review_comment", "pr_comment"}
        and normalize_scalar(evidence.get("user_type")).lower() == "user"
        and clean_evidence_text(evidence.get("body"))
    )


def count_bot_comment_evidences(evidences: Sequence[Dict]) -> int:
    return sum(
        1
        for evidence in evidences
        if evidence.get("source") in {"pr_review_comment", "pr_comment"}
        and normalize_scalar(evidence.get("user_type")).lower() == "bot"
        and clean_evidence_text(evidence.get("body"))
    )


def evidence_quality_score(best_evidence: Dict, evidences: Sequence[Dict]) -> int:
    score = 0
    best_text = clean_evidence_text(best_evidence.get("body"))
    if best_text:
        score += 1
    if best_evidence.get("source") != "pull_request":
        score += 2
    if normalize_scalar(best_evidence.get("user_type")).lower() == "user":
        score += 2
    if count_evidences(evidences, state="CHANGES_REQUESTED") > 0:
        score += 3
    if count_human_comment_evidences(evidences) > 0:
        score += 1
    if len([evidence for evidence in evidences if clean_evidence_text(evidence.get("body"))]) > 2:
        score += 1
    return min(score, 10)


def discard_candidate_reason(
    best_evidence: Dict,
    evidences: Sequence[Dict],
    needs_manual_context_check: str,
) -> str:
    if not clean_evidence_text(best_evidence.get("body")):
        return "sin_texto_util"
    if needs_manual_context_check == "true" and best_evidence.get("source") == "pull_request":
        return "solo_titulo_o_descripcion"
    if count_human_comment_evidences(evidences) == 0 and count_evidences(
        evidences, source="pr_review"
    ) == 0:
        return "sin_revision_o_comentario_humano"
    if evidence_quality_score(best_evidence, evidences) < 4:
        return "evidencia_debil"
    return ""


def build_api_pull_url(pr_row: Dict) -> str:
    repo_url = normalize_scalar(pr_row.get("repo_url"))
    number = normalize_scalar(pr_row.get("number"))
    if repo_url and number:
        return f"{repo_url}/pulls/{number}"
    return ""


def github_html_to_api_pull_url(html_url: str) -> str:
    if is_missing(html_url):
        return ""
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", str(html_url))
    if not match:
        return ""
    owner, repo, number = match.groups()
    return f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"


def evidence_record(
    source: str,
    source_rank: int,
    body,
    state="",
    user="",
    user_type="",
    created_at="",
    evidence_id="",
    path="",
    diff_hunk="",
) -> Dict:
    text_parts = []
    if path:
        text_parts.append(f"File: {path}")
    if diff_hunk:
        text_parts.append(f"Diff context: {diff_hunk}")
    if body:
        text_parts.append(str(body))

    return {
        "source": source,
        "source_rank": source_rank,
        "body": "\n\n".join(text_parts),
        "state": normalize_scalar(state),
        "user": normalize_scalar(user),
        "user_type": normalize_scalar(user_type),
        "created_at": normalize_scalar(created_at),
        "id": normalize_scalar(evidence_id),
        "path": normalize_scalar(path),
        "diff_hunk": normalize_scalar(diff_hunk),
    }


def select_best_evidence(evidences: Sequence[Dict]) -> Dict:
    candidates = [
        evidence
        for evidence in evidences
        if clean_evidence_text(evidence.get("body"))
    ]
    if not candidates:
        return evidence_record(
            source="pull_request",
            source_rank=90,
            body="",
        )

    return sorted(
        candidates,
        key=lambda evidence: (
            int(evidence.get("source_rank", 999)),
            normalize_scalar(evidence.get("created_at")),
            normalize_scalar(evidence.get("id")),
        ),
    )[0]


def make_context_summary(pr_row: Dict, max_length: int = 500) -> str:
    title = normalize_scalar(pr_row.get("title"))
    body = clean_evidence_text(pr_row.get("body"), max_length=350)
    pieces = []
    if title:
        pieces.append(f"Title: {title}")
    if body:
        pieces.append(f"PR body: {body}")
    pieces.append(
        "Metadata: "
        f"agent={normalize_scalar(pr_row.get('agent')) or 'unknown'}, "
        f"language={normalize_scalar(pr_row.get('language')) or 'unknown'}, "
        f"task_type={normalize_scalar(pr_row.get('task_type')) or 'unknown'}, "
        f"commits={normalize_scalar(pr_row.get('commit_count')) or 'unknown'}"
    )
    summary = " | ".join(pieces)
    if len(summary) <= max_length:
        return summary
    return summary[: max_length - 3].rstrip() + "..."


def build_rejection_card(
    pr_row: Dict,
    evidence: Dict,
    evidence_count: int,
    evidences: Optional[Sequence[Dict]] = None,
) -> Dict:
    all_evidences = list(evidences or [evidence])
    pr_id = normalize_scalar(pr_row.get("pr_id") or pr_row.get("id"))
    evidence_text = clean_evidence_text(evidence.get("body"))
    evidence_raw_text = normalize_scalar(evidence.get("body"))
    evidence_source = normalize_scalar(evidence.get("source"))
    needs_manual = "false"

    if not evidence_text:
        evidence_source = "sin_evidencia_suficiente"
        evidence_text = clean_evidence_text(
            f"{pr_row.get('title', '')}\n\n{pr_row.get('body', '')}"
        )
        needs_manual = "true"

    if evidence_source == "pull_request":
        needs_manual = "true"

    textual_evidences = [
        item for item in all_evidences if clean_evidence_text(item.get("body"))
    ]
    non_pr_textual_evidences = [
        item for item in textual_evidences if item.get("source") != "pull_request"
    ]
    evidence_dates = sorted(
        normalize_scalar(item.get("created_at"))
        for item in textual_evidences
        if normalize_scalar(item.get("created_at"))
    )
    quality_score = evidence_quality_score(evidence, all_evidences)

    return {
        "card_id": f"{pr_id}-A",
        "pr_id": pr_id,
        "population_case_type": normalize_scalar(
            pr_row.get("population_case_type") or "rejected"
        ),
        "pr_state": normalize_scalar(pr_row.get("state")),
        "merged": boolish_text(pr_row.get("merged"))
        or ("false" if is_missing(pr_row.get("merged_at")) else "true"),
        "repo_id": normalize_scalar(pr_row.get("repo_id")),
        "repo_full_name": normalize_scalar(pr_row.get("full_name")),
        "html_url": normalize_scalar(pr_row.get("html_url")),
        "agent": normalize_scalar(pr_row.get("agent")),
        "pr_author": normalize_scalar(pr_row.get("user")),
        "language": normalize_scalar(pr_row.get("language")),
        "task_type": normalize_scalar(pr_row.get("task_type")),
        "task_confidence": normalize_scalar(pr_row.get("task_confidence")),
        "created_at": normalize_scalar(pr_row.get("created_at")),
        "closed_at": normalize_scalar(pr_row.get("closed_at")),
        "merged_at": normalize_scalar(pr_row.get("merged_at")),
        "time_to_close_hours": normalize_scalar(pr_row.get("time_to_close_hours"))
        or duration_hours(pr_row.get("created_at"), pr_row.get("closed_at")),
        "time_to_merge_hours": normalize_scalar(pr_row.get("time_to_merge_hours"))
        or duration_hours(pr_row.get("created_at"), pr_row.get("merged_at")),
        "complexity_bin": normalize_scalar(
            pr_row.get("complexity_bin") or pr_row.get("change_complexity_bin")
        ),
        "repo_popularity_bin": normalize_scalar(pr_row.get("repo_popularity_bin")),
        "stars": normalize_scalar(pr_row.get("stars")),
        "forks": normalize_scalar(pr_row.get("forks")),
        "commit_count": normalize_scalar(pr_row.get("commit_count")),
        "file_count": normalize_scalar(pr_row.get("file_count")),
        "total_changes": normalize_scalar(pr_row.get("total_changes")),
        "review_count": normalize_scalar(pr_row.get("review_count"))
        or str(count_evidences(all_evidences, source="pr_review")),
        "human_review_count": normalize_scalar(pr_row.get("human_review_count"))
        or str(
            sum(
                1
                for item in all_evidences
                if item.get("source") == "pr_review"
                and normalize_scalar(item.get("user_type")).lower() == "user"
            )
        ),
        "bot_review_count": normalize_scalar(pr_row.get("bot_review_count"))
        or str(
            sum(
                1
                for item in all_evidences
                if item.get("source") == "pr_review"
                and normalize_scalar(item.get("user_type")).lower() == "bot"
            )
        ),
        "approved_review_count": normalize_scalar(pr_row.get("approved_review_count"))
        or str(count_evidences(all_evidences, source="pr_review", state="APPROVED")),
        "changes_requested_review_count": normalize_scalar(
            pr_row.get("changes_requested_review_count")
        )
        or str(
            count_evidences(
                all_evidences,
                source="pr_review",
                state="CHANGES_REQUESTED",
            )
        ),
        "commented_review_count": normalize_scalar(pr_row.get("commented_review_count"))
        or str(count_evidences(all_evidences, source="pr_review", state="COMMENTED")),
        "review_comment_count": str(
            count_evidences(all_evidences, source="pr_review_comment")
        ),
        "pr_comment_count": str(count_evidences(all_evidences, source="pr_comment")),
        "timeline_event_count": str(count_evidences(all_evidences, source="pr_timeline")),
        "human_comment_count": str(count_human_comment_evidences(all_evidences)),
        "bot_comment_count": str(count_bot_comment_evidences(all_evidences)),
        "textual_evidence_count": str(len(textual_evidences)),
        "non_pr_textual_evidence_count": str(len(non_pr_textual_evidences)),
        "review_state": normalize_scalar(evidence.get("state")),
        "evidence_text": evidence_text,
        "evidence_raw_text": evidence_raw_text,
        "evidence_source": evidence_source,
        "evidence_path": normalize_scalar(evidence.get("path")),
        "evidence_diff_hunk": normalize_scalar(evidence.get("diff_hunk")),
        "context_summary": make_context_summary(pr_row),
        "pr_title": normalize_scalar(pr_row.get("title")),
        "pr_body_text": clean_evidence_text(pr_row.get("body"), max_length=1800),
        "all_evidence_text": evidence_texts_for(
            non_pr_textual_evidences,
            max_length=4000,
        ),
        "all_evidence_json": evidences_json_for(all_evidences),
        "pr_reviews_json": evidences_json_for(all_evidences, source="pr_review"),
        "pr_review_comments_json": evidences_json_for(
            all_evidences,
            source="pr_review_comment",
        ),
        "pr_comments_json": evidences_json_for(all_evidences, source="pr_comment"),
        "changes_requested_text": evidence_texts_for(
            all_evidences,
            state="CHANGES_REQUESTED",
            max_length=2000,
        ),
        "review_comment_text": evidence_texts_for(
            all_evidences,
            source="pr_review_comment",
            max_length=2000,
        ),
        "pr_comment_text": evidence_texts_for(
            all_evidences,
            source="pr_comment",
            max_length=2000,
        ),
        "timeline_text": evidence_texts_for(
            all_evidences,
            source="pr_timeline",
            max_length=1200,
        ),
        "evidence_sources": source_counts_text(all_evidences, "source"),
        "evidence_states": source_counts_text(all_evidences, "state"),
        "evidence_users": unique_join(item.get("user") for item in all_evidences),
        "first_evidence_created_at": evidence_dates[0] if evidence_dates else "",
        "last_evidence_created_at": evidence_dates[-1] if evidence_dates else "",
        "needs_manual_context_check": needs_manual,
        "evidence_quality_score": str(quality_score),
        "discard_candidate_reason": discard_candidate_reason(
            evidence,
            all_evidences,
            needs_manual,
        ),
        "evidence_user": normalize_scalar(evidence.get("user")),
        "evidence_user_type": normalize_scalar(evidence.get("user_type")),
        "evidence_created_at": normalize_scalar(evidence.get("created_at")),
        "evidence_id": normalize_scalar(evidence.get("id")),
        "evidence_count": str(evidence_count),
    }


def load_csv_rows(path: Path) -> List[Dict]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv_rows(path: Path, rows: Sequence[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CARD_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CARD_FIELDS})


def first_approval_created_at(card: Dict) -> Optional[datetime]:
    try:
        reviews = json.loads(card.get("pr_reviews_json") or "[]")
    except json.JSONDecodeError:
        return None

    approval_dates = [
        parse_github_datetime(review.get("created_at"))
        for review in reviews
        if review.get("state") == "APPROVED"
    ]
    approval_dates = [value for value in approval_dates if value is not None]
    return min(approval_dates) if approval_dates else None


def manual_template_row(card: Dict) -> Dict:
    created_at = parse_github_datetime(card.get("created_at"))
    first_approval_at = first_approval_created_at(card)
    merged_at = parse_github_datetime(card.get("merged_at"))
    approval_hours = duration_hours_between(created_at, first_approval_at)
    merge_hours = duration_hours_between(created_at, merged_at)

    if approval_hours:
        acceptance_hours = approval_hours
        acceptance_source = "primera_review_aprobada"
    elif merge_hours:
        acceptance_hours = merge_hours
        acceptance_source = "merge_sin_review_aprobada"
    else:
        acceptance_hours = ""
        acceptance_source = "sin_fecha_disponible"

    return {
        "card_id": card.get("card_id", ""),
        "pr_id": card.get("pr_id", ""),
        "population_case_type": card.get("population_case_type", ""),
        "pr_state": card.get("pr_state", ""),
        "merged": card.get("merged", ""),
        "repo_id": card.get("repo_id", ""),
        "html_url": card.get("html_url", ""),
        "resumen_justificacion_categoria": "",
        "horas_creacion_a_primera_aprobacion": approval_hours,
        "horas_creacion_a_merge": merge_hours,
        "horas_creacion_a_aceptacion": acceptance_hours,
        "fuente_tiempo_aceptacion": acceptance_source,
        "categoria_retrabajo_pre_merge": "",
    }


def write_manual_template(path: Path, cards: Sequence[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=MANUAL_TEMPLATE_FIELDS)
        writer.writeheader()
        for card in cards:
            writer.writerow(manual_template_row(card))


def index_rows(rows: Iterable[Dict], key_field: str) -> Dict[str, List[Dict]]:
    index: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        key = normalize_scalar(row.get(key_field))
        if key:
            index[key].append(row)
    return dict(index)


def load_evidence_tables() -> Dict[str, List[Dict]]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas and pyarrow are required to load AIDev parquet files. "
            "Install exploration/aidev/requirements-notebook.txt first."
        ) from exc

    configs = [
        "pr_reviews",
        "pr_review_comments",
        "pr_review_comments_v2",
        "pr_comments",
        "pr_timeline",
    ]
    urls = get_parquet_urls(configs)
    missing = [config for config in configs if config not in urls]
    if missing:
        raise RuntimeError(f"Missing parquet URLs for configs: {', '.join(missing)}")

    return {
        config: pd.read_parquet(urls[config]).to_dict("records")
        for config in configs
    }


def build_evidence_indexes(tables: Dict[str, List[Dict]]) -> Dict[str, Dict[str, List[Dict]]]:
    review_comments_by_pull_url: Dict[str, List[Dict]] = defaultdict(list)
    seen_review_comments = set()
    review_comment_rows = (
        tables.get("pr_review_comments_v2", [])
        + tables.get("pr_review_comments", [])
    )
    for row in review_comment_rows:
        dedupe_key = (
            normalize_scalar(row.get("id")),
            normalize_scalar(row.get("pull_request_url")),
            normalize_scalar(row.get("path")),
            normalize_scalar(row.get("body")),
        )
        if dedupe_key in seen_review_comments:
            continue
        seen_review_comments.add(dedupe_key)
        key = normalize_scalar(row.get("pull_request_url"))
        if key:
            review_comments_by_pull_url[key].append(row)

    return {
        "reviews_by_pr_id": index_rows(tables.get("pr_reviews", []), "pr_id"),
        "comments_by_pr_id": index_rows(tables.get("pr_comments", []), "pr_id"),
        "timeline_by_pr_id": index_rows(tables.get("pr_timeline", []), "pr_id"),
        "review_comments_by_pull_url": dict(review_comments_by_pull_url),
    }


def evidence_for_pr(pr_row: Dict, indexes: Dict[str, Dict[str, List[Dict]]]) -> List[Dict]:
    pr_id = normalize_scalar(pr_row.get("pr_id") or pr_row.get("id"))
    api_pull_url = build_api_pull_url(pr_row) or github_html_to_api_pull_url(
        normalize_scalar(pr_row.get("html_url"))
    )
    evidences: List[Dict] = []

    for row in indexes.get("reviews_by_pr_id", {}).get(pr_id, []):
        state = normalize_scalar(row.get("state"))
        user_type = normalize_scalar(row.get("user_type"))
        if state == "CHANGES_REQUESTED":
            rank = 10
        elif user_type == "User":
            rank = 20
        else:
            rank = 40
        evidences.append(
            evidence_record(
                source="pr_review",
                source_rank=rank,
                body=row.get("body"),
                state=state,
                user=row.get("user"),
                user_type=user_type,
                created_at=row.get("submitted_at"),
                evidence_id=row.get("id"),
            )
        )

    for row in indexes.get("review_comments_by_pull_url", {}).get(api_pull_url, []):
        user_type = normalize_scalar(row.get("user_type"))
        rank = 20 if user_type == "User" else 50
        evidences.append(
            evidence_record(
                source="pr_review_comment",
                source_rank=rank,
                body=row.get("body"),
                state="COMMENTED",
                user=row.get("user"),
                user_type=user_type,
                created_at=row.get("created_at"),
                evidence_id=row.get("id"),
                path=row.get("path"),
                diff_hunk=row.get("diff_hunk"),
            )
        )

    for row in indexes.get("comments_by_pr_id", {}).get(pr_id, []):
        user_type = normalize_scalar(row.get("user_type"))
        rank = 30 if user_type == "User" else 60
        evidences.append(
            evidence_record(
                source="pr_comment",
                source_rank=rank,
                body=row.get("body"),
                state="COMMENTED",
                user=row.get("user"),
                user_type=user_type,
                created_at=row.get("created_at"),
                evidence_id=row.get("id"),
            )
        )

    for row in indexes.get("timeline_by_pr_id", {}).get(pr_id, []):
        event = normalize_scalar(row.get("event"))
        if event in {"committed", "head_ref_force_pushed"}:
            continue
        if is_missing(row.get("message")):
            continue
        evidences.append(
            evidence_record(
                source="pr_timeline",
                source_rank=70,
                body=row.get("message"),
                state=event,
                user=row.get("actor"),
                user_type="",
                created_at=row.get("created_at"),
                evidence_id=row.get("commit_id"),
            )
        )

    evidences.append(
        evidence_record(
            source="pull_request",
            source_rank=90,
            body=f"{pr_row.get('title', '')}\n\n{pr_row.get('body', '')}",
            state="",
            user=pr_row.get("user"),
            user_type="",
            created_at=pr_row.get("created_at"),
            evidence_id=pr_id,
        )
    )
    return evidences


def build_rejection_cards(sample_rows: Sequence[Dict], indexes: Dict[str, Dict[str, List[Dict]]]) -> List[Dict]:
    cards = []
    seen_pr_ids = set()
    for row in sample_rows:
        pr_id = normalize_scalar(row.get("pr_id") or row.get("id"))
        if pr_id in seen_pr_ids:
            continue
        seen_pr_ids.add(pr_id)
        evidences = evidence_for_pr(row, indexes)
        best = select_best_evidence(evidences)
        cards.append(
            build_rejection_card(
                row,
                best,
                evidence_count=len(evidences),
                evidences=evidences,
            )
        )
    return cards


def filter_cards_with_human_comments(cards: Sequence[Dict]) -> List[Dict]:
    return [
        dict(card)
        for card in cards
        if to_int(card.get("human_comment_count")) > 0
    ]


def summarize_cards(cards: Sequence[Dict], source_card_count: Optional[int] = None) -> Dict:
    source_count = len(cards) if source_card_count is None else source_card_count
    return {
        "card_count": len(cards),
        "source_card_count": source_count,
        "filtered_out_without_human_comments": source_count - len(cards),
        "filter_rule": "human_comment_count > 0",
        "manual_context_check_count": sum(
            1 for card in cards if card.get("needs_manual_context_check") == "true"
        ),
        "discard_candidate_reason_counts": dict(
            Counter(card.get("discard_candidate_reason", "") for card in cards)
        ),
        "evidence_source_counts": dict(
            Counter(card.get("evidence_source", "") for card in cards)
        ),
        "review_state_counts": dict(Counter(card.get("review_state", "") for card in cards)),
        "population_case_type_counts": dict(
            Counter(card.get("population_case_type", "") for card in cards)
        ),
        "agent_counts": dict(Counter(card.get("agent", "") for card in cards)),
        "language_counts": dict(Counter(card.get("language", "") for card in cards)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare card rows from the merged-after-rework AIDev sample."
    )
    parser.add_argument("--sample-csv", type=Path, default=DEFAULT_SAMPLE_CSV)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--template-csv", type=Path, default=DEFAULT_TEMPLATE_CSV)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sample_rows = load_csv_rows(args.sample_csv)
    tables = load_evidence_tables()
    indexes = build_evidence_indexes(tables)
    source_cards = build_rejection_cards(sample_rows, indexes)
    cards = filter_cards_with_human_comments(source_cards)
    summary = {
        "sample_csv": str(args.sample_csv),
        "output_csv": str(args.output_csv),
        "summary_json": str(args.summary_json),
        "template_csv": str(args.template_csv),
        **summarize_cards(cards, source_card_count=len(source_cards)),
    }

    if args.dry_run:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    write_csv_rows(args.output_csv, cards)
    write_manual_template(args.template_csv, cards)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output_csv": str(args.output_csv),
                "summary_json": str(args.summary_json),
                "template_csv": str(args.template_csv),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
