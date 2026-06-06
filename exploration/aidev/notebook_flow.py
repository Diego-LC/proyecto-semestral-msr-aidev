"""Reusable table builders for the merged-after-rework notebook."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from exploration.aidev.preparation.rejection_cards import (
    DEFAULT_OUTPUT_CSV as DEFAULT_CARDS_CSV,
    DEFAULT_SUMMARY_JSON as DEFAULT_PREPARATION_SUMMARY_JSON,
    DEFAULT_TEMPLATE_CSV,
    MANUAL_TEMPLATE_FIELDS,
    write_manual_template,
)
from exploration.aidev.sampling.stratified_sampler import (
    DEFAULT_OUTPUT_CSV as DEFAULT_SAMPLE_CSV,
    DEFAULT_SUMMARY_JSON as DEFAULT_SAMPLING_SUMMARY_JSON,
)


@dataclass
class FlowArtifacts:
    root: Path
    sampling_summary_path: Path
    sample_csv_path: Path
    preparation_summary_path: Path
    cards_csv_path: Path
    template_csv_path: Path
    sampling_summary: dict
    preparation_summary: dict
    sample_df: pd.DataFrame
    cards_df: pd.DataFrame
    template_df: pd.DataFrame


def find_repo_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / "exploration" / "aidev").exists():
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
            return path
    raise RuntimeError("No se encontro la raiz del repositorio")


def resolve_repo_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def is_missing_or_empty(path: Path) -> bool:
    return not path.exists() or path.stat().st_size == 0


def run_flow_script(root: Path, script_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(resolve_repo_path(root, script_path))],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Fallo la ejecucion del flujo\n"
            f"script: {script_path}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def load_or_rebuild_template(template_csv_path: Path, cards_df: pd.DataFrame) -> pd.DataFrame:
    def rebuild() -> pd.DataFrame:
        card_rows = cards_df.to_dict("records")
        write_manual_template(template_csv_path, card_rows)
        return pd.read_csv(template_csv_path)

    try:
        template_df = pd.read_csv(template_csv_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return rebuild()

    expected_columns = list(MANUAL_TEMPLATE_FIELDS)
    if list(template_df.columns) != expected_columns or len(template_df) != len(cards_df):
        return rebuild()

    return template_df


def ensure_flow_outputs(root: Optional[Path] = None, force: bool = False) -> FlowArtifacts:
    repo_root = find_repo_root(root)
    sampling_summary_path = resolve_repo_path(repo_root, DEFAULT_SAMPLING_SUMMARY_JSON)
    sample_csv_path = resolve_repo_path(repo_root, DEFAULT_SAMPLE_CSV)
    preparation_summary_path = resolve_repo_path(repo_root, DEFAULT_PREPARATION_SUMMARY_JSON)
    cards_csv_path = resolve_repo_path(repo_root, DEFAULT_CARDS_CSV)
    template_csv_path = resolve_repo_path(repo_root, DEFAULT_TEMPLATE_CSV)

    sampling_paths = [sampling_summary_path, sample_csv_path]
    preparation_paths = [preparation_summary_path, cards_csv_path, template_csv_path]

    if force or any(is_missing_or_empty(path) for path in sampling_paths):
        run_flow_script(repo_root, Path("exploration/aidev/sampling/stratified_sampler.py"))

    if force or any(is_missing_or_empty(path) for path in preparation_paths):
        run_flow_script(repo_root, Path("exploration/aidev/preparation/rejection_cards.py"))

    return load_flow_artifacts(repo_root)


def load_flow_artifacts(root: Optional[Path] = None) -> FlowArtifacts:
    repo_root = find_repo_root(root)
    sampling_summary_path = resolve_repo_path(repo_root, DEFAULT_SAMPLING_SUMMARY_JSON)
    sample_csv_path = resolve_repo_path(repo_root, DEFAULT_SAMPLE_CSV)
    preparation_summary_path = resolve_repo_path(repo_root, DEFAULT_PREPARATION_SUMMARY_JSON)
    cards_csv_path = resolve_repo_path(repo_root, DEFAULT_CARDS_CSV)
    template_csv_path = resolve_repo_path(repo_root, DEFAULT_TEMPLATE_CSV)

    sampling_summary = read_json(sampling_summary_path)
    preparation_summary = read_json(preparation_summary_path)
    sample_df = pd.read_csv(sample_csv_path)
    cards_df = pd.read_csv(cards_csv_path)

    return FlowArtifacts(
        root=repo_root,
        sampling_summary_path=sampling_summary_path,
        sample_csv_path=sample_csv_path,
        preparation_summary_path=preparation_summary_path,
        cards_csv_path=cards_csv_path,
        template_csv_path=template_csv_path,
        sampling_summary=sampling_summary,
        preparation_summary=preparation_summary,
        sample_df=sample_df,
        cards_df=cards_df,
        template_df=load_or_rebuild_template(template_csv_path, cards_df),
    )


def relative_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def build_raw_overview(summary: dict) -> pd.DataFrame:
    counts = summary["population_filter_counts"]
    return pd.DataFrame(
        [
            {
                "metrica": "PRs totales en pull_request",
                "definicion": "Todos los registros del parquet pull_request",
                "total": counts["all_pull_request"],
            },
            {
                "metrica": "PRs cerrados",
                "definicion": "state = closed",
                "total": counts["closed"],
            },
            {
                "metrica": "PRs mergeados",
                "definicion": "merged_at no nulo",
                "total": counts["merged"],
            },
            {
                "metrica": "PRs cerrados sin merge",
                "definicion": "state = closed y merged_at nulo",
                "total": counts["closed_unmerged"],
            },
            {
                "metrica": "PRs mergeados con commits adicionales",
                "definicion": "merged_at no nulo y commit_count > 1",
                "total": counts["merged_with_additional_commits"],
            },
            {
                "metrica": "Poblacion operacional",
                "definicion": "merged_at no nulo, commit_count > 1 y human_comment_count > 0",
                "total": counts["merged_with_additional_commits_and_human_comments"],
            },
        ]
    )


def build_files_table(artifacts: FlowArtifacts) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "artefacto": "Resumen de muestreo",
                "ruta": relative_path(artifacts.sampling_summary_path, artifacts.root),
            },
            {
                "artefacto": "Muestra estratificada",
                "ruta": relative_path(artifacts.sample_csv_path, artifacts.root),
            },
            {
                "artefacto": "Resumen de preparacion",
                "ruta": relative_path(artifacts.preparation_summary_path, artifacts.root),
            },
            {
                "artefacto": "Tarjetas con evidencia",
                "ruta": relative_path(artifacts.cards_csv_path, artifacts.root),
            },
            {
                "artefacto": "Plantilla manual",
                "ruta": relative_path(artifacts.template_csv_path, artifacts.root),
            },
        ]
    )


def build_funnel(artifacts: FlowArtifacts) -> pd.DataFrame:
    counts = artifacts.sampling_summary["population_filter_counts"]
    total = counts["all_pull_request"]
    rows = [
        ("Universo bruto AIDev", "Todos los PRs en pull_request", total),
        ("PRs mergeados", "merged_at no nulo", counts["merged"]),
        (
            "PRs mergeados con commits adicionales",
            "commit_count > 1",
            counts["merged_with_additional_commits"],
        ),
        (
            "Poblacion antes de estratificar",
            "commit_count > 1 y human_comment_count > 0",
            artifacts.sampling_summary["population_size"],
        ),
        (
            "Muestra estratificada por agente",
            "cuotas proporcionales por agent",
            len(artifacts.sample_df),
        ),
        ("Tarjetas candidatas", "una tarjeta por PR de la muestra", len(artifacts.sample_df)),
        (
            "Tarjetas listas para card sorting",
            "guardia de calidad human_comment_count > 0",
            len(artifacts.cards_df),
        ),
        ("Plantilla manual", "archivo para categorizacion manual", len(artifacts.template_df)),
    ]

    previous = None
    records = []
    for step, criterion, count in rows:
        records.append(
            {
                "paso": step,
                "criterio": criterion,
                "total": count,
                "retencion_vs_universo": count / total,
                "retencion_vs_paso_anterior": 1.0 if previous is None else count / previous,
            }
        )
        previous = count
    return pd.DataFrame(records)


def build_agent_distribution(artifacts: FlowArtifacts) -> pd.DataFrame:
    return (
        pd.DataFrame(
            {
                "poblacion_antes_de_estratificar": pd.Series(
                    artifacts.sampling_summary["stratum_sizes"]
                ),
                "muestra_estratificada": pd.Series(artifacts.sampling_summary["quotas"]),
                "tarjetas_finales": artifacts.cards_df["agent"].value_counts(),
            }
        )
        .fillna(0)
        .astype(int)
        .sort_values("poblacion_antes_de_estratificar", ascending=False)
    )


def build_preparation_flow(artifacts: FlowArtifacts) -> pd.DataFrame:
    summary = artifacts.preparation_summary
    return pd.DataFrame(
        [
            {
                "paso": "Tarjetas candidatas",
                "criterio": "PRs de la muestra antes de la guardia de calidad",
                "filas": summary["source_card_count"],
            },
            {
                "paso": "Tarjetas listas",
                "criterio": summary["filter_rule"],
                "filas": summary["card_count"],
            },
            {
                "paso": "Descartes",
                "criterio": "sin comentarios humanos detectados en evidencia",
                "filas": summary["filtered_out_without_human_comments"],
            },
        ]
    )


def build_evidence_tables(artifacts: FlowArtifacts):
    summary = artifacts.preparation_summary
    evidence = pd.DataFrame(
        summary["evidence_source_counts"].items(),
        columns=["fuente_evidencia", "tarjetas"],
    ).sort_values("tarjetas", ascending=False)
    review_states = pd.DataFrame(
        summary["review_state_counts"].items(),
        columns=["estado_review", "tarjetas"],
    ).sort_values("tarjetas", ascending=False)
    return evidence, review_states


def build_outputs_flow(artifacts: FlowArtifacts) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "artefacto": "Tarjetas con evidencia",
                "ruta": relative_path(artifacts.cards_csv_path, artifacts.root),
                "filas": len(artifacts.cards_df),
            },
            {
                "artefacto": "Plantilla manual",
                "ruta": relative_path(artifacts.template_csv_path, artifacts.root),
                "filas": len(artifacts.template_df),
            },
        ]
    )


def build_template_preview(artifacts: FlowArtifacts) -> pd.DataFrame:
    trace_columns = ["card_id", "pr_id", "pr_state", "merged", "repo_id", "html_url"]
    manual_columns = [
        "resumen_justificacion_categoria",
        "horas_creacion_a_primera_aprobacion",
        "horas_creacion_a_merge",
        "horas_creacion_a_aceptacion",
        "fuente_tiempo_aceptacion",
        "categoria_retrabajo_pre_merge",
    ]
    available_columns = [
        column
        for column in [*trace_columns, *manual_columns]
        if column in artifacts.template_df.columns
    ]
    return artifacts.template_df[available_columns].head()


def validate_flow(artifacts: FlowArtifacts) -> str:
    summary = artifacts.sampling_summary
    filter_counts = summary["population_filter_counts"]

    assert summary["population_mode"] == "merged-after-rework"
    assert summary["requested_strata_fields"] == ["agent"]
    assert summary["used_strata_fields"] == ["agent"]
    assert (
        summary["population_size"]
        == filter_counts["merged_with_additional_commits_and_human_comments"]
    )
    assert summary["population_distributions"]["population_case_type"] == {
        "merged_after_rework": summary["population_size"]
    }
    assert summary["sample_distributions"]["population_case_type"] == {
        "merged_after_rework": len(artifacts.sample_df)
    }
    assert len(artifacts.sample_df) == summary["sample_size"] == 300
    assert (pd.to_numeric(artifacts.sample_df["commit_count"], errors="raise") > 1).all()
    assert (
        pd.to_numeric(artifacts.sample_df["human_comment_count"], errors="raise") > 0
    ).all()
    assert (
        len(artifacts.cards_df)
        == artifacts.preparation_summary["card_count"]
        == len(artifacts.template_df)
    )
    assert artifacts.preparation_summary["source_card_count"] == len(artifacts.sample_df)
    assert artifacts.preparation_summary["filtered_out_without_human_comments"] == 0
    assert (pd.to_numeric(artifacts.cards_df["human_comment_count"], errors="raise") > 0).all()
    assert list(artifacts.template_df.columns) == MANUAL_TEMPLATE_FIELDS
    assert MANUAL_TEMPLATE_FIELDS[-1] == "categoria_retrabajo_pre_merge"
    assert artifacts.template_df["categoria_retrabajo_pre_merge"].fillna("").eq("").all()
    assert pd.to_numeric(
        artifacts.template_df["horas_creacion_a_merge"], errors="coerce"
    ).notna().all()
    assert pd.to_numeric(
        artifacts.template_df["horas_creacion_a_aceptacion"], errors="coerce"
    ).notna().all()
    assert artifacts.template_df["fuente_tiempo_aceptacion"].isin(
        {"primera_review_aprobada", "merge_sin_review_aprobada"}
    ).all()
    return "Validaciones completadas"
