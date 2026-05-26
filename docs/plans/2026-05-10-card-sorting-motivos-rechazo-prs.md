# Plan Metodológico Versionado: Card Sorting para Categorizar Motivos de Rechazo de PRs

## Resumen

El estudio debe construir una taxonomía inductiva de razones de rechazo de PRs generados por agentes de IA, usando card sorting abierto sobre una muestra estadísticamente controlada. La unidad de análisis será una "tarjeta" por PR rechazado, con evidencia textual suficiente: comentarios de revisión, comentarios inline, estado de revisión, título/body del PR, URL y metadatos contextuales.

El flujo recomendado es híbrido: primero card sorting abierto para descubrir categorías, luego etiquetado controlado en `Labeling Machine` para aplicar la taxonomía final y medir consistencia entre evaluadores.

Fuentes usadas: [docs/card-sorting.pdf](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/docs/card-sorting.pdf), [propuesta.md](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/docs/plans/propuesta.md), [Labeling Machine README](https://github.com/emadpres/labeling-machine), [models.py](https://github.com/emadpres/labeling-machine/blob/minimal/webapp/src/database/models.py), [initdb.py](https://github.com/emadpres/labeling-machine/blob/minimal/webapp/src/database/initdb.py), [routes_labeling.py](https://github.com/emadpres/labeling-machine/blob/minimal/webapp/src/routes/routes_labeling.py).

## Estrategia De Muestreo

La población de estudio son los PRs rechazados del dataset. Operacionalmente, esto significa seleccionar PRs con:

```text
state = closed
merged_at IS NULL
```

Es decir, PRs que fueron cerrados y no llegaron a merge. Desde esa población se debe extraer una muestra que sea aleatoria, pero también equilibrada. Si se toma una muestra aleatoria simple, existe el riesgo de que la muestra quede dominada por los agentes, lenguajes o repositorios más frecuentes. Eso puede ocultar motivos de rechazo menos comunes, pero importantes.

Por eso se recomienda usar `muestreo aleatorio estratificado` (dividir la población en grupos comparables y luego tomar casos al azar dentro de cada grupo). Cada grupo se llama `estrato`. Por ejemplo, un estrato podría estar formado por PRs del mismo agente, lenguaje y nivel de complejidad.

Variables de control recomendadas:

- `agent`: agente que generó el PR.
- `language`: lenguaje principal del repositorio.
- `change_complexity_bin`: complejidad del cambio agrupada como baja, media o alta. Puede calcularse usando cantidad de commits, archivos modificados, líneas agregadas/eliminadas o información de `pr_commit_details`.
- `repo_popularity_bin`: popularidad del repositorio agrupada como baja, media o alta, por ejemplo usando `stars` o percentiles (divisiones ordenadas del dataset).
- `created_period`: periodo temporal del PR, por ejemplo mes de creación o terciles de `created_at` (tres grupos: antiguo, intermedio y reciente).
- `task_type`: si `pr_task_type` está disponible.

### Método Principal: Muestreo Aleatorio Estratificado

1. Filtrar todos los PRs rechazados.
2. Agregar a cada PR sus variables de control: agente, lenguaje, complejidad, popularidad, periodo y tipo de tarea.
3. Convertir variables numéricas en grupos simples. Por ejemplo, la complejidad puede quedar como baja, media o alta.
4. Crear estratos combinando variables clave. Una combinación inicial razonable es:

```text
agent + language + change_complexity_bin + created_period
```

5. Tomar PRs al azar dentro de cada estrato usando una semilla fija:

```text
random_seed = 20260510
```

La semilla aleatoria permite que otra persona pueda reconstruir la misma muestra y verificar el procedimiento.

La cantidad de PRs a tomar por estrato se calcula con asignación proporcional y un mínimo por grupo. La fórmula es:

```text
n_h = max(m, round(n * N_h / N))
```

Donde:

- `n_h`: cantidad de PRs a tomar del estrato `h`.
- `n`: tamaño total deseado de la muestra.
- `N_h`: cantidad total de PRs existentes en el estrato `h`.
- `N`: cantidad total de PRs rechazados elegibles.
- `m`: mínimo de PRs por estrato, por ejemplo `3` o `5`.

En palabras simples: si un grupo representa cerca del 20% de los PRs rechazados, debería representar cerca del 20% de la muestra. Pero si un grupo es pequeño, se le reserva un mínimo de casos para no desaparecer del análisis.

Si la suma final supera el tamaño de muestra deseado, se reducen los estratos más grandes manteniendo el mínimo de los estratos pequeños.

### Método Alternativo Si Hay Demasiados Estratos

Si combinar muchas variables produce grupos demasiado pequeños, se recomienda simplificar el muestreo usando solo:

```text
agent + language + change_complexity_bin
```

En ese caso, `repo_popularity_bin`, `created_period` y `task_type` no se usan para formar la muestra, pero sí se revisan después para confirmar que la muestra no quedó sesgada. Este control posterior consiste en comparar porcentajes entre el dataset completo y la muestra.

### Control De Calidad De La Muestra

Después de extraer la muestra, se debe comparar la distribución del dataset completo contra la muestra en:

- agente;
- lenguaje;
- complejidad;
- popularidad del repositorio;
- periodo temporal;
- tipo de tarea.

Si la muestra se aleja demasiado del dataset original, se repite la extracción ajustando cuotas por estrato. Este paso debe quedar documentado junto con la fecha de ejecución, el código usado y la semilla aleatoria.

Tamaño recomendado:

- `n = 150` tarjetas para card sorting abierto inicial.
- `n = 250-300` para etiquetado cerrado posterior si el tiempo lo permite.
- Con población aproximada de `9.575` PRs rechazados, `n = 150` da un margen de error cercano a `8%` con 95% de confianza. El margen de error indica cuánta variación podría existir entre la muestra y la población completa. Con `n = 300`, el margen baja a cerca de `5.6%`.

No se debe interpretar la frecuencia de categorías como verdad absoluta del fenómeno si el card sorting se hace solo sobre `150` casos. La frecuencia sirve como señal descriptiva, no como prueba causal.

## Preparación De Datos

La preparación de datos debe producir una tabla final llamada `rejection_cards`, donde cada fila representa una tarjeta a clasificar. La tarjeta puede representar un PR completo o un motivo específico de rechazo dentro de un PR.

Pasos recomendados:

1. Cargar las tablas necesarias del dataset: `pull_request`, `repository`, `pr_reviews`, `pr_review_comments`, `pr_comments`, `pr_commits`, `pr_commit_details`, `pr_task_type` y, si aplica, `pr_timeline`.
2. Filtrar solo PRs rechazados usando `state = closed` y `merged_at IS NULL`.
3. Agregar contexto de cada PR: agente, lenguaje, repositorio, fecha de creación, fecha de cierre, cantidad de commits, tamaño del cambio y tipo de tarea.
4. Extraer evidencia textual desde comentarios de revisión, comentarios inline, comentarios generales, título y descripción del PR.
5. Crear tarjetas con identificador único. Si un PR tiene dos razones de rechazo claramente distintas, crear dos tarjetas con el mismo `pr_id` pero distinto `card_id`, por ejemplo `PR123-A` y `PR123-B`.
6. Separar casos sin evidencia textual suficiente. Estos casos no deben forzarse dentro de categorías técnicas; se marcan como `sin_evidencia_suficiente`.

Cada fila de `rejection_cards` debe contener:

```text
card_id
pr_id
repo_id
html_url
agent
language
task_type
created_at
closed_at
complexity_bin
repo_popularity_bin
review_state
evidence_text
evidence_source
context_summary
needs_manual_context_check
```

Reglas de limpieza:

- Excluir duplicados exactos por `pr_id`.
- Mantener PRs sin evidencia textual como grupo separado `sin_evidencia_suficiente`, no mezclarlos con PRs clasificables.
- Unificar texto desde `pr_reviews.body`, `pr_review_comments.body`, `pr_comments.body`, título/body del PR y eventos relevantes de `pr_timeline`.
- Limpiar Markdown excesivo, logs largos, stack traces repetidos y texto generado automáticamente, pero conservar fragmentos técnicos que expliquen el rechazo.
- Si un PR tiene varias evidencias, priorizar en este orden: `CHANGES_REQUESTED`, comentario humano inline, comentario humano general, comentario bot, body/título.
- Guardar siempre el texto original y el texto limpio para trazabilidad.

La tarjeta debe representar una sola idea principal. Esto facilita el card sorting, porque cada tarjeta se puede mover a una categoría sin mezclar varios problemas distintos.

## Uso De Labeling Machine

`Labeling Machine` es una aplicación Flask ligera. Su README indica que se adapta modificando tres zonas: el modelo `Artifact`, la carga en `initdb.py`, y la visualización/formulario de etiquetado. La herramienta usa SQLite por defecto, SQLAlchemy, y corre con `flask initdb` y `flask run`; también ofrece despliegue con Docker.

Adaptación mínima para este estudio:

- En `Artifact`, agregar campos de tarjeta: `pr_id`, `html_url`, `agent`, `language`, `task_type`, `evidence_text`, `context_summary`, `complexity_bin`.
- En `LabelingData`, guardar: `category_parent`, `subcategory`, `confidence`, `rationale`, `needs_discussion`, `username`, `duration_sec`.
- En `initdb.py > import_my_data()`, cargar `rejection_cards.csv` en la tabla `Artifact`.
- En `artifact.html`, mostrar evidencia textual, metadatos, link al PR y contexto del repositorio.
- En `labeling_layout.html`, usar un formulario con selección de categoría/subcategoría, campo de comentario metodológico y opción de marcar caso ambiguo.
- En `routes_labeling.py > label()`, guardar la etiqueta y permitir actualizar una etiqueta previa del mismo evaluador.

Uso dentro del proceso:

- Durante card sorting abierto, usar `Labeling Machine` como soporte digital para presentar tarjetas, registrar grupos emergentes como etiquetas y tomar notas.
- Durante etiquetado cerrado, congelar la taxonomía y usar la herramienta para que dos evaluadores clasifiquen independientemente cada tarjeta.
- Exportar `LabelingData` desde SQLite a CSV para análisis de acuerdo inter-evaluador y métricas finales.

## Protocolo De Card Sorting

Seguir el enfoque del PDF de Zimmermann: preparación, ejecución y análisis. El método recomendado es `card sorting abierto`, que significa que las categorías no se definen antes de mirar los datos, sino que nacen desde las tarjetas revisadas.

En este estudio, cada tarjeta contiene evidencia sobre un posible motivo de rechazo de un PR. El objetivo del card sorting es agrupar tarjetas similares hasta construir una taxonomía, es decir, una organización de categorías y subcategorías.

Preparación:

- Crear tarjetas con un identificador único y metadatos mínimos.
- Asegurar una idea por tarjeta.
- Mantener información contextual que ayude al clasificador: agente, lenguaje, tipo de tarea, URL y evidencia textual.
- Ordenar tarjetas aleatoriamente dentro de cada estrato para evitar sesgo temporal o de repositorio.

Ejecución abierta:

- Hacer una sesión de calibración con 20 tarjetas entre ambos evaluadores. La calibración sirve para alinear criterios antes de clasificar el resto.
- Clasificar tarjetas sin categorías predefinidas. Si una tarjeta se parece a un grupo existente, se asigna a ese grupo.
- Crear un grupo nuevo cuando una tarjeta no calce razonablemente en los grupos existentes.
- Revisar grupos grandes para decidir si deben dividirse en subgrupos más específicos.
- Fusionar grupos que expresen la misma idea con nombres distintos.
- Renombrar grupos para que el nombre describa claramente el motivo de rechazo.
- Mantener grupos especiales: `sin evidencia suficiente`, `rechazo no técnico`, `ambiguo`.
- Registrar decisiones difíciles en notas metodológicas. Esto permite explicar después por qué una tarjeta quedó en cierta categoría.
- Evitar sesiones de más de 2-3 horas; si hay muchas tarjetas, dividir en bloques.

Análisis por afinidad:

- Revisar consistencia interna de cada grupo. Esto significa comprobar que las tarjetas de una misma categoría realmente hablen de un problema similar.
- Fusionar grupos equivalentes y separar grupos demasiado amplios.
- Construir una jerarquía de dos niveles: `categoria_padre` y `subcategoria`. Por ejemplo, una categoría padre podría ser `problema funcional`, con subcategorías como `logica incorrecta` o `caso borde no manejado`.
- Congelar la taxonomía cuando los evaluadores acuerden que los grupos son estables. Desde ese momento no se crean categorías nuevas sin justificarlo.
- Crear un `codebook` (manual de codificación) con definición de cada categoría, criterios de inclusión, criterios de exclusión y ejemplos.

## Etiquetado Y Validación

Después del card sorting abierto, ejecutar etiquetado cerrado sobre la muestra completa o una segunda muestra. El etiquetado cerrado significa que los evaluadores ya no crean categorías libremente, sino que clasifican cada tarjeta usando la taxonomía congelada.

Diseño recomendado:

- Dos evaluadores etiquetan de forma independiente el 100% de las tarjetas si `n <= 150`.
- Si `n > 300`, ambos etiquetan al menos 30%-40% solapado y el resto se divide.
- Cada tarjeta recibe `categoria_padre`, `subcategoria`, `confidence` (nivel de seguridad del evaluador) y `rationale` (breve justificación).
- Los desacuerdos se resuelven en una reunión de adjudicación, pero se conserva la etiqueta original de cada evaluador.

Métricas de consistencia:

El `acuerdo inter-evaluador` mide cuánto coinciden dos o más personas al clasificar las mismas tarjetas. Es importante porque muestra si la taxonomía es clara y aplicable por más de una persona.

- Usar `Cohen's kappa` para dos evaluadores. Esta métrica mide acuerdo corrigiendo el acuerdo que podría ocurrir por azar.
- Usar `Krippendorff's alpha` si hay más de dos evaluadores o si algunas tarjetas quedan sin etiqueta.
- Calcular acuerdo en dos niveles: categoría padre y subcategoría.
- Interpretación práctica: menor a `0.60` indica acuerdo débil; entre `0.60` y `0.80` indica acuerdo aceptable; mayor a `0.80` indica acuerdo fuerte.
- Si el acuerdo queda bajo `0.60`, revisar el `codebook`, aclarar definiciones y repetir una ronda de calibración.

Entregables de validación:

- Matriz de confusión entre evaluadores.
- Lista de categorías con mayor desacuerdo.
- Versión final del codebook.
- Dataset final con `card_id`, `pr_id`, etiquetas originales, etiqueta adjudicada y evidencia textual.

## Análisis De Resultados

Transformar etiquetas en análisis cualitativo y cuantitativo.

Análisis descriptivo:

- Frecuencia de categorías padre y subcategorías.
- Distribución por agente, lenguaje, tipo de tarea y complejidad.
- Proporción de casos sin evidencia textual suficiente.
- Ejemplos representativos por categoría, evitando sobrecitar texto largo.

Análisis de esfuerzo:

- Calcular tiempo entre `created_at` y `closed_at` para PR rechazado.
- Para casos que luego se aceptan, estimar tiempo hasta aceptación usando PRs relacionados por `related_issue`, repositorio y secuencia temporal.
- Medir intervenciones: commits posteriores, autores humanos distintos, rondas de review, `CHANGES_REQUESTED`, comentarios humanos.
- Comparar esfuerzo por categoría de rechazo.

Análisis estadístico:

- Usar tablas cruzadas para comparar categorías con agente, lenguaje o tipo de tarea.
- Usar pruebas `chi-square` o Fisher para evaluar si dos variables parecen estar asociadas. Por ejemplo, si ciertos agentes concentran más rechazos de una categoría específica.
- Usar Kruskal-Wallis o Mann-Whitney para comparar tiempos entre categorías. Estas pruebas sirven cuando los tiempos no siguen una distribución normal, algo común en datos de PRs.
- Reportar tamaños de efecto, no solo `p-values`. El tamaño de efecto indica que tan grande es la diferencia observada.
- Si hay muestra suficiente, usar regresión logística para modelar la probabilidad de rechazo según variables de contexto. Esta técnica estima si ciertas variables se asocian con mayor o menor probabilidad de rechazo, pero no demuestra causalidad por sí sola.

Cautela metodológica:

- No concluir que una categoría es "más importante" solo porque aparece más.
- Una categoría frecuente indica visibilidad en la muestra, no necesariamente severidad o impacto.
- Una categoría poco frecuente puede ser muy relevante si produce mucho retrabajo, demora la aceptación o evidencia una limitación importante del agente.
- Los casos sin comentario explícito deben reportarse como limitación, no forzarse dentro de categorías técnicas.

## Supuestos Y Decisiones Fijadas

- Se usará card sorting abierto para descubrir categorías y etiquetado cerrado para validarlas.
- La unidad primaria será una tarjeta por motivo de rechazo, no necesariamente una tarjeta por PR si hay múltiples motivos claros.
- Se trabajará inicialmente con `n = 150` tarjetas y, si el tiempo alcanza, se extenderá a `n = 300`.
- La muestra será estratificada por agente, lenguaje, complejidad, popularidad del repositorio y periodo temporal.
- `Labeling Machine` se usará como herramienta de registro y etiquetado, no como herramienta automática de descubrimiento de categorías.
- La salida final será una taxonomía jerárquica, un dataset etiquetado y un análisis de patrones de rechazo y esfuerzo de corrección.


### Comentarios del profesor 12-05
- Proyecto
- Metodologia
    * Filtro de Datos: (Filtros, muestra (1000 -> 300 + 15 -> 315))
    * Cómo analizarlo: (Cómo, 15 casos)

Metodologia: 
- Objetivos
- Preguntas
- Como respondo

Goal standard: se tiene un conjunto de datos que antes no tenia etiquetas y ahora si. Se puede crear un modelo con la muestra inicial y al validarlo se puede hacer con el total de datos.

Hacer clasificacion solo por agente, no por complejidad de cada agente independiente.
Nos interesan dos casos: 
- PR Rechazado? no se sabe si existe rechazo en primera instancia -> PR Aceptado (cuenta con: "created_at", "closed_at" y "merged_at")
- PR Rechazado -> PR Rechazado (solo tenemos "created_at", "closed_at")

deberiamos avanzar hasta llegar a los 15 casos de resultado.