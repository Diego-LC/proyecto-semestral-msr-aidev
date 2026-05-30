# Labeling Machine para card sorting de PRs mergeados tras retrabajo

Esta carpeta contiene la integración entre las tarjetas preparadas en
`exploration/aidev/preparation` y la herramienta open source
`Labeling Machine`.

El flujo es:

1. Convertir `merged_after_rework_cards_seed_20260510.csv` al formato de importación.
2. Clonar Labeling Machine en una carpeta local de trabajo.
3. Copiar el `overlay` de esta carpeta sobre el checkout de Labeling Machine.
4. Inicializar la base SQLite con las tarjetas.
5. Etiquetar los casos desde la interfaz web.
6. Exportar las etiquetas para calcular acuerdo entre evaluadores y analizar motivos de rechazo.

## 1. Generar datos para Labeling Machine

Desde la raíz del proyecto:

```bash
.venv/bin/python exploration/aidev/labeling_machine/labeling_machine_adapter.py
```

Salidas principales:

- `outputs/rejection_cards_for_labeling_machine.csv`: tarjetas listas para importar.
- `outputs/labeling_machine_schema.json`: campos de artefactos y etiquetas esperadas.
- `outputs/rejection_cards_for_labeling_machine_summary.json`: resumen de control.

El campo `artifact_id` es un número secuencial usado por las rutas internas de
Labeling Machine. La identidad real del caso se mantiene en `card_id` y `pr_id`.

## 2. Instalar Labeling Machine

Se recomienda no versionar el repositorio externo dentro de este proyecto. Una
opción práctica es clonarlo en `tools/`, que puede quedar como carpeta local de
trabajo:

```bash
mkdir -p tools
git clone --depth 1 --branch minimal https://github.com/emadpres/labeling-machine.git tools/labeling-machine-aidev
```

Copiar la personalización:

```bash
cp -R exploration/aidev/labeling_machine/overlay/webapp/* tools/labeling-machine-aidev/webapp/
mkdir -p tools/labeling-machine-aidev/webapp/data
cp exploration/aidev/labeling_machine/outputs/rejection_cards_for_labeling_machine.csv \
  tools/labeling-machine-aidev/webapp/data/
```

## 3. Inicializar y ejecutar

```bash
cd tools/labeling-machine-aidev
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd webapp
rm -f db/app.sqlite
export FLASK_APP=src
flask initdb
flask run
```

Luego abrir `http://127.0.0.1:5000`, registrarse con un usuario y entrar a
`Label`.

Si el CSV queda en otra ruta, usar:

```bash
export AIDEV_REJECTION_CARDS_CSV=/ruta/absoluta/rejection_cards_for_labeling_machine.csv
```

antes de ejecutar `flask initdb`.

## 4. Protocolo de uso para el card sorting

Durante la fase abierta, cada evaluador crea categorías desde los datos en
`Main category`. La `Subcategory` permite registrar un motivo más específico sin
forzar todavía una taxonomía final.

Campos usados:

- `Main category`: motivo principal de rechazo.
- `Subcategory`: detalle opcional dentro del motivo principal.
- `Confidence`: seguridad del evaluador (`high`, `medium`, `low`).
- `Rationale`: justificación breve basada en la evidencia visible.
- `Discuss`: marcar casos ambiguos para reunión de consenso.

Después de una ronda inicial, el equipo debe revisar categorías similares,
fusionar/dividir donde corresponda y congelar una taxonomía para una segunda
ronda más consistente.

## 5. Exportar etiquetas

Con la app detenida o usando una copia de la base:

```bash
sqlite3 tools/labeling-machine-aidev/webapp/db/app.sqlite \
  ".headers on" \
  ".mode csv" \
  "select
      a.id as artifact_id,
      a.card_id,
      a.pr_id,
      a.html_url,
      a.agent,
      a.language,
      a.task_type,
      a.complexity_bin,
      a.evidence_source,
      l.username,
      l.category_parent,
      l.subcategory,
      l.confidence,
      l.rationale,
      l.needs_discussion,
      l.duration_sec,
      l.created_at
    from LabelingData l
    join Artifact a on a.id = l.artifact_id;" \
  > exploration/aidev/labeling_machine/outputs/labeling_machine_labels.csv
```

Ese CSV es la entrada esperada para calcular acuerdo inter-evaluador (cuánto
coinciden dos personas clasificando los mismos casos), por ejemplo con Cohen's
kappa si hay dos evaluadores o Krippendorff's alpha si hay más evaluadores o
faltan algunas etiquetas.

## Archivos del overlay

- `overlay/webapp/src/database/models.py`: agrega campos de PR y campos de etiquetado.
- `overlay/webapp/src/database/initdb.py`: importa el CSV generado.
- `overlay/webapp/src/helper/tools_labeling.py`: ajusta el progreso al número real de tarjetas.
- `overlay/webapp/src/routes/routes_labeling.py`: guarda categorías, confianza y justificación.
- `overlay/webapp/frontend/templates/labeling_pages/artifact.html`: muestra evidencia y metadatos del PR.
- `overlay/webapp/frontend/templates/labeling_pages/labeling_layout.html`: formulario de card sorting.
