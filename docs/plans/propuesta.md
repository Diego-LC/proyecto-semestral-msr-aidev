Integrantes: Javier Alcalde y Diego Labrin.

# Propuesta 1 Seleccionada

## Título tentativo

**¿Qué revela la intervención humana sobre la autonomía de los agentes de IA como contribuidores de software?**

## Idea central

La propuesta seleccionada estudia pull requests generados por agentes de IA usando el dataset `AIDev`. El foco no estará solo en medir si los humanos intervienen o no, sino en interpretar esa intervención —y las razones de rechazo— como señales del nivel de autonomía real del agente.

La idea es que tanto la intervención humana como los patrones de rechazo permitan responder una pregunta más relevante: ¿los agentes ya pueden contribuir de manera efectiva al desarrollo de software o todavía requieren supervisión y correcciones importantes antes de que sus cambios puedan integrarse?

## Motivación

Medir únicamente la frecuencia de intervención humana no es suficiente. Ese dato tiene valor cuando se interpreta en términos de:

- confiabilidad práctica de los agentes;
- capacidad de integrarse al flujo real de desarrollo;
- costo adicional de supervisión humana;
- contextos donde los agentes sí o no son útiles.

Si la mayoría de los PRs requiere cambios humanos significativos antes del merge, eso sugiere una autonomía limitada. Si muchos PRs se integran sin cambios relevantes, entonces los agentes pueden entenderse como contribuidores efectivos al menos en ciertos escenarios. Adicionalmente, comprender **por qué** un PR es rechazado —fallo funcional, tests que no pasan, diseño inadecuado, entre otros— permite identificar las limitaciones concretas de los agentes, más allá de la simple tasa de rechazo.

## Objetivo

Evaluar en qué medida los pull requests generados por agentes de IA pueden integrarse como contribuciones efectivas de software, usando tanto la intervención humana como las razones de rechazo como señales del nivel real de autonomía del agente.

## Preguntas de investigación

1. ¿Qué proporción de los PRs creados por agentes puede integrarse sin intervención humana significativa?
2. Cuando un PR no es integrable tal como fue generado, ¿qué tipos de intervenciones significativas realizan los humanos?
3. ¿Qué proporción de los PRs generados por agentes es rechazada, y cuáles son las razones de rechazo más frecuentes según la taxonomía propuesta?
4. ¿Cómo varía la distribución de razones de rechazo según el contexto: lenguaje de programación, agente, tamaño del PR o características del repositorio?
5. ¿Cómo se relaciona el nivel de intervención y el tipo de rechazo con el resultado final del PR, como merge, rechazo o tiempo de integración?

## Taxonomía de intervenciones y rechazos

Un aporte metodológico central de esta propuesta es distinguir entre tipos de intervención y razones de rechazo. Para ello se define la siguiente taxonomía:

### Intervenciones humanas

| Categoría | Descripción |
|---|---|
| **Superficial** | Formato, documentación menor, sincronización de ramas, ajustes triviales de estilo |
| **Significativa** | Correcciones de lógica, tests, configuración, errores funcionales o cambios que afectan la aceptabilidad del PR |

La distinción entre categorías se operacionaliza a partir de la magnitud del cambio (`commit_stats_additions`, `commit_stats_deletions` en `pr_commit_details`) y del contenido de los archivos modificados (`filename`, `patch`).

### Razones de rechazo

| Categoría | Descripción | Fuente en el dataset |
|---|---|---|
| **Fallo funcional** | El código no cumple el comportamiento esperado | `pr_reviews.body`, `pr_review_comments.body` con keywords como "doesn't work", "broken", "fails" |
| **Tests fallidos** | Tests existentes o nuevos no pasan al momento del cierre | `pr_reviews.body` con keywords como "test", "failing", "CI"; eventos en `pr_timeline` |
| **Violación de estilo o convenciones** | Linting, formato, naming no alineado con el proyecto | `pr_review_comments.body` con referencias a estilo; `pr_reviews.state = 'changes_requested'` |
| **Diseño inadecuado** | Solución correcta pero mal estructurada o que no sigue patrones del proyecto | `pr_review_comments.body` con keywords como "refactor", "pattern", "structure" |
| **Scope incorrecto** | El PR resuelve algo diferente al issue original o introduce cambios fuera del alcance | Cruce de `related_issue` con `issue.body` y `pull_request.body`; comentarios del maintainer |
| **Conflictos o dependencias** | El PR introduce conflictos de merge o dependencias problemáticas | `pr_timeline.event` con eventos de conflicto; `pr_review_comments` con keywords como "conflict", "dependency" |
| **Abandono sin explicación** | PR cerrado sin actividad ni justificación clara | `pull_request.state = 'closed'` con ausencia de `pr_reviews` y `pr_comments` posteriores |

Esta taxonomía permitirá calcular la distribución total de razones de rechazo, analizar co-ocurrencias entre categorías y comparar patrones entre agentes o contextos.

## Fuentes de datos y mapeo al schema

El dataset `AIDev` provee las siguientes tablas, cada una con un rol específico en el estudio:

| Fuente de evidencia | Tabla(s) del dataset | Campos clave |
|---|---|---|
| Identificación del agente | `pull_request` | `agent` |
| Estado final del PR | `pull_request` | `state`, `merged_at`, `closed_at` |
| Autoría de commits (agente vs. humano) | `pr_commits`, `pr_commit_details` | `author`, `committer` |
| Magnitud de cambios por commit | `pr_commit_details` | `commit_stats_additions`, `commit_stats_deletions`, `additions`, `deletions` |
| Archivos y parches modificados | `pr_commit_details` | `filename`, `patch`, `status` |
| Secuencia temporal de eventos | `pr_timeline` | `event`, `created_at`, `actor` |
| Comentarios de revisión (texto libre) | `pr_reviews`, `pr_review_comments` | `body`, `state`, `diff_hunk`, `path` |
| Estado formal de revisión | `pr_reviews` | `state` (approved, changes_requested, etc.) |
| Contexto del repositorio | `repository` | `language`, `forks`, `stars` |
| Issue relacionado | `related_issue`, `issue` | `issue_id`, `body`, `title`, `state` |
| Tipo de tarea del PR | `pr_task_type` | `type` |

## Enfoque metodológico

El estudio usará PRs del dataset `AIDev` con historial suficiente de commits y estado final conocido. A partir de eso se reconstruirá la secuencia del PR para distinguir qué cambios provienen del agente y cuáles fueron agregados después por humanos.

### Clasificación de intervenciones

Para cada PR que llegó a merge, se identificará si existieron intervenciones humanas comparando el campo `author` de cada entrada en `pr_commits` con el valor de `pull_request.agent`. Los commits posteriores a la creación del PR cuyo autor no corresponda al agente serán considerados intervenciones humanas. La magnitud de esa intervención se estimará con los campos `commit_stats_additions` y `commit_stats_deletions` de `pr_commit_details`, y el tipo de archivos modificados (`filename`) permitirá distinguir entre cambios superficiales (documentación, configuración de formato) y significativos (código fuente, tests).

### Clasificación de razones de rechazo

El dataset no registra directamente los resultados de CI/CD como checks individuales, por lo que la detección de fallos de tests y otras razones de rechazo se realizará mediante la combinación de las siguientes fuentes disponibles:

1. **Análisis textual de comentarios**: los campos `body` de `pr_reviews` y `pr_review_comments` serán analizados mediante patrones de palabras clave asociadas a cada categoría de la taxonomía. Por ejemplo, términos como "test", "failing", "doesn't work" para fallo funcional o tests fallidos; "out of scope", "unrelated" para scope incorrecto.

2. **Estado formal de revisión**: el campo `pr_reviews.state` permite identificar PRs donde los revisores solicitaron cambios explícitamente (`changes_requested`) o rechazaron la contribución, lo que acota el conjunto de PRs a clasificar.

3. **Secuencia de eventos en el timeline**: `pr_timeline` registra eventos como asignaciones, labels y cambios de estado que pueden indicar la razón del cierre, especialmente para casos de abandono o conflictos.

4. **Presencia de commits humanos correctivos antes del cierre**: si existen commits de autores distintos al agente pero el PR fue igualmente rechazado, esto sugiere que la corrección humana no fue suficiente para resolver el problema original.

Dado que la detección de CI/CD es indirecta, se adoptará un enfoque conservador: los PRs cuya razón de rechazo no pueda determinarse con suficiente evidencia serán clasificados en la categoría "Abandono sin explicación" o marcados como no clasificables, reportando esta limitación explícitamente.

Cada PR rechazado podrá ser asignado a una o más categorías de la taxonomía, permitiendo reportar los conteos totales por categoría, su distribución relativa y la co-ocurrencia entre razones.

### Análisis contextual

Una vez clasificados los PRs, se analizará cómo varía el comportamiento según variables de contexto extraídas del dataset: lenguaje de programación (`repository.language`), agente involucrado (`pull_request.agent`), tamaño del PR (`commit_stats_additions + commit_stats_deletions`), tipo de tarea (`pr_task_type.type`) y popularidad del repositorio (`repository.stars`, `repository.forks`).

## Aporte esperado

Este estudio puede aportar en dos niveles. Primero, permite entender mejor los límites actuales de los agentes de IA como participantes del proceso de desarrollo, no solo en términos de frecuencia de rechazo sino de las causas concretas. Segundo, puede ayudar a identificar en qué contextos su uso parece realmente útil y en cuáles todavía implica un costo alto de revisión y corrección.

En ese sentido, la contribución no es solo descriptiva. Los resultados podrían servir para apoyar decisiones de adopción en equipos de desarrollo y también para orientar futuras investigaciones sobre autonomía y confiabilidad de agentes en ingeniería de software.

## Cierre

En resumen, la propuesta no se centra únicamente en contar intervenciones humanas, sino en usar tanto esas intervenciones como las razones de rechazo para inferir algo más importante: cuándo un agente actúa como contribuidor efectivo y cuándo todavía depende de supervisión humana significativa o produce contribuciones que no alcanzan el estándar mínimo de integración. La metodología está diseñada para aprovechar las fuentes de evidencia disponibles en el schema del dataset, reconociendo explícitamente sus limitaciones —como la ausencia de logs directos de CI/CD— y adoptando estrategias alternativas basadas en el análisis textual y la secuencia de eventos.