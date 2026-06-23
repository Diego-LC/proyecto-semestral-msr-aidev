#!/usr/bin/env python3
"""
Gráfico de radar (spider chart) para comparar perfiles de retrabajo por agente.
Visualización alternativa para el póster.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Cargar datos
data_path = Path("exploration/aidev/taxonomy/analysis/merged_after_rework_final_taxonomy_contrast.csv")
df = pd.read_csv(data_path)

# Categorías principales (P1-P4 que representan 76% del total)
categories = ['validacion_calidad_ci', 'implementacion_logica', 'arquitectura_diseno', 'proceso_gobernanza']
category_labels = ['P1: CI/Validación', 'P2: Implementación', 'P3: Arquitectura', 'P4: Gobernanza']

# Calcular porcentajes por agente
agent_pcts = {}
for agent in df['agent'].unique():
    agent_data = df[df['agent'] == agent]
    total = len(agent_data)
    pcts = []
    for cat in categories:
        count = len(agent_data[agent_data['categoria_padre_final'] == cat])
        pcts.append((count / total) * 100)
    agent_pcts[agent] = pcts

# Ordenar agentes por tamaño de muestra
agent_order = df['agent'].value_counts().index.tolist()
colors = plt.cm.Set3(range(5))

# Crear figura
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

# Calcular ángulos
angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
angles += angles[:1]  # Cerrar el círculo

# Dibujar cada agente
for idx, agent in enumerate(agent_order):
    values = agent_pcts[agent]
    values += values[:1]  # Cerrar el círculo
    
    ax.plot(angles, values, 'o-', linewidth=2, label=agent, color=colors[idx % len(colors)])
    ax.fill(angles, values, alpha=0.15, color=colors[idx % len(colors)])

# Etiquetas de categorías
ax.set_xticks(angles[:-1])
ax.set_xticklabels(category_labels, fontsize=11, fontweight='bold')

# Líneas de grid
ax.set_yticks(np.arange(0, 70, 10))
ax.set_yticklabels(np.arange(0, 70, 10), fontsize=9, alpha=0.7)
ax.grid(True, linestyle='--', alpha=0.5)

# Leyenda
legend = ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10, 
                   title='Agente de IA', title_fontsize=11, frameon=True, fancybox=True)
legend.get_frame().set_alpha(0.8)

# Título
plt.title('Perfiles de Retrabajo por Agente de IA\n(Comparación de Categorías Principales P1-P4)', 
          fontsize=14, fontweight='bold', pad=20, y=1.08)

# Ajustar layout
plt.tight_layout()

# Guardar
output_dir = Path('exploration/aidev/analysis/outputs')
output_dir.mkdir(exist_ok=True)
output_path = output_dir / 'agent_radar_profile.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

print(f"✅ Gráfico de radar guardado en: {output_path}")
print(f"\n📊 Datos ploteados (porcentajes por categoría):")
for agent in agent_order:
    pcts = agent_pcts[agent]
    print(f"{agent:15} | P1: {pcts[0]:5.1f}% | P2: {pcts[1]:5.1f}% | P3: {pcts[2]:5.1f}% | P4: {pcts[3]:5.1f}%")