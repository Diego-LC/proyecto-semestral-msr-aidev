# Preparación del póster académico A0

Este documento consolida los pendientes necesarios antes de construir el póster académico final del proyecto. El póster se realizará en **LaTeX**, en **español**, con formato **A0** y con estilo visual institucional de la **Universidad de La Frontera**. La skill recomendada para esta etapa es `latex-posters`, orientada a pósters académicos con `beamerposter`, `tikzposter` o `baposter`.

## Fuentes revisadas

- `docs/notas.md`: lista de pendientes metodológicos, narrativos y visuales.
- `docs/presentacion_poster/presentacion-final-aidev.pptx.pdf`: presentación actual del proyecto.
- `docs/presentacion_poster/reporte.pdf`: referencia académica sobre usabilidad de asistentes de programación con IA.
- `docs/presentacion_poster/2025ASE-Qrirx.pdf`: referencia visual de póster académico tipo conferencia.
- `docs/taxonomia-final-merged-after-rework.md`: taxonomía final de motivos de retrabajo.

## Análisis de cumplimiento en la presentación actual

La presentación ya cubre varios puntos solicitados para el póster, pero todavía requiere consolidación, corrección ortográfica y adaptación al formato A0.

| Elemento requerido | Estado en el PPT | Observación para el póster |
| --- | --- | --- |
| Contexto y problema | Cumplido | La diapositiva de motivación explica que los PRs de agentes IA pueden requerir intervención humana antes del merge. |
| Pregunta principal | Cumplido | Está formulada explícitamente: motivos de retrabajo humano en PRs de agentes IA antes de su integración. |
| Pregunta complementaria | Cumplido | Está formulada en términos de esfuerzo y tiempo hasta el merge. |
| Objetivo general | Cumplido | Aparece como construcción de taxonomía inductiva y relación con esfuerzo/tiempo. |
| Objetivos específicos | Parcial | El PPT muestra cinco objetivos específicos; para el póster conviene resumirlos a tres. |
| Metodología en tres etapas | Cumplido | La presentación usa Preparation, Execution y Analysis. |
| Criterios de inclusión/exclusión | Cumplido | Se explican fuente, caso operacional, inclusión y exclusión. |
| Embudo de datos | Cumplido | Existe tabla/gráfico desde universo AIDev hasta muestra. |
| Fórmula de muestreo estratificado | Cumplido | Se muestra `n_h = round(n × N_h / N)`. |
| Card sorting | Cumplido | Se explica preparación, ejecución, análisis y soundness. |
| Resultados de taxonomía | Cumplido | El PPT incluye imágenes de treemap y barras por categorías. |
| Discusión | Pendiente | Falta contrastar los hallazgos con literatura previa sobre asistentes IA y revisión de código. |
| Implicancias | Pendiente | Deben explicitarse recomendaciones para desarrolladores, investigadores y constructores de herramientas. |
| Limitaciones y amenazas a la validez | Pendiente | Deben incluirse en el póster para no sobregeneralizar resultados cualitativos. |
| Nombres autoexplicativos de categorías | Parcial | Hay nombres legibles en figuras, pero falta una leyenda completa de categorías padre e hijas. |
| Ortografía y tildes | Pendiente | El PDF presenta errores de codificación y palabras sin tilde; deben corregirse en el póster final. |

## Decisiones para el póster final

- **Formato:** A0 vertical (841 x 1189 mm) en LaTeX.
- **Idioma:** español.
- **Estilo visual:** sobrio, inspirado en artículo académico tipo ACM: fondo blanco, cabecera textual, reglas finas, tablas limpias y dos columnas principales.
- **Visual principal:** barras horizontales, tablas compactas y diagramas TikZ autocontenidos; el póster no depende de imágenes externas en Overleaf.
- **Visuales secundarios:** diagrama metodológico, embudo de datos, cuotas por agente, protocolo de card sorting y tablas completas de categorías/subcategorías.
- **Extensión textual:** densidad media-alta para ocupar el A0 vertical, con frases breves, etiquetas autoexplicativas y lectura en dos columnas similar al reporte académico de referencia.

## Estructura recomendada del póster A0

1. **Título, autores y afiliación.**
   - Título propuesto: *Taxonomía de motivos de retrabajo en pull requests de agentes de IA*.
   - Autores: Javier Alcalde y Diego Labrin.
   - Afiliación: Departamento de Computación e Informática, Universidad de La Frontera.
2. **Contexto y problema.**
   - Los agentes IA aceleran la generación de PRs, pero parte de esos PRs requiere intervención humana antes del merge.
3. **Preguntas de investigación.**
   - RQ1: ¿Qué motivos de retrabajo humano emergen en PRs de agentes IA antes de su integración?
   - RQ2: ¿Cómo se relacionan esos motivos con esfuerzo y tiempo hasta el merge?
4. **Metodología.**
   - Preparation: AIDev, filtros, muestra estratificada y tarjetas.
   - Execution: card sorting abierto con evidencia textual.
   - Analysis: consolidación de taxonomía y métricas.
5. **Datos y muestra.**
   - Universo AIDev: 33.596 PRs.
   - Población operacional `merged_after_rework`: 3.166 PRs.
   - Muestra estratificada: 300 PRs, seed `20260510`.
6. **Resultado principal.**
   - Taxonomía de dos niveles con categorías padre e hijas.
   - Las cuatro primeras familias concentran 228 de 300 casos (76%).
7. **Leyenda de taxonomía.**
   - Usar las tablas de nombres autoexplicativos definidas en este documento.
8. **Discusión e implicancias.**
   - El retrabajo no se limita a errores funcionales: también incluye CI, estilo, pruebas, diseño, documentación y reglas de integración.
9. **Limitaciones y reproducibilidad.**
   - Resultado asistido, sin consenso interevaluador definitivo; muestra estratificada y trazabilidad completa en el repositorio.

## Nombres autoexplicativos para categorías padre

Estos nombres deben usarse en el póster en lugar de las claves internas con guion bajo. Las claves se conservan solo para trazabilidad con los archivos del repositorio.

| Código visual | Clave interna | Nombre para el póster | Definición breve |
| --- | --- | --- | --- |
| P1 | `validacion_calidad_ci` | Validación, calidad y CI | Retrabajo por fallos de integración continua, build, tests, lint, formato, estilo o ausencia de pruebas suficientes. |
| P2 | `implementacion_logica` | Corrección de implementación y lógica | Cambios requeridos porque el código no resolvía completamente la lógica esperada, casos borde, compatibilidad, rendimiento o comportamiento de interfaz. |
| P3 | `arquitectura_diseno` | Diseño, alcance y reutilización | Ajustes relacionados con estructura de solución, diseño de API/modelo, duplicación, reutilización o exceso de alcance. |
| P4 | `proceso_gobernanza` | Gobernanza del PR y coordinación de merge | Retrabajo causado por reglas del repositorio, aprobaciones, orden de integración, dependencias entre PRs o coordinación humana. |
| P5 | `dependencias_versionado` | Dependencias y versionado | Cambios requeridos por dependencias, versiones, actualizaciones o compatibilidad entre paquetes. |
| P6 | `documentacion_descripcion` | Documentación y descripción del cambio | Retrabajo por documentación, descripción del PR o explicación técnica incompleta, incorrecta o insuficiente. |
| P7 | `configuracion_automatizacion` | Configuración y automatización | Ajustes en configuración de CI, despliegue, scripts, workflows o automatizaciones del proyecto. |
| P8 | `seguridad_permisos` | Seguridad, permisos y validaciones | Cambios asociados a permisos, validaciones, controles de seguridad o manejo seguro de datos/acciones. |
| P9 | `mantenimiento_refactor` | Mantenimiento menor y refactorización | Limpieza, renombrado, simplificación o refactorizaciones pequeñas solicitadas durante la revisión. |
| P10 | `evidencia_insuficiente` | Evidencia insuficiente | Casos donde la evidencia textual disponible no permite determinar con seguridad el motivo principal de retrabajo. |

## Nombres autoexplicativos para subcategorías

| Código visual | Categoría padre | Clave interna | Nombre para el póster | Definición breve |
| --- | --- | --- | --- | --- |
| S1 | P1 | `fallos_ci_build_o_tests` | Fallos de CI, build o tests | La revisión o integración se detuvo por fallos automatizados, errores de compilación, build o pruebas existentes. |
| S2 | P1 | `lint_formato_o_estilo` | Lint, formato y estilo de código | El retrabajo se debió a reglas de formato, estilo, convenciones, lint o presentación del código. |
| S3 | P1 | `pruebas_faltantes_o_insuficientes` | Pruebas faltantes o insuficientes | El PR necesitó agregar, corregir o ampliar pruebas para cubrir el cambio. |
| S4 | P2 | `manejo_errores_o_casos_borde` | Manejo de errores y casos borde | El cambio no consideraba errores, entradas excepcionales, estados límite o rutas alternativas. |
| S5 | P2 | `compatibilidad_o_migracion` | Compatibilidad o migración | El retrabajo buscó mantener compatibilidad, adaptar migraciones o resolver diferencias entre versiones/entornos. |
| S6 | P2 | `rendimiento_concurrencia_o_recursos` | Rendimiento, concurrencia o recursos | Se solicitaron ajustes por uso de recursos, eficiencia, concurrencia, bloqueos o escalabilidad. |
| S7 | P2 | `ui_ux_o_frontend` | UI/UX y comportamiento frontend | El cambio requirió ajustar interfaz, experiencia de usuario, presentación visual o comportamiento del frontend. |
| S8 | P2 | `correccion_funcional` | Corrección funcional de lógica | El código no implementaba correctamente la funcionalidad esperada y necesitó corrección directa. |
| S9 | P3 | `duplicacion_o_falta_de_reutilizacion` | Duplicación o falta de reutilización | El PR duplicaba lógica existente o no reutilizaba abstracciones, helpers o patrones ya disponibles. |
| S10 | P3 | `reduccion_alcance_o_sobrecodigo` | Reducción de alcance o sobrecódigo | La revisión pidió eliminar complejidad, comportamiento innecesario o cambios fuera del alcance esperado. |
| S11 | P3 | `diseno_api_modelo_o_arquitectura` | Diseño de API, modelo o arquitectura | Se solicitó ajustar contratos, modelos, interfaces, separación de responsabilidades o estructura arquitectónica. |
| S12 | P4 | `requisito_formal_o_gobernanza` | Requisito formal o regla del repositorio | El PR debía cumplir políticas, plantillas, aprobaciones, checks obligatorios o reglas de contribución. |
| S13 | P4 | `dependencia_u_orden_de_merge` | Dependencia u orden de merge | El retrabajo dependía de otro PR, rama, cambio previo, sincronización o secuencia de integración. |
| S14 | P4 | `revision_o_aprobacion_pendiente` | Revisión o aprobación pendiente | La integración se retrasó o requirió cambios por falta de revisión, aprobación o respuesta humana. |
| S15 | P5 | `dependencias_o_versionado` | Dependencias o versionado | Se necesitó modificar paquetes, versiones, locks, compatibilidad de dependencias o actualizaciones. |
| S16 | P6 | `documentacion_o_descripcion_incompleta` | Documentación o descripción incompleta | La descripción, documentación, comentario o explicación del cambio era insuficiente, errónea o poco clara. |
| S17 | P7 | `configuracion_ci_o_automatizacion` | Configuración de CI o automatización | El PR requería ajustes en pipelines, workflows, scripts, despliegue o configuración automatizada. |
| S18 | P8 | `seguridad_permisos_o_validacion` | Seguridad, permisos o validación | La revisión pidió reforzar permisos, validaciones, autorización, sanitización o controles de seguridad. |
| S19 | P9 | `refactor_limpieza_o_nombres` | Refactor, limpieza o nombres | Cambios menores de limpieza, nombres, orden, simplificación o legibilidad. |
| S20 | P10 | `evidencia_insuficiente` | Evidencia insuficiente para clasificar | No hay evidencia textual suficiente para inferir el motivo de retrabajo sin riesgo de sobreinterpretación. |

## Leyenda compacta sugerida para el póster

Para no sobrecargar el póster, la leyenda puede mostrar solo el código, el nombre corto y el conteo. Las definiciones completas pueden quedar en un QR o anexo.

| Código | Nombre corto | n | % |
| --- | --- | ---: | ---: |
| P1 | Validación, calidad y CI | 104 | 34,7% |
| P2 | Corrección de implementación y lógica | 57 | 19,0% |
| P3 | Diseño, alcance y reutilización | 37 | 12,3% |
| P4 | Gobernanza del PR y coordinación de merge | 30 | 10,0% |
| P5 | Dependencias y versionado | 20 | 6,7% |
| P6 | Documentación y descripción del cambio | 17 | 5,7% |
| P7 | Configuración y automatización | 16 | 5,3% |
| P8 | Seguridad, permisos y validaciones | 11 | 3,7% |
| P9 | Mantenimiento menor y refactorización | 4 | 1,3% |
| P10 | Evidencia insuficiente | 4 | 1,3% |

## Correcciones ortográficas obligatorias antes del póster final

El PDF exportado de la presentación muestra problemas de tildes y de codificación. En el póster final deben revisarse especialmente estas palabras y expresiones:

| Forma incorrecta o dudosa | Forma corregida |
| --- | --- |
| Motivacion | Motivación |
| metodologia / metodologico | metodología / metodológico |
| taxonomia | taxonomía |
| categorias / categoria | categorías / categoría |
| discusion | discusión |
| implicancia | implicancia o implicancias, según contexto |
| validacion | validación |
| revision | revisión |
| integracion | integración |
| poblacion | población |
| clasificacion | clasificación |
| decision | decisión |
| automatizacion | automatización |
| configuracion | configuración |
| diseno | diseño |
| codigo | código |
| mas | más, cuando indica cantidad |
| que / por que | qué / por qué, cuando corresponde a pregunta o explicación |

Además, se debe evitar texto corrupto por codificación, como caracteres partidos o símbolos insertados en palabras con tilde. La exportación final debe revisarse visualmente en PDF.

## Pendientes antes de implementar el póster LaTeX

1. Confirmar colores institucionales exactos de la Universidad de La Frontera y del Departamento de Computación e Informática.
2. Seleccionar las imágenes finales de taxonomía desde el PPT o regenerarlas como SVG/PDF para máxima resolución.
3. Redactar una discusión breve contrastada con literatura sobre asistentes IA, revisión de código y retrabajo en PRs.
4. Redactar implicancias para desarrolladores, investigadores y constructores de herramientas.
5. Agregar limitaciones y amenazas a la validez: resultado asistido, evidencia textual incompleta y ausencia de consenso interevaluador definitivo.
6. Revisar ortografía, tildes y consistencia de nombres antes de exportar el PDF.

## Validación esperada después de implementar

Cuando se cree el archivo LaTeX del póster, la validación mínima debe incluir:

- Compilación del póster sin errores.
- Revisión visual del PDF A0 exportado.
- Verificación de que todas las imágenes tengan resolución suficiente o formato vectorial.
- Revisión ortográfica completa en español.
- Verificación de coherencia entre conteos del póster y `docs/taxonomia-final-merged-after-rework.md`.
- Confirmación de que la leyenda de categorías padre e hijas coincide con esta guía.
