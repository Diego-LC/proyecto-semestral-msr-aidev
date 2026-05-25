import csv
import os
from pathlib import Path

from src import app, db
from src.database.models import *


DEFAULT_ARTIFACT_CSV = Path("data/rejection_cards_for_labeling_machine.csv")


# Registers 'initdb' cli command.
# Usage: `flask initdb`
@app.cli.command('initdb')
def initdb():
    print("Creating non-existing tables ...", end='')
    db.create_all(app=app)
    print("\t[SUCCESS]")

    initialize_database()
    import_my_data()


def initialize_database():
    print("Initializing tables with basic data ...", end='')
    print("\t[SUCCESS]")


def _artifact_csv_path():
    configured_path = os.environ.get("AIDEV_REJECTION_CARDS_CSV")
    if configured_path:
        return Path(configured_path)
    return DEFAULT_ARTIFACT_CSV


def _as_int(value):
    if value is None or str(value).strip() == "":
        return None
    return int(str(value).strip())


def _as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y", "si", "sí"}


def import_my_data():
    print("Loading AIDev rejection artifacts ...", end='')
    if Artifact.query.count() != 0:
        print("\t[ALREADY DONE]")
        return

    artifact_csv = _artifact_csv_path()
    if not artifact_csv.exists():
        raise RuntimeError(
            "Missing artifact CSV. Copy "
            "exploration/aidev/labeling_machine/outputs/"
            "rejection_cards_for_labeling_machine.csv to webapp/data/, "
            "or set AIDEV_REJECTION_CARDS_CSV."
        )

    with artifact_csv.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            db.session.add(
                Artifact(
                    id=_as_int(row.get("artifact_id")),
                    card_id=row.get("card_id", ""),
                    pr_id=row.get("pr_id", ""),
                    repo_id=row.get("repo_id", ""),
                    html_url=row.get("html_url", ""),
                    agent=row.get("agent", ""),
                    language=row.get("language", ""),
                    task_type=row.get("task_type", ""),
                    created_at=row.get("created_at", ""),
                    closed_at=row.get("closed_at", ""),
                    complexity_bin=row.get("complexity_bin", ""),
                    repo_popularity_bin=row.get("repo_popularity_bin", ""),
                    review_state=row.get("review_state", ""),
                    evidence_text=row.get("evidence_text", ""),
                    evidence_source=row.get("evidence_source", ""),
                    context_summary=row.get("context_summary", ""),
                    needs_manual_context_check=_as_bool(
                        row.get("needs_manual_context_check")
                    ),
                    evidence_user=row.get("evidence_user", ""),
                    evidence_user_type=row.get("evidence_user_type", ""),
                    evidence_created_at=row.get("evidence_created_at", ""),
                    evidence_id=row.get("evidence_id", ""),
                    evidence_count=_as_int(row.get("evidence_count")),
                    commit_count=_as_int(row.get("commit_count")),
                )
            )

    db.session.commit()
    print("\t[SUCCESS]")
