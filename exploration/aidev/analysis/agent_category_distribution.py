#!/usr/bin/env python3
"""
Análisis de distribución de categorías de retrabajo por agente de IA.
Genera un gráfico de barras apiladas para validar si existen patrones diferenciados.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuración de estilo
sns.set_style("whitegrid")
sns.set_context("notebook", font_scale=1.1)

# Cargar datos
data_path = Path("exploration/aidev/taxonomy/analysis/merged_after_rework_final_taxonomy_contrast.csv")
df = pd.read_csv(data_path)

# Contar distribución por agente y categoría
distribution = df.groupby(['agent', 'categoria_padre_final']).size().unstack(fill_value=0)

# Calcular porcentajes por agente (para comparar perfiles)
distribution_pct = distribution.div(distribution.sum(axis=1), axis=0) * 100

# Ordenar agentes por tamaño de muestra
agent_order = distribution.sum(axis=1).sort_values(ascending=False).index.tolist()
distribution_pct = distribution_pct.reindex(agent_order)

# Crear figura
fig, ax = plt.subplots(figsize=(14, 8))

# Barras apiladas
colors = plt.cm.Set3(range(10))
distribution_pct.plot(kind='barh', stacked=True, ax=ax, color=colors, edgecolor='white', linewidth=0.5)

# Etiquetas y título
ax.set_xlabel('Porcentaje de PRs por categoría (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('Agente de IA', fontsize=12, fontweight='bold')
ax.set_title('Distribución de Categorías de Retrabajo por Agente de IA\n(n=300, muestra estratificada seed 20260510)', 
             fontsize=14, fontweight='bold', pad=15)

# Leyenda
ax.legend(title='Categoría Padre', bbox_to_anchor=(1.05, 1), loc='upper left', 
          fontsize=10, title_fontsize=11, frameon=True, fancybox=True)

# Invertir eje Y para que el agente más grande quede arriba
ax.invert_yaxis()

# Grid horizontal suave
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)

# Ajustar layout
plt.tight_layout()

# Guardar
output_dir = Path('exploration/aidev/analysis/outputs')
output_dir.mkdir(exist_ok=True)
output_path = output_dir / 'agent_category_distribution_stacked.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

print(f"✅ Gráfico guardado en: {output_path}")
print(f"\n📊 Distribución de muestras por agente:")
print(df['agent'].value_counts().to_string())
print(f"\n📈 Distribución de categorías por agente (porcentajes):")
print(distribution_pct.round(1).to_string())

# Mostrar tabla de conteos crudos
print(f"\n📋 Conteos crudos por agente y categoría:")
print(distribution.to_string())