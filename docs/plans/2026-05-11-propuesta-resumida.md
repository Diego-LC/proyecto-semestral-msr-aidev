# Propuesta resumida

## Titulo

**Que revela la intervencion humana cuando los pull requests de agentes de IA requieren retrabajo antes del merge?**

## Descripcion y contexto

El proyecto estudia pull requests generados por agentes de IA en el dataset `AIDev`, con foco en casos `merged_after_rework`: PRs que finalmente fueron mergeados, pero solo despues de commits adicionales y comentarios humanos. Este subconjunto permite observar contribuciones que no fueron aceptadas de manera inmediata.

En vez de medir solo si un PR fue mergeado, el estudio busca entender que problemas aparecieron durante la revision y que revelan esos casos sobre las limitaciones actuales de los agentes de IA como contribuidores de software.

## Problema

Los PRs generados por agentes de IA pueden requerir intervencion humana antes de ser aceptados. Sin embargo, la simple presencia de merge no explica que fallo durante la revision ni cuanto esfuerzo adicional implico para el equipo.

El problema central es que aun no existe una caracterizacion clara, basada en datos reales, de los motivos por los cuales estos PRs requieren retrabajo antes de integrarse. Sin esa taxonomia, es dificil evaluar en que casos los agentes funcionan como contribuidores utiles y en que casos generan mas trabajo de revision o correccion.

## Enfoque propuesto

El estudio propone construir una taxonomia inductiva de razones de retrabajo, es decir, una clasificacion que emerge desde los propios datos y no desde categorias definidas previamente.

Para ello, se analizaran comentarios, revisiones y evidencia textual asociada a PRs aceptados despues de retrabajo. Cada PR seleccionado se transformara en una tarjeta de analisis, que luego sera clasificada mediante card sorting abierto.

Ademas, se analizara si ciertos motivos aparecen con mayor frecuencia segun variables como agente, lenguaje de programacion, tipo de tarea o complejidad del cambio.

## Metodologia resumida

1. Seleccionar PRs `merged_after_rework` del dataset `AIDev`, considerando PRs cerrados y mergeados con commits adicionales y comentarios humanos.
2. Extraer una muestra inicial de 300 PRs con muestreo aleatorio estratificado solo por agente, manteniendo lenguaje, complejidad y tipo de tarea como controles posteriores.
3. Preparar una tarjeta por PR con evidencia textual relevante: comentario de revision, comentario general, comentario inline, timeline o descripcion del PR si no existe mejor evidencia.
4. Completar manualmente la plantilla de categorizacion producida por el flujo de preparacion.
5. Aplicar card sorting abierto para crear categorias y subcategorias de motivos de retrabajo.
6. Validar la consistencia entre evaluadores usando acuerdo inter-evaluador, como Cohen's kappa o Krippendorff's alpha.
7. Analizar la distribucion de categorias por agente, lenguaje, tipo de tarea y complejidad.
8. Cuando sea posible, medir el esfuerzo previo al merge, considerando tiempo hasta aceptacion e intervenciones humanas necesarias.

## Referencia a la propuesta detallada

La version completa de la propuesta metodologica esta disponible en:

[docs/plans/plan-metodologico-card-sorting.md](plan-metodologico-card-sorting.md)
