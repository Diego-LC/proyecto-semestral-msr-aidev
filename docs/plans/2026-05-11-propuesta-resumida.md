# Propuesta resumida

## Título

**¿Qué revela la intervención humana cuando se rechazan los pull requests de agentes de IA?**

## Descripción y contexto

El proyecto estudia pull requests generados por agentes de IA en el dataset `AIDev`, con foco en aquellos que fueron cerrados sin ser mergeados. Este subconjunto permite observar casos donde la contribución del agente no fue aceptada directamente por el equipo de desarrollo.

En vez de medir solo cuántos PRs fueron rechazados, el estudio busca entender **por qué** fueron rechazados y qué revelan esos rechazos sobre las limitaciones actuales de los agentes de IA como contribuidores de software.

## Problema

Los PRs generados por agentes de IA pueden requerir intervención humana antes de ser aceptados o incluso ser rechazados completamente. Sin embargo, la simple presencia de rechazo no explica qué falló ni cuánto esfuerzo adicional implicó para el equipo.

El problema central es que aún no existe una caracterización clara, basada en datos reales, de los motivos por los cuales estos PRs son rechazados. Sin esa taxonomía, es difícil evaluar en qué casos los agentes funcionan como contribuidores útiles y en qué casos generan más trabajo de revisión o corrección.

## Enfoque propuesto

El estudio propone construir una **taxonomía inductiva** de razones de rechazo, es decir, una clasificación que emerge desde los propios datos y no desde categorías definidas previamente.

Para ello, se analizarán comentarios, revisiones y evidencia textual asociada a PRs rechazados. Cada PR seleccionado se transformará en una tarjeta de análisis, que luego será clasificada mediante **card sorting abierto**, una técnica cualitativa que permite agrupar casos similares y descubrir patrones comunes.

Además, se analizará si ciertos motivos de rechazo aparecen con mayor frecuencia según variables como agente, lenguaje de programación, tipo de tarea o complejidad del cambio.

## Metodología resumida

1. Seleccionar PRs rechazados del dataset `AIDev`, considerando PRs cerrados sin merge.
2. Extraer una muestra inicial de 300 PRs con muestreo aleatorio estratificado solo por agente, manteniendo lenguaje, complejidad y tipo de tarea como controles posteriores.
3. Preparar una tarjeta por PR con evidencia textual relevante: comentario de revisión, comentario general, comentario inline, timeline o descripción del PR si no existe mejor evidencia.
4. Cargar las tarjetas en `Labeling Machine` para realizar el proceso de clasificación manual.
5. Aplicar card sorting abierto para crear categorías y subcategorías de motivos de rechazo.
6. Validar la consistencia entre evaluadores usando acuerdo inter-evaluador, como Cohen's kappa o Krippendorff's alpha.
7. Analizar la distribución de categorías por agente, lenguaje, tipo de tarea y complejidad.
8. Cuando sea posible, medir el esfuerzo posterior al rechazo o al retrabajo, considerando tiempo hasta aceptación e intervenciones humanas necesarias.

También se validará una población ampliada de PRs mergeados solo después de cambios al código. Estos casos son posibles de identificar con `merged_at`, commits/retrabajo, reviews y eventos de timeline, pero deben marcarse como `merged_after_rework` para analizarlos separados de los rechazos definitivos.

## Referencia a la propuesta detallada

La versión completa de la propuesta metodológica está disponible en:

[docs/plans/propuesta.md](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/docs/plans/propuesta.md)
