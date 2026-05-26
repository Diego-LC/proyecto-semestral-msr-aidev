# Stratified Sampling for Rejected AIDev PRs

Esta carpeta implementa la primera parte de la actividad: extraer una muestra aleatoria estratificada de PRs rechazados para preparar el card sorting.

El muestreo se ubica dentro de `exploration/aidev` porque depende directamente del dataset `hao-li/AIDev` y reutiliza utilidades existentes para acceder a los Parquet oficiales.

## Qué hace

El script [stratified_sampler.py](/mnt/e/UFRO/5to-2026/mineria-repositorio/proyecto-semestral/exploration/aidev/sampling/stratified_sampler.py):

- filtra PRs rechazados (`state = closed` y `merged_at IS NULL`);
- agrega variables de control para revisar sesgos posteriores;
- calcula cuotas proporcionales con mínimo por estrato;
- mantiene lenguaje, popularidad, periodo y tipo de tarea como variables de control para revisar sesgos;
- usa el agente como única variable de estratificación por defecto;
- toma la muestra con semilla fija `20260510` (para reproducibilidad del muestreo);
- exporta un CSV de muestra y un JSON de resumen.

## Método implementado

Por defecto intenta muestrear con:

```text
agent
```

Esta decisión evita fragmentar demasiado la muestra inicial y asegura cobertura proporcional por agente:

- `agent`: quién generó el PR.

La complejidad, el lenguaje, la popularidad del repositorio, el periodo y el tipo de tarea quedan como variables de control para comparar muestra vs. población después del muestreo.

La cuota por estrato usa la regla definida en el plan:

```text
n_h = max(m, round(n * N_h / N))
```

Donde `n_h` es la cantidad de PRs que se toman de un estrato, `n` es el tamaño total de muestra, `N_h` es el tamaño del estrato, `N` es la población total y `m` es el mínimo por estrato.

Si se fuerza manualmente una estratificación que incluya `language`, el script puede agrupar lenguajes poco frecuentes en `other` con:

```bash
--max-language-values 8
```

## Uso con AIDev

Para generar una muestra real desde los Parquet oficiales:

```bash
python3 exploration/aidev/sampling/stratified_sampler.py \
  --source aidev \
  --sample-size 300 \
  --min-per-stratum 3 \
  --seed 20260510 \
  --output-csv exploration/aidev/sampling/outputs/rejection_sample.csv \
  --summary-json exploration/aidev/sampling/outputs/rejection_sample_summary.json
```

El script requiere `pandas` y `pyarrow` para leer Parquet. Si faltan:

```bash
python3 -m pip install --user -r exploration/aidev/requirements-notebook.txt
```

## Uso con CSV local

Para probar con un CSV ya preparado:

```bash
python3 exploration/aidev/sampling/stratified_sampler.py \
  --source csv \
  --input-csv path/to/rejected_prs.csv \
  --sample-size 300 \
  --dry-run
```

El CSV debe incluir al menos:

```text
id,state,merged_at,agent,created_at
```

Si incluye `commit_count`, el script deriva `change_complexity_bin` para control posterior. Si incluye `language`, `stars` o `task_type`, esas variables se usan como controles en el resumen, no como estratos por defecto.

## Población ampliada opcional

Por defecto se usan solo PRs rechazados (`state = closed` y `merged_at IS NULL`). Para validar una población inicial más amplia que incluya PRs mergeados solo después de retrabajo, se puede usar:

```bash
python3 exploration/aidev/sampling/stratified_sampler.py \
  --source aidev \
  --population-mode rejected-or-reworked-merged \
  --sample-size 300 \
  --dry-run
```

El script marca esos casos como `population_case_type = merged_after_rework` cuando hay merge, más de un cambio de código o cambio posterior a revisión, y señales de feedback/review antes de la aceptación. Es una inclusión viable, pero metodológicamente debe analizarse como grupo separado de los `rejected`.

## Salidas

El CSV de muestra contiene las filas seleccionadas más campos de control:

- `_stratum_key`: estrato usado para seleccionar la fila;
- `_sample_seed`: semilla usada para reproducibilidad.

El JSON de resumen contiene:

- tamaño de población;
- tamaño de muestra;
- campos de estratificación usados;
- tamaños por estrato;
- cuotas por estrato;
- distribuciones de población y muestra para comparar sesgos.

## Verificación

Tests asociados:

```bash
python3 -m unittest exploration.aidev.tests.test_stratified_sampler
```
