#!/usr/bin/env python3
"""Validate Diego's taxonomy against complete evidence and optionally apply it."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


DEFAULT_DIEGO_CSV = Path(
    "exploration/aidev/taxonomy/initial/merged_after_rework_manual_categories_diego.csv"
)
DEFAULT_CARDS_CSV = Path(
    "exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510.csv"
)
DEFAULT_AUDIT_CSV = Path(
    "exploration/aidev/taxonomy/analysis/merged_after_rework_diego_taxonomy_validation.csv"
)

VALIDATION_FIELDS = [
    "veredicto_evidencia_completa",
    "categoria_sugerida_evidencia_completa",
    "confianza_validacion",
    "origen_veredicto",
    "justificacion_validacion",
    "cita_causal_pre_merge",
    "fuente_cita_causal",
    "fecha_cita_causal",
    "evidencias_textuales_pre_merge",
    "evidencias_con_senal_causal",
    "puntaje_categoria_actual",
    "puntaje_categoria_sugerida",
    "evidencia_seleccionada_es_pre_merge",
    "requiere_revision_humana",
]

APPLIED_CONFIDENCE_CHOICES = ("baja", "media", "alta")


CATEGORY_PATTERNS: Dict[str, Tuple[str, ...]] = {
    "documentacion_o_descripcion_incompleta": (
        r"\bpr description\b",
        r"\bpull request description\b",
        r"\bdescription\b.{0,40}\b(?:wrong|incorrect|confusing|incomplete|missing)\b",
        r"\b(?:update|fix|change|add|remove)\b.{0,35}\b(?:docs?|documentation|readme|changelog|release notes?|title|description)\b",
        r"\b(?:docs?|documentation|readme|swagger|changelog|release notes?)\b.{0,35}\b(?:missing|incorrect|wrong|outdated|incomplete)\b",
        r"\b(?:doc changes?|typo|spelling|wording)\b",
        r"\b(?:update|fix|change|add|remove)\b.{0,25}\b(?:comment|message)\b",
    ),
    "lint_formato_o_estilo": (
        r"\b(?:lint|linter|eslint|ruff|clippy|prettier|checkstyle)\b",
        r"\b(?:format|formatting|style|indentation|whitespace|blank line)\b",
        r"\b(?:uppercase|lowercase|casing)\b.{0,30}\b(?:pattern|style|consistent|consistency)\b",
        r"\b\.editorconfig\b",
    ),
    "pruebas_faltantes_o_insuficientes": (
        r"\b(?:add|include|write|need|needs|missing|expand)\b.{0,40}\b(?:test|tests|coverage|test case|test cases)\b",
        r"\b(?:test|tests|coverage)\b.{0,35}\b(?:missing|insufficient|needed|required|not covered)\b",
        r"\bcover (?:this|that|the) (?:case|scenario|path)\b",
    ),
    "fallos_ci_build_o_tests": (
        r"\b(?:ci|build|check|checks|test|tests|compilation|compiler)\b.{0,45}\b(?:fail|failed|failing|failure|broken|error|timeout)\b",
        r"\b(?:fail|failed|failing|failure|broken|error|timeout)\b.{0,45}\b(?:ci|build|check|checks|test|tests|compilation|compiler)\b",
        r"\bdoes not pass\b",
    ),
    "configuracion_ci_o_automatizacion": (
        r"\b(?:workflow|github actions|buildkite|codecov|coveralls|pre-commit|pipeline|deployment|deploy)\b.{0,45}\b(?:configure|configuration|change|update|fix|permission|script|job|step)\b",
        r"\b(?:configure|configuration|change|update|fix|permission|script|job|step)\b.{0,45}\b(?:workflow|github actions|buildkite|codecov|coveralls|pre-commit|pipeline|deployment|deploy)\b",
        r"\.github/workflows",
        r"\bpowershell\b.{0,30}\bbash\b",
    ),
    "requisito_formal_o_gobernanza": (
        r"\b(?:cla|contributor license agreement|dco|signed-off-by)\b",
        r"\b(?:sign|signed)\b.{0,30}\b(?:commit|commits|agreement|cla)\b",
        r"\b(?:license header|copyright header)\b",
    ),
    "diseno_api_modelo_o_arquitectura": (
        r"\b(?:api design|public api|interface|signature|return type|contract|abstraction|architecture)\b",
        r"\b(?:should|could|better to)\b.{0,35}\b(?:class|function|method|property|parameter|interface|type|model)\b",
        r"\b(?:behavior|behaviour) change\b",
    ),
    "reduccion_alcance_o_sobrecodigo": (
        r"\b(?:out of scope|scope too|separate pr|not needed|unnecessary|better off without)\b",
        r"\b(?:remove|delete|drop)\b.{0,45}\b(?:file|code|method|function|option|change|logic|feature|implementation)\b",
        r"\b(?:avoid|without)\b.{0,25}\bunnecessary\b",
    ),
    "dependencias_o_versionado": (
        r"\b(?:dependency|dependencies|package|sdk)\b.{0,40}\b(?:version|upgrade|downgrade|pin|latest|release|update)\b",
        r"\b(?:version|upgrade|downgrade|pin|latest release)\b.{0,40}\b(?:dependency|dependencies|package|sdk|release)\b",
        r"\bupcoming version\b",
    ),
    "correccion_funcional": (
        r"\b(?:does not|doesn't|did not|didn't|won't|cannot|can't)\b.{0,35}\b(?:work|fix|return|handle|produce|resolve)\b",
        r"\b(?:wrong|incorrect|broken|bug|regression|unintentionally changed)\b",
        r"\b(?:should|must|needs to)\b.{0,35}\b(?:return|work|behave|use|run|call|set|match)\b",
        r"\bstill (?:did not|didn't|does not|doesn't)\b",
    ),
    "ui_ux_o_frontend": (
        r"\b(?:ui|ux|frontend|button|dialog|layout|screen|click|render|visual|styling|caption|field placement)\b",
        r"\b(?:move|place|display|show|hide|align|click)\b.{0,40}\b(?:field|button|dialog|screen|layout|caption|ui)\b",
    ),
    "duplicacion_o_falta_de_reutilizacion": (
        r"\b(?:duplicate|duplicated|duplication)\b",
        r"\b(?:reuse|re-use)\b.{0,35}\b(?:existing|same|component|function|method|code|logic)\b",
        r"\b(?:already exists|instead of having [0-9]+|one .* instead of)\b",
    ),
    "manejo_errores_o_casos_borde": (
        r"\b(?:error handling|handle error|handle the error|exception|fallback|invalid input|edge case|null|undefined)\b",
        r"\b(?:if not|if no|when .* fails?)\b.{0,40}\b(?:return an error|fail|default value|handle)\b",
        r"\bpreserv(?:e|ing) the original error\b",
    ),
    "refactor_limpieza_o_nombres": (
        r"\b(?:rename|refactor|cleanup|clean up|simplify|extract|move)\b",
        r"\b(?:unused|dead code|informative variable name|readability|maintainability)\b",
    ),
    "seguridad_permisos_o_validacion": (
        r"\b(?:security|vulnerability|permission|authorization|authentication|secret|sanitize|injection|untrusted|hmac)\b",
        r"\b(?:access|authenticated users?)\b.{0,40}\b(?:only|permission|authorize|restrict|member)\b",
    ),
    "rendimiento_concurrencia_o_recursos": (
        r"\b(?:performance|concurrency|concurrent|race condition|thread|memory leak|resource leak|rate limit|latency)\b",
        r"\b(?:slow|timeout)\b.{0,35}\b(?:operation|request|resource|performance)\b",
    ),
    "compatibilidad_o_migracion": (
        r"\b(?:backward compatible|backwards compatible|compatibility|incompatible|migration|migrate|deprecated|platform)\b",
        r"\b(?:windows|linux|macos)\b.{0,35}\b(?:support|work|fail|compatible)\b",
    ),
    "implementacion_incompleta_o_cambio_omitido": (
        r"\b(?:forgot|missing|did not|didn't|not committed|not included)\b.{0,45}\b(?:file|change|implementation|code|commit|propagate|apply)\b",
        r"\b(?:also|same change)\b.{0,35}\b(?:apply|update|change)\b",
        r"\b(?:regenerate|generate)\b.{0,40}\bcommit\b",
    ),
    "dependencia_u_orden_de_merge": (
        r"\b(?:blocked by|depends on|dependency on)\b",
        r"\b(?:merge|merged|ship|shipping|deploy)\b.{0,35}\b(?:first|before|order)\b",
        r"\b(?:first|before|order)\b.{0,35}\b(?:merge|merged|ship|shipping|deploy)\b",
    ),
    "revision_o_aprobacion_pendiente": (
        r"\b(?:needs|need|request|waiting for)\b.{0,35}\b(?:review|approval|maintainer|code owner)\b",
        r"\b(?:codeowners?|maintainer approval)\b",
    ),
}

CATEGORY_REASONS = {
    "configuracion_ci_o_automatizacion": (
        "la configuracion de CI, workflows o automatizacion necesitaba ajustes"
    ),
    "compatibilidad_o_migracion": (
        "el cambio requeria ajustes de compatibilidad o migracion"
    ),
    "correccion_funcional": (
        "la implementacion no producia completamente el comportamiento esperado"
    ),
    "dependencia_u_orden_de_merge": (
        "el PR dependia de otro cambio o de un orden de integracion previo"
    ),
    "dependencias_o_versionado": (
        "las dependencias o versiones utilizadas necesitaban correccion"
    ),
    "diseno_api_modelo_o_arquitectura": (
        "el diseno de la API, el modelo o la arquitectura necesitaba revision"
    ),
    "documentacion_o_descripcion_incompleta": (
        "la documentacion, descripcion o comunicacion del cambio era incompleta o incorrecta"
    ),
    "duplicacion_o_falta_de_reutilizacion": (
        "el cambio duplicaba logica o no reutilizaba componentes existentes"
    ),
    "evidencia_insuficiente": (
        "no se encontro evidencia textual suficiente para explicar la no aprobacion inmediata"
    ),
    "fallos_ci_build_o_tests": (
        "habia fallos observables en CI, build o pruebas que debian resolverse"
    ),
    "implementacion_incompleta_o_cambio_omitido": (
        "faltaba completar, propagar o incluir una parte necesaria del cambio"
    ),
    "lint_formato_o_estilo": (
        "el cambio incumplia reglas de lint, formato o estilo del proyecto"
    ),
    "manejo_errores_o_casos_borde": (
        "faltaba manejar errores, entradas invalidas, nulos o casos borde"
    ),
    "pruebas_faltantes_o_insuficientes": (
        "faltaban pruebas o cobertura suficiente para validar el cambio"
    ),
    "reduccion_alcance_o_sobrecodigo": (
        "se pidio reducir el alcance o eliminar implementacion innecesaria"
    ),
    "refactor_limpieza_o_nombres": (
        "se solicitaron ajustes de limpieza, simplificacion, estructura o nombres"
    ),
    "rendimiento_concurrencia_o_recursos": (
        "habia problemas de rendimiento, concurrencia o manejo de recursos"
    ),
    "requisito_formal_o_gobernanza": (
        "faltaba cumplir un requisito formal de contribucion o gobernanza"
    ),
    "revision_o_aprobacion_pendiente": (
        "faltaba una revision, aprobacion o coordinacion humana requerida"
    ),
    "seguridad_permisos_o_validacion": (
        "faltaban controles de seguridad, permisos, autorizacion o validacion de confianza"
    ),
    "ui_ux_o_frontend": (
        "el comportamiento o la presentacion de la interfaz necesitaba correccion"
    ),
}

NON_CAUSAL_PATTERNS = (
    r"^\s*(?:lgtm|approved|looks good|fix looks good)[.! ]*$",
    r"^\s*(?:thanks|thank you)\b",
    r"^\s*file:\s+.+\s+[👍✅]+\s*$",
    r"^\s*[👍✅🎉👏]+\s*$",
    r"^\s*here'?s what you should know:",
    r"^\s*pull request overview\b",
    r"^\s*summary\b",
)

# Decisions from manual review of disagreements between the category and the
# complete pre-merge evidence. These overrides are intentionally explicit so
# the audit remains reproducible instead of hiding contextual judgments.
VALIDATION_OVERRIDES: Dict[str, Tuple[str, str, str, str]] = {
    "3076981888-A": (
        "parcial",
        "documentacion_o_descripcion_incompleta",
        "media",
        "La evidencia pide completar o corregir informacion del PR; el componente formal existe, pero no es la razon principal.",
    ),
    "3084021151-A": (
        "si",
        "dependencias_o_versionado",
        "alta",
        "La revision solicita ajustar explicitamente una version o dependencia antes de integrar.",
    ),
    "3084861928-A": (
        "parcial",
        "compatibilidad_o_migracion",
        "media",
        "La evidencia incluye compatibilidad o migracion, aunque tambien aparecen casos borde y manejo de nulos.",
    ),
    "3086540771-A": (
        "no",
        "dependencias_o_versionado",
        "alta",
        "El bloqueo se relaciona con la version o actualizacion de una dependencia, no con la categoria asignada.",
    ),
    "3104405109-A": (
        "no",
        "diseno_api_modelo_o_arquitectura",
        "alta",
        "La solicitud cuestiona la interfaz o estructura de la solucion y requiere un cambio de diseno.",
    ),
    "3166697799-A": (
        "no",
        "pruebas_faltantes_o_insuficientes",
        "alta",
        "La revision exige cobertura para el cambio; la carencia demostrada es de pruebas.",
    ),
    "3169100701-A": (
        "no",
        "reduccion_alcance_o_sobrecodigo",
        "alta",
        "La evidencia solicita retirar logica innecesaria y reducir el alcance de la implementacion.",
    ),
    "3176217773-A": (
        "no",
        "fallos_ci_build_o_tests",
        "alta",
        "La evidencia reporta una comprobacion automatizada fallida que impide aceptar el PR.",
    ),
    "3190568208-A": (
        "no",
        "refactor_limpieza_o_nombres",
        "alta",
        "La solicitud concreta es renombrar o reorganizar codigo para mejorar claridad y mantenimiento.",
    ),
    "3192728541-A": (
        "parcial",
        "refactor_limpieza_o_nombres",
        "media",
        "La evidencia principal pide refactorizacion o renombre, aunque tambien solicita pruebas.",
    ),
    "3198732250-A": (
        "no",
        "refactor_limpieza_o_nombres",
        "alta",
        "La iteracion surge de una solicitud explicita de limpieza o refactorizacion.",
    ),
    "3222480219-A": (
        "no",
        "lint_formato_o_estilo",
        "alta",
        "La evidencia solicita un ajuste de formato o estilo, no el motivo indicado originalmente.",
    ),
    "3228390000-A": (
        "no",
        "documentacion_o_descripcion_incompleta",
        "alta",
        "El cambio requerido afecta texto o documentacion que debia corregirse antes del merge.",
    ),
    "3235469054-A": (
        "no",
        "correccion_funcional",
        "alta",
        "La revision identifica comportamiento incorrecto que requiere una correccion funcional.",
    ),
    "3135169379-A": (
        "no",
        "seguridad_permisos_o_validacion",
        "alta",
        "La evidencia cuestiona permisos, acceso o validacion de datos y apunta a seguridad.",
    ),
    "3184110162-A": (
        "no",
        "reduccion_alcance_o_sobrecodigo",
        "alta",
        "La revision identifica imports y mocks innecesarios que deben retirarse o simplificarse.",
    ),
    "3235036061-A": (
        "no",
        "manejo_errores_o_casos_borde",
        "alta",
        "La evidencia exige manejar un error o escenario limite que la implementacion omitio.",
    ),
    "2968159813-A": (
        "si",
        "reduccion_alcance_o_sobrecodigo",
        "alta",
        "La evidencia pide eliminar una parte innecesaria de la solucion antes de aceptarla.",
    ),
    "3029374639-A": (
        "no",
        "correccion_funcional",
        "alta",
        "El comentario describe una conducta incorrecta que debe repararse.",
    ),
    "3058723574-A": (
        "no",
        "fallos_ci_build_o_tests",
        "alta",
        "El PR queda pendiente por una falla concreta de build, CI o pruebas.",
    ),
    "3113332396-A": (
        "no",
        "reduccion_alcance_o_sobrecodigo",
        "alta",
        "La revision indica que una comprobacion es redundante por las reglas existentes y debe retirarse.",
    ),
    "3152123723-A": (
        "si",
        "evidencia_insuficiente",
        "alta",
        "Solo hay aprobacion y un mensaje condicional de automatizacion; no se demuestra una causa de retrabajo.",
    ),
    "3083568715-A": (
        "no",
        "requisito_formal_o_gobernanza",
        "alta",
        "El bloqueo observable es el CLA sin firmar; no hay una falla tecnica concreta demostrada.",
    ),
    "3084106426-A": (
        "no",
        "ui_ux_o_frontend",
        "alta",
        "La revision solicita corregir contraste y presentacion visual en modo claro.",
    ),
    "3119688458-A": (
        "si",
        "correccion_funcional",
        "alta",
        "La evidencia identifica una llamada con cantidad incorrecta de argumentos, una falla funcional.",
    ),
    "3153811253-A": (
        "no",
        "refactor_limpieza_o_nombres",
        "alta",
        "La solicitud es mover y reorganizar logica, por lo que corresponde a refactorizacion.",
    ),
    "3156412763-A": (
        "no",
        "correccion_funcional",
        "alta",
        "La evidencia indica que var! debe poder utilizarse en el nivel superior; existe una falla funcional concreta.",
    ),
    "3161958337-A": (
        "no",
        "ui_ux_o_frontend",
        "alta",
        "La revision cuestiona el tamano visual de una flecha, por lo que si existe evidencia de UI.",
    ),
    "3021989795-A": (
        "no",
        "documentacion_o_descripcion_incompleta",
        "alta",
        "Los comentarios piden corregir textos de error y una errata; hay evidencia textual suficiente.",
    ),
    "3213265669-A": (
        "no",
        "documentacion_o_descripcion_incompleta",
        "alta",
        "La evidencia solicita retirar una entrada y corregir una errata en documentacion o changelog.",
    ),
    "3095409522-A": (
        "si",
        "dependencia_u_orden_de_merge",
        "alta",
        "La aceptacion depende explicitamente de integrar otro cambio primero.",
    ),
    "3098938231-A": (
        "si",
        "manejo_errores_o_casos_borde",
        "alta",
        "La evidencia pide preservar o manejar correctamente el error original.",
    ),
    "3114898378-A": (
        "no",
        "configuracion_ci_o_automatizacion",
        "alta",
        "El cambio requerido corresponde a configuracion de workflow o automatizacion.",
    ),
    "3221925890-A": (
        "si",
        "manejo_errores_o_casos_borde",
        "alta",
        "La revision exige manejar un escenario de error o caso borde antes del merge.",
    ),
    "3261628283-A": (
        "no",
        "correccion_funcional",
        "alta",
        "La evidencia demuestra un comportamiento incorrecto que requiere correccion.",
    ),
    "3130792767-A": (
        "no",
        "correccion_funcional",
        "alta",
        "La solicitud corrige la logica o el resultado funcional de la implementacion.",
    ),
    "2941643405-A": (
        "si",
        "lint_formato_o_estilo",
        "alta",
        "La evidencia solicita de forma directa un ajuste de formato o estilo.",
    ),
    "2958369170-A": (
        "no",
        "manejo_errores_o_casos_borde",
        "alta",
        "El comentario identifica un escenario limite o manejo de error omitido.",
    ),
    "3167827984-A": (
        "si",
        "ui_ux_o_frontend",
        "alta",
        "La evidencia requiere un ajuste concreto de interfaz o comportamiento visual.",
    ),
    "3233131994-A": (
        "si",
        "documentacion_o_descripcion_incompleta",
        "alta",
        "La revision solicita corregir documentacion o texto antes de integrar.",
    ),
    "3175058659-A": (
        "si",
        "pruebas_faltantes_o_insuficientes",
        "alta",
        "La evidencia pide explicitamente agregar o ampliar pruebas.",
    ),
}

OVERRIDE_QUOTE_PATTERNS = {
    "3084021151-A": r"latest release of 2\.1",
    "3098938231-A": r"preserving the original error as a 'cause'",
    "3114898378-A": r"same as for pull.request but for push",
    "3156412763-A": r"var! should be usable under the top level",
    "3166697799-A": r"address the patch coverage issue",
    "3161958337-A": r"arrow is much smaller",
    "3184110162-A": r"(?:no import needed|mock really help|not needed)",
    "2968159813-A": r"don't edit anything other than migration.web",
    "3021989795-A": r"check error strings too",
    "3113332396-A": r"allowing duplicate names might not be a problem",
    "3119688458-A": r"appears to expect three parameters",
    "3083568715-A": r"cla assistant check",
    "3084106426-A": r"light mode",
    "3153811253-A": r"move this logic",
}


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_rows(path: Path, rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalized(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def reason_for_category(category: str) -> str:
    reason = CATEGORY_REASONS.get(category)
    if not reason:
        return "La evidencia causal pre-merge respalda la categoria asignada."
    if category == "evidencia_insuficiente":
        return f"No se aprobo inmediatamente por una razon no determinable: {reason}."
    return f"No se aprobo inmediatamente porque {reason}."


def parse_date(value: str | None) -> datetime | None:
    value = normalized(value)
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def comment_only(evidence: Dict[str, object]) -> str:
    text = normalized(str(evidence.get("text") or ""))
    diff_hunk = normalized(str(evidence.get("diff_hunk") or ""))
    path = normalized(str(evidence.get("path") or ""))
    if evidence.get("source") == "pr_review_comment" and diff_hunk:
        prefix = normalized(f"File: {path} Diff context: {diff_hunk}")
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
        elif text.startswith("File:") and "Diff context:" in text:
            # The cards output truncates long diff hunks independently from the
            # combined text. In that case the reviewer body cannot be separated
            # reliably, so the code context must not be treated as causal text.
            return ""
    return text


def is_non_causal(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in NON_CAUSAL_PATTERNS)


def pre_merge_evidence(card: Dict[str, str]) -> List[Dict[str, str]]:
    try:
        evidence_items = json.loads(card.get("all_evidence_json") or "[]")
    except json.JSONDecodeError:
        return []

    merged_at = parse_date(card.get("merged_at"))
    pr_author = normalized(card.get("pr_author")).casefold()
    selected: List[Dict[str, str]] = []
    seen = set()

    for raw in evidence_items:
        source = normalized(str(raw.get("source") or ""))
        if source not in {"pr_review_comment", "pr_review", "pr_comment"}:
            continue

        created_at = parse_date(str(raw.get("created_at") or ""))
        if merged_at and created_at and created_at > merged_at:
            continue

        text = comment_only(raw)
        if not text or is_non_causal(text):
            continue

        dedupe_key = re.sub(r"\W+", "", text.casefold())[:500]
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        user = normalized(str(raw.get("user") or ""))
        user_type = normalized(str(raw.get("user_type") or ""))
        if user.casefold() == pr_author:
            continue
        selected.append(
            {
                "source": source,
                "state": normalized(str(raw.get("state") or "")),
                "user": user,
                "user_type": user_type,
                "created_at": normalized(str(raw.get("created_at") or "")),
                "text": text,
                "is_author": "si" if user.casefold() == pr_author else "no",
            }
        )

    return selected


def evidence_weight(evidence: Dict[str, str]) -> int:
    source_weight = {
        "pr_review_comment": 5,
        "pr_review": 4,
        "pr_comment": 2,
    }.get(evidence["source"], 1)
    if evidence["state"] == "CHANGES_REQUESTED":
        source_weight += 4
    if evidence["user_type"].casefold() != "bot" and evidence["is_author"] == "no":
        source_weight += 2
    if evidence["user_type"].casefold() == "bot":
        source_weight -= 1
    return max(source_weight, 1)


def score_categories(
    evidences: Iterable[Dict[str, str]],
) -> Tuple[Dict[str, int], Dict[str, Dict[str, str]], int]:
    scores: Counter[str] = Counter()
    best_evidence: Dict[str, Dict[str, str]] = {}
    evidence_with_signal = 0

    for evidence in evidences:
        text = evidence["text"].casefold()
        matched_any = False
        for category, patterns in CATEGORY_PATTERNS.items():
            matches = sum(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in patterns)
            if not matches:
                continue
            matched_any = True
            contribution = evidence_weight(evidence) + min(matches - 1, 2)
            scores[category] += contribution
            previous = best_evidence.get(category)
            if previous is None or int(previous["score"]) < contribution:
                best_evidence[category] = {
                    **evidence,
                    "score": str(contribution),
                }
        if matched_any:
            evidence_with_signal += 1

    return dict(scores), best_evidence, evidence_with_signal


def selected_evidence_is_pre_merge(
    selected: Dict[str, str], card: Dict[str, str]
) -> str:
    if not selected:
        return "no_aplica"
    created_at = parse_date(selected.get("created_at"))
    merged_at = parse_date(card.get("merged_at"))
    if not created_at or not merged_at:
        return "no_identificada"
    return "si" if created_at <= merged_at else "no"


def override_evidence(
    card_id: str, evidences: Sequence[Dict[str, str]]
) -> Dict[str, str]:
    pattern = OVERRIDE_QUOTE_PATTERNS.get(card_id)
    if not pattern:
        return {}
    for evidence in evidences:
        if re.search(pattern, evidence["text"], re.IGNORECASE):
            return evidence
    return {}


def verdict(
    category: str,
    scores: Dict[str, int],
    evidences: Sequence[Dict[str, str]],
) -> Tuple[str, str, str, str]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    suggested = ranked[0][0] if ranked else "evidencia_insuficiente"
    suggested_score = ranked[0][1] if ranked else 0
    current_score = scores.get(category, 0)

    if not evidences or suggested_score < 5:
        if category == "evidencia_insuficiente":
            return (
                "si",
                "evidencia_insuficiente",
                "alta" if not evidences else "media",
                "No hay evidencia textual pre-merge suficientemente causal para atribuir un motivo.",
            )
        return (
            "no_determinable",
            "evidencia_insuficiente",
            "baja",
            "La evidencia pre-merge no permite demostrar que la categoria explique la iteracion.",
        )

    if category == "evidencia_insuficiente":
        return (
            "no",
            suggested,
            "alta" if suggested_score >= 9 else "media",
            "Existe evidencia causal pre-merge que permite proponer una razon concreta.",
        )

    if category == suggested and current_score >= 7:
        return (
            "si",
            suggested,
            "alta",
            "La evidencia pre-merge contiene una solicitud o problema explicito consistente con la categoria.",
        )
    if category == suggested or current_score >= max(5, suggested_score - 2):
        return (
            "parcial",
            suggested,
            "media",
            "La categoria tiene apoyo, pero la evidencia es indirecta o comparte senales con otra razon.",
        )
    if suggested_score >= 8 and current_score < 5:
        return (
            "no",
            suggested,
            "alta",
            "La evidencia pre-merge apunta con mayor claridad a una categoria diferente.",
        )
    return (
        "no_determinable",
        suggested,
        "baja",
        "Las evidencias disponibles son ambiguas y no permiten validar la categoria con suficiente certeza.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Diego categories against complete pre-merge evidence and "
            "optionally apply suggestions by confidence level."
        )
    )
    parser.add_argument("--diego-csv", type=Path, default=DEFAULT_DIEGO_CSV)
    parser.add_argument("--cards-csv", type=Path, default=DEFAULT_CARDS_CSV)
    parser.add_argument("--audit-csv", type=Path, default=DEFAULT_AUDIT_CSV)
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--apply-confidence",
        nargs="*",
        choices=APPLIED_CONFIDENCE_CHOICES,
        default=[],
        help=(
            "Apply suggested category, justification, quote and evidence metadata "
            "to the manual CSV for these confidence levels."
        ),
    )
    parser.add_argument(
        "--show-verdict",
        choices=("si", "parcial", "no", "no_determinable"),
        help="Print rows with the selected verdict for manual review.",
    )
    return parser.parse_args()


def apply_suggestions(
    diego_rows: Sequence[Dict[str, str]],
    audit_rows: Sequence[Dict[str, str]],
    confidence_levels: Sequence[str],
) -> Tuple[List[Dict[str, str]], Counter[str], Counter[str]]:
    requested_confidence = {level.casefold() for level in confidence_levels}
    audit_by_card = {row["card_id"]: row for row in audit_rows if row.get("card_id")}
    counters: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    updated_rows: List[Dict[str, str]] = []

    if len(audit_by_card) != len(audit_rows):
        raise ValueError("Audit rows must have unique non-empty card_id values")

    for row in diego_rows:
        card_id = row["card_id"]
        audit = audit_by_card.get(card_id)
        if audit is None:
            raise ValueError(f"Missing audit row for {card_id}")

        updated = dict(row)
        confidence = normalized(audit.get("confianza_validacion")).casefold()
        confidence_counts[confidence or "sin_confianza"] += 1

        if confidence not in requested_confidence:
            counters["skipped_by_confidence"] += 1
            updated_rows.append(updated)
            continue

        suggested_category = normalized(
            audit.get("categoria_sugerida_evidencia_completa")
        )
        justification = normalized(audit.get("justificacion_validacion"))
        quote = normalized(audit.get("cita_causal_pre_merge"))
        evidence_source = normalized(audit.get("fuente_cita_causal"))
        evidence_created_at = normalized(audit.get("fecha_cita_causal"))

        if not suggested_category:
            raise ValueError(f"Missing suggested category for {card_id}")
        if not justification:
            raise ValueError(f"Missing validation justification for {card_id}")

        if updated["categoria_retrabajo_pre_merge"] != suggested_category:
            counters["category_changed"] += 1
        if updated["justificacion_breve"] != justification:
            counters["justification_changed"] += 1
        if updated["cita_textual_retrabajo"] != quote:
            counters["quote_changed"] += 1
        if evidence_source and updated["evidence_source"] != evidence_source:
            counters["evidence_source_changed"] += 1
        if evidence_created_at and updated["evidence_created_at"] != evidence_created_at:
            counters["evidence_created_at_changed"] += 1

        updated["categoria_retrabajo_pre_merge"] = suggested_category
        updated["justificacion_breve"] = justification
        updated["cita_textual_retrabajo"] = quote
        if evidence_source:
            updated["evidence_source"] = evidence_source
        if evidence_created_at:
            updated["evidence_created_at"] = evidence_created_at

        counters["applied"] += 1
        updated_rows.append(updated)

    return updated_rows, counters, confidence_counts


def main() -> None:
    args = parse_args()
    diego_rows = read_rows(args.diego_csv)
    cards = {row["card_id"]: row for row in read_rows(args.cards_csv)}
    existing_audit = {
        row["card_id"]: row
        for row in read_rows(args.audit_csv)
        if row.get("card_id")
    }

    if len(diego_rows) != 300 or len({row["card_id"] for row in diego_rows}) != 300:
        raise ValueError("Expected 300 unique Diego cards")

    output_rows: List[Dict[str, str]] = []
    verdict_counts: Counter[str] = Counter()
    suggested_changes = 0

    for row in diego_rows:
        card_id = row["card_id"]
        card = cards.get(card_id)
        if card is None:
            raise ValueError(f"Missing card evidence for {card_id}")

        evidences = pre_merge_evidence(card)
        scores, best_evidence, evidence_with_signal = score_categories(evidences)
        category = normalized(row.get("categoria_retrabajo_pre_merge"))
        result, suggested, confidence, rationale = verdict(category, scores, evidences)
        override = VALIDATION_OVERRIDES.get(card_id)
        origin = "reglas"
        if override:
            override_result, suggested, confidence, rationale = override
            result = override_result
            if category == suggested and override_result == "no":
                result = "si" if confidence == "alta" else "parcial"
                rationale = reason_for_category(suggested)
            origin = "revision_contextual"

        selected: Dict[str, str] = {}
        if suggested != "evidencia_insuficiente":
            if override:
                selected = override_evidence(card_id, evidences)
            if not selected:
                selected = best_evidence.get(suggested, {})
            if not selected and override and evidences:
                selected = max(evidences, key=evidence_weight)

        audit = dict(existing_audit.get(card_id, {}))
        if not audit:
            audit = {
                "card_id": card_id,
                "categoria_anterior": category,
                "categoria_base_normalizada": category,
                "categoria_validada": category,
                "cambio_semantico": "no",
                "motivo_cambio": "sin_auditoria_previa",
                "patron_evidencia": "",
                "evidencia_revisada": normalized(row.get("cita_textual_retrabajo")),
            }

        audit.update(
            {
                "categoria_validada": category,
                "veredicto_evidencia_completa": result,
                "categoria_sugerida_evidencia_completa": suggested,
                "confianza_validacion": confidence,
                "origen_veredicto": origin,
                "justificacion_validacion": rationale,
                "cita_causal_pre_merge": selected.get("text", ""),
                "fuente_cita_causal": selected.get("source", ""),
                "fecha_cita_causal": selected.get("created_at", ""),
                "evidencias_textuales_pre_merge": str(len(evidences)),
                "evidencias_con_senal_causal": str(evidence_with_signal),
                "puntaje_categoria_actual": str(scores.get(category, 0)),
                "puntaje_categoria_sugerida": str(scores.get(suggested, 0)),
                "evidencia_seleccionada_es_pre_merge": selected_evidence_is_pre_merge(
                    selected, card
                ),
                "requiere_revision_humana": (
                    "no" if result == "si" and confidence == "alta" else "si"
                ),
            }
        )
        output_rows.append(audit)
        verdict_counts[result] += 1
        if suggested != category:
            suggested_changes += 1

    fields = list(output_rows[0].keys())
    for field in VALIDATION_FIELDS:
        if field not in fields:
            fields.append(field)

    diego_fields = list(diego_rows[0].keys())
    apply_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    updated_diego_rows: List[Dict[str, str]] = []
    if args.apply_confidence:
        updated_diego_rows, apply_counts, confidence_counts = apply_suggestions(
            diego_rows, output_rows, args.apply_confidence
        )

    if args.write:
        write_rows(args.audit_csv, output_rows, fields)
        if args.apply_confidence:
            write_rows(args.diego_csv, updated_diego_rows, diego_fields)

    print(f"Rows validated: {len(output_rows)}")
    print(f"Suggested category changes: {suggested_changes}")
    print(f"Write enabled: {args.write}")
    for result, count in verdict_counts.most_common():
        print(f"  {result}: {count}")
    if args.apply_confidence:
        print("Apply confidence levels:")
        for level in args.apply_confidence:
            print(f"  {level}")
        print("Confidence counts:")
        for confidence, count in sorted(confidence_counts.items()):
            print(f"  {confidence}: {count}")
        print("Apply counts:")
        for key in (
            "applied",
            "skipped_by_confidence",
            "category_changed",
            "justification_changed",
            "quote_changed",
            "evidence_source_changed",
            "evidence_created_at_changed",
        ):
            print(f"  {key}: {apply_counts[key]}")
    if args.show_verdict:
        print(f"Rows with verdict={args.show_verdict}:")
        for audit in output_rows:
            if audit["veredicto_evidencia_completa"] != args.show_verdict:
                continue
            quote = audit["cita_causal_pre_merge"][:220]
            print(
                f"  {audit['card_id']} | "
                f"{audit['categoria_validada']} -> "
                f"{audit['categoria_sugerida_evidencia_completa']} | "
                f"actual={audit['puntaje_categoria_actual']} "
                f"sugerida={audit['puntaje_categoria_sugerida']} | {quote}"
            )


if __name__ == "__main__":
    main()
