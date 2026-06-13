# Clasificacion asistida por Codex para revision humana

## Proposito y estado del artefacto

Este documento describe el borrador de clasificacion asistida generado para las 300
tarjetas de la muestra `merged_after_rework`. Su objetivo es acelerar la revision
manual sin reemplazar el juicio del evaluador ni modificar las taxonomias manuales
versionadas.

El artefacto principal es:

```text
exploration/aidev/preparation/outputs/merged_after_rework_codex_review_manual_categories.csv
```

Este CSV es un **borrador revisable**, no una taxonomia final. Todas sus filas parten
con `decision_humana = pendiente`; las categorias propuestas solo se consideran
aceptadas cuando Javier las revise.

El archivo se encuentra ignorado por Git mediante la regla existente
`exploration/aidev/preparation/outputs/*manual_categories.csv`. El CSV manual original
de Javier no se sobrescribe.

## Entradas, exclusiones y trazabilidad

El script reproducible es:

```text
exploration/aidev/taxonomy/analysis/build_codex_review.py
```

Entradas utilizadas:

1. `merged_after_rework_cards_seed_20260510.csv`: aporta las 300 tarjetas y toda la
   evidencia textual local.
2. `merged_after_rework_manual_categories_Javier.csv`: aporta solamente las 51
   categorias narrativas ya creadas por Javier, que se preservan en
   `categoria_original_javier` como antecedente auditable.

La clasificacion de Diego no se consulta ni se incorpora en el script o en el CSV de
revision. Esta separacion busca reducir sesgo de anclaje antes del contraste entre
evaluadores.

Cada propuesta conserva:

- `card_id`, `pr_id`, `agent` y `html_url` para trazabilidad;
- `context_summary`, `evidence_text` y `all_evidence_text` para revision;
- una cita textual extraida desde la evidencia local;
- la categoria original de Javier, cuando existe;
- categoria padre, subcategoria, justificacion y confianza propuestas;
- campos vacios para registrar la decision humana final.

## Enfoque de clasificacion

La clasificacion implementada es **heuristica, basada en evidencia y asistida por
reglas**. No utiliza un clasificador estadistico entrenado ni entrega probabilidades.
La intencion metodologica es representar dos pasos:

1. **Identificacion del motivo abierto**: localizar en la evidencia el problema o
   solicitud que explica el retrabajo humano. El resultado se registra en
   `motivo_abierto_codex`.
2. **Normalizacion taxonomica**: mapear ese motivo a una categoria padre y una
   subcategoria reutilizable mediante un catalogo explicito de reglas textuales.

La implementacion clasifica el motivo que produjo retrabajo, no la funcionalidad
general del PR ni el hecho de que finalmente haya sido mergeado.

### Preparacion de evidencia

Para cada tarjeta, el script:

1. Prioriza `evidence_raw_text`, que corresponde a la evidencia principal seleccionada
   durante la preparacion de tarjetas.
2. Cuando la evidencia es un comentario inline, separa el texto del revisor del
   `diff_hunk` para reducir falsos positivos causados por palabras presentes solo en
   el codigo.
3. Incorpora evidencias secundarias desde `all_evidence_json` con menor peso.
4. Descarta como no accionables mensajes positivos o puramente administrativos, por
   ejemplo `LGTM`, `approved`, agradecimientos o checks exitosos sin solicitud de
   cambio.
5. Marca `evidencia_insuficiente/motivo_no_identificable` cuando no existe una señal
   defendible para atribuir el retrabajo.

### Catalogo normalizado

El catalogo actual contiene 10 categorias padre y 21 subcategorias:

| Categoria padre | Subcategorias |
|---|---|
| `validacion_calidad_ci` | `fallos_tests_ci`, `lint_formato_analisis_estatico`, `cobertura_o_pruebas_insuficientes` |
| `implementacion_logica` | `manejo_errores_y_validacion_inputs`, `compatibilidad_o_migracion`, `rendimiento_concurrencia_o_recursos`, `ui_ux_y_comportamiento_frontend`, `correccion_funcional` |
| `arquitectura_diseno` | `alcance_o_sobrecodigo`, `reutilizacion_y_duplicacion`, `diseno_api_modelo_o_interfaz` |
| `proceso_gobernanza` | `cumplimiento_cla_dco`, `dependencia_o_orden_de_merge`, `revision_o_aprobacion_pendiente` |
| `dependencias_versionado` | `versiones_o_dependencias` |
| `documentacion_descripcion` | `descripcion_pr_incorrecta_o_incompleta`, `documentacion_codigo_o_usuario` |
| `configuracion_integracion` | `ci_workflows_y_automatizacion` |
| `seguridad_permisos` | `seguridad_autorizacion_o_validacion` |
| `mantenimiento_refactor` | `limpieza_simplificacion_o_nombres` |
| `evidencia_insuficiente` | `motivo_no_identificable` |

Cada subcategoria define:

- un motivo abierto normalizado;
- una explicacion reutilizable;
- patrones textuales asociados;
- una prioridad para resolver señales frecuentes o especificas.

El catalogo es una propuesta inicial. Durante la revision humana pueden aparecer
categorias nuevas, fusiones o divisiones necesarias para representar mejor los datos.

## Puntaje y confianza

La confianza sirve para **priorizar la revision humana**. No debe interpretarse como
probabilidad de acierto, acuerdo interevaluador ni confianza estadistica.

### Puntaje de las reglas

Cada regla se evalua sobre cada pieza de evidencia. Cuando una regla encuentra uno o
mas patrones, calcula:

```text
puntaje = prioridad_de_la_regla + peso_de_la_fuente + coincidencias_adicionales
```

- Evidencia principal: peso `8`.
- Cada evidencia secundaria: peso `2`.
- Coincidencias adicionales dentro de la misma evidencia: hasta `2` puntos.
- Solo se conserva el mejor puntaje obtenido por la regla en una pieza de evidencia;
  no se suman indiscriminadamente menciones repetidas de toda la conversacion.

La regla con mayor puntaje se propone como clasificacion. Si el mejor puntaje es menor
a `5`, la tarjeta se clasifica como evidencia insuficiente.

### Margen entre alternativas

El script compara las dos reglas con mayor puntaje:

```text
margen = mejor_puntaje - segundo_mejor_puntaje
```

Un margen amplio indica que una regla destaca frente a las alternativas. Un margen
pequeno indica superposicion o ambiguedad entre posibles motivos.

### Calidad de evidencia de las tarjetas

El campo preexistente `evidence_quality_score` entrega un valor entre 0 y 10:

| Condicion | Puntos |
|---|---:|
| La evidencia principal contiene texto | +1 |
| La fuente no es solo el titulo o descripcion del PR | +2 |
| La evidencia principal proviene de un usuario humano | +2 |
| Existe una review `CHANGES_REQUESTED` | +3 |
| Existe al menos un comentario humano | +1 |
| Existen mas de dos evidencias textuales | +1 |

Este puntaje mide disponibilidad y procedencia de evidencia; no demuestra que la
categoria propuesta sea correcta.

### Umbrales de confianza

| Confianza | Condicion aplicada |
|---|---|
| `alta` | mejor puntaje >= 15, margen >= 4 y calidad de evidencia >= 7 |
| `media` | mejor puntaje >= 9 y margen >= 2 |
| `baja` | evidencia insuficiente o no cumple los umbrales anteriores |

`motivo_duda` explica por que una fila requiere revision y registra hasta tres señales
textuales que influyeron en propuestas de confianza media o baja.

## Resultado generado

El borrador contiene 300 tarjetas unicas. Distribucion por categoria padre:

| Categoria padre propuesta | Tarjetas | Porcentaje |
|---|---:|---:|
| `validacion_calidad_ci` | 104 | 34,7% |
| `implementacion_logica` | 57 | 19,0% |
| `arquitectura_diseno` | 37 | 12,3% |
| `proceso_gobernanza` | 30 | 10,0% |
| `dependencias_versionado` | 20 | 6,7% |
| `documentacion_descripcion` | 17 | 5,7% |
| `configuracion_integracion` | 16 | 5,3% |
| `seguridad_permisos` | 11 | 3,7% |
| `evidencia_insuficiente` | 4 | 1,3% |
| `mantenimiento_refactor` | 4 | 1,3% |

Distribucion de confianza:

| Confianza | Tarjetas | Porcentaje |
|---|---:|---:|
| `alta` | 19 | 6,3% |
| `media` | 107 | 35,7% |
| `baja` | 174 | 58,0% |

La proporcion elevada de confianza baja es deliberadamente conservadora. Muchas
tarjetas contienen mensajes indirectos, evidencia de bots, multiples motivos o
comentarios que no expresan claramente la razon del retrabajo. Estas propuestas deben
revisarse antes de usarse como resultados de investigacion.

## Columnas del CSV de revision

| Columna | Uso |
|---|---|
| `card_id`, `pr_id`, `agent`, `html_url` | Identificacion y trazabilidad |
| `evidence_source` | Fuente de la evidencia principal |
| `context_summary`, `evidence_text`, `all_evidence_text` | Contexto disponible para revision |
| `cita_textual_retrabajo` | Fragmento local seleccionado como soporte de la propuesta |
| `categoria_original_javier` | Etiqueta narrativa previa, presente en 51 casos |
| `motivo_abierto_codex` | Descripcion normalizada del motivo identificado |
| `categoria_padre_propuesta` | Familia amplia propuesta |
| `subcategoria_propuesta` | Motivo especifico propuesto |
| `justificacion_breve` | Explicacion reutilizable de la asignacion |
| `confianza_codex` | Prioridad heuristica de revision: alta, media o baja |
| `motivo_duda` | Ambiguedad y señales que requieren inspeccion |
| `decision_humana` | Estado de revision; inicialmente `pendiente` |
| `categoria_padre_final`, `subcategoria_final` | Campos para la decision corregida o aceptada |

## Protocolo recomendado de revision

1. Revisar primero las 174 filas de confianza baja, comenzando por
   `evidencia_insuficiente` y por los casos con `motivo_duda` poco especifico.
2. Revisar las 107 filas de confianza media, verificando si la segunda alternativa
   plausible representa mejor el motivo principal.
3. Confirmar las 19 filas de confianza alta; confianza alta no equivale a aceptacion
   automatica.
4. Comparar la cita con `evidence_text` y, cuando sea necesario, con
   `all_evidence_text` o el enlace del PR.
5. Registrar `decision_humana = aceptada` cuando la propuesta sea correcta.
6. Registrar `decision_humana = corregida` y completar las columnas finales cuando sea
   necesario cambiar la clasificacion.
7. No utilizar el borrador en analisis cuantitativos hasta que las 300 decisiones hayan
   sido revisadas.

## Reproduccion y validaciones

Generar el borrador:

```bash
.venv/bin/python exploration/aidev/taxonomy/analysis/build_codex_review.py
```

Validar sin escribir archivos:

```bash
.venv/bin/python exploration/aidev/taxonomy/analysis/build_codex_review.py --dry-run
```

El script valida que:

- existen exactamente 300 filas y 300 `card_id` unicos;
- todas las decisiones humanas comienzan pendientes;
- categoria padre, subcategoria, cita, justificacion y confianza estan completas;
- cada cita aparece dentro de la evidencia local de su tarjeta.

En la generacion documentada tambien se comprobo que:

- las 51 categorias originales de Javier se preservaron;
- las 300 citas fueron verificadas contra la evidencia local;
- el CSV original de Javier mantuvo su hash sin cambios;
- ni el script ni el borrador contienen referencias a Diego;
- el nuevo CSV permanece ignorado por Git.

## Limitaciones y amenazas a la validez

- Las reglas dependen de patrones escritos principalmente en ingles; evidencia en otros
  idiomas puede quedar subclasificada.
- Una tarjeta puede contener multiples motivos, pero el borrador propone solo un motivo
  principal.
- Evidencias secundarias pueden describir problemas distintos ocurridos durante el
  mismo PR.
- La prioridad y los umbrales fueron definidos heurísticamente y no fueron calibrados
  contra un conjunto etiquetado independiente.
- `evidence_quality_score` mide calidad observable de evidencia, no correccion de la
  etiqueta.
- La distribucion presentada describe propuestas pendientes de revision y no debe
  reportarse como resultado final de la investigacion.
- El acuerdo con Diego debe calcularse solamente despues de completar la revision ciega
  de Javier.
