Integrantes: Javier Alcalde y Diego Labrin.

# Propuesta revisada

## Título

**¿Qué revela la intervención humana cuando se rechazan los pull requests de agentes de IA?**

## Idea central

Esta propuesta estudia los pull requests **rechazados** generados por agentes de IA en el dataset `AIDev`. El foco está en entender por qué esos PRs no son aceptados, utilizando los comentarios de revisión y la actividad en GitHub como fuente de evidencia.

A diferencia de propuestas que parten de una taxonomía predefinida, aquí las **categorías de rechazo emergen de los datos** mediante un proceso de análisis manual sistemático conocido como card sorting abierto (Zimmermann). Esto permite construir una taxonomía inductiva que refleje los patrones reales presentes en el dataset, en lugar de imponer categorías a priori que podrían no ser representativas.

Adicionalmente, para los PRs que fueron rechazados pero eventualmente aceptados en iteraciones posteriores, se medirá el **esfuerzo de corrección**: cuánto tiempo tomó llegar a la aceptación y cuántas intervenciones humanas fueron necesarias en el camino.

## Motivación

El dataset `AIDev` contiene 33.596 PRs generados por agentes de IA, de los cuales aproximadamente el 28,5% fue rechazado (~9.575 PRs). Este subconjunto representa una oportunidad para estudiar cuándo y por qué los agentes fallan como contribuidores de software, más allá de la simple tasa de rechazo.

Entender las razones de rechazo tiene valor práctico concreto:

- Permite identificar las limitaciones técnicas y de proceso más frecuentes de los agentes actuales.
- Revela si ciertos agentes, lenguajes o tipos de tarea producen más rechazos de cierto tipo.
- Permite cuantificar el costo de corrección (tiempo + iteraciones) asociado a cada tipo de problema.

Sin una taxonomía válida y derivada de los datos reales, cualquier análisis cuantitativo posterior carece de fundamento. Por eso el card sorting es el paso metodológico central de esta propuesta.

## Objetivo

Construir una taxonomía inductiva de razones de rechazo en pull requests de agentes de IA —mediante card sorting abierto sobre una muestra aleatoria— y utilizarla para analizar la distribución de esas razones y el esfuerzo de corrección asociado a cada categoría.

## Preguntas de investigación

1. **RQ1** ¿Qué categorías de razones de rechazo emergen del análisis manual (card sorting) de los comentarios en PRs rechazados por agentes de IA?
2. **RQ2** ¿Cuánto tiempo transcurre entre el rechazo de un PR y su eventual aceptación, y cuántas intervenciones humanas se producen en ese período?
3. **RQ3** ¿Cómo se distribuyen las categorías de rechazo según agente, lenguaje de programación y tipo de tarea?
4. **RQ4** ¿Cuál es la relación entre la categoría de rechazo y el tiempo/esfuerzo requerido hasta la aceptación final?

## Metodología

### Selección y muestreo

El análisis se centra en los PRs del subset `pull_request` del dataset `AIDev` con las siguientes condiciones:

- `state = 'closed'`
- `merged_at IS NULL` (rechazados, no mergeados)

Con ~9.575 PRs rechazados, un análisis manual exhaustivo no es viable. Se tomará una **muestra aleatoria estratificada solo por agente** de **300 PRs** como muestra inicial. Luego se filtrarán los casos con peor evidencia textual antes del card sorting final. Lenguaje, complejidad del cambio y tipo de tarea quedan como variables de control posterior, no como estratos.

Las consultas de extracción se ejecutarán directamente en SQL sobre los archivos Parquet del dataset mediante DuckDB:

```sql
-- PRs rechazados con al menos un comentario de revisión
SELECT
    pr.id,
    pr.number,
    pr.agent,
    pr.repo_id,
    pr.html_url,
    pr.created_at,
    pr.closed_at,
    r.body  AS review_body,
    r.state AS review_state
FROM pull_request pr
LEFT JOIN pr_reviews r ON r.pr_id = pr.id
WHERE pr.state    = 'closed'
  AND pr.merged_at IS NULL
  AND r.body IS NOT NULL
ORDER BY random()
LIMIT 300;
```

Para cada PR en la muestra se generará una **tarjeta** con:

| Campo | Fuente |
|---|---|
| ID único del PR | `pull_request.id` |
| Agente | `pull_request.agent` |
| Fragmento del comentario de rechazo | `pr_reviews.body` o `pr_review_comments.body` |
| URL en GitHub | `pull_request.html_url` |
| Lenguaje del repositorio | `repository.language` |
| Complejidad del cambio | `commit_count` o `pr_commit_details` agrupado en baja, media y alta |
| Señales de calidad de evidencia | conteos de reviews/comentarios, `CHANGES_REQUESTED`, texto agregado y flag de descarte |

Las tarjetas se exportan como CSV/JSON para ser cargadas en la herramienta de clasificación (ver sección siguiente).

### Card sorting (metodología central)

Se aplica **card sorting abierto** (Zimmermann, "Card-sorting: From text to themes") para derivar inductivamente la taxonomía de razones de rechazo. En el card sorting abierto, los grupos no están predefinidos: emergen y evolucionan durante el proceso de clasificación.

#### Fase 1 — Preparación

1. Extraer la muestra inicial de 300 PRs rechazados mediante la consulta SQL anterior.
2. Revisar cada PR en GitHub para leer el contexto completo de la discusión (no solo el texto extraído del dataset).
3. Generar una tarjeta por PR con el fragmento de texto más representativo de la razón de rechazo.
4. Cargar las tarjetas en la herramienta de clasificación.

#### Fase 2 — Ejecución (sorting manual)

1. **Calibración conjunta**: ambos integrantes clasifican juntos las primeras 20 tarjetas para alinear criterios y acordar una semántica compartida para los grupos iniciales.
2. Dividir el resto de las tarjetas entre ambos, manteniendo comunicación activa al crear grupos nuevos.
3. Usar la herramienta de clasificación para asignar cada tarjeta a un grupo existente o crear uno nuevo.
4. Al finalizar, revisar el conjunto completo para verificar consistencia interna de los grupos.
5. Documentar el nombre descriptivo de cada grupo y, si algún grupo es muy grande, evaluar si contiene subtemas relevantes.

#### Fase 3 — Análisis (affinity diagrams)

1. Una vez fijos los grupos, aplicar **affinity diagrams** (Zimmermann) para identificar grupos similares que puedan unificarse.
2. Resultado esperado: jerarquía de dos niveles — **categorías padre** (temas generales) con **subcategorías** (variantes específicas).
3. Registrar el mapeo `pr_id → subcategoría → categoría_padre` como salida estructurada del card sorting.
4. Esta taxonomía es el insumo principal para los análisis cuantitativos de RQ2, RQ3 y RQ4.

> **Nota metodológica**: una limitación conocida del card sorting es la dependencia del criterio inter-codificador. Sin una métrica de acuerdo formal (e.g., Cohen's kappa), existe riesgo de sesgo subjetivo. La fase de calibración conjunta y la revisión cruzada al finalizar buscan mitigar este riesgo; se reportará explícitamente el proceso seguido para asegurar trazabilidad.

### Análisis cuantitativo: tiempo y esfuerzo hasta aceptación

Para los PRs rechazados que **eventualmente fueron aceptados** (en el mismo PR reabierto o en un nuevo PR asociado al mismo issue), se calculan:

- **Tiempo hasta aceptación**: diferencia entre `created_at` del PR rechazado y `merged_at` del PR aceptado final, en horas.
- **Número de intervenciones**: suma de commits de autores distintos al agente (`pr_commits`) + rondas de `pr_reviews.state = 'CHANGES_REQUESTED'` antes del merge.
- Estas métricas se desglosan **por categoría de rechazo** obtenida del card sorting.

La asociación entre un PR rechazado y su re-envío aceptado se realiza cruzando `related_issue.issue_id` y `repository.repo_id` para identificar PRs del mismo issue en el mismo repositorio.

Además, es viable incluir en una población ampliada PRs que sí fueron mergeados, pero solo después de modificaciones al código. Estos casos se identifican con `pull_request.merged_at`, múltiples commits o eventos de `pr_timeline` posteriores a revisión, y señales de feedback en `pr_reviews` o comentarios. Deben marcarse como `merged_after_rework` y analizarse separados de los rechazos definitivos, porque no representan rechazo final sino aceptación no inmediata.

```sql
-- Tiempo de resolución: del primer PR rechazado al merge final, por issue
SELECT
    ri.issue_id,
    MIN(pr_rejected.created_at) AS first_rejection_date,
    MAX(pr_accepted.merged_at)  AS final_merge_date,
    COUNT(DISTINCT pr_rejected.id) AS rejection_count
FROM pull_request pr_rejected
JOIN related_issue ri         ON ri.pr_id  = pr_rejected.id
JOIN pull_request pr_accepted ON pr_accepted.repo_id = pr_rejected.repo_id
WHERE pr_rejected.state    = 'closed'
  AND pr_rejected.merged_at IS NULL
  AND pr_accepted.merged_at  IS NOT NULL
GROUP BY ri.issue_id;
```

### Herramienta de clasificación

Para asistir el proceso de card sorting se construirá una pequeña utilidad CLI en Python que permita:

- Cargar el CSV/JSON de tarjetas exportadas.
- Presentar una tarjeta a la vez con el texto del comentario y la URL del PR.
- Asignar la tarjeta a una categoría existente (con autocompletado) o crear una nueva.
- Soporte para categorías padre e hijo (jerarquía de dos niveles).
- Guardar el resultado incrementalmente para no perder trabajo si se interrumpe la sesión.
- Exportar el resultado final como CSV/JSON con la columna `pr_id → categoría → categoría_padre`.

**Tecnología**: Python stdlib (`json`, `csv`, `readline`). Sin dependencias externas.

## Taxonomía (resultado esperado)

La taxonomía **no está predefinida**. Es el producto del card sorting. Se espera que emerja una estructura de dos niveles similar a la siguiente (ilustrativa, sujeta a cambio tras el análisis):

| Categoría padre (tema) | Subcategorías posibles |
|---|---|
| Problemas funcionales | Lógica incorrecta, comportamiento inesperado, casos borde no manejados |
| Calidad de código | Estilo, naming, complejidad excesiva, falta de tests |
| Desalineación con el proyecto | Scope incorrecto, patrón de diseño inadecuado, dependencias no deseadas |
| Problemas de integración | Conflictos de merge, CI/CD fallido, incompatibilidad de versiones |
| Abandono / sin explicación | Cerrado sin comentario, issue resuelto por otro medio |

La estructura final puede diferir sustancialmente de esta tabla inicial.

## Fuentes de datos y mapeo al schema

| Fuente de evidencia | Tabla(s) del dataset | Campos clave |
|---|---|---|
| PRs rechazados | `pull_request` | `state`, `merged_at`, `closed_at`, `agent`, `html_url` |
| Comentarios de revisión (texto libre) | `pr_reviews`, `pr_review_comments` | `body`, `state`, `diff_hunk`, `path` |
| Estado formal de revisión | `pr_reviews` | `state` (APPROVED, CHANGES_REQUESTED, COMMENTED) |
| Secuencia temporal de eventos | `pr_timeline` | `event`, `created_at`, `actor` |
| Commits por autor (agente vs. humano) | `pr_commits`, `pr_commit_details` | `author`, `committer`, `commit_stats_*` |
| Contexto del repositorio | `repository` | `language`, `forks`, `stars` |
| Issue relacionado | `related_issue`, `issue` | `issue_id`, `body`, `title`, `state` |
| Tipo de tarea del PR | `pr_task_type` | `type` |

## Limitaciones

- **Tamaño de la muestra**: la muestra inicial de 300 PRs reduce el margen de error aproximado frente a 150, pero el filtro posterior puede disminuir el tamaño efectivo. Conclusiones sobre el universo completo deben tomarse con cautela.
- **Inter-rater agreement**: sin métricas formales de acuerdo entre codificadores (Cohen's kappa), el riesgo de sesgo subjetivo en el card sorting es real. Se mitiga con calibración conjunta y revisión cruzada.
- **PRs abandonados sin comentario**: un subconjunto de PRs rechazados no tiene texto de revisión disponible. Estos no son clasificables por card sorting y se reportarán como una categoría especial ("sin evidencia textual").
- **Rastreo de re-envíos**: algunos PRs rechazados se re-envían como un PR nuevo en lugar de reabrirse. Trazar automáticamente esta relación depende de que ambos PRs estén asociados al mismo issue en `related_issue`, lo que no siempre ocurre.
- **CI/CD indirecto**: el dataset no registra resultados de pipelines de CI/CD directamente. La detección de fallos de tests es inferida desde el texto de los comentarios.

## Aporte esperado

Este estudio aporta en dos niveles. Primero, produce una taxonomía inductiva de razones de rechazo en PRs de agentes de IA, derivada desde los datos reales y no impuesta a priori, lo que le otorga validez empírica. Segundo, combina ese análisis cualitativo con métricas cuantitativas de esfuerzo de corrección, permitiendo responder no solo "por qué fallan" los agentes sino también "cuánto cuesta corregirlo" según el tipo de problema.

Los resultados pueden apoyar decisiones de adopción de agentes IA en equipos de desarrollo y orientar futuras mejoras en los propios agentes.

## Referencias

- Zimmermann, T. "Card-sorting: From text to themes." En: *Perspectives on Data Science for Software Engineering*. Elsevier, 2016. pp. 137–141.
- Dataset AIDev: <https://huggingface.co/datasets/hao-li/AIDev>

---

### Comentarios del profesor (referencia)

> Necesitamos conocer toda las interacciones en los pull requests.
> Cual es la razón por la cual fue rechazado = taxonomia (no le gustó el código, etc.)
> desde los datos deriva las categorías de la categoría. Analizar manualmente, en el github.
>
> **metodologia Card-sorting** tedioso pero necesario.
>
> ¿que me gustaría ver a mi? (profesor)
> tomar una muestra del total de merges rechazados, ya que se debe hacer el análisis manualmente. Es necesaria una muestra aleatoria.
>
> De todos los rechazos, en las iteraciones hay muchos que van a ser aceptados. Cuanto se demora en ser aceptado un pr y cuanto número de intervenciones hubo antes de la aceptación (medir el esfuerzo en tiempo)
>
> Para los rechazos por categoría, conocer el tiempo de demora hasta ser aceptado.
>
> tenemos todo el texto de la explicación del rechazo, a esa descripción se le debe dar una categoría de clasificación. Van a haber categorías que son similares y se pueden unir. Categorías padres y sub categorías. Construir una pequeña herramienta.
