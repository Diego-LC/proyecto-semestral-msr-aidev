---
description: Realizar commits del avance actual del proyecto según convenciones
---


1. Verificar que el proyecto se encuentra en el directorio correcto
2. Verficar el estado actual del repositorio con el comando `git status`
3. Si existe un archivo con cambios del que no se sabe su estado o sus cambios, se debe verificar con el comando `git diff`
4. Asegurarse de que los mensajes sean en español y descriptivos
5. Añadir los archivos con cambios al repositorio con el comando `git add <archivo>` `<archivo>`... añadiendo solamente los archivos con cambios relacionados a cierta caracteristica, evitando crear un commit global a menos que se especifique explícitamente.
6. Seguir las convenciones y consideraciones de los commits descritas en el punto 8.
7. Realizar el commit con el comando `git commit -m "mensaje"`
8. Ejemplo de convenciones:

## Versionado y Commits
- **Idioma:** Todos los mensajes de commit deben ser claros y descriptivos en español.
- **Frecuencia:** Commits pequeños y enfocados.
- **Conventional Commits:** 
  - `feat:` Nuevas funcionalidades.
  - `fix:` Corrección de errores.
  - `docs:` Cambios en documentación.
  - `refactor:` Mejora de código sin cambio funcional.
  - `style:` Cambios en formato, sin cambios en funcionalidad.
  - `test:` Cambios en pruebas, sin cambios en funcionalidad.
  - `chore:` Cambios en mantenimiento, sin cambios en funcionalidad.
  - `perf:` Mejora de rendimiento, sin cambios en funcionalidad.
  - `ci:` Cambios en CI/CD, sin cambios en funcionalidad.
- **Estructura:** Idealmente multilineal, con la siguiente estructura:

```
<tipo>(alcance): <descripción breve y clara>
<LINEA_EN_BLANCO>
- [cuerpo con tono imperativo]
```

- **Ramas:**
  - `main`: Producción.
  - `develop`: Desarrollo activo.
  - `feature/nombre`: Ramas de tareas específicas.
  - `bugfix/nombre`: Ramas de correcciones de errores críticos.
  - `hotfix/nombre`: Ramas de correcciones de errores críticos en producción.
  - `release/nombre`: Ramas de lanzamientos.
  - `support/nombre`: Ramas de soporte.
  - `test/nombre`: Ramas de pruebas.
  - `ci/nombre`: Ramas de CI/CD.
- **PRs:** Explicar qué ha cambiado, por qué y cómo se ha verificado.
- **Otros:** Verificar constantemente los cambios con `git status` o `git diff`.
