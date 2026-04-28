# Propuesta Seleccionada para el Proyecto

## Propuesta elegida

Se selecciona la `Propuesta 1`, pero con un enfoque reformulado:

> La intervención humana en PRs generados por agentes de IA no se estudia como fin en sí mismo, sino como una señal observable para estimar la autonomía real, la confiabilidad práctica y la capacidad de integración de esos agentes dentro del proceso de desarrollo de software.

En otras palabras, la pregunta central deja de ser solo "cuánto intervienen los humanos" y pasa a ser "qué nos dice esa intervención sobre la capacidad real de los agentes para contribuir de forma útil y aceptable en un proyecto".

## Título tentativo

**¿Qué revela la intervención humana sobre la autonomía de los agentes de IA como contribuidores de software? Un estudio de pull requests en AIDev**

## Motivación

El dataset `AIDev` ofrece una oportunidad concreta para observar cómo se comportan en la práctica los pull requests creados por agentes de IA. Sin embargo, medir únicamente la frecuencia de intervención humana sería insuficiente: por sí sola, esa medida no explica por qué los resultados importan ni qué se puede aprender de ellos.

El valor del estudio aparece cuando la intervención humana se interpreta como una señal del nivel de autonomía del agente. Si la mayoría de los PRs necesita cambios humanos significativos antes de integrarse, entonces los agentes todavía operan con una autonomía limitada y su uso implica un costo adicional de supervisión y corrección. Si, en cambio, una fracción importante de PRs puede integrarse sin cambios relevantes, eso sugiere que los agentes ya pueden actuar como contribuidores efectivos en ciertos contextos.

Además, es razonable esperar que este comportamiento no sea uniforme. La necesidad de intervención podría variar según el lenguaje, el tamaño del PR, el tipo de repositorio, la popularidad del proyecto o el agente que generó el cambio. Identificar esos contextos haría que los resultados fueran útiles tanto para investigadores como para equipos que evalúan incorporar agentes a sus flujos de desarrollo.

## Objetivo general

Evaluar en qué medida los pull requests generados por agentes de IA pueden integrarse como contribuciones efectivas de software, usando la intervención humana como señal para estimar su autonomía práctica y sus límites actuales.

## Objetivos específicos

1. Medir qué proporción de PRs generados por agentes es integrable sin cambios humanos significativos.
2. Caracterizar qué tipos de intervenciones significativas realizan los humanos cuando el PR no es integrable tal como fue propuesto.
3. Analizar cómo cambia este comportamiento según factores de contexto, como lenguaje, tamaño del PR, agente y características del repositorio.
4. Estudiar cómo el nivel de intervención humana se relaciona con el resultado final del PR y con el tiempo que tarda en resolverse o integrarse.

## Preguntas de investigación

1. ¿Qué proporción de los PRs creados por agentes de IA puede integrarse sin intervención humana significativa?
2. Cuando un PR no es integrable en su estado original, ¿qué tipos de intervenciones significativas son necesarias para hacerlo aceptable?
3. ¿Cómo varía la necesidad y el tipo de intervención según el contexto del PR, por ejemplo lenguaje, tamaño, agente autor o características del repositorio?
4. ¿Qué relación existe entre el nivel de intervención humana y el destino final del PR, como merge, cierre sin merge o mayor tiempo de integración?
5. ¿En qué escenarios los agentes se comportan más como contribuidores efectivos y en cuáles siguen requiriendo supervisión intensiva?

## Idea central del estudio

La contribución principal del proyecto no será reportar simplemente cuántos PRs reciben cambios humanos, sino proponer una lectura más útil del fenómeno:

- `baja intervención significativa` sugiere mayor autonomía práctica del agente;
- `alta intervención significativa` sugiere menor autonomía y mayor costo de adopción;
- `patrones distintos según contexto` permiten identificar cuándo el uso de agentes es más conveniente y cuándo todavía no lo es.

Eso permite conectar los resultados con decisiones reales, por ejemplo la adopción de agentes en empresas, la definición de flujos de revisión o la identificación de límites actuales para futuras investigaciones.

## Definiciones operacionales

Para que el estudio sea más riguroso, no se asumirá que cualquier cambio humano posterior equivale a una intervención relevante. Se distinguirán al menos dos niveles:

### Intervención superficial

Cambios que no alteran de forma importante la capacidad del PR para ser aceptado, por ejemplo:

- formateo;
- ajustes menores de documentación;
- cambios cosméticos o renombres triviales;
- actualizaciones automáticas de merge o sincronización;
- pequeños ajustes de configuración sin impacto funcional claro.

### Intervención significativa

Cambios que sí modifican la aceptabilidad o corrección del PR, por ejemplo:

- correcciones de lógica o bugs;
- incorporación o corrección de tests relevantes;
- cambios en configuración, build o CI que afectan la ejecución;
- modificaciones de código que alteran comportamiento, contratos o funcionalidad;
- ajustes relacionados con seguridad, validación o manejo de errores.

Con esto, un PR podrá considerarse `integrable sin cambios significativos` si llega a merge sin modificaciones humanas o si solo recibe intervenciones superficiales antes de integrarse.

## Método propuesto

1. Seleccionar del dataset `AIDev` los PRs con trazabilidad suficiente de commits, autores, estado final y metadatos del repositorio.
2. Reconstruir la secuencia temporal de cada PR para distinguir los aportes del agente y las modificaciones posteriores hechas por humanos.
3. Diseñar una clasificación de intervenciones basada en archivos modificados, tipo de cambio, rutas afectadas y, cuando aporte valor, mensajes de commit o comentarios de revisión.
4. Separar las intervenciones humanas en superficiales y significativas, y dentro de las significativas identificar subtipos como corrección funcional, testing o configuración.
5. Calcular métricas descriptivas como:
   - proporción de PRs integrables sin cambios significativos;
   - frecuencia y distribución de tipos de intervención;
   - tasa de merge según nivel de intervención;
   - tiempo hasta resolución o integración.
6. Analizar variación por cofactores, por ejemplo lenguaje de programación, tamaño del PR, popularidad del repositorio, agente y tamaño del proyecto.
7. Validar manualmente una muestra estratificada de PRs para comprobar que la clasificación automática distingue de forma razonable entre intervención superficial y significativa.
8. Si el tiempo lo permite, complementar con modelos estadísticos simples para controlar el efecto de cofactores sobre la probabilidad de merge o de intervención significativa.

## Variables y señales principales

- `Variable principal de interpretación`: nivel de intervención humana necesaria antes del resultado final del PR.
- `Señal de autonomía`: proporción de PRs integrables sin cambios significativos.
- `Resultados del PR`: merge, cierre sin merge, tiempo hasta resolución.
- `Factores de contexto`: agente, lenguaje, tamaño del cambio, cantidad de archivos, popularidad del repositorio y tipo de proyecto.

## Aporte esperado

Este proyecto puede generar conclusiones con valor práctico y académico:

1. Entregar evidencia sobre cuánto se puede confiar hoy en agentes de IA como contribuidores de software.
2. Identificar en qué contextos los agentes parecen ser útiles y en cuáles todavía generan sobrecarga de revisión o corrección.
3. Ofrecer una forma metodológicamente más crítica de estudiar PRs de agentes, evitando tratar toda intervención humana como equivalente.
4. Producir resultados que puedan informar decisiones de adopción en equipos de desarrollo y servir como base para trabajos posteriores.

## Factibilidad para el curso

La propuesta sigue siendo viable para un equipo de dos personas porque mantiene un enfoque empírico claro, se apoya en un dataset ya disponible y no exige construir un modelo complejo como componente obligatorio. El principal desafío está en operacionalizar bien la diferencia entre intervención superficial y significativa, por lo que conviene:

- acotar inicialmente el análisis a un subconjunto manejable del dataset;
- definir una guía de codificación simple y explícita;
- usar validación manual sobre una muestra para reforzar la credibilidad del análisis.

## Riesgos metodológicos y mitigaciones

- `Riesgo`: asumir que todo cambio humano implica una corrección importante.
  `Mitigación`: distinguir explícitamente entre intervención superficial y significativa, y validar esa clasificación con una muestra manual.
- `Riesgo`: atribuir incorrectamente la autoría humana o del agente en commits posteriores.
  `Mitigación`: usar metadatos de autor, patrones de bots y revisión manual de casos ambiguos.
- `Riesgo`: que las heurísticas dependan demasiado de convenciones de nombres o estructura de archivos.
  `Mitigación`: acotar el estudio a ecosistemas donde esas señales sean razonablemente estables o reportar la limitación de forma explícita.
- `Riesgo`: confundir asociación con causalidad al relacionar intervención y resultado del PR.
  `Mitigación`: presentar los resultados como evidencia observacional y controlar cofactores básicos en el análisis cuando sea posible.

## Resumen de la reformulación

La propuesta seleccionada ya no se presenta como un estudio sobre "rescatar PRs de agentes", sino como una investigación sobre la autonomía real de esos agentes dentro del proceso de desarrollo. La intervención humana sigue siendo el dato observable, pero ahora está al servicio de una pregunta más profunda y defendible: cuándo los agentes funcionan como contribuidores efectivos y cuándo siguen dependiendo de supervisión humana sustantiva.

## Fuentes base

- MSR 2026 Mining Challenge: <https://2026.msrconf.org/track/msr-2026-mining-challenge#Call-for-Mining-Challenge-Papers>
- AIDev preprint: <https://arxiv.org/abs/2507.15003>
