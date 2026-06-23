# Análisis de Distribución de Categorías por Agente

**Fecha:** 22 de junio de 2026  
**Muestra:** 300 PRs estratificados por agente (seed 20260510)  
**Objetivo:** Identificar patrones diferenciados de retrabajo por agente de IA

---

## 📊 Hallazgos Principales

### 1. **Copilot (n=145, 48.3% de la muestra)**
**Perfil:** Distribución balanceada con dominancia moderada de P1 y P2

| Categoría | n | % |
|-----------|---|----|
| P1 (Validación/CI) | 31 | 21.4% |
| P2 (Implementación) | 35 | 24.1% |
| P4 (Gobernanza) | 16 | 11.0% |
| P5 (Dependencias) | 14 | 9.7% |
| P6 (Documentación) | 13 | 9.0% |

**Interpretación:** Copilot muestra el perfil más diversificado. La combinación P1+P2 (45.5%) indica que los problemas son tanto de validación automática como de lógica de implementación.

---

### 2. **Devin (n=86, 28.7% de la muestra)**
**Perfil:** Altamente concentrado en P1 (CI/validación)

| Categoría | n | % |
|-----------|---|----|
| **P1 (Validación/CI)** | **57** | **66.3%** |
| P2 (Implementación) | 12 | 14.0% |
| P4 (Gobernanza) | 3 | 3.5% |

**Interpretación:** ⚠️ **Hallazgo crítico:** Devin tiene una concentración extrema en P1 (66.3% vs. 34.7% promedio). Esto sugiere que Devin genera código funcionalmente correcto pero falla consistentemente en tests/CI locales antes de solicitar revisión.

**Recomendación específica:** Devin necesita loops de auto-verificación de CI antes de abrir PRs.

---

### 3. **OpenAI Codex (n=45, 15.0% de la muestra)**
**Perfil:** Similar a Copilot pero con más gobernanza

| Categoría | n | % |
|-----------|---|----|
| P1 (Validación/CI) | 14 | 31.1% |
| P2 (Implementación) | 8 | 17.8% |
| P4 (Gobernanza) | 6 | 13.3% |
| P7 (Configuración) | 4 | 8.9% |
| P3 (Arquitectura) | 4 | 8.9% |

**Interpretación:** Perfil balanceado con énfasis en validación y gobernanza.

---

### 4. **Cursor (n=17, 5.7% de la muestra)**
**Perfil:** Dominancia de arquitectura y gobernanza

| Categoría | n | % |
|-----------|---|----|
| P3 (Arquitectura) | 3 | 17.6% |
| P4 (Gobernanza) | 4 | 23.5% |
| P5 (Dependencias) | 3 | 17.6% |
| P1 (Validación/CI) | 1 | 5.9% |

**Interpretación:** ⚠️ **Patrón atípico:** Cursor tiene el P1 más bajo (5.9% vs. 34.7% promedio) pero alto en gobernanza y arquitectura. Sugiere que Cursor genera código que pasa CI pero requiere ajustes de diseño y coordinación.

**Nota:** Muestra pequeña (n=17), interpretar con cautela.

---

### 5. **Claude Code (n=7, 2.3% de la muestra)**
**Perfil:** Dominancia extrema de arquitectura

| Categoría | n | % |
|-----------|---|----|
| **P3 (Arquitectura)** | **3** | **42.9%** |
| P1/P4/P8/P10 | 1 c/u | 14.3% |

**Interpretación:** ⚠️ **Patrón único:** Claude Code es el único agente donde P3 domina (42.9% vs. 12.3% promedio). Sugiere que Claude Code genera soluciones arquitectónicamente problemáticas pero pasa CI.

**Nota:** Muestra muy pequeña (n=7), requiere validación con más datos.

---

## 🎯 Conclusiones Estadísticas

### Prueba de independencia (Chi-cuadrado)
- **Hipótesis nula:** La distribución de categorías es independiente del agente
- **Resultado preliminar:** Las diferencias observadas (especialmente Devin P1=66.3% y Claude Code P3=42.9%) sugieren **dependencia significativa** entre agente y tipo de retrabajo.
- **Acción recomendada:** Ejecutar prueba Chi-cuadrado formal con `scipy.stats.chi2_contingency`.

### Implicancias para la Investigación

1. **Los agentes NO son intercambiables:** Cada agente tiene un "perfil de retrabajo" distintivo.
2. **Devin requiere intervención temprana en CI:** 66% de sus PRs fallan en tests/build.
3. **Claude Code requiere revisión arquitectónica:** 43% de sus PRs tienen problemas de diseño/duplicación.
4. **Copilot es el más "equilibrado":** Su distribución se asemeja al promedio general.

---

## 📈 Recomendaciones para el Póster

### Elemento Visual Propuesto: **Gráfico de Radar (Spider Chart)**

**Descripción:** Un gráfico de radar con 5 ejes (uno por agente) mostrando el perfil de cada agente en las 4 categorías principales (P1, P2, P3, P4).

**Ventajas:**
- Permite comparar perfiles de forma intuitiva
- Muestra claramente la "forma" distintiva de cada agente
- Ocupa poco espacio (~15x10 cm)

**Datos a plotear:**
```
Agente        | P1    | P2    | P3    | P4
Copilot       | 21.4% | 24.1% | 13.1% | 11.0%
Devin         | 66.3% | 14.0% |  9.3% |  3.5%
OpenAI_Codex  | 31.1% | 17.8% |  8.9% | 13.3%
Cursor        |  5.9% | 11.8% | 17.6% | 23.5%
Claude_Code   | 14.3% |  0.0% | 42.9% | 14.3%
```

**Ubicación sugerida:** Mitad inferior del póster, entre "Discusión" y "Alcance/Límites".

**Título propuesto:** "Perfiles de Retrabajo por Agente: ¿Son Intercambiables los Agentes de IA?"

---

## 📝 Elementos Visuales Adicionales para Mitad Inferior

### Opción A: **Diagrama de Flujo del Card Sorting**
- 3 cajas horizontales: Preparation → Execution → Analysis
- Iconos: 🔍 (filtros), 📊 (muestra), 🏷️ (clasificación), ✅ (taxonomía)
- Tamaño: ~20x8 cm

### Opción B: **Iconos de Categorías Padre**
- 10 iconos pequeños (uno por categoría P1-P10)
- Cada icono representa visualmente el tipo de retrabajo
- Ejemplo: P1 = 🧪 (test tube), P2 = 🐛 (bug), P3 = 🏗️ (construcción)
- Tamaño: ~25x6 cm en fila

### Opción C: **Timeline de Retrabajo** (si se implementa RQ2)
- Línea de tiempo desde `created_at` → `primer comentario` → `merged_at`
- Mostraría la duración mediana por categoría
- Tamaño: ~25x8 cm

**Recomendación:** Usar **Opción A (Diagrama de Flujo)** + **gráfico de radar por agente** como elementos complementarios.

---

## 🔤 Traducción de Anglicismos

| Anglicismo | Traducción Propuesta | Primera Mención | Subsecuentes |
|------------|---------------------|-----------------|--------------|
| card sorting | clasificación abierta de tarjetas | "clasificación abierta de tarjetas (card sorting)" | "clasificación" |
| soundness | validez metodológica | "validez metodológica (soundness)" | "validez" |
| merge | integración | "integración (merge)" | "integración" |
| merged | integrado | "PR integrado" | "integrado" |
| build | compilación | "compilación (build)" | "compilación" |
| CI | integración continua | "integración continua (CI)" | "CI" (aceptable por ser acrónimo) |
| lint | verificación de estilo | "verificación de estilo (lint)" | "lint" (técnico) |
| PR | solicitud de cambios | "solicitud de cambios (pull request, PR)" | "PR" (aceptable) |
| commit | confirmación de código | "confirmación de código (commit)" | "commit" (técnico) |
| review | revisión de código | "revisión de código" | "revisión" |
| feedback | retroalimentación | "retroalimentación" | "retroalimentación" |
| prompt | instrucción | "instrucción (prompt)" | "prompt" (técnico) |
| checklist | lista de verificación | "lista de verificación" | "lista" |
| owner | responsable | "responsable del módulo" | "responsable" |
| lock | archivo de bloqueo | "archivo de bloqueo (lockfile)" | "lockfile" |

---

## ✅ Checklist Ortográfico

### Errores Comunes a Verificar

- [ ] Tildes en mayúsculas: "TAXONOMÍA" → "Taxonomía"
- [ ] Tildes en palabras técnicas: "métrica", "estratégico", "análisis"
- [ ] Comillas latinas: ```texto''` → `"texto"` o `«texto»`
- [ ] Consistencia en números: "3.166" (punto como mil) vs "3,166" (coma como mil)
- [ ] Espacios antes de signos: "300 ." → "300."
- [ ] Abreviaturas: "Dr." (con punto), "etc." (con punto)
- [ ] Extrangerismos en cursiva: *card sorting*, *soundness*, *build*

### Puntos Críticos en el Póster Actual

1. Línea 100: "Taxonomía" (bien)
2. Línea 117: "AIDev" (definir en primera mención)
3. Línea 128: "card sorting" → "clasificación abierta de tarjetas (card sorting)"
4. Línea 133: "soundness" → "validez metodológica"
5. Línea 164: "merge" → "integración"
6. Línea 172: "treemap" → "mapa jerárquico (treemap)"
7. Línea 183: "build" → "compilación"
8. Línea 183: "CI" → "integración continua (CI)"
9. Línea 195: "checks" → "verificaciones"
10. Línea 195: "prompts" → "instrucciones"

---

## 📋 Próximos Pasos

1. **Validar gráfico de radar** con el equipo
2. **Ejecutar prueba Chi-cuadrado** formal para independencia agente-categoría
3. **Aplicar traducciones** al archivo `poster-a0.tex`
4. **Revisión ortográfica** línea por línea
5. **Insertar diagrama de flujo** en la sección metodológica
6. **Compilar y validar** sin errores de overfull

---

**Archivos Generados:**
- `exploration/aidev/analysis/outputs/agent_category_distribution_stacked.png` (288 KB)
- `docs/analysis/agent_category_analysis.md` (este documento)