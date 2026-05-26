import random

from sqlalchemy import distinct, func

from src import db
from src.database.models import Artifact, FlaggedArtifact, LabelingData
from src.helper.consts import N_API_NEEDS_LABELING
from src.helper.tools_common import (
    get_false_positive_artifacts,
    get_locked_artifacts,
    who_is_signed_in,
)


def get_target_artifact_count():
    artifact_count = Artifact.query.count()
    if artifact_count > 0:
        return artifact_count
    return N_API_NEEDS_LABELING


def get_labeling_status(username):
    if username is None:
        return None

    labeling_status = {
        'username': username,
        'total_n_api': get_n_labeled_artifact_per_user().get(username, 0),
        'total_n_sentence': 0,
        'total_n_reviewed': 0,
    }
    return labeling_status


def get_overall_labeling_progress():
    labeling_status = {
        'source_id': 0,
        'source_name': "AIDev rejected PR cards",
        'n_artifacts_labeled': get_n_artifacts_labeled_by_n_or_more(2),
        'n_artifacts_to_be_labeled': get_target_artifact_count(),
        'n_artifacts_reviewed': 0,
    }
    return labeling_status


def get_n_labeled_artifact_per_user():
    """
    Return a dictionary of {username: n_labeled_artifact, ...}
    """
    result = (
        db.session.query(
            LabelingData.username,
            func.count(distinct(LabelingData.artifact_id)),
        )
        .group_by(LabelingData.username)
        .all()
    )
    ret = {}
    for row in result:
        ret[row[0]] = row[1]
    return ret


def get_n_artifacts_labeled_by_n_or_more(num):
    artifacts_labeled_num_times = (
        db.session.query(LabelingData.artifact_id)
        .group_by(LabelingData.artifact_id)
        .having(func.count(distinct(LabelingData.username)) >= num)
    )
    artifacts_flagged_2_times = (
        FlaggedArtifact.query.with_entities(FlaggedArtifact.artifact_id)
        .group_by(FlaggedArtifact.artifact_id)
        .having(func.count() > 1)
    )
    result = (
        artifacts_labeled_num_times.except_(artifacts_flagged_2_times)
        .with_entities(func.count(LabelingData.artifact_id))
        .scalar()
    )
    return result or 0


def choose_next_random_api():
    candidate_artifact_ids = {row[0] for row in db.session.query(Artifact.id).all()}

    labeled_artifact_ids = {
        row[0]
        for row in db.session.query(distinct(LabelingData.artifact_id))
        .filter(LabelingData.username == who_is_signed_in())
        .all()
    }
    candidate_artifact_ids -= labeled_artifact_ids

    locked_artifacts = get_locked_artifacts()
    locked_artifacts_by_2 = set(k for k, v in locked_artifacts.items() if v >= 2)
    candidate_artifact_ids -= locked_artifacts_by_2

    fp_artifact_ids = get_false_positive_artifacts()
    candidate_artifact_ids -= fp_artifact_ids

    if len(candidate_artifact_ids) == 0:
        return -1

    n_tagger_per_artifact = {
        row[0]: row[1]
        for row in db.session.query(
            LabelingData.artifact_id,
            func.count(distinct(LabelingData.username)),
        )
        .group_by(LabelingData.artifact_id)
        .all()
    }
    candidate_groups = [[], []]
    for artifact_id in candidate_artifact_ids:
        if artifact_id not in n_tagger_per_artifact.keys():
            candidate_groups[0].append(artifact_id)
        elif n_tagger_per_artifact[artifact_id] == 1:
            candidate_groups[1].append(artifact_id)

    if len(candidate_groups[1]) > 0:
        return random.choice(candidate_groups[1])
    if len(candidate_groups[0]) > 0:
        return random.choice(candidate_groups[0])
    return -2
