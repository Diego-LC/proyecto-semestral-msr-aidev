#!/usr/bin/env python3
"""Build a separate, evidence-based Codex classification draft for human review."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


DEFAULT_CARDS_CSV = Path(
    "exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510.csv"
)
DEFAULT_JAVIER_CSV = Path(
    "exploration/aidev/taxonomy/initial/merged_after_rework_manual_categories_Javier.csv"
)
DEFAULT_OUTPUT_CSV = Path(
    "exploration/aidev/preparation/outputs/merged_after_rework_codex_review_manual_categories.csv"
)

OUTPUT_FIELDS = [
    "card_id",
    "pr_id",
    "agent",
    "html_url",
    "evidence_source",
    "context_summary",
    "evidence_text",
    "all_evidence_text",
    "cita_textual_retrabajo",
    "categoria_original_javier",
    "motivo_abierto_codex",
    "categoria_padre_propuesta",
    "subcategoria_propuesta",
    "justificacion_breve",
    "confianza_codex",
    "motivo_duda",
    "decision_humana",
    "categoria_padre_final",
    "subcategoria_final",
]


@dataclass(frozen=True)
class Rule:
    parent: str
    subcategory: str
    motive: str
    explanation: str
    patterns: Tuple[str, ...]
    priority: int = 0


RULES: Tuple[Rule, ...] = (
    Rule(
        "proceso_gobernanza",
        "cumplimiento_cla_dco",
        "falta de cumplimiento de requisitos de contribucion",
        "La evidencia exige completar un requisito formal de contribucion antes de integrar el PR.",
        (r"cla assistant", r"contributor license agreement", r"not_signed", r"signed-off-by", r"\bdco\b"),
        8,
    ),
    Rule(
        "validacion_calidad_ci",
        "fallos_tests_ci",
        "fallos en pruebas o validaciones automatizadas",
        "La evidencia reporta pruebas o checks fallidos que requieren correccion antes del merge.",
        (
            r"tests? (?:are |is |were )?failing",
            r"test failure",
            r"failures? in \[?build",
            r"\bfailed tests?\b",
            r"\bci (?:is )?fail",
            r"check(?:s)? (?:is |are )?fail",
            r"does not pass",
            r"make (?:the )?tests? pass",
            r"fix (?:the )?(?:unit )?tests?",
            r"timeout on",
        ),
        8,
    ),
    Rule(
        "validacion_calidad_ci",
        "lint_formato_analisis_estatico",
        "incumplimiento de lint, formato o analisis estatico",
        "La evidencia solicita corregir reglas de lint, formato o analisis estatico.",
        (
            r"\blint(?:er|ing)?\b",
            r"formatting",
            r"format check",
            r"prettier",
            r"ruff",
            r"clippy",
            r"eslint",
            r"style check",
            r"remove this.*allow\(deprecated\)",
        ),
        7,
    ),
    Rule(
        "validacion_calidad_ci",
        "cobertura_o_pruebas_insuficientes",
        "cobertura o pruebas insuficientes",
        "La evidencia solicita agregar o ampliar pruebas para validar el cambio.",
        (
            r"add (?:a |more )?(?:unit |integration |e2e )?tests?",
            r"missing tests?",
            r"test coverage",
            r"add coverage",
            r"needs? (?:a |more )?tests?",
            r"please test",
            r"test cases? for",
            r"cover this case",
        ),
        6,
    ),
    Rule(
        "documentacion_descripcion",
        "descripcion_pr_incorrecta_o_incompleta",
        "descripcion del PR incorrecta, confusa o incompleta",
        "La evidencia pide corregir la descripcion o comunicacion del alcance del PR.",
        (
            r"pr description",
            r"pull request description",
            r"description (?:is |seems )?(?:confusing|incorrect|incomplete|wrong)",
            r"update (?:the )?description",
            r"describe (?:the )?changes",
            r"changelog",
            r"release note",
        ),
        7,
    ),
    Rule(
        "documentacion_descripcion",
        "documentacion_codigo_o_usuario",
        "documentacion tecnica o de usuario requiere ajustes",
        "La evidencia solicita corregir o completar documentacion asociada al cambio.",
        (
            r"\breadme\b",
            r"documentation comment",
            r"docs? (?:are |is )?(?:wrong|incorrect|missing|outdated)",
            r"update (?:the )?docs?",
            r"document this",
            r"missing documentation",
            r"typo",
            r"spelling",
            r"four bytes comments",
        ),
        4,
    ),
    Rule(
        "proceso_gobernanza",
        "dependencia_o_orden_de_merge",
        "dependencia externa u orden de integracion pendiente",
        "La evidencia indica que el PR depende de otro cambio o de un orden de despliegue/merge.",
        (
            r"should be merged (?:in )?first",
            r"needs? to be merged first",
            r"before this pr",
            r"blocked by",
            r"depends on",
            r"specific order for shipping",
            r"retro-compatible",
            r"see #[0-9]+",
        ),
        7,
    ),
    Rule(
        "proceso_gobernanza",
        "revision_o_aprobacion_pendiente",
        "revision, aprobacion o coordinacion humana pendiente",
        "La evidencia muestra que el avance depende de revision, aprobacion o coordinacion adicional.",
        (
            r"needs? (?:a |another )?review",
            r"request (?:a )?review",
            r"code ?owners?",
            r"maintainer approval",
            r"waiting for",
            r"why was it closed",
            r"reopen",
        ),
        5,
    ),
    Rule(
        "configuracion_integracion",
        "ci_workflows_y_automatizacion",
        "configuracion de CI, workflows o automatizacion requiere ajustes",
        "La evidencia identifica un problema en workflows, checks o automatizacion del repositorio.",
        (
            r"\.github/workflows",
            r"github actions",
            r"workflow",
            r"buildkite",
            r"coveralls",
            r"codecov",
            r"install the .*codecov app",
            r"autoformat",
            r"pre-commit",
        ),
        5,
    ),
    Rule(
        "dependencias_versionado",
        "versiones_o_dependencias",
        "dependencias o versiones requieren ajuste",
        "La evidencia solicita actualizar, restringir o reutilizar una dependencia o version.",
        (
            r"latest (?:release|version)",
            r"dependency",
            r"dependencies",
            r"add .* as a dependency",
            r"version (?:is |should|must|needs)",
            r"upgrade",
            r"downgrade",
            r"pin (?:the )?version",
            r"package version",
            r"sdk version",
        ),
        6,
    ),
    Rule(
        "seguridad_permisos",
        "seguridad_autorizacion_o_validacion",
        "riesgo de seguridad, permisos o validacion de confianza",
        "La evidencia solicita reforzar permisos, autorizacion, validacion o manejo seguro de datos.",
        (
            r"security",
            r"vulnerab",
            r"permission",
            r"authorization",
            r"authentication",
            r"secret",
            r"sanitize",
            r"injection",
            r"untrusted",
            r"hmac",
            r"rls",
        ),
        6,
    ),
    Rule(
        "arquitectura_diseno",
        "reutilizacion_y_duplicacion",
        "duplicacion o falta de reutilizacion",
        "La evidencia pide reutilizar componentes existentes y eliminar duplicacion innecesaria.",
        (
            r"duplicat(?:e|ed|ion)",
            r"re-?use (?:the |its |existing)",
            r"already exists",
            r"do not reinvent",
            r"avoid adding.*new",
        ),
        7,
    ),
    Rule(
        "arquitectura_diseno",
        "diseno_api_modelo_o_interfaz",
        "diseno de API, modelo o interfaz requiere revision",
        "La evidencia cuestiona la forma de la API, modelo, contrato o abstraccion implementada.",
        (
            r"public api",
            r"api design",
            r"interface",
            r"signature",
            r"parameter",
            r"return type",
            r"breaking change",
            r"backward compat",
            r"should (?:this|it) be (?:a |an )?(?:class|function|method|property|option)",
            r"better (?:to|as|off)",
        ),
        4,
    ),
    Rule(
        "arquitectura_diseno",
        "alcance_o_sobrecodigo",
        "alcance excesivo o implementacion innecesaria",
        "La evidencia solicita reducir el alcance o eliminar codigo que no corresponde al cambio.",
        (
            r"out of scope",
            r"scope (?:is )?too",
            r"unnecessary",
            r"not needed",
            r"remove this",
            r"better off without",
            r"separate pr",
            r"keep this pr",
        ),
        5,
    ),
    Rule(
        "mantenimiento_refactor",
        "limpieza_simplificacion_o_nombres",
        "limpieza, simplificacion o nombres requieren ajuste",
        "La evidencia solicita simplificar, renombrar o eliminar elementos innecesarios.",
        (
            r"rename",
            r"simplif",
            r"clean ?up",
            r"unused",
            r"dead code",
            r"remove this",
            r"no import needed",
            r"extract (?:this|it)",
            r"refactor",
        ),
        4,
    ),
    Rule(
        "implementacion_logica",
        "compatibilidad_o_migracion",
        "compatibilidad entre plataformas, versiones o migraciones",
        "La evidencia reporta una incompatibilidad o necesidad de migracion/retrocompatibilidad.",
        (
            r"does not work on",
            r"tested on .* does not",
            r"compatib",
            r"migration",
            r"migrate",
            r"windows",
            r"macos",
            r"linux",
            r"platform",
            r"deprecated",
        ),
        5,
    ),
    Rule(
        "implementacion_logica",
        "manejo_errores_y_validacion_inputs",
        "manejo de errores, nulos o validacion de entradas",
        "La evidencia identifica casos borde, entradas invalidas o manejo de errores insuficiente.",
        (
            r"error handling",
            r"handle (?:the )?(?:error|exception|failure|null|undefined)",
            r"validation",
            r"validate",
            r"invalid input",
            r"edge case",
            r"null",
            r"undefined",
            r"exception",
            r"fallback",
        ),
        5,
    ),
    Rule(
        "implementacion_logica",
        "rendimiento_concurrencia_o_recursos",
        "rendimiento, concurrencia o manejo de recursos",
        "La evidencia identifica problemas de rendimiento, concurrencia, memoria o recursos.",
        (
            r"performance",
            r"concurren",
            r"race condition",
            r"thread",
            r"async",
            r"memory leak",
            r"resource leak",
            r"timeout",
            r"buffer",
            r"slow",
        ),
        5,
    ),
    Rule(
        "implementacion_logica",
        "ui_ux_y_comportamiento_frontend",
        "comportamiento de interfaz o experiencia de usuario",
        "La evidencia solicita corregir comportamiento visual, interaccion o experiencia de usuario.",
        (
            r"\bui\b",
            r"\bux\b",
            r"frontend",
            r"render",
            r"button",
            r"dialog",
            r"toast",
            r"layout",
            r"screen",
            r"click",
        ),
        3,
    ),
    Rule(
        "implementacion_logica",
        "correccion_funcional",
        "comportamiento funcional incorrecto o incompleto",
        "La evidencia indica que la implementacion no resuelve correctamente el comportamiento esperado.",
        (
            r"does not fix",
            r"doesn't fix",
            r"does not work",
            r"not working",
            r"incorrect",
            r"wrong",
            r"bug",
            r"broken",
            r"fails? to",
            r"should instead",
            r"can you (?:please )?fix",
            r"needs? to (?:be )?fix",
            r"issue has been updated",
        ),
        3,
    ),
)

INSUFFICIENT_PATTERNS = (
    r"^\s*lgtm[.!\s]*$",
    r"^\s*looks good to me[.!\s]*$",
    r"^\s*approved[.!\s]*$",
    r"^\s*fyi\s+@[\w-]+[.!\s]*$",
    r"^\s*@[\w-]+\s+review[.!\s]*$",
    r"^\s*see #[0-9]+[.!\s]*$",
)


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def normalized(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


NON_ACTIONABLE_PATTERNS = (
    r"^\s*lgtm[.!\s]*$",
    r"^\s*looks good(?: to me)?[.!\s]*$",
    r"^\s*approved[.!\s]*$",
    r"^\s*thank(?:s| you)[^?]*[.!\s]*$",
    r"checks? have passed.*no issues",
    r"working as intended.*looks fine",
    r"^\s*@[\w-]+\s+review[.!\s]*$",
)


def feedback_text(text: str | None, diff_hunk: str | None = None) -> str:
    cleaned = normalized(text)
    hunk = normalized(diff_hunk)
    if hunk and hunk in cleaned:
        cleaned = cleaned.split(hunk, 1)[1].strip()
    return re.sub(r"^File:\s*.+?\s+Diff context:\s*", "", cleaned).strip()


def evidence_parts(card: Dict[str, str]) -> Tuple[Tuple[str, str, int], ...]:
    parts: List[Tuple[str, str, int]] = []
    primary = feedback_text(card.get("evidence_raw_text"), card.get("evidence_diff_hunk"))
    if primary:
        parts.append(("evidence_primary", primary, 8))
    try:
        evidences = json.loads(card.get("all_evidence_json") or "[]")
    except json.JSONDecodeError:
        evidences = []
    seen = {primary}
    for index, evidence in enumerate(evidences):
        text = feedback_text(evidence.get("text"), evidence.get("diff_hunk"))
        if not text or text in seen:
            continue
        seen.add(text)
        parts.append((f"evidence_{index}", text, 2))
    return tuple(parts)


def rule_score(rule: Rule, card: Dict[str, str]) -> Tuple[int, List[str]]:
    best_score = 0
    best_matches: List[str] = []
    for field, value, weight in evidence_parts(card):
        text = normalized(value).casefold()
        if not text or any(re.search(pattern, text) for pattern in NON_ACTIONABLE_PATTERNS):
            continue
        field_matches = [pattern for pattern in rule.patterns if re.search(pattern, text)]
        if field_matches:
            score = rule.priority + weight + min(2, len(field_matches) - 1)
            if score > best_score:
                best_score = score
                best_matches = [f"{field}:{pattern}" for pattern in field_matches]
    return best_score, best_matches


def is_insufficient(card: Dict[str, str]) -> bool:
    actionable = []
    for _, value, _ in evidence_parts(card):
        text = normalized(value).casefold()
        if text and not any(re.search(pattern, text) for pattern in NON_ACTIONABLE_PATTERNS):
            actionable.append(text)
    return not actionable or all(
        any(re.fullmatch(pattern, text) for pattern in INSUFFICIENT_PATTERNS)
        for text in actionable
    )


def classify(card: Dict[str, str]) -> Tuple[Rule | None, int, int, List[str]]:
    if is_insufficient(card):
        return None, 0, 0, []
    scored_rules = []
    for rule in RULES:
        score, matches = rule_score(rule, card)
        scored_rules.append((score, rule, matches))
    scored = sorted(
        scored_rules,
        key=lambda item: (item[0], item[1].priority),
        reverse=True,
    )
    best_score, best_rule, matches = scored[0]
    second_score = scored[1][0]
    if best_score < 5:
        return None, best_score, second_score, matches
    return best_rule, best_score, second_score, matches


def quote_for(card: Dict[str, str], rule: Rule | None, max_length: int = 600) -> str:
    parts = evidence_parts(card)
    text = next((value for _, value, _ in parts if value), card.get("evidence_text", ""))
    selected_field = parts[0][0] if parts else "evidence_primary"
    if rule is not None:
        for field, candidate, _ in parts:
            if any(re.search(pattern, candidate, flags=re.IGNORECASE) for pattern in rule.patterns):
                selected_field = field
                text = candidate
                break
    if len(text) <= max_length:
        return text
    if selected_field != "evidence_primary":
        return text[-max_length:]
    if rule is not None:
        for pattern in rule.patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                start = max(0, match.start() - max_length // 3)
                end = min(len(text), start + max_length)
                return text[start:end]
    return text[:max_length]


def confidence_for(card: Dict[str, str], best: int, second: int, rule: Rule | None) -> Tuple[str, str]:
    if rule is None:
        return "baja", "La evidencia principal no expresa un motivo de retrabajo suficientemente especifico."
    quality = int(float(card.get("evidence_quality_score") or 0))
    margin = best - second
    if best >= 15 and margin >= 4 and quality >= 7:
        return "alta", ""
    if best >= 9 and margin >= 2:
        return "media", "Revisar la categoria porque existen senales cercanas o contexto parcialmente ambiguo."
    return "baja", "Revisar evidencia completa: la regla ganadora tiene poco margen sobre alternativas."


def build_row(card: Dict[str, str], javier: Dict[str, str]) -> Dict[str, str]:
    rule, best, second, matches = classify(card)
    if rule is None:
        parent = "evidencia_insuficiente"
        subcategory = "motivo_no_identificable"
        motive = "evidencia sin motivo de retrabajo identificable"
        explanation = (
            "La evidencia disponible no permite atribuir un motivo de retrabajo defendible; "
            "requiere revision humana del contexto completo."
        )
    else:
        parent = rule.parent
        subcategory = rule.subcategory
        motive = rule.motive
        explanation = rule.explanation
    confidence, doubt = confidence_for(card, best, second, rule)
    if matches and confidence != "alta":
        doubt = f"{doubt} Senales: {', '.join(matches[:3])}".strip()
    return {
        "card_id": card.get("card_id", ""),
        "pr_id": card.get("pr_id", ""),
        "agent": card.get("agent", ""),
        "html_url": card.get("html_url", ""),
        "evidence_source": card.get("evidence_source", ""),
        "context_summary": card.get("context_summary", ""),
        "evidence_text": card.get("evidence_text", ""),
        "all_evidence_text": card.get("all_evidence_text", ""),
        "cita_textual_retrabajo": quote_for(card, rule),
        "categoria_original_javier": javier.get("categoria_retrabajo_pre_merge", ""),
        "motivo_abierto_codex": motive,
        "categoria_padre_propuesta": parent,
        "subcategoria_propuesta": subcategory,
        "justificacion_breve": explanation,
        "confianza_codex": confidence,
        "motivo_duda": doubt,
        "decision_humana": "pendiente",
        "categoria_padre_final": "",
        "subcategoria_final": "",
    }


def validate(rows: Sequence[Dict[str, str]], cards: Sequence[Dict[str, str]]) -> None:
    assert len(rows) == 300, f"Expected 300 rows, got {len(rows)}"
    assert len({row["card_id"] for row in rows}) == 300, "card_id values must be unique"
    assert all(row["decision_humana"] == "pendiente" for row in rows)
    required = (
        "categoria_padre_propuesta",
        "subcategoria_propuesta",
        "justificacion_breve",
        "confianza_codex",
        "cita_textual_retrabajo",
    )
    assert all(all(row[field].strip() for field in required) for row in rows)
    cards_by_id = {card["card_id"]: card for card in cards}
    for row in rows:
        card = cards_by_id[row["card_id"]]
        haystack = normalized(" ".join(value for _, value, _ in evidence_parts(card)))
        assert normalized(row["cita_textual_retrabajo"]) in haystack, row["card_id"]


def write_rows(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cards-csv", type=Path, default=DEFAULT_CARDS_CSV)
    parser.add_argument("--javier-csv", type=Path, default=DEFAULT_JAVIER_CSV)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cards = read_rows(args.cards_csv)
    javier_rows = read_rows(args.javier_csv)
    javier_by_card = {row["card_id"]: row for row in javier_rows}
    rows = [build_row(card, javier_by_card.get(card["card_id"], {})) for card in cards]
    validate(rows, cards)
    if not args.dry_run:
        write_rows(args.output_csv, rows)
    counts: Dict[str, int] = {}
    for row in rows:
        key = f"{row['categoria_padre_propuesta']}/{row['subcategoria_propuesta']}"
        counts[key] = counts.get(key, 0) + 1
    print(f"rows={len(rows)} dry_run={args.dry_run} output={args.output_csv}")
    for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"{count:3d} {key}")


if __name__ == "__main__":
    main()
