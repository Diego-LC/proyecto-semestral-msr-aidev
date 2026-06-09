# Contraste de categorización manual: Diego vs Javier

## Fuentes analizadas

- `exploration/aidev/taxonomy/initial/merged_after_rework_manual_categories_diego.csv`
- `exploration/aidev/taxonomy/initial/merged_after_rework_manual_categories_Javier.csv`

> Nota operativa: al momento de generar este contraste, estos CSV fueron tomados desde el árbol principal actual provisto por el usuario. La rama `feature/integracion-poblacion-muestreo-javier` todavía no versiona esas dos hojas manuales de origen.

## Objetivo

Contrastar las tarjetas que ambos evaluadores completaron para estimar el nivel de discrepancia actual y entender si la diferencia proviene de desacuerdo real o de marcos de categorización distintos.

## Cobertura por evaluador

| Evaluador | Filas | Tarjetas con categoría | Tarjetas con cita | Tarjetas con justificación |
| --- | --- | --- | --- | --- |
| Diego | 300 | 300 | 288 | 300 |
| Javier | 300 | 51 | 50 | 50 |

## Base comparable real

Aunque ambos CSV contienen 300 filas, la comparación justa hoy debe hacerse solo sobre las tarjetas con categoría en ambos archivos.

| Métrica | Valor |
| --- | --- |
| Tarjetas completadas por ambos | 51 |
| Coincidencias exactas de etiqueta | 0 |
| Discrepancias exactas de etiqueta | 51 |
| Coincidencias por familia sugerida (heurística) | 14 / 51 (27.5%) |

## Lectura principal

La discrepancia literal es **51 de 51** tarjetas compartidas. Sin embargo, esta cifra **no debe interpretarse todavía como desacuerdo inter-evaluador clásico**, porque ambos evaluadores están usando **niveles de abstracción distintos**:

- **Diego** usa una taxonomía más compacta y normalizada, centrada en el **motivo técnico inmediato** del retrabajo.
- **Javier** usa una taxonomía más narrativa, contextual y casi caso-a-caso, centrada en el **patrón sociotécnico o causal** del caso completo.

## Evidencia del cambio de granularidad

En las 51 tarjetas compartidas:

- Diego usa **15 categorías distintas**.
- Javier usa **51 categorías distintas para 51 tarjetas**.

Distribución de categorías de Diego dentro del solapamiento:

| Categoría Diego en el solapamiento | Casos |
| --- | --- |
| estilo_formato_lint | 11 |
| documentacion_descripcion_incorrecta | 8 |
| pruebas_faltantes_o_insuficientes | 7 |
| configuracion_ci_despliegue | 6 |
| cumplimiento_proceso_pr | 3 |
| ajustes_implementacion_review | 3 |
| ajuste_diseno_api_modelo | 2 |
| correccion_funcional_logica | 2 |
| dependencias_versiones_migracion | 2 |
| reduccion_alcance_o_sobrecodigo | 2 |
| evidencia_insuficiente_rechazo_inicial | 1 |
| ajuste_menor_review | 1 |
| falla_ci_tests | 1 |
| rendimiento_concurrencia | 1 |
| correcion_logica_frontend | 1 |

Esto muestra que Diego está agrupando muchos casos bajo familias técnicas recurrentes, mientras Javier está describiendo historias causales mucho más específicas.

## Coincidencia semántica aproximada (heurística)

Para no quedarnos solo con coincidencia literal, se construyó una **familia sugerida** para cada categoría. Esta agrupación es heurística y sirve solo como apoyo para reconciliación posterior.

Las 10 combinaciones de familia más frecuentes son:

| Familia Diego | Familia Javier | Casos |
| --- | --- | --- |
| validacion_calidad_ci | implementacion_logica | 7 |
| implementacion_logica | implementacion_logica | 5 |
| validacion_calidad_ci | validacion_calidad_ci | 5 |
| configuracion_automatizacion | proceso_gobernanza | 2 |
| validacion_calidad_ci | proceso_gobernanza | 2 |
| proceso_gobernanza | proceso_gobernanza | 2 |
| configuracion_automatizacion | dependencias_versionado | 2 |
| configuracion_automatizacion | feature_producto | 2 |
| documentacion_descripcion | mantenimiento_refactor | 2 |
| validacion_calidad_ci | mantenimiento_refactor | 2 |

Con esta heurística, hay **14 coincidencias de familia sobre 51 tarjetas compartidas** (27.5%).

### Ejemplos donde sí hay alineación semántica parcial

| card_id | Categoría Diego | Categoría Javier | Familia común sugerida |
| --- | --- | --- | --- |
| 3076981888-A | cumplimiento_proceso_pr | Cambio Menor Abandonado por Falta de Revisión - Reactivación Manual | proceso_gobernanza |
| 3078006902-A | ajuste_diseno_api_modelo | Ausencia de Patrón de Referencia Documentado (scope grande) | arquitectura_diseno |
| 3081576661-A | correccion_funcional_logica | Errores de build y ajustes en la implementación | implementacion_logica |
| 3084021151-A | dependencias_versiones_migracion | Actualización de dependencias sin conflictos | dependencias_versionado |
| 3087813875-A | pruebas_faltantes_o_insuficientes | Falsos positivos en análisis estático / ajuste de reglas | validacion_calidad_ci |

### Ejemplos donde la diferencia de enfoque es clara

| card_id | Categoría Diego | Categoría Javier | Familias sugeridas |
| --- | --- | --- | --- |
| 3074788987-A | documentacion_descripcion_incorrecta | Feedback Contradictorio de Múltiples Reviewers Causando Iteración Caótica | documentacion_descripcion vs proceso_gobernanza |
| 3075024592-A | evidencia_insuficiente_rechazo_inicial | Timeout de Code Owner - Bypass por Conveniencia | evidencia_insuficiente vs proceso_gobernanza |
| 3075216235-A | configuracion_ci_despliegue | Múltiples Iteraciones de Feedback Secuencial del Revisor | configuracion_automatizacion vs proceso_gobernanza |
| 3075286950-A | documentacion_descripcion_incorrecta | Corrección de Especificación Incorrecta Requiriendo Reescritura Múltiple | documentacion_descripcion vs arquitectura_diseno |
| 3075799511-A | estilo_formato_lint | Bot Malfuncionando Requiriendo Bypass Manual - Retraso Extremo | validacion_calidad_ci vs proceso_gobernanza |
| 3077383006-A | cumplimiento_proceso_pr | Corrección Iterativa Bien Coordinada Entre Revisor y Bot | proceso_gobernanza vs implementacion_logica |
| 3080755872-A | configuracion_ci_despliegue | Merge con Checks Fallando - Confianza del Owner | configuracion_automatizacion vs proceso_gobernanza |
| 3081566388-A | ajustes_implementacion_review | Errores en tests unitarios / compilación | implementacion_logica vs validacion_calidad_ci |

## Hallazgos metodológicos

1. **No hay acuerdo literal usable todavía**. Calcular kappa o porcentaje de acuerdo simple en este punto sería engañoso.
2. **La diferencia principal es el nivel de análisis**:
   - Diego etiqueta el síntoma o motivo inmediato del retrabajo.
   - Javier etiqueta la historia causal, de coordinación o de gobernanza que explica el caso.
3. **Hay un subconjunto con alineación semántica parcial** cuando ambos, aun con distinto nivel de detalle, apuntan a la misma familia amplia.
4. **Hay otro subconjunto claramente desalineado** donde uno codifica proceso/gobernanza y el otro codifica implementación/CI/documentación.

## Inconsistencias de datos detectadas

### 1. Escala distinta en columnas temporales

- `horas_creacion_a_primera_aprobacion`: 31/31 valores comparables están exactamente en escala x1000 en Javier respecto de Diego.
- `horas_creacion_a_merge`: 51/51 valores comparables están exactamente en escala x1000 en Javier respecto de Diego.
- `horas_creacion_a_aceptacion`: 51/51 valores comparables están exactamente en escala x1000 en Javier respecto de Diego.

Esto indica que, antes de cualquier análisis conjunto de tiempos, los valores de Javier deben normalizarse.

### 2. Soporte textual incompleto en algunos casos compartidos

- Diego tiene 2 casos compartidos sin cita o sin justificación completa: 3075024592-A, 3269741497-A.
- Javier tiene 1 casos compartidos sin cita o sin justificación completa: 3095409522-A.

## Recomendación de reconciliación

### Paso 1
Congelar el conjunto común actual de **51 tarjetas compartidas** como base de calibración.

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

- CSV derivado para revisión manual: `exploration/aidev/taxonomy/analysis/merged_after_rework_diego_javier_contrast.csv`
- Este reporte: `docs/contraste-categorizacion-diego-javier.md`
