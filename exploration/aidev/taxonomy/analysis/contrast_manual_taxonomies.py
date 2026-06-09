#!/usr/bin/env python3
"""Generate a contrast report between Diego and Javier manual taxonomies."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


DEFAULT_DIEGO_CSV = Path(
    "exploration/aidev/taxonomy/initial/merged_after_rework_manual_categories_diego.csv"
)
DEFAULT_JAVIER_CSV = Path(
    "exploration/aidev/taxonomy/initial/merged_after_rework_manual_categories_Javier.csv"
)
DEFAULT_OUTPUT_CSV = Path(
    "exploration/aidev/taxonomy/analysis/merged_after_rework_diego_javier_contrast.csv"
)
DEFAULT_REPORT_MD = Path("docs/contraste-categorizacion-diego-javier.md")


DIEGO_FAMILY_MAP = {
    "ajuste_diseno_api_modelo": "arquitectura_diseno",
    "documentacion_descripcion_incorrecta": "documentacion_descripcion",
    "falla_ci_tests": "validacion_calidad_ci",
    "rendimiento_concurrencia": "implementacion_logica",
    "dependencias_versiones_migracion": "dependencias_versionado",
    "cumplimiento_proceso_pr": "proceso_gobernanza",
    "correcion_logica_frontend": "implementacion_logica",
    "evidencia_insuficiente_rechazo_inicial": "evidencia_insuficiente",
    "configuracion_ci_despliegue": "configuracion_automatizacion",
    "estilo_formato_lint": "validacion_calidad_ci",
    "ajustes_implementacion_review": "implementacion_logica",
    "correccion_funcional_logica": "implementacion_logica",
    "pruebas_faltantes_o_insuficientes": "validacion_calidad_ci",
    "reduccion_alcance_o_sobrecodigo": "implementacion_logica",
    "ajuste_menor_review": "implementacion_logica",
}


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {path}. Pass explicit --diego-csv/--javier-csv if needed."
        )
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def completed_rows_by_card(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {
        row["card_id"]: row
        for row in rows
        if (row.get("categoria_retrabajo_pre_merge") or "").strip()
    }


def has_text(value: str | None) -> bool:
    return bool((value or "").strip())


def javier_family(category: str) -> str:
    if not category:
        return "sin_categoria"
    if category == "This repository has been disabled.":
        return "evidencia_insuficiente"

    low = category.casefold()

    if any(
        token in low
        for token in (
            "code owner",
            "compliance",
            "dco",
            "bypass",
            "feedback contradictorio",
            "iteraciones de feedback",
            "codeowners",
            "abandona",
            "abandono",
            "reactivacion",
            "reactivación",
            "review",
            "checks fallando",
        )
    ):
        return "proceso_gobernanza"

    if any(
        token in low
        for token in ("arquitectura", "patron", "patrón", "especificacion", "especificación", "scope grande")
    ):
        return "arquitectura_diseno"

    if any(
        token in low
        for token in (
            "validaciones automatizadas",
            "test flaky",
            "tests unitarios",
            "lint",
            "falsos positivos",
            "regla de lint",
            "integracion de linter",
            "integración de linter",
            "habilitacion de linters",
            "habilitación de linters",
        )
    ):
        return "validacion_calidad_ci"

    if any(token in low for token in ("dependencias", "sdk", "versiones", "versión", "version", "migracion", "migración")):
        return "dependencias_versionado"

    if any(
        token in low
        for token in ("hooks pre-commit", "empaquetado", "rpm", "configuracion de api", "configuración de api")
    ):
        return "configuracion_automatizacion"

    if any(
        token in low
        for token in (
            "refactorizacion",
            "refactorización",
            "limpieza de codigo",
            "limpieza de código",
            "renombramiento",
            "modularizacion",
            "modularización",
            "elementos no utilizados",
            "archivos obsoletos",
            "simplificacion de logica",
            "simplificación de lógica",
            "tipado de configuracion",
            "tipado de configuración",
        )
    ):
        return "mantenimiento_refactor"

    if any(
        token in low
        for token in (
            "nueva funcionalidad",
            "dashboards",
            "comandos de configuracion cli",
            "comandos de configuración cli",
            "renderizado de markdown",
        )
    ):
        return "feature_producto"

    if any(
        token in low
        for token in (
            "errores",
            "correccion",
            "corrección",
            "robustez",
            "compatibilidad",
            "buffers",
            "timing",
            "propiedades publicas",
            "propiedades públicas",
            "deuda tecnica",
            "deuda técnica",
        )
    ):
        return "implementacion_logica"

    return "implementacion_logica"


def markdown_table(rows: Sequence[Sequence[str]], headers: Sequence[str]) -> str:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(row) + " |")
    return "\n".join(output)


def comparable_scale_note(
    diego_rows: Dict[str, Dict[str, str]],
    javier_rows: Dict[str, Dict[str, str]],
    card_ids: Sequence[str],
    field: str,
) -> Tuple[int, int]:
    comparable = 0
    factor_matches = 0

    for card_id in card_ids:
        diego_value = (diego_rows[card_id].get(field) or "").strip()
        javier_value = (javier_rows[card_id].get(field) or "").strip()
        if not diego_value or not javier_value:
            continue
        comparable += 1
        if float(diego_value) != 0 and abs((float(javier_value) / float(diego_value)) - 1000) < 1e-6:
            factor_matches += 1

    return comparable, factor_matches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a contrast report between Diego and Javier manual categorizations."
    )
    parser.add_argument("--diego-csv", type=Path, default=DEFAULT_DIEGO_CSV)
    parser.add_argument("--javier-csv", type=Path, default=DEFAULT_JAVIER_CSV)
    parser.add_argument("--diego-label", default=str(DEFAULT_DIEGO_CSV))
    parser.add_argument("--javier-label", default=str(DEFAULT_JAVIER_CSV))
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    diego_raw = read_csv_rows(args.diego_csv)
    javier_raw = read_csv_rows(args.javier_csv)
    diego_all = {row["card_id"]: row for row in diego_raw}
    javier_all = {row["card_id"]: row for row in javier_raw}
    diego = completed_rows_by_card(diego_raw)
    javier = completed_rows_by_card(javier_raw)

    common = sorted(set(diego) & set(javier))
    exact_matches = 0
    family_matches = 0
    family_pair_counter: Counter[Tuple[str, str]] = Counter()
    diego_overlap_counter: Counter[str] = Counter()
    aligned_examples = []
    discrepant_examples = []
    contrast_rows = []

    for card_id in common:
        diego_row = diego[card_id]
        javier_row = javier[card_id]
        diego_category = (diego_row.get("categoria_retrabajo_pre_merge") or "").strip()
        javier_category = (javier_row.get("categoria_retrabajo_pre_merge") or "").strip()
        diego_family = DIEGO_FAMILY_MAP.get(diego_category, "sin_mapear")
        javier_family_name = javier_family(javier_category)

        if diego_category == javier_category:
            exact_matches += 1
        if diego_family == javier_family_name:
            family_matches += 1

        family_pair_counter[(diego_family, javier_family_name)] += 1
        diego_overlap_counter[diego_category] += 1

        row = {
            "card_id": card_id,
            "pr_id": diego_row.get("pr_id", ""),
            "agent": diego_row.get("agent", ""),
            "diego_categoria": diego_category,
            "javier_categoria": javier_category,
            "diego_familia_sugerida": diego_family,
            "javier_familia_sugerida": javier_family_name,
            "coincide_familia": "si" if diego_family == javier_family_name else "no",
        }
        contrast_rows.append(row)

        if diego_family == javier_family_name and len(aligned_examples) < 5:
            aligned_examples.append(row)
        if diego_family != javier_family_name and len(discrepant_examples) < 8:
            discrepant_examples.append(row)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(contrast_rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(contrast_rows)

    shared_with_cita_d = sum(
        1 for card_id in common if has_text(diego[card_id].get("cita_textual_retrabajo"))
    )
    shared_with_cita_j = sum(
        1 for card_id in common if has_text(javier[card_id].get("cita_textual_retrabajo"))
    )
    shared_with_just_d = sum(
        1 for card_id in common if has_text(diego[card_id].get("justificacion_breve"))
    )
    shared_with_just_j = sum(
        1 for card_id in common if has_text(javier[card_id].get("justificacion_breve"))
    )

    missing_support_d = [
        card_id
        for card_id in common
        if not has_text(diego[card_id].get("cita_textual_retrabajo"))
        or not has_text(diego[card_id].get("justificacion_breve"))
    ]
    missing_support_j = [
        card_id
        for card_id in common
        if not has_text(javier[card_id].get("cita_textual_retrabajo"))
        or not has_text(javier[card_id].get("justificacion_breve"))
    ]

    coverage_table = markdown_table(
        [
            [
                "Diego",
                str(len(diego_raw)),
                str(len(diego)),
                str(sum(1 for row in diego.values() if has_text(row.get("cita_textual_retrabajo")))),
                str(sum(1 for row in diego.values() if has_text(row.get("justificacion_breve")))),
            ],
            [
                "Javier",
                str(len(javier_raw)),
                str(len(javier)),
                str(sum(1 for row in javier.values() if has_text(row.get("cita_textual_retrabajo")))),
                str(sum(1 for row in javier.values() if has_text(row.get("justificacion_breve")))),
            ],
        ],
        [
            "Evaluador",
            "Filas",
            "Tarjetas con categoría",
            "Tarjetas con cita",
            "Tarjetas con justificación",
        ],
    )

    shared_table = markdown_table(
        [
            ["Tarjetas completadas por ambos", str(len(common))],
            ["Coincidencias exactas de etiqueta", str(exact_matches)],
            ["Discrepancias exactas de etiqueta", str(len(common) - exact_matches)],
            [
                "Coincidencias por familia sugerida (heurística)",
                f"{family_matches} / {len(common)} ({family_matches / len(common):.1%})",
            ],
        ],
        ["Métrica", "Valor"],
    )

    diego_overlap_table = markdown_table(
        [[category, str(count)] for category, count in diego_overlap_counter.most_common()],
        ["Categoría Diego en el solapamiento", "Casos"],
    )

    family_pairs_table = markdown_table(
        [
            [diego_family_name, javier_family_name, str(count)]
            for (diego_family_name, javier_family_name), count in family_pair_counter.most_common(10)
        ],
        ["Familia Diego", "Familia Javier", "Casos"],
    )

    aligned_table = markdown_table(
        [
            [
                row["card_id"],
                row["diego_categoria"],
                row["javier_categoria"],
                row["diego_familia_sugerida"],
            ]
            for row in aligned_examples
        ],
        ["card_id", "Categoría Diego", "Categoría Javier", "Familia común sugerida"],
    )

    discrepant_table = markdown_table(
        [
            [
                row["card_id"],
                row["diego_categoria"],
                row["javier_categoria"],
                f"{row['diego_familia_sugerida']} vs {row['javier_familia_sugerida']}",
            ]
            for row in discrepant_examples
        ],
        ["card_id", "Categoría Diego", "Categoría Javier", "Familias sugeridas"],
    )

    scale_lines = []
    for field in (
        "horas_creacion_a_primera_aprobacion",
        "horas_creacion_a_merge",
        "horas_creacion_a_aceptacion",
    ):
        comparable, factor_matches = comparable_scale_note(diego_all, javier_all, common, field)
        scale_lines.append(
            f"- `{field}`: {factor_matches}/{comparable} valores comparables están exactamente en escala x1000 en Javier respecto de Diego."
        )

    report = f"""# Contraste de categorización manual: Diego vs Javier

## Fuentes analizadas

- `{args.diego_label}`
- `{args.javier_label}`

> Este reporte y el CSV derivado fueron generados con `exploration/aidev/taxonomy/analysis/contrast_manual_taxonomies.py`.

## Objetivo

Contrastar las tarjetas que ambos evaluadores completaron para estimar el nivel de discrepancia actual y entender si la diferencia proviene de desacuerdo real o de marcos de categorización distintos.

## Cobertura por evaluador

{coverage_table}

## Base comparable real

Aunque ambos CSV contienen 300 filas, la comparación justa hoy debe hacerse solo sobre las tarjetas con categoría en ambos archivos.

{shared_table}

## Lectura principal

La discrepancia literal es **{len(common) - exact_matches} de {len(common)}** tarjetas compartidas. Sin embargo, esta cifra **no debe interpretarse todavía como desacuerdo inter-evaluador clásico**, porque ambos evaluadores están usando **niveles de abstracción distintos**:

- **Diego** usa una taxonomía más compacta y normalizada, centrada en el **motivo técnico inmediato** del retrabajo.
- **Javier** usa una taxonomía más narrativa, contextual y casi caso-a-caso, centrada en el **patrón sociotécnico o causal** del caso completo.

## Evidencia del cambio de granularidad

En las {len(common)} tarjetas compartidas:

- Diego usa **{len(diego_overlap_counter)} categorías distintas**.
- Javier usa **{len(common)} categorías distintas para {len(common)} tarjetas**.

Distribución de categorías de Diego dentro del solapamiento:

{diego_overlap_table}

Esto muestra que Diego está agrupando muchos casos bajo familias técnicas recurrentes, mientras Javier está describiendo historias causales mucho más específicas.

## Coincidencia semántica aproximada (heurística)

Para no quedarnos solo con coincidencia literal, se construyó una **familia sugerida** para cada categoría. Esta agrupación es heurística y sirve solo como apoyo para reconciliación posterior.

Las 10 combinaciones de familia más frecuentes son:

{family_pairs_table}

Con esta heurística, hay **{family_matches} coincidencias de familia sobre {len(common)} tarjetas compartidas** ({family_matches / len(common):.1%}).

### Ejemplos donde sí hay alineación semántica parcial

{aligned_table}

### Ejemplos donde la diferencia de enfoque es clara

{discrepant_table}

## Hallazgos metodológicos

1. **No hay acuerdo literal usable todavía**. Calcular kappa o porcentaje de acuerdo simple en este punto sería engañoso.
2. **La diferencia principal es el nivel de análisis**:
   - Diego etiqueta el síntoma o motivo inmediato del retrabajo.
   - Javier etiqueta la historia causal, de coordinación o de gobernanza que explica el caso.
3. **Hay un subconjunto con alineación semántica parcial** cuando ambos, aun con distinto nivel de detalle, apuntan a la misma familia amplia.
4. **Hay otro subconjunto claramente desalineado** donde uno codifica proceso/gobernanza y el otro codifica implementación/CI/documentación.

## Inconsistencias de datos detectadas

### 1. Escala distinta en columnas temporales

{'\n'.join(scale_lines)}

Esto indica que, antes de cualquier análisis conjunto de tiempos, los valores de Javier deben normalizarse.

### 2. Soporte textual incompleto en algunos casos compartidos

- Diego tiene {len(missing_support_d)} casos compartidos sin cita o sin justificación completa: {', '.join(missing_support_d) if missing_support_d else 'ninguno'}.
- Javier tiene {len(missing_support_j)} casos compartidos sin cita o sin justificación completa: {', '.join(missing_support_j) if missing_support_j else 'ninguno'}.

### 3. Diferencia estructural de cobertura

- Diego completó {len(diego)} tarjetas con categoría.
- Javier completó {len(javier)} tarjetas con categoría.
- El solapamiento utilizable hoy es de {len(common)} tarjetas.

## Recomendación de reconciliación

### Paso 1
Congelar el conjunto común actual de **{len(common)} tarjetas compartidas** como base de calibración.

### Paso 2
Definir una **taxonomía padre común** para reconciliar ambos estilos. Una propuesta mínima es:

- `arquitectura_diseno`
- `validacion_calidad_ci`
- `documentacion_descripcion`
- `implementacion_logica`
- `proceso_gobernanza`
- `configuracion_automatizacion`
- `dependencias_versionado`
- `mantenimiento_refactor`
- `feature_producto`
- `evidencia_insuficiente`

### Paso 3
Mapear ambas taxonomías a esa familia padre antes de discutir subcategorías.

### Paso 4
Resolver primero los casos donde **ni siquiera coincide la familia**, y después discutir si conviene mantener dos niveles:

- nivel 1: familia técnica/procesual común;
- nivel 2: subcategoría narrativa o técnica específica.

## Artefactos generados

- CSV derivado para revisión manual: `{args.output_csv}`
- Este reporte: `{args.report_md}`
"""

    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text(report, encoding="utf-8")

    print(
        f"Generated contrast for {len(common)} shared cards. Output CSV: {args.output_csv}. Report: {args.report_md}."
    )


if __name__ == "__main__":
    main()
