#!/usr/bin/env python3
"""Build final taxonomy contrast between Javier/Codex and Diego validation."""

from __future__ import annotations

import argparse
import csv
from html import escape
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

DEFAULT_JAVIER_CSV = Path(
    "exploration/aidev/taxonomy/analysis/merged_after_rework_javier_taxonomy_manual_categories.csv"
)
DEFAULT_DIEGO_CSV = Path(
    "exploration/aidev/taxonomy/analysis/merged_after_rework_diego_taxonomy_validation.csv"
)
DEFAULT_OUTPUT_CSV = Path(
    "exploration/aidev/taxonomy/analysis/merged_after_rework_final_taxonomy_contrast.csv"
)
DEFAULT_SUMMARY_CSV = Path(
    "exploration/aidev/taxonomy/analysis/merged_after_rework_final_taxonomy_summary.csv"
)
DEFAULT_REPORT_MD = Path("docs/taxonomia-final-merged-after-rework.md")
DEFAULT_TREEMAP_SVG = Path("docs/taxonomia-final-merged-after-rework-treemap.svg")

TOTAL_SAMPLE = 300
ROOT_NODE = "PRs_merged_after_rework"

SUBCATEGORY_TO_PARENT = {
    "fallos_ci_build_o_tests": "validacion_calidad_ci",
    "lint_formato_o_estilo": "validacion_calidad_ci",
    "pruebas_faltantes_o_insuficientes": "validacion_calidad_ci",
    "correccion_funcional": "implementacion_logica",
    "manejo_errores_o_casos_borde": "implementacion_logica",
    "compatibilidad_o_migracion": "implementacion_logica",
    "rendimiento_concurrencia_o_recursos": "implementacion_logica",
    "ui_ux_o_frontend": "implementacion_logica",
    "implementacion_incompleta_o_cambio_omitido": "implementacion_logica",
    "diseno_api_modelo_o_arquitectura": "arquitectura_diseno",
    "duplicacion_o_falta_de_reutilizacion": "arquitectura_diseno",
    "reduccion_alcance_o_sobrecodigo": "arquitectura_diseno",
    "requisito_formal_o_gobernanza": "proceso_gobernanza",
    "dependencia_u_orden_de_merge": "proceso_gobernanza",
    "revision_o_aprobacion_pendiente": "proceso_gobernanza",
    "documentacion_o_descripcion_incompleta": "documentacion_descripcion",
    "configuracion_ci_o_automatizacion": "configuracion_automatizacion",
    "dependencias_o_versionado": "dependencias_versionado",
    "seguridad_permisos_o_validacion": "seguridad_permisos",
    "refactor_limpieza_o_nombres": "mantenimiento_refactor",
    "evidencia_insuficiente": "evidencia_insuficiente",
}

PARENT_LABELS = {
    "validacion_calidad_ci": "Validacion, calidad y CI",
    "implementacion_logica": "Implementacion y logica",
    "arquitectura_diseno": "Arquitectura y diseno",
    "proceso_gobernanza": "Proceso y gobernanza",
    "dependencias_versionado": "Dependencias y versionado",
    "documentacion_descripcion": "Documentacion y descripcion",
    "configuracion_automatizacion": "Configuracion y automatizacion",
    "seguridad_permisos": "Seguridad y permisos",
    "evidencia_insuficiente": "Evidencia insuficiente",
    "mantenimiento_refactor": "Mantenimiento y refactor",
}

PARENT_COLORS = {
    "validacion_calidad_ci": "#2f80ed",
    "implementacion_logica": "#f2994a",
    "arquitectura_diseno": "#9b51e0",
    "proceso_gobernanza": "#eb5757",
    "dependencias_versionado": "#56ccf2",
    "documentacion_descripcion": "#27ae60",
    "configuracion_automatizacion": "#00a896",
    "seguridad_permisos": "#f2c94c",
    "evidencia_insuficiente": "#828282",
    "mantenimiento_refactor": "#6fcf97",
}

JAVIER_SUBCATEGORY_MAP = {
    "fallos_tests_ci": "fallos_ci_build_o_tests",
    "lint_formato_analisis_estatico": "lint_formato_o_estilo",
    "cobertura_o_pruebas_insuficientes": "pruebas_faltantes_o_insuficientes",
    "correccion_funcional": "correccion_funcional",
    "manejo_errores_y_validacion_inputs": "manejo_errores_o_casos_borde",
    "compatibilidad_o_migracion": "compatibilidad_o_migracion",
    "rendimiento_concurrencia_o_recursos": "rendimiento_concurrencia_o_recursos",
    "ui_ux_y_comportamiento_frontend": "ui_ux_o_frontend",
    "diseno_api_modelo_o_interfaz": "diseno_api_modelo_o_arquitectura",
    "reutilizacion_y_duplicacion": "duplicacion_o_falta_de_reutilizacion",
    "alcance_o_sobrecodigo": "reduccion_alcance_o_sobrecodigo",
    "cumplimiento_cla_dco": "requisito_formal_o_gobernanza",
    "dependencia_o_orden_de_merge": "dependencia_u_orden_de_merge",
    "revision_o_aprobacion_pendiente": "revision_o_aprobacion_pendiente",
    "descripcion_pr_incorrecta_o_incompleta": "documentacion_o_descripcion_incompleta",
    "documentacion_codigo_o_usuario": "documentacion_o_descripcion_incompleta",
    "ci_workflows_y_automatizacion": "configuracion_ci_o_automatizacion",
    "versiones_o_dependencias": "dependencias_o_versionado",
    "seguridad_autorizacion_o_validacion": "seguridad_permisos_o_validacion",
    "limpieza_simplificacion_o_nombres": "refactor_limpieza_o_nombres",
    "motivo_no_identificable": "evidencia_insuficiente",
}

DIEGO_SUBCATEGORY_MAP = {
    key: key for key in SUBCATEGORY_TO_PARENT
}
DIEGO_SUBCATEGORY_MAP.update(
    {
        "documentacion_descripcion_incorrecta": "documentacion_o_descripcion_incompleta",
        "estilo_formato_lint": "lint_formato_o_estilo",
        "falla_ci_tests": "fallos_ci_build_o_tests",
        "configuracion_ci_despliegue": "configuracion_ci_o_automatizacion",
        "cumplimiento_proceso_pr": "requisito_formal_o_gobernanza",
        "ajuste_diseno_api_modelo": "diseno_api_modelo_o_arquitectura",
        "ajustes_implementacion_review": "correccion_funcional",
        "reduccion_alcance_o_sobrecodigo": "reduccion_alcance_o_sobrecodigo",
        "dependencias_versiones_migracion": "dependencias_o_versionado",
        "evidencia_insuficiente_rechazo_inicial": "evidencia_insuficiente",
        "correccion_funcional_logica": "correccion_funcional",
        "correcion_logica_frontend": "ui_ux_o_frontend",
        "ajuste_ui_ux": "ui_ux_o_frontend",
        "ajuste_menor_review": "correccion_funcional",
        "rendimiento_concurrencia": "rendimiento_concurrencia_o_recursos",
        "seguridad_permisos_validacion": "seguridad_permisos_o_validacion",
        "pruebas_faltantes_o_insuficientes": "pruebas_faltantes_o_insuficientes",
    }
)

CONTRAST_FIELDS = [
    "card_id",
    "pr_id",
    "agent",
    "html_url",
    "categoria_padre_final",
    "subcategoria_final",
    "n_categoria_padre_final",
    "porcentaje_categoria_padre_final",
    "n_subcategoria_final",
    "porcentaje_subcategoria_final",
    "javier_categoria_padre_original",
    "javier_subcategoria_original",
    "javier_categoria_padre_canonica",
    "javier_subcategoria_canonica",
    "diego_categoria_validada",
    "diego_categoria_padre_canonica",
    "diego_subcategoria_canonica",
    "diego_categoria_sugerida_evidencia_completa",
    "diego_sugerida_padre_canonica",
    "diego_sugerida_subcategoria_canonica",
    "acuerdo_subcategoria",
    "acuerdo_categoria_padre",
    "tipo_contraste",
    "prioridad_revision",
    "confianza_codex",
    "confianza_validacion_diego",
    "veredicto_evidencia_completa_diego",
    "requiere_revision_humana_diego",
    "cita_javier_codex",
    "cita_diego",
    "justificacion_javier_codex",
    "justificacion_validacion_diego",
]

SUMMARY_FIELDS = [
    "categoria_padre_final",
    "subcategoria_final",
    "n",
    "porcentaje_muestra",
    "n_categoria_padre",
    "porcentaje_categoria_padre",
    "n_acuerdo_diego_subcategoria",
    "n_acuerdo_diego_padre",
    "n_discrepancia_diego",
    "ejemplo_card_id",
    "cita_representativa",
]


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"No existe el CSV requerido: {path}")
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def text(value: str | None) -> str:
    return (value or "").strip()


def pct(value: int, total: int = TOTAL_SAMPLE) -> str:
    return f"{(value / total) * 100:.1f}"


def pct_es(value: int, total: int = TOTAL_SAMPLE) -> str:
    return pct(value, total).replace(".", ",") + "%"


def canonical_subcategory(value: str, mapping: Dict[str, str], source: str) -> str:
    normalized = text(value)
    if not normalized:
        raise ValueError(f"Etiqueta vacia en {source}")
    if normalized not in mapping:
        raise ValueError(f"Etiqueta sin mapeo en {source}: {normalized}")
    canonical = mapping[normalized]
    if canonical not in SUBCATEGORY_TO_PARENT:
        raise ValueError(f"Subcategoria canonica desconocida desde {source}: {canonical}")
    return canonical


def parent_for(subcategory: str) -> str:
    return SUBCATEGORY_TO_PARENT[subcategory]


def contrast_type(final_sub: str, diego_sub: str) -> str:
    final_parent = parent_for(final_sub)
    diego_parent = parent_for(diego_sub)
    if final_sub == diego_sub:
        return "acuerdo_total"
    if final_parent == diego_parent:
        return "acuerdo_padre"
    if final_sub == "evidencia_insuficiente" or diego_sub == "evidencia_insuficiente":
        return "evidencia_insuficiente"
    return "discrepancia"


def review_priority(
    final_sub: str,
    diego_sub: str,
    codex_confidence: str,
    diego_confidence: str,
    diego_requires_review: str,
) -> str:
    if final_sub != diego_sub and diego_confidence == "alta":
        return "alta"
    if parent_for(final_sub) != parent_for(diego_sub):
        return "media"
    if codex_confidence == "baja" or diego_confidence == "baja" or diego_requires_review == "si":
        return "media"
    return "baja"


def validate_inputs(javier_rows: Sequence[Dict[str, str]], diego_rows: Sequence[Dict[str, str]]) -> None:
    for label, rows in (("Javier/Codex", javier_rows), ("Diego", diego_rows)):
        card_ids = [row.get("card_id", "") for row in rows]
        if len(rows) != TOTAL_SAMPLE:
            raise ValueError(f"{label} debe tener {TOTAL_SAMPLE} filas, tiene {len(rows)}")
        if len(set(card_ids)) != TOTAL_SAMPLE:
            raise ValueError(f"{label} debe tener {TOTAL_SAMPLE} card_id unicos")
    common = {row["card_id"] for row in javier_rows} & {row["card_id"] for row in diego_rows}
    if len(common) != TOTAL_SAMPLE:
        raise ValueError(f"El solapamiento debe ser {TOTAL_SAMPLE}, es {len(common)}")


def build_contrast_rows(
    javier_rows: Sequence[Dict[str, str]],
    diego_rows: Sequence[Dict[str, str]],
) -> List[Dict[str, str]]:
    diego_by_card = {row["card_id"]: row for row in diego_rows}
    prepared = []
    for row in javier_rows:
        diego = diego_by_card[row["card_id"]]
        final_sub = canonical_subcategory(
            row.get("subcategoria_propuesta", ""),
            JAVIER_SUBCATEGORY_MAP,
            "Javier/Codex",
        )
        final_parent = parent_for(final_sub)
        diego_sub = canonical_subcategory(
            diego.get("categoria_validada", ""),
            DIEGO_SUBCATEGORY_MAP,
            "Diego categoria_validada",
        )
        diego_parent = parent_for(diego_sub)
        suggested_value = text(diego.get("categoria_sugerida_evidencia_completa", "")) or diego.get(
            "categoria_validada", ""
        )
        suggested_sub = canonical_subcategory(
            suggested_value,
            DIEGO_SUBCATEGORY_MAP,
            "Diego categoria_sugerida_evidencia_completa",
        )
        suggested_parent = parent_for(suggested_sub)
        prepared.append(
            {
                "card_id": row.get("card_id", ""),
                "pr_id": row.get("pr_id", ""),
                "agent": row.get("agent", ""),
                "html_url": row.get("html_url", ""),
                "categoria_padre_final": final_parent,
                "subcategoria_final": final_sub,
                "javier_categoria_padre_original": row.get("categoria_padre_propuesta", ""),
                "javier_subcategoria_original": row.get("subcategoria_propuesta", ""),
                "javier_categoria_padre_canonica": final_parent,
                "javier_subcategoria_canonica": final_sub,
                "diego_categoria_validada": diego.get("categoria_validada", ""),
                "diego_categoria_padre_canonica": diego_parent,
                "diego_subcategoria_canonica": diego_sub,
                "diego_categoria_sugerida_evidencia_completa": diego.get(
                    "categoria_sugerida_evidencia_completa", ""
                ),
                "diego_sugerida_padre_canonica": suggested_parent,
                "diego_sugerida_subcategoria_canonica": suggested_sub,
                "acuerdo_subcategoria": "si" if final_sub == diego_sub else "no",
                "acuerdo_categoria_padre": "si" if final_parent == diego_parent else "no",
                "tipo_contraste": contrast_type(final_sub, diego_sub),
                "prioridad_revision": review_priority(
                    final_sub,
                    diego_sub,
                    row.get("confianza_codex", ""),
                    diego.get("confianza_validacion", ""),
                    diego.get("requiere_revision_humana", ""),
                ),
                "confianza_codex": row.get("confianza_codex", ""),
                "confianza_validacion_diego": diego.get("confianza_validacion", ""),
                "veredicto_evidencia_completa_diego": diego.get("veredicto_evidencia_completa", ""),
                "requiere_revision_humana_diego": diego.get("requiere_revision_humana", ""),
                "cita_javier_codex": row.get("cita_textual_retrabajo", ""),
                "cita_diego": diego.get("cita_causal_pre_merge", ""),
                "justificacion_javier_codex": row.get("justificacion_breve", ""),
                "justificacion_validacion_diego": diego.get("justificacion_validacion", ""),
            }
        )
    parent_counts = Counter(row["categoria_padre_final"] for row in prepared)
    sub_counts = Counter(row["subcategoria_final"] for row in prepared)
    for row in prepared:
        parent_count = parent_counts[row["categoria_padre_final"]]
        sub_count = sub_counts[row["subcategoria_final"]]
        row["n_categoria_padre_final"] = str(parent_count)
        row["porcentaje_categoria_padre_final"] = pct(parent_count)
        row["n_subcategoria_final"] = str(sub_count)
        row["porcentaje_subcategoria_final"] = pct(sub_count)
    return sorted(prepared, key=lambda row: row["card_id"])


def build_summary_rows(contrast_rows: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    parent_counts = Counter(row["categoria_padre_final"] for row in contrast_rows)
    sub_counts = Counter((row["categoria_padre_final"], row["subcategoria_final"]) for row in contrast_rows)
    rows_by_sub: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in contrast_rows:
        rows_by_sub[(row["categoria_padre_final"], row["subcategoria_final"])].append(row)

    summary_rows = []
    for (parent, sub), count in sorted(
        sub_counts.items(),
        key=lambda item: (-parent_counts[item[0][0]], item[0][0], -item[1], item[0][1]),
    ):
        group = rows_by_sub[(parent, sub)]
        agreement_sub = sum(row["acuerdo_subcategoria"] == "si" for row in group)
        agreement_parent = sum(row["acuerdo_categoria_padre"] == "si" for row in group)
        discrepancy = sum(row["acuerdo_categoria_padre"] == "no" for row in group)
        example = sorted(
            group,
            key=lambda row: (
                row["prioridad_revision"] != "baja",
                row["confianza_codex"] != "alta",
                row["card_id"],
            ),
        )[0]
        summary_rows.append(
            {
                "categoria_padre_final": parent,
                "subcategoria_final": sub,
                "n": str(count),
                "porcentaje_muestra": pct(count),
                "n_categoria_padre": str(parent_counts[parent]),
                "porcentaje_categoria_padre": pct(parent_counts[parent]),
                "n_acuerdo_diego_subcategoria": str(agreement_sub),
                "n_acuerdo_diego_padre": str(agreement_parent),
                "n_discrepancia_diego": str(discrepancy),
                "ejemplo_card_id": example["card_id"],
                "cita_representativa": example["cita_javier_codex"],
            }
        )
    return summary_rows


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def parent_summary_table(contrast_rows: Sequence[Dict[str, str]]) -> str:
    parent_counts = Counter(row["categoria_padre_final"] for row in contrast_rows)
    sub_counts = Counter((row["categoria_padre_final"], row["subcategoria_final"]) for row in contrast_rows)
    rows = []
    for parent, count in parent_counts.most_common():
        subs = [
            f"`{sub}` {sub_count}"
            for (sub_parent, sub), sub_count in sorted(
                sub_counts.items(), key=lambda item: (-item[1], item[0][1])
            )
            if sub_parent == parent
        ]
        rows.append([f"`{parent}`", str(count), pct_es(count), "; ".join(subs)])
    return markdown_table(["Categoria padre", "n", "%", "Subcategorias"], rows)


def subcategory_summary_table(summary_rows: Sequence[Dict[str, str]]) -> str:
    return markdown_table(
        ["Categoria padre", "Subcategoria", "n", "%", "Acuerdo subcat. Diego", "Acuerdo padre Diego"],
        [
            [
                f"`{row['categoria_padre_final']}`",
                f"`{row['subcategoria_final']}`",
                row["n"],
                row["porcentaje_muestra"].replace(".", ",") + "%",
                row["n_acuerdo_diego_subcategoria"],
                row["n_acuerdo_diego_padre"],
            ]
            for row in summary_rows
        ],
    )


def taxonomy_tree_mermaid(contrast_rows: Sequence[Dict[str, str]]) -> str:
    parent_counts = Counter(row["categoria_padre_final"] for row in contrast_rows)
    sub_counts = Counter((row["categoria_padre_final"], row["subcategoria_final"]) for row in contrast_rows)
    lines = [
        "```mermaid",
        "flowchart TD",
        "    root[\"PRs merged_after_rework<br/>300 entradas\"]",
        "",
    ]
    for index, (parent, count) in enumerate(parent_counts.most_common(), start=1):
        parent_id = f"cat{index}"
        lines.append(f"    {parent_id}[\"{parent}<br/>{count} casos ({pct_es(count)})\"]")
        lines.append(f"    root --> {parent_id}")
        child_index = 0
        for (sub_parent, sub), sub_count in sorted(
            sub_counts.items(), key=lambda item: (-item[1], item[0][1])
        ):
            if sub_parent != parent:
                continue
            child_index += 1
            sub_id = f"cat{index}_sub{child_index}"
            entries_id = f"cat{index}_sub{child_index}_entries"
            lines.append(f"    {sub_id}[\"{sub}\"]")
            lines.append(f"    {entries_id}[\"{sub_count} entradas<br/>{pct_es(sub_count)}\"]")
            lines.append(f"    {parent_id} --> {sub_id}")
            lines.append(f"    {sub_id} --> {entries_id}")
        lines.append("")
    lines.extend(
        [
            "    classDef root fill:#2f95d0,color:#ffffff,stroke:#1f6f9f,stroke-width:2px;",
            "    classDef category fill:#3498db,color:#ffffff,stroke:#1f6f9f,stroke-width:2px;",
            "    classDef subcategory fill:#3498db,color:#ffffff,stroke:#1f6f9f,stroke-width:2px;",
            "    classDef entries fill:#e8f2f7,color:#111111,stroke:#6aa7c8,stroke-width:2px;",
            "    class root root;",
        ]
    )
    for index, (parent, _) in enumerate(parent_counts.most_common(), start=1):
        lines.append(f"    class cat{index} category;")
        child_count = sum(1 for sub_parent, _ in sub_counts if sub_parent == parent)
        for child_index in range(1, child_count + 1):
            lines.append(f"    class cat{index}_sub{child_index} subcategory;")
            lines.append(f"    class cat{index}_sub{child_index}_entries entries;")
    lines.append("```")
    return "\n".join(lines)


def bar_chart_mermaid(contrast_rows: Sequence[Dict[str, str]]) -> str:
    parent_counts = Counter(row["categoria_padre_final"] for row in contrast_rows)
    ordered = parent_counts.most_common()
    labels = ", ".join(f'"C{index}"' for index, _ in enumerate(ordered, start=1))
    values = ", ".join(str(count) for _, count in ordered)
    max_value = max((count for _, count in ordered), default=0)
    y_axis_max = ((max_value + 9) // 10) * 10 if max_value else 10
    lines = [
        "```mermaid",
        "xychart-beta",
        "    title \"Casos por categoria padre\"",
        f"    x-axis [{labels}]",
        f"    y-axis \"Casos\" 0 --> {y_axis_max}",
        f"    bar [{values}]",
        "```",
    ]
    return "\n".join(lines)


def bar_chart_legend(contrast_rows: Sequence[Dict[str, str]]) -> str:
    parent_counts = Counter(row["categoria_padre_final"] for row in contrast_rows)
    rows = []
    for index, (parent, count) in enumerate(parent_counts.most_common(), start=1):
        rows.append([f"C{index}", f"`{parent}`", str(count), pct_es(count)])
    return markdown_table(["Codigo", "Categoria padre", "n", "%"], rows)


def bar_fallback(contrast_rows: Sequence[Dict[str, str]]) -> str:
    parent_counts = Counter(row["categoria_padre_final"] for row in contrast_rows)
    rows = []
    max_count = max(parent_counts.values())
    for parent, count in parent_counts.most_common():
        bar = "█" * max(1, round((count / max_count) * 24))
        rows.append([f"`{parent}`", str(count), pct_es(count), bar])
    return markdown_table(["Categoria padre", "n", "%", "Barra relativa"], rows)


def hex_to_rgb(color: str) -> Tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


def blend_hex(color: str, other: str = "#ffffff", factor: float = 0.25) -> str:
    rgb = hex_to_rgb(color)
    other_rgb = hex_to_rgb(other)
    blended = tuple(round(a * (1 - factor) + b * factor) for a, b in zip(rgb, other_rgb))
    return rgb_to_hex(blended)


def display_label(value: str) -> str:
    return value.replace("_", " ")


def wrap_label(label: str, max_chars: int, max_lines: int) -> List[str]:
    words = label.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and words:
        used = " ".join(lines)
        if len(used) < len(label) and len(lines[-1]) > 3:
            lines[-1] = lines[-1][:-1].rstrip() + "..."
    return lines


def binary_treemap(
    items: Sequence[Tuple[str, int]], x: float, y: float, width: float, height: float
) -> List[Tuple[str, int, float, float, float, float]]:
    items = [(label, count) for label, count in items if count > 0]
    if not items:
        return []
    if len(items) == 1:
        label, count = items[0]
        return [(label, count, x, y, width, height)]

    total = sum(count for _, count in items)
    running = 0
    best_index = 1
    best_diff = total
    for index in range(1, len(items)):
        running += items[index - 1][1]
        diff = abs((total / 2) - running)
        if diff < best_diff:
            best_index = index
            best_diff = diff

    left_items = items[:best_index]
    right_items = items[best_index:]
    left_total = sum(count for _, count in left_items)
    ratio = left_total / total if total else 0

    if width >= height:
        left_width = width * ratio
        return binary_treemap(left_items, x, y, left_width, height) + binary_treemap(
            right_items, x + left_width, y, width - left_width, height
        )

    top_height = height * ratio
    return binary_treemap(left_items, x, y, width, top_height) + binary_treemap(
        right_items, x, y + top_height, width, height - top_height
    )


def svg_text(
    x: float,
    y: float,
    text: str,
    size: int,
    fill: str = "#111111",
    weight: str = "400",
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        f"{escape(text)}</text>"
    )


def build_treemap_svg(summary_rows: Sequence[Dict[str, str]]) -> str:
    width = 2400
    height = 1400
    margin = 40
    header_height = 110
    legend_width = 620
    gap = 32
    plot_x = margin
    plot_y = header_height
    plot_width = width - (margin * 2) - legend_width - gap
    plot_height = height - header_height - margin
    legend_x = plot_x + plot_width + gap
    legend_y = header_height

    rows_by_parent: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in summary_rows:
        rows_by_parent[row["categoria_padre_final"]].append(row)

    parent_items = sorted(
        (
            (parent, sum(int(row["n"]) for row in rows))
            for parent, rows in rows_by_parent.items()
        ),
        key=lambda item: (-item[1], item[0]),
    )
    parent_rects = binary_treemap(parent_items, plot_x, plot_y, plot_width, plot_height)
    parent_codes = {parent: f"P{index}" for index, (parent, _) in enumerate(parent_items, start=1)}
    child_items_all = [
        (row["subcategoria_final"], row["categoria_padre_final"], int(row["n"]))
        for row in summary_rows
    ]
    child_items_all.sort(key=lambda item: (-item[2], item[1], item[0]))
    child_codes = {child: f"S{index}" for index, (child, _, _) in enumerate(child_items_all, start=1)}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Treemap de taxonomia final merged_after_rework">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(margin, 48, "Taxonomia final de motivos de retrabajo humano", 36, "#111111", "700"),
        svg_text(margin, 86, "Treemap jerarquico: categoria padre -> subcategoria, area proporcional a n (300 tarjetas)", 20, "#444444"),
    ]

    for parent, parent_count, x, y, rect_width, rect_height in parent_rects:
        base_color = PARENT_COLORS.get(parent, "#3498db")
        parent_label = PARENT_LABELS.get(parent, display_label(parent))
        parent_code = parent_codes[parent]
        percent = pct_es(parent_count)
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{rect_width:.1f}" height="{rect_height:.1f}" '
            f'fill="{blend_hex(base_color, "#ffffff", 0.84)}" stroke="#ffffff" stroke-width="8"/>'
        )
        header_h = 52 if rect_height >= 120 else 38
        parts.append(
            f'<rect x="{x + 4:.1f}" y="{y + 4:.1f}" width="{max(rect_width - 8, 0):.1f}" height="{header_h:.1f}" '
            f'fill="{base_color}" rx="8" ry="8"/>'
        )
        compact_parent = rect_width < 275 or rect_height < 135
        if compact_parent:
            # Formato compacto: codigo + conteo principal
            header_label = f"{parent_code}  {parent_count}"
            parts.append(svg_text(x + 14, y + 29, header_label, 18, "#ffffff", "700"))
            # Solo mostrar porcentaje si hay espacio suficiente
            if rect_width >= 200:
                parts.append(svg_text(x + rect_width - 14, y + 29, percent, 14, "#ffffff", "700", "end"))
        else:
            # Calcular espacio disponible para el texto
            max_text_width = rect_width - 140  # Reservar espacio para el conteo a la derecha
            chars_available = max(8, int(max_text_width / 10))
            title_lines = wrap_label(f"{parent_code} {parent_label}", chars_available, 2)
            
            # Ajustar posicion Y segun cantidad de lineas
            if len(title_lines) == 1:
                parts.append(svg_text(x + 16, y + 35, title_lines[0], 17, "#ffffff", "700"))
            else:
                for index, line in enumerate(title_lines):
                    parts.append(svg_text(x + 16, y + 30 + (index * 18), line, 16, "#ffffff", "700"))
            
            # Posicionar el conteo verticalmente centrado respecto al texto
            text_height = 18 if len(title_lines) == 1 else 36
            count_y = y + 30 + (text_height / 2) + 5
            parts.append(svg_text(x + rect_width - 16, count_y, f"{parent_count} ({percent})", 16, "#ffffff", "700", "end"))

        inner_x = x + 10
        inner_y = y + header_h + 10
        inner_width = max(rect_width - 20, 1)
        inner_height = max(rect_height - header_h - 20, 1)
        child_items = sorted(
            ((row["subcategoria_final"], int(row["n"])) for row in rows_by_parent[parent]),
            key=lambda item: (-item[1], item[0]),
        )
        child_rects = binary_treemap(child_items, inner_x, inner_y, inner_width, inner_height)
        for child, child_count, cx, cy, child_width, child_height in child_rects:
            child_code = child_codes[child]
            fill = blend_hex(base_color, "#ffffff", 0.28)
            parts.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{child_width:.1f}" height="{child_height:.1f}" '
                f'fill="{fill}" stroke="#ffffff" stroke-width="4" rx="6" ry="6">'
                f'<title>{escape(parent_code)} {escape(parent_label)} / {escape(child_code)} {escape(display_label(child))}: {child_count} casos ({pct_es(child_count)})</title></rect>'
            )
            # Determinar estrategia de etiquetado segun espacio disponible
            min_width_for_text = 220
            min_height_for_two_lines = 100
            min_height_for_three_lines = 140
            
            if child_width < min_width_for_text or child_height < 70:
                # Recuadro muy pequeno: solo codigo centrado
                parts.append(svg_text(cx + child_width/2, cy + child_height/2 + 6, child_code, 20, "#111111", "800", "middle"))
                # Si hay espacio vertical, mostrar conteo con porcentaje
                if child_height >= 55:
                    stats_text = f"n={child_count} | {pct_es(child_count)}"
                    parts.append(svg_text(cx + child_width/2, cy + child_height - 10, stats_text, 12, "#111111", "600", "middle"))
                elif child_height >= 45:
                    # Solo conteo si hay muy poco espacio
                    parts.append(svg_text(cx + child_width/2, cy + child_height - 10, f"n={child_count}", 13, "#111111", "600", "middle"))
                continue
            
            if child_height < min_height_for_two_lines:
                # Solo una linea de texto + conteo
                short_label = wrap_label(display_label(child), max(6, int((child_width - 20) / 9)), 1)
                parts.append(svg_text(cx + 12, cy + 28, short_label[0] if short_label else child_code, 14, "#111111", "700"))
                parts.append(svg_text(cx + 12, cy + child_height - 10, f"n={child_count}", 13, "#111111", "700"))
                continue
            
            # Espacio suficiente para multiple lineas
            max_lines = 3 if child_height >= min_height_for_three_lines else 2
            label_lines = wrap_label(display_label(child), max(10, int((child_width - 20) / 9)), max_lines)
            
            text_start_y = cy + 26
            line_spacing = 19
            for index, line in enumerate(label_lines):
                parts.append(svg_text(cx + 12, text_start_y + (index * line_spacing), line, 15, "#111111", "700"))
            
            stats_y = cy + child_height - 14
            parts.append(svg_text(cx + 12, stats_y, f"n={child_count} | {pct_es(child_count)}", 13, "#111111", "700"))

    parts.append(
        f'<rect x="{legend_x:.1f}" y="{legend_y:.1f}" width="{legend_width:.1f}" height="{plot_height:.1f}" '
        'fill="#f8fafc" stroke="#d0d7de" stroke-width="2" rx="12" ry="12"/>'
    )
    parts.append(svg_text(legend_x + 22, legend_y + 36, "Leyenda para poster", 24, "#111111", "700"))
    parts.append(svg_text(legend_x + 22, legend_y + 64, "Los bloques pequenos usan codigos para mantener legibilidad.", 14, "#444444"))
    cursor_y = legend_y + 102
    parts.append(svg_text(legend_x + 22, cursor_y, "Categorias padre", 17, "#111111", "700"))
    cursor_y += 28
    for parent, count in parent_items:
        color = PARENT_COLORS.get(parent, "#3498db")
        label = PARENT_LABELS.get(parent, display_label(parent))
        code = parent_codes[parent]
        parts.append(f'<rect x="{legend_x + 22:.1f}" y="{cursor_y - 15:.1f}" width="16" height="16" fill="{color}" rx="3" ry="3"/>')
        parts.append(svg_text(legend_x + 46, cursor_y, f"{code} {label}", 14, "#111111", "700"))
        parts.append(svg_text(legend_x + legend_width - 24, cursor_y, f"{count} | {pct_es(count)}", 13, "#111111", "700", "end"))
        cursor_y += 24

    cursor_y += 18
    parts.append(svg_text(legend_x + 22, cursor_y, "Subcategorias", 17, "#111111", "700"))
    cursor_y += 28
    for child, parent, count in child_items_all:
        color = PARENT_COLORS.get(parent, "#3498db")
        code = child_codes[child]
        parts.append(f'<rect x="{legend_x + 22:.1f}" y="{cursor_y - 13:.1f}" width="12" height="12" fill="{blend_hex(color, "#ffffff", 0.28)}" stroke="{color}" stroke-width="1" rx="2" ry="2"/>')
        label_lines = wrap_label(f"{code} {display_label(child)}", 42, 2)
        for index, line in enumerate(label_lines):
            parts.append(svg_text(legend_x + 42, cursor_y + (index * 16), line, 13, "#111111", "700" if index == 0 else "400"))
        parts.append(svg_text(legend_x + legend_width - 24, cursor_y, f"{count} | {pct_es(count)}", 12, "#111111", "700", "end"))
        cursor_y += 34 if len(label_lines) > 1 else 23

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def contrast_metrics(contrast_rows: Sequence[Dict[str, str]]) -> Dict[str, int]:
    return {
        "n_total": len(contrast_rows),
        "n_acuerdo_total": sum(row["acuerdo_subcategoria"] == "si" for row in contrast_rows),
        "n_acuerdo_padre": sum(row["acuerdo_categoria_padre"] == "si" for row in contrast_rows),
        "n_discrepancia": sum(row["acuerdo_categoria_padre"] == "no" for row in contrast_rows),
        "n_prioridad_alta": sum(row["prioridad_revision"] == "alta" for row in contrast_rows),
    }


def top_discrepancy_pairs(contrast_rows: Sequence[Dict[str, str]], limit: int = 12) -> str:
    pairs = Counter(
        (row["subcategoria_final"], row["diego_subcategoria_canonica"])
        for row in contrast_rows
        if row["acuerdo_subcategoria"] == "no"
    )
    return markdown_table(
        ["Subcategoria final Javier/Codex", "Subcategoria Diego", "Casos"],
        [[f"`{left}`", f"`{right}`", str(count)] for (left, right), count in pairs.most_common(limit)],
    )


def high_priority_table(contrast_rows: Sequence[Dict[str, str]], limit: int = 20) -> str:
    rows = [row for row in contrast_rows if row["prioridad_revision"] == "alta"][:limit]
    if not rows:
        return "No hay casos de prioridad alta."
    return markdown_table(
        ["card_id", "Javier/Codex", "Diego", "conf. Diego", "veredicto Diego"],
        [
            [
                row["card_id"],
                f"`{row['subcategoria_final']}`",
                f"`{row['diego_subcategoria_canonica']}`",
                row["confianza_validacion_diego"],
                row["veredicto_evidencia_completa_diego"],
            ]
            for row in rows
        ],
    )


def build_report(
    contrast_rows: Sequence[Dict[str, str]],
    summary_rows: Sequence[Dict[str, str]],
    treemap_svg_path: Path = DEFAULT_TREEMAP_SVG,
) -> str:
    metrics = contrast_metrics(contrast_rows)
    type_counts = Counter(row["tipo_contraste"] for row in contrast_rows)
    priority_counts = Counter(row["prioridad_revision"] for row in contrast_rows)
    treemap_svg_link = treemap_svg_path.name
    report = f"""# Taxonomia final merged_after_rework

## Resumen

Se construye una taxonomia final de dos niveles para las 300 tarjetas `merged_after_rework`.
La categoria final usa Javier/Codex como base y Diego como contraste para estimar acuerdo,
discrepancias y prioridad de revision futura. Estos resultados son asistidos y deben
reportarse junto con sus limitaciones metodologicas.

## Cobertura

{markdown_table(['Fuente', 'Filas', 'card_id unicos'], [['Javier/Codex', '300', '300'], ['Diego validado', '300', '300'], ['Solapamiento', '300', '300']])}

## Taxonomia final con conteos

{parent_summary_table(contrast_rows)}

## Subcategorias finales

{subcategory_summary_table(summary_rows)}

## Recomendacion para poster

Para el poster, el formato recomendado es un treemap jerarquico de dos niveles:
las categorias padre funcionan como bloques principales y las subcategorias como
bloques internos. El area de cada bloque debe representar `n`, por lo que el lector
puede ver al mismo tiempo estructura taxonomica y peso relativo de cada motivo de
retrabajo.

Figura SVG generada para usar en poster:

![Treemap jerarquico de taxonomia final]({treemap_svg_link})

Usar esta composicion:

| Rol en el poster | Formato recomendado | Proposito |
| --- | --- | --- |
| Visual principal | Treemap jerarquico categoria padre -> subcategoria | Mostrar taxonomia y volumen relativo en una sola figura compacta |
| Visual de apoyo | Barras horizontales por categoria padre | Comparar rapidamente el peso de las categorias principales |
| Detalle numerico | Tabla compacta con `n` y `%` | Conservar valores exactos para lectura academica |

Codificacion visual sugerida para el treemap:

| Elemento | Recomendacion |
| --- | --- |
| Bloque externo | Categoria padre |
| Bloque interno | Subcategoria |
| Area | Numero de tarjetas `n` |
| Etiqueta | Nombre corto, `n` y porcentaje |
| Color | Un color por categoria padre; tonos del mismo color para sus subcategorias |

El arbol Mermaid de este reporte sirve para explicar la estructura completa, pero
puede ocupar demasiado espacio en un poster. El Sankey no se recomienda como figura
principal porque aqui no hay una transicion entre estados, sino una jerarquia de
clasificacion.

## Diagrama de taxonomia

El diagrama principal recomendado es un arbol jerarquico de tres niveles visuales:
raiz de la muestra, categorias padre y subcategorias. Bajo cada subcategoria se agrega
una caja de entradas con el conteo absoluto y porcentaje sobre las 300 tarjetas. Este
formato sigue la lectura `categoria -> subcategoria -> entradas`, similar al esquema
visual usado en card sorting.

Colores sugeridos: raiz y categorias en azul, subcategorias en azul consistente y
entradas en celeste claro para separar conteos de conceptos.

{taxonomy_tree_mermaid(contrast_rows)}

## Diagrama de barras por categoria padre

El segundo diagrama resume la cantidad de tarjetas por categoria padre. Sirve como
visual compacto para informe o poster cuando el arbol completo resulta demasiado
extenso. Para evitar etiquetas sobrepuestas, el eje X usa codigos cortos y la
leyenda conserva los nombres completos de las categorias.

{bar_chart_mermaid(contrast_rows)}

Leyenda del grafico de barras:

{bar_chart_legend(contrast_rows)}

Como fallback textual para informe o poster, usar barras horizontales por categoria
padre junto con la tabla de subcategorias:

{bar_fallback(contrast_rows)}

## Contraste con Diego

{markdown_table(['Metrica', 'Valor'], [['Acuerdo exacto de subcategoria', str(metrics['n_acuerdo_total'])], ['Acuerdo de categoria padre', str(metrics['n_acuerdo_padre'])], ['Discrepancia de categoria padre', str(metrics['n_discrepancia'])], ['Casos de prioridad alta de revision', str(metrics['n_prioridad_alta'])]])}

Distribucion de tipos de contraste:

{markdown_table(['Tipo de contraste', 'Casos'], [[key, str(value)] for key, value in type_counts.most_common()])}

Distribucion de prioridad de revision:

{markdown_table(['Prioridad', 'Casos'], [[key, str(value)] for key, value in priority_counts.most_common()])}

### Top discrepancias por subcategoria

{top_discrepancy_pairs(contrast_rows)}

### Casos de prioridad alta

{high_priority_table(contrast_rows)}

## Decision metodologica

La base final se toma desde Javier/Codex porque no se alcanzo a realizar una validacion
manual completa adicional. Diego se usa como una validacion contrastiva: no reemplaza
automaticamente la categoria final, pero permite identificar acuerdos, discrepancias y
casos de revision prioritaria.

## Limitaciones

- La clasificacion Javier/Codex es asistida y mantiene decisiones humanas pendientes.
- La validacion de Diego contiene muchos casos `no_determinable`, por lo que no debe
  interpretarse como consenso cerrado.
- Cada tarjeta queda asignada a una sola subcategoria principal, aunque puede contener
  multiples motivos de retrabajo.
- La taxonomia final es apta para reportar distribuciones y orientar discusion, pero
  debe presentarse como resultado asistido y no como acuerdo interevaluador definitivo.
"""
    return report


def validate_outputs(contrast_rows: Sequence[Dict[str, str]], summary_rows: Sequence[Dict[str, str]]) -> None:
    if len(contrast_rows) != TOTAL_SAMPLE:
        raise ValueError(f"El contraste final debe tener {TOTAL_SAMPLE} filas")
    if len({row["card_id"] for row in contrast_rows}) != TOTAL_SAMPLE:
        raise ValueError("El contraste final debe tener card_id unicos")
    if sum(int(row["n"]) for row in summary_rows) != TOTAL_SAMPLE:
        raise ValueError("El resumen de taxonomia no suma 300")
    for row in contrast_rows:
        if not row["categoria_padre_final"] or not row["subcategoria_final"]:
            raise ValueError(f"Fila sin categoria final: {row['card_id']}")
        if parent_for(row["subcategoria_final"]) != row["categoria_padre_final"]:
            raise ValueError(f"Padre/subcategoria inconsistente: {row['card_id']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--javier-csv", type=Path, default=DEFAULT_JAVIER_CSV)
    parser.add_argument("--diego-csv", type=Path, default=DEFAULT_DIEGO_CSV)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY_CSV)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--treemap-svg", type=Path, default=DEFAULT_TREEMAP_SVG)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    javier_rows = read_csv_rows(args.javier_csv)
    diego_rows = read_csv_rows(args.diego_csv)
    validate_inputs(javier_rows, diego_rows)
    contrast_rows = build_contrast_rows(javier_rows, diego_rows)
    summary_rows = build_summary_rows(contrast_rows)
    validate_outputs(contrast_rows, summary_rows)
    report = build_report(contrast_rows, summary_rows, args.treemap_svg)
    treemap_svg = build_treemap_svg(summary_rows)
    if not args.dry_run:
        write_csv(args.output_csv, contrast_rows, CONTRAST_FIELDS)
        write_csv(args.summary_csv, summary_rows, SUMMARY_FIELDS)
        args.report_md.parent.mkdir(parents=True, exist_ok=True)
        args.report_md.write_text(report, encoding="utf-8")
        args.treemap_svg.parent.mkdir(parents=True, exist_ok=True)
        args.treemap_svg.write_text(treemap_svg, encoding="utf-8")
    metrics = contrast_metrics(contrast_rows)
    print(f"rows={len(contrast_rows)} dry_run={args.dry_run}")
    print(
        "agreement_subcategory={n_acuerdo_total} agreement_parent={n_acuerdo_padre} "
        "parent_discrepancy={n_discrepancia} high_priority={n_prioridad_alta}".format(**metrics)
    )
    for row in summary_rows:
        print(
            f"{row['categoria_padre_final']}/{row['subcategoria_final']} "
            f"n={row['n']} pct={row['porcentaje_muestra']}"
        )


if __name__ == "__main__":
    main()
