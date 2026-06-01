# Plan metodologico: card sorting sobre PRs aceptados despues de retrabajo

## Resumen

El proyecto estudia pull requests generados por agentes de IA en el dataset `hao-li/AIDev`, con foco en casos `merged_after_rework`: PRs que finalmente fueron mergeados, pero solo despues de commits adicionales y comentarios humanos. Estos casos no son rechazos definitivos; son aceptaciones no inmediatas que permiten observar problemas detectados durante revision y el retrabajo necesario antes de integrar el cambio.

La metodologia combina muestreo estratificado, preparacion de tarjetas con evidencia textual y card sorting abierto para construir una taxonomia inductiva de problemas que hacen que los PRs de agentes de IA requieran intervencion humana.

## Pregunta y objetivo

Pregunta principal:

**Que tipos de problemas hacen que los pull requests generados por agentes de IA no sean aceptados de manera inmediata y requieran retrabajo antes de poder integrarse?**

Objetivo:

Caracterizar, a partir de evidencia real de revision, los motivos de retrabajo previo al merge en PRs generados por agentes de IA y analizar como esos motivos se distribuyen por agente, lenguaje, tipo de tarea y complejidad.

## Poblacion y muestreo

La poblacion operacional se construye desde el dataset AIDev aplicando estos filtros:

1. PR cerrado y mergeado: `state = closed` y `merged_at` no nulo.
2. Evidencia de retrabajo: `commit_count > 1`.
3. Evidencia de intervencion humana: `human_comment_count > 0`.
4. Marcado explicito: `population_case_type = merged_after_rework`.

La muestra vigente usa:

- tamano objetivo: 300 PRs;
- semilla: `20260510`;
- estratificacion: `agent`;
- controles posteriores: lenguaje, complejidad del cambio, popularidad del repositorio, periodo de creacion y tipo de tarea.

El muestreo produce:

- `exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510.csv`;
- `exploration/aidev/sampling/outputs/merged_after_rework_sample_seed_20260510_summary.json`.

## Preparacion de tarjetas

Cada PR muestreado se transforma en una tarjeta para card sorting. La tarjeta mantiene trazabilidad hacia el PR original y resume evidencia textual relevante.

La preparacion prioriza evidencia en este orden:

1. reviews con `CHANGES_REQUESTED`;
2. comentarios inline humanos de revision;
3. comentarios generales humanos del PR;
4. reviews o comentarios de bots;
5. eventos de timeline;
6. titulo y descripcion del PR como respaldo.

Campos principales de cada tarjeta:

- identificadores: `card_id`, `pr_id`, `html_url`, `repo_id`;
- contexto: `agent`, `language`, `task_type`, `commit_count`, `created_at`, `merged_at`;
- evidencia: `evidence_source`, `review_state`, `evidence_text`, `context_summary`;
- control de calidad: `human_comment_count`, `textual_evidence_count`, `needs_manual_context_check`, `evidence_quality_score`.

La preparacion produce:

- `exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510.csv`;
- `exploration/aidev/preparation/outputs/merged_after_rework_cards_seed_20260510_summary.json`;
- `exploration/aidev/preparation/outputs/merged_after_rework_manual_categories_template.csv`.

## Protocolo de card sorting

El card sorting sera abierto: las categorias emergen desde las tarjetas, no desde una taxonomia previa.

Procedimiento:

1. Revisar tarjetas con evidencia insuficiente o ambigua.
2. Agrupar tarjetas por similitud del problema observado.
3. Asignar nombres descriptivos a categorias y subcategorias.
4. Registrar reglas de inclusion, exclusion y ejemplos representativos por categoria.
5. Refinar categorias cuando existan solapamientos o grupos demasiado amplios.
6. Aplicar la taxonomia final sobre la muestra completa.

La plantilla manual conserva tiempos de aceptacion y una columna final vacia `categoria_retrabajo_pre_merge`, que puede ampliarse durante el analisis si se requieren subcategorias, notas o codificacion por evaluador. La columna `fuente_tiempo_aceptacion` distingue si el tiempo de aceptacion proviene de la primera review aprobada o del merge cuando no existe aprobacion explicita.

## Analisis

Analisis cualitativo:

- construir la taxonomia inductiva de motivos de retrabajo;
- documentar ejemplos representativos por categoria;
- separar problemas tecnicos, de alcance, calidad, integracion, pruebas, documentacion y comunicacion cuando emerjan desde los datos.

Analisis cuantitativo:

- frecuencia de categorias en la muestra;
- distribucion por agente;
- distribucion por lenguaje y tipo de tarea;
- relacion con complejidad del cambio, comentarios humanos y tiempo hasta merge.

Validacion:

- doble codificacion sobre una submuestra si hay mas de un evaluador;
- revision de desacuerdos;
- calculo de acuerdo inter-evaluador cuando corresponda, por ejemplo Cohen's kappa o Krippendorff's alpha.

## Supuestos y limitaciones

- `merged_after_rework` no equivale a rechazo definitivo; representa aceptacion no inmediata.
- La presencia de comentarios humanos y commits adicionales es una aproximacion operacional al retrabajo.
- El dataset no registra directamente todos los resultados de CI/CD; fallos de pruebas o calidad se infieren desde texto de reviews y comentarios.
- La taxonomia final depende de la evidencia visible en GitHub y puede subrepresentar discusiones externas al PR.
- La muestra se estratifica por agente para asegurar comparabilidad basica entre generadores; otras variables se analizan como controles posteriores.
