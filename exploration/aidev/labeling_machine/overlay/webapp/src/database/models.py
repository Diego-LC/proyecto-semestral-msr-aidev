from sqlalchemy.orm import validates
from sqlalchemy.sql import func

from src import db


class User(db.Model):
    """
    Registered Users
    """
    __tablename__ = 'User'
    username = db.Column(db.Text, primary_key=True)
    gender = db.Column(db.Text)
    education = db.Column(db.Text)
    occupation = db.Column(db.Text)
    affiliation = db.Column(db.Text)
    years_xp = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=func.now())

    @validates('username', 'gender', 'education', 'occupation')
    def convert_lower(self, key, value):
        return value.title()


class Note(db.Model):
    """
    Additional notes on artifacts. e.g., "Nice example", "Needs extra caution".
    """
    __tablename__ = 'Note'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    artifact_id = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text, nullable=False)
    added_by = db.Column(db.Text, nullable=False)
    added_at = db.Column(db.DateTime, default=func.now())


class FlaggedArtifact(db.Model):
    __tablename__ = 'FlaggedArtifact'
    artifact_id = db.Column(db.Integer, primary_key=True)
    added_by = db.Column(db.Text, primary_key=True)
    added_at = db.Column(db.DateTime, default=func.now())


class LockedArtifact(db.Model):
    __tablename__ = 'LockedArtifact'
    username = db.Column(db.Text, primary_key=True)
    artifact_id = db.Column(db.Integer)
    locked_at = db.Column(db.DateTime, default=func.now())


class Artifact(db.Model):
    __tablename__ = 'Artifact'
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Text, unique=True, nullable=False)
    pr_id = db.Column(db.Text, index=True)
    repo_id = db.Column(db.Text)
    html_url = db.Column(db.Text)
    agent = db.Column(db.Text)
    language = db.Column(db.Text)
    task_type = db.Column(db.Text)
    created_at = db.Column(db.Text)
    closed_at = db.Column(db.Text)
    complexity_bin = db.Column(db.Text)
    repo_popularity_bin = db.Column(db.Text)
    review_state = db.Column(db.Text)
    evidence_text = db.Column(db.Text)
    evidence_source = db.Column(db.Text)
    context_summary = db.Column(db.Text)
    needs_manual_context_check = db.Column(db.Boolean, default=False)
    evidence_user = db.Column(db.Text)
    evidence_user_type = db.Column(db.Text)
    evidence_created_at = db.Column(db.Text)
    evidence_id = db.Column(db.Text)
    evidence_count = db.Column(db.Integer)
    commit_count = db.Column(db.Integer)


class LabelingData(db.Model):
    __tablename__ = 'LabelingData'
    labeling_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    artifact_id = db.Column(db.Integer)

    category_parent = db.Column(db.Text)
    subcategory = db.Column(db.Text)
    confidence = db.Column(db.Text)
    rationale = db.Column(db.Text)
    needs_discussion = db.Column(db.Boolean, default=False)

    # Compatibility with the original Labeling Machine statistics/UI code.
    labeling = db.Column(db.Text)
    remark = db.Column(db.Text)

    username = db.Column(db.Text)
    duration_sec = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=func.now())
