#!/usr/bin/env python3
"""
Gráfico de barras apiladas mejorado para el informe.
Incluye: contornos, etiquetas P1-P10, colores mejorados, valores en barras.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import seaborn as sns
from pathlib import Path

# Configuración de estilo mejorado
sns.set_style("whitegrid")
sns.set_context("notebook", font_scale=1.2)

# Cargar datos
data_path = Path("exploration/aidev/taxonomy/analysis/merged_after_rework_final_taxonomy_contrast.csv")
df = pd.read_csv(data_path)

# Mapeo de categorías a códigos P1-P10
category_mapping = {
    'validacion_calidad_ci': ('P1', 'CI/Validación'),
    'implementacion_logica': ('P2', 'Implementación'),
    'arquitectura_diseno': ('P3', 'Arquitectura'),
    'proceso_gobernanza': ('P4', 'Gobernanza'),
    'dependencias_versionado': ('P5', 'Dependencias'),
    'documentacion_descripcion': ('P6', 'Documentación'),
    'configuracion_automatizacion': ('P7', 'Configuración'),
    'seguridad_permisos': ('P8', 'Seguridad'),
    'mantenimiento_refactor': ('P9', 'Refactor'),
    'evidencia_insuficiente': ('P10', 'Evidencia Insuf.')
}

# Calcular distribución por agente y categoría
distribution = df.groupby(['agent', 'categoria_padre_final']).size().unstack(fill_value=0)
distribution_pct = distribution.div(distribution.sum(axis=1), axis=0) * 100

# Ordenar agentes por tamaño de muestra
agent_order = distribution.sum(axis=1).sort_values(ascending=False).index.tolist()
distribution_pct = distribution_pct.reindex(agent_order)
distribution = distribution.reindex(agent_order)

# Reordenar columnas según P1-P10
ordered_cats = list(category_mapping.keys())
distribution_pct = distribution_pct[ordered_cats]
distribution = distribution[ordered_cats]

# Paleta de colores mejorada (más contraste)
colors = [
    '#9B59B6',  # P1: Morado intenso
    '#E67E22',  # P2: Naranja
    '#1ABC9C',  # P3: Turquesa
    '#3498DB',  # P4: Azul
    '#F39C12',  # P5: Dorado
    '#E74C3C',  # P6: Rojo
    '#2ECC71',  # P7: Verde
    '#95A5A6',  # P8: Gris
    '#1F4E79',  # P9: Azul oscuro
    '#D7BDE2'   # P10: Lavanda
]

# Crear figura
fig, ax = plt.subplots(figsize=(16, 9))

# Barras apiladas con contornos
bottoms = [0] * len(agent_order)
bars = []

for idx, cat in enumerate(ordered_cats):
    rects = ax.barh(
        agent_order, 
        distribution_pct[cat], 
        left=bottoms,
        color=colors[idx], 
        edgecolor='black', 
        linewidth=1.2,
        label=f"{category_mapping[cat][0]}: {category_mapping[cat][1]}"
    )
    
    # Actualizar bottoms
    for i, val in enumerate(distribution_pct[cat]):
        bottoms[i] += val
    
    # Agregar etiquetas en barras > 5% (umbral más bajo)
    for i, (agent, val) in enumerate(zip(agent_order, distribution_pct[cat])):
        if val > 5:  # Etiquetar barras > 5%
            center_x = bottoms[i] - val / 2
            center_y = i
            # Determinar color de texto según luminosidad del fondo
            # Colores oscuros: P1, P4, P5, P9 → texto blanco
            # Colores claros: resto → texto negro
            dark_colors = [0, 3, 4, 8]  # índices de colores oscuros
            text_color = 'white' if idx in dark_colors else 'black'
            
            # Para barras muy pequeñas (<10%), usar fuente más pequeña
            fontsize = 9 if val < 10 else 10
            
            ax.text(
                center_x, center_y, 
                f'{val:.0f}%',
                va='center', 
                ha='center',
                fontsize=fontsize,
                fontweight='bold',
                color=text_color
            )

# Configuración de ejes
ax.set_xlabel('Porcentaje de PRs por Categoría (%)', fontsize=13, fontweight='bold', labelpad=10)
ax.set_ylabel('Agente de IA', fontsize=13, fontweight='bold')
ax.set_title(
    'Distribución de Categorías de Retrabajo por Agente de IA\n'
    '(n=300, muestra estratificada seed 20260510)',
    fontsize=15, 
    fontweight='bold', 
    pad=20
)

# Invertir eje Y
ax.invert_yaxis()

# Grid vertical suave
ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.7)
ax.set_axisbelow(True)

# Leyenda mejorada
legend_elements = [
    mpatches.Patch(
        facecolor=colors[idx], 
        edgecolor='black', 
        linewidth=1.2,
        label=f"{category_mapping[cat][0]}: {category_mapping[cat][1]}"
    )
    for idx, cat in enumerate(ordered_cats)
]

legend = ax.legend(
    handles=legend_elements,
    title='Categoría Padre',
    bbox_to_anchor=(1.05, 1),
    loc='upper left',
    fontsize=10,
    title_fontsize=11,
    frameon=True,
    fancybox=True,
    shadow=True
)
legend.get_frame().set_alpha(0.95)
legend.get_frame().set_edgecolor('black')
legend.get_frame().set_linewidth(1)

# Ajustar layout
plt.tight_layout()

# Guardar en alta resolución
output_dir = Path('docs/poster')
output_dir.mkdir(exist_ok=True)
output_path = output_dir / 'agent_category_distribution_improved.png'
plt.savefig(
    output_path, 
    dpi=300, 
    bbox_inches='tight', 
    facecolor='white',
    edgecolor='none'
)

print(f"✅ Gráfico mejorado guardado en: {output_path}")
print(f"\n📊 Resumen de muestras por agente:")
for agent in agent_order:
    n = len(df[df['agent'] == agent])
    print(f"  {agent:15} → n={n:3d} PRs")