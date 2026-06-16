#!/usr/bin/env python3
"""Build presentation-ready SVG charts for the final merged_after_rework taxonomy."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


DEFAULT_SUMMARY_CSV = Path(
    "exploration/aidev/taxonomy/analysis/merged_after_rework_final_taxonomy_summary.csv"
)
DEFAULT_VALIDATION_CSV = Path(
    "exploration/aidev/taxonomy/analysis/merged_after_rework_diego_taxonomy_validation.csv"
)
DEFAULT_OUTPUT_DIR = Path("docs")
TOTAL_SAMPLE = 300

PARENT_LABELS = {
    "validacion_calidad_ci": "Validacion, calidad y CI",
    "implementacion_logica": "Implementacion y logica",
    "arquitectura_diseno": "Arquitectura y diseno",
    "proceso_gobernanza": "Proceso y gobernanza",
    "dependencias_versionado": "Dependencias y versionado",
    "documentacion_descripcion": "Documentacion y descripcion",
    "configuracion_automatizacion": "Configuracion y automatizacion",
    "seguridad_permisos": "Seguridad y permisos",
    "mantenimiento_refactor": "Mantenimiento y refactor",
    "evidencia_insuficiente": "Evidencia insuficiente",
}

SUBCATEGORY_LABELS = {
    "fallos_ci_build_o_tests": "Fallos CI/build/tests",
    "lint_formato_o_estilo": "Lint, formato o estilo",
    "pruebas_faltantes_o_insuficientes": "Pruebas faltantes",
    "manejo_errores_o_casos_borde": "Errores/casos borde",
    "compatibilidad_o_migracion": "Compatibilidad/migracion",
    "rendimiento_concurrencia_o_recursos": "Rendimiento/recursos",
    "ui_ux_o_frontend": "UI/UX/frontend",
    "correccion_funcional": "Correccion funcional",
    "duplicacion_o_falta_de_reutilizacion": "Duplicacion/reuso",
    "reduccion_alcance_o_sobrecodigo": "Reduccion de alcance",
    "diseno_api_modelo_o_arquitectura": "Diseno API/arquitectura",
    "requisito_formal_o_gobernanza": "Requisito formal",
    "dependencia_u_orden_de_merge": "Orden de merge",
    "revision_o_aprobacion_pendiente": "Revision pendiente",
    "dependencias_o_versionado": "Dependencias/versionado",
    "documentacion_o_descripcion_incompleta": "Documentacion/descripcion",
    "configuracion_ci_o_automatizacion": "Configuracion/automatizacion",
    "seguridad_permisos_o_validacion": "Seguridad/permisos",
    "refactor_limpieza_o_nombres": "Refactor/nombres",
    "evidencia_insuficiente": "Evidencia insuficiente",
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
    "mantenimiento_refactor": "#6fcf97",
    "evidencia_insuficiente": "#828282",
}

STATUS_COLORS = {
    "si": "#27ae60",
    "parcial": "#f2c94c",
    "no_determinable": "#828282",
    "alta": "#2f80ed",
    "media": "#f2994a",
    "baja": "#828282",
}


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def pct(value: int, total: int = TOTAL_SAMPLE) -> str:
    return f"{(value / total) * 100:.1f}%".replace(".", ",")


def svg_frame(width: int, height: int, title: str, subtitle: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <style>
    .title {{ font: 700 28px Arial, sans-serif; fill: #1f2933; }}
    .subtitle {{ font: 400 15px Arial, sans-serif; fill: #52616b; }}
    .label {{ font: 600 15px Arial, sans-serif; fill: #1f2933; }}
    .small {{ font: 400 13px Arial, sans-serif; fill: #52616b; }}
    .value {{ font: 700 14px Arial, sans-serif; fill: #1f2933; }}
    .inside {{ font: 700 14px Arial, sans-serif; fill: #ffffff; }}
    .axis {{ stroke: #d9e2ec; stroke-width: 1; }}
  </style>
  <text x="40" y="42" class="title">{escape(title)}</text>
  <text x="40" y="68" class="subtitle">{escape(subtitle)}</text>
{body}
</svg>
"""


def parent_totals(summary_rows: Sequence[Dict[str, str]]) -> List[Tuple[str, int]]:
    totals: Dict[str, int] = {}
    for row in summary_rows:
        parent = row["categoria_padre_final"]
        totals[parent] = int(row["n_categoria_padre"])
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))


def subcategory_totals(summary_rows: Sequence[Dict[str, str]]) -> List[Tuple[str, str, int]]:
    rows = [
        (
            row["categoria_padre_final"],
            row["subcategoria_final"],
            int(row["n"]),
        )
        for row in summary_rows
    ]
    return sorted(rows, key=lambda item: (-item[2], item[1]))


def build_parent_bar_chart(summary_rows: Sequence[Dict[str, str]]) -> str:
    rows = parent_totals(summary_rows)
    width, height = 1200, 720
    left, top, bar_width, bar_height, gap = 345, 115, 720, 36, 22
    max_n = max(value for _, value in rows)
    elements = []

    for index, (parent, value) in enumerate(rows):
        y = top + index * (bar_height + gap)
        length = int((value / max_n) * bar_width)
        color = PARENT_COLORS[parent]
        label = PARENT_LABELS.get(parent, parent)
        elements.append(
            f'  <text x="40" y="{y + 24}" class="label">{escape(label)}</text>'
        )
        elements.append(
            f'  <rect x="{left}" y="{y}" width="{bar_width}" height="{bar_height}" rx="4" fill="#edf2f7"/>'
        )
        elements.append(
            f'  <rect x="{left}" y="{y}" width="{length}" height="{bar_height}" rx="4" fill="{color}"/>'
        )
        text_class = "inside" if length > 95 else "value"
        text_x = left + min(max(length - 78, 8), bar_width - 82)
        if length <= 95:
            text_x = left + length + 12
        elements.append(
            f'  <text x="{text_x}" y="{y + 24}" class="{text_class}">{value} ({pct(value)})</text>'
        )

    body = "\n".join(elements)
    return svg_frame(
        width,
        height,
        "Motivos de retrabajo por categoria",
        "Distribucion de 300 PRs merged_after_rework segun categoria padre",
        body,
    )


def build_subcategory_bar_chart(summary_rows: Sequence[Dict[str, str]], top_n: int = 12) -> str:
    rows = subcategory_totals(summary_rows)[:top_n]
    width, height = 1200, 760
    left, top, bar_width, bar_height, gap = 360, 120, 700, 34, 18
    max_n = max(value for _, _, value in rows)
    elements = []

    for index, (parent, subcategory, value) in enumerate(rows):
        y = top + index * (bar_height + gap)
        length = int((value / max_n) * bar_width)
        color = PARENT_COLORS[parent]
        label = SUBCATEGORY_LABELS.get(subcategory, subcategory)
        elements.append(
            f'  <text x="40" y="{y + 23}" class="label">{escape(label)}</text>'
        )
        elements.append(
            f'  <rect x="{left}" y="{y}" width="{bar_width}" height="{bar_height}" rx="4" fill="#edf2f7"/>'
        )
        elements.append(
            f'  <rect x="{left}" y="{y}" width="{length}" height="{bar_height}" rx="4" fill="{color}"/>'
        )
        text_x = left + length + 12
        text_class = "value"
        if length > 110:
            text_x = left + length - 84
            text_class = "inside"
        elements.append(
            f'  <text x="{text_x}" y="{y + 23}" class="{text_class}">{value} ({pct(value)})</text>'
        )
        elements.append(
            f'  <text x="40" y="{y + 40}" class="small">{escape(PARENT_LABELS[parent])}</text>'
        )

    body = "\n".join(elements)
    return svg_frame(
        width,
        height,
        "Subcategorias mas frecuentes",
        f"Top {top_n} motivos especificos dentro de la taxonomia final",
        body,
    )


def build_status_chart(validation_rows: Sequence[Dict[str, str]]) -> str:
    verdict_counts = Counter(row["veredicto_evidencia_completa"] for row in validation_rows)
    confidence_counts = Counter(row["confianza_validacion"] for row in validation_rows)
    width, height = 1200, 520
    left, bar_width = 260, 760
    rows = [
        (
            "Veredicto de evidencia",
            [("si", "Respaldada"), ("parcial", "Parcial"), ("no_determinable", "No determinable")],
            verdict_counts,
            150,
        ),
        (
            "Confianza de validacion",
            [("alta", "Alta"), ("media", "Media"), ("baja", "Baja")],
            confidence_counts,
            310,
        ),
    ]
    elements = []

    for title, parts, counts, y in rows:
        total = sum(counts.values())
        elements.append(f'  <text x="40" y="{y + 26}" class="label">{escape(title)}</text>')
        x = left
        for key, label in parts:
            value = counts[key]
            segment_width = int((value / total) * bar_width) if total else 0
            color = STATUS_COLORS[key]
            elements.append(
                f'  <rect x="{x}" y="{y}" width="{segment_width}" height="52" fill="{color}"/>'
            )
            if segment_width > 85:
                elements.append(
                    f'  <text x="{x + 12}" y="{y + 32}" class="inside">{value}</text>'
                )
            x += segment_width
        elements.append(
            f'  <rect x="{left}" y="{y}" width="{bar_width}" height="52" fill="none" stroke="#d9e2ec"/>'
        )
        legend_x = left
        for key, label in parts:
            value = counts[key]
            elements.append(
                f'  <rect x="{legend_x}" y="{y + 72}" width="16" height="16" fill="{STATUS_COLORS[key]}"/>'
            )
            elements.append(
                f'  <text x="{legend_x + 24}" y="{y + 85}" class="small">{escape(label)}: {value} ({pct(value, total)})</text>'
            )
            legend_x += 220

    body = "\n".join(elements)
    return svg_frame(
        width,
        height,
        "Estado de validacion de categorias",
        "Auditoria de Diego contra evidencia completa pre-merge",
        body,
    )


def write_svg(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate presentation SVG charts for the final taxonomy."
    )
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY_CSV)
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary_rows = read_rows(args.summary_csv)
    validation_rows = read_rows(args.validation_csv)

    outputs = {
        "taxonomia-final-categorias-padre-barras.svg": build_parent_bar_chart(
            summary_rows
        ),
        "taxonomia-final-top-subcategorias.svg": build_subcategory_bar_chart(
            summary_rows
        ),
        "taxonomia-final-validacion-evidencia.svg": build_status_chart(
            validation_rows
        ),
    }

    for filename, content in outputs.items():
        output_path = args.output_dir / filename
        write_svg(output_path, content)
        print(output_path)


if __name__ == "__main__":
    main()
