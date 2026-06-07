# Integración selectiva de población/muestreo y mejoras de Javier

Fecha: 2026-06-06  
Rama de trabajo: `feature/integracion-poblacion-muestreo-javier`

## Objetivo

Integrar selectivamente los aportes de `feature/javier` sin perder la separación metodológica necesaria para la investigación:

```text
population_filter.py → población operacional auditable
stratified_sampler.py → muestra estratificada reproducible
rejection_cards.py → tarjetas con evidencia textual
notebook_flow.py → validación y reporte del flujo
```

La decisión principal fue conservar la arquitectura de población y muestreo separados porque permite auditar cómo se define la población `merged_after_rework` antes de seleccionar la muestra.

## Qué se mantuvo

Se mantuvo el enfoque de flujo separado:

- `exploration/aidev/sampling/population_filter.py` descarga Parquets, calcula métricas poblacionales, aplica filtros y escribe artefactos de población.
- `exploration/aidev/sampling/stratified_sampler.py` lee `merged_after_rework_population.csv`, calcula cuotas y selecciona la muestra.
- Los artefactos poblacionales siguen siendo canónicos:
  - `exploration/aidev/sampling/outputs/merged_after_rework_population.csv`
  - `exploration/aidev/sampling/outputs/merged_after_rework_population_summary.json`

Esto evita mezclar dos decisiones metodológicas distintas: definición de población y diseño muestral.

## Qué se integró

### 1. Métricas y controles en población

Las mejoras técnicas de `feature/javier` se incorporaron donde corresponden metodológicamente: en `population_filter.py`.

La población conserva o calcula campos como:

- conteos de reviews y reviewers;
- reviews humanas y bot;
- comentarios PR humanos y bot;
- comentarios de review humanos y bot;
- `human_comment_count` y `bot_comment_count`;
- `change_complexity_bin`;
- `repo_popularity_bin`;
- `created_period`;
- `task_type`.

Estos campos permiten comparar población y muestra sin reconstruir la población dentro del muestreador.

### 2. Normalización y limpieza de campos poblacionales

Se reforzó `prepare_population_rows()` para:

- normalizar `task_type` faltante a `unknown`;
- normalizar `language` faltante a `unknown`;
- quitar `_created_at_rank` antes de escribir población, porque es un campo auxiliar interno usado solo para calcular `created_period`.

### 3. Validación de población

Se agregó `validate_population_rows()` en `population_filter.py` para comprobar que:

- la población no quede vacía;
- existan campos críticos (`pr_id`, `agent`, `state`, `merged_at`, `commit_count`, `human_comment_count` y campos de control);
- no existan `pr_id` duplicados;
- todos los casos cumplan la definición operacional:

```text
PR cerrado y mergeado
+ commit_count > 1
+ human_comment_count > 0
+ population_case_type = merged_after_rework
```

### 4. Validación del muestreo

Se agregó `validate_population_input()` en `stratified_sampler.py` para comprobar que:

- el CSV poblacional exista y no esté vacío;
- los campos de estratificación estén presentes;
- el tamaño del CSV coincida con `population_summary.json` cuando el resumen existe;
- no existan `pr_id` duplicados en la población.

También se valida que la muestra no contenga `pr_id` duplicados.

### 5. Validaciones del notebook

Se reforzó `validate_flow()` en `notebook_flow.py` para verificar que los campos de control existan en:

- `population_summary`;
- `sampling_summary`;
- `population_df`;
- `sample_df`.

Esto ayuda a detectar desalineaciones entre artefactos y summaries.

### 6. Documentación

Se actualizaron:

- `README.md`;
- `exploration/aidev/README.md`;
- `exploration/aidev/sampling/README.md`.

La documentación ahora explicita que `stratified_sampler.py` no descarga Parquets ni reconstruye la población; solo consume el artefacto poblacional auditable.

## Por qué se hizo así

Para la investigación, el flujo debe poder justificar:

1. cuál es el universo bruto;
2. qué filtros definen la población operacional;
3. cuántos casos quedan antes de muestrear;
4. cómo se estratifica la muestra;
5. cómo se preserva trazabilidad desde población → muestra → tarjetas.

Si `stratified_sampler.py` reconstruyera población internamente, sería más simple de ejecutar, pero menos claro para auditoría metodológica. Por eso las mejoras técnicas se ubicaron en población y no en muestreo.

## Verificaciones realizadas

Se ejecutaron verificaciones sin escribir nuevos artefactos canónicos:

```bash
.venv/bin/python -m compileall exploration/aidev
```

Resultado: PASS.

```bash
.venv/bin/python exploration/aidev/sampling/population_filter.py --dry-run
```

Resultado: PASS. La población operacional reportada fue de 3.166 PRs.

```bash
.venv/bin/python exploration/aidev/sampling/stratified_sampler.py --dry-run
```

Resultado: PASS. La muestra reportada fue de 300 PRs con 5 estratos por `agent`.

```bash
.venv/bin/python exploration/aidev/preparation/rejection_cards.py --dry-run
```

Resultado: PASS. Se reportaron 300 tarjetas y 0 descartes por falta de comentarios humanos.

También se verificó que `stratified_sampler.py` no contenga llamadas a carga de Parquets ni reconstrucción de población.

## Incoherencias o riesgos detectados

### 0. Ambigüedad documental corregida

Durante la verificación se detectó que el `README.md` raíz aún mencionaba `has_post_review_code_change` / `post_review_code_change_count` como alternativa para detectar retrabajo. Esa frase podía sugerir un criterio operacional más amplio que el implementado.

Se corrigió para dejar explícito que el flujo vigente usa:

```text
commit_count > 1
human_comment_count > 0
```

Las demás métricas de reviews/comentarios se conservan para caracterizar y auditar población/muestra, pero no reemplazan los criterios de inclusión.

### 1. Artefactos canónicos no regenerados

Los cambios de código no sobrescribieron los outputs canónicos. Esto fue intencional para preservar artefactos históricos y evitar modificar resultados manuales sin confirmación.

Como consecuencia, los CSV existentes pueden conservar diferencias de esquema respecto del código nuevo hasta que se regeneren explícitamente.

Hallazgo actual:

- `merged_after_rework_population.csv` contiene aún `_created_at_rank`.
- `merged_after_rework_sample_seed_20260510.csv` contiene aún `_created_at_rank`.
- El código actualizado ya elimina ese campo al reconstruir población.

Recomendación: si se decide actualizar artefactos canónicos, generar primero outputs temporales, comparar filas/distribuciones y solo después reemplazar población y muestra.

### 2. Normalización de `language`

El summary de sampling normaliza valores faltantes a `unknown`, pero el summary de cards puede mostrar valores vacíos (`""`) porque usa los artefactos existentes.

Esto no rompe el flujo actual, pero indica que los outputs históricos todavía no reflejan la normalización nueva de `language` en `population_filter.py`.

Recomendación: regenerar población y muestra si se quiere alinear completamente artefactos y código.

### 3. Validación del notebook fija `sample_size == 300`

`validate_flow()` conserva la expectativa canónica de 300 casos. Es correcto para el flujo vigente, pero si se cambia el tamaño muestral en el futuro, esa validación deberá parametrizarse.

### 4. Acoplamiento leve entre muestreo y población

`stratified_sampler.py` importa helpers desde `population_filter.py` (`CONTROL_FIELDS`, `value_counts`, `write_csv_rows`, etc.). Esto no reconstruye población ni descarga Parquets, pero mantiene acoplamiento entre ambos módulos.

Recomendación futura: si se desea reducir acoplamiento, mover helpers compartidos a un módulo común, por ejemplo `exploration/aidev/sampling/common.py`.

## Criterio de aceptación

La integración se considera correcta porque:

- la construcción de población sigue separada del muestreo;
- `stratified_sampler.py` consume `population.csv` y no Parquets;
- se preservan artefactos de población;
- se integran métricas y bins de control en la fase poblacional;
- se agregan validaciones de población, muestra y notebook;
- los comandos canónicos en modo `--dry-run` pasan.

Queda como decisión pendiente si se deben regenerar los artefactos canónicos para eliminar `_created_at_rank` y normalizar `language` en los CSV existentes.
