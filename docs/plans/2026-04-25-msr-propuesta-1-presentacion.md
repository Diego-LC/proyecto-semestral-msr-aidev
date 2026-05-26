# Propuesta 1 Seleccionada

## Título tentativo

**¿Qué revela la intervención humana sobre la autonomía de los agentes de IA como contribuidores de software?**

## Idea central

La propuesta seleccionada estudia pull requests generados por agentes de IA usando el dataset `AIDev`. El foco no estará solo en medir si los humanos intervienen o no, sino en interpretar esa intervención como una señal del nivel de autonomía real del agente.

La idea es que la intervención humana permita responder una pregunta más relevante: ¿los agentes ya pueden contribuir de manera efectiva al desarrollo de software o todavía requieren supervisión y correcciones importantes antes de que sus cambios puedan integrarse?

## Motivación

Medir únicamente la frecuencia de intervención humana no es suficiente. Ese dato tiene valor cuando se interpreta en términos de:

- confiabilidad práctica de los agentes;
- capacidad de integrarse al flujo real de desarrollo;
- costo adicional de supervisión humana;
- contextos donde los agentes sí o no son útiles.

Si la mayoría de los PRs requiere cambios humanos significativos antes del merge, eso sugiere una autonomía limitada. Si muchos PRs se integran sin cambios relevantes, entonces los agentes pueden entenderse como contribuidores efectivos al menos en ciertos escenarios.

## Objetivo

Evaluar en qué medida los pull requests generados por agentes de IA pueden integrarse como contribuciones efectivas de software, usando la intervención humana como señal de autonomía práctica.

## Preguntas de investigación

1. ¿Qué proporción de los PRs creados por agentes puede integrarse sin intervención humana significativa?
2. Cuando un PR no es integrable tal como fue generado, ¿qué tipos de intervenciones significativas realizan los humanos?
3. ¿Cómo cambia este comportamiento según el contexto, por ejemplo lenguaje, tamaño del PR, agente o características del repositorio?
4. ¿Cómo se relaciona el nivel de intervención con el resultado final del PR, como merge, rechazo o tiempo de integración?

## Enfoque metodológico

El estudio usará PRs del dataset `AIDev` con historial suficiente de commits y estado final. A partir de eso se reconstruirá la secuencia del PR para distinguir qué cambios provienen del agente y cuáles fueron agregados después por humanos.

Un punto clave será diferenciar entre:

- `intervenciones superficiales`: formato, documentación menor, sincronizaciones o ajustes triviales;
- `intervenciones significativas`: correcciones de lógica, tests, configuración, errores funcionales o cambios que afectan la aceptabilidad del PR.

Con esa distinción se podrá estimar qué PRs eran realmente integrables y cuáles dependieron de trabajo humano sustantivo para llegar a merge o incluso para no ser rechazados.

## Aporte esperado

Este estudio puede aportar en dos niveles. Primero, permite entender mejor los límites actuales de los agentes de IA como participantes del proceso de desarrollo. Segundo, puede ayudar a identificar en qué contextos su uso parece realmente útil y en cuáles todavía implica un costo alto de revisión y corrección.

En ese sentido, la contribución no es solo descriptiva. Los resultados podrían servir para apoyar decisiones de adopción en equipos de desarrollo y también para orientar futuras investigaciones sobre autonomía y confiabilidad de agentes en ingeniería de software.

## Cierre

En resumen, la propuesta ya no se centra únicamente en contar intervenciones humanas, sino en usar esas intervenciones para inferir algo más importante: cuándo un agente actúa como contribuidor efectivo y cuándo todavía depende de supervisión humana significativa.
