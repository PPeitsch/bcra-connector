# Protocolo de Desarrollo para Agentes - BCRA Connector

Este documento define el Procedimiento Operativo Estándar (SOP) para agentes de IA trabajando en este repositorio. Sigue estas instrucciones estrictamente.

## 1. Contexto del Entorno

- **OS**: Windows.
- **Shell**: PowerShell.
- **Gestor de Paquetes**: `pip` (con `venv`).
- **Build System**: `hatch` (configurado en `pyproject.toml`).
- **Version Source**: `src/bcra_connector/__about__.py`.

## 2. Fase de Exploración Inicial

Al iniciar una tarea, ejecuta siempre:
1.  `git status` (Verificar limpieza del workspace).
2.  `git pull origin main` (Sincronizar).
3.  Leer `CHANGELOG.md` (Entender la última versión).
4.  Leer `pyproject.toml` (Verificar dependencias actuales).

## 3. Flujo de Implementación (Features/Fixes)

Para cada tarea asignada:

1.  **Creación de Rama**:
    - Naming convention: `type/issue-id-short-description`
    - Tipos: `feature`, `fix`, `docs`, `refactor`.
    - Ejemplo: `git checkout -b fix/issue-52-setuptools-vuln`

2.  **Desarrollo**:
    - Realiza los cambios necesarios en el código.
    - Si agregas dependencias, actualiza `pyproject.toml` (sección `dependencies` o `optional-dependencies`).

3.  **Verificación (Obligatoria)**:
    - Ejecutar tests: `pytest`
    - Ejecutar linter: `pre-commit run --all-files`
    - **CRÍTICO**: Si el linter modifica archivos (ej. trailing whitespace), vuelve a ejecutarlo hasta que pase (Exit Code 0).

4.  **Commit**:
    - Formato: `[TYPE] Descripción concisa`
    - Cuerpo: `Resolves: #IssueID`
    - Ejemplo: `git commit -m "[FIX] Update setuptools constraint" -m "Resolves: #52"`

5.  **Pull Request**:
    - Push: `git push origin nombre-rama`
    - **CRÍTICO**: Usar el template de `.github/PULL_REQUEST_TEMPLATE.md` como base para el body. Asegurar que los checklists estén completos.
    - **VERIFICACIÓN CI**:
        - **JAMÁS MERGEAR SIN VERIFICACIÓN**: El agente TIENE PROHIBIDO mergear un PR sin antes validar que todos los checks de CI (GitHub Actions) hayan pasado exitosamente.
        - Usar `gh run list --branch nombre-rama` para monitorear el estado.
        - Si CI falla, arreglar el problema en la misma rama. JAMÁS ignorar un fallo de CI.
    - Merge: `gh pr merge --admin --merge --delete-branch` (Solo y ÚNICAMENTE si todos los tests pasan en CI).

## 4. Reglas de Calidad y Seguridad (Hard Rules)

1.  **NO MERGEAR CON ERRORES**: Prohibido mergear si `pre-commit` o `pytest` fallan localmente.
2.  **PRE-COMMIT OBLIGATORIO**: Ejecutar `pre-commit run --all-files` antes de CADA commit significativo. Si autocrige archivos, añadirlos y commitear de nuevo.
3.  **TESTS OBLIGATORIOS**: Ejecutar `pytest` antes de crear el PR.
4.  **No Inventar Comandos**: Usar solo los comandos definidos en el entorno (`hatch`, `pip`, etc.).

## 5. Protocolo de Release (Automatización)

Este proyecto usa **Release Automation**. El agente NO debe crear el release en GitHub manualmente, sino disparar el workflow mediante tags.

**Pasos exactos:**

1.  **Determinar Versión**:
    - Leer `src/bcra_connector/__about__.py` para ver la versión actual.
    - Decidir la nueva versión (SemVer: Patch, Minor, o Major).

2.  **Editar Archivos de Versión**:
    - **`src/bcra_connector/__about__.py`**:
        - Actualizar variable `__version__ = "X.Y.Z"`.
        - **NOTA**: `docs/source/conf.py` lee esta versión automáticamente, no requiere edición manual.
    - **`CHANGELOG.md`**:
        - Cambiar el título `## [Unreleased]` por `## [X.Y.Z] - YYYY-MM-DD`.
        - Añadir una nueva sección vacía `## [Unreleased]` arriba.
        - Actualizar los links de comparación al final del archivo:
            - `[X.Y.Z]: .../compare/vPrevious...vX.Y.Z`
    - **IMPORTANTE**: JAMÁS editar `src/bcra_connector/_version.py` (es generado automáticamente).

3.  **Comprometer Cambios de Versión**:
    ```powershell
    git add src/bcra_connector/__about__.py CHANGELOG.md
    git commit -m "[RELEASE] Version X.Y.Z"
    ```

4.  **Taggear**:
    - El tag debe coincidir exactamente con la versión y tener prefijo `v`.
    ```powershell
    git tag -a vX.Y.Z -m "Release vX.Y.Z"
    ```

5.  **Disparar Automatización**:
    ```powershell
    git push origin main
    git push origin vX.Y.Z
    ```

6.  **Verificación**:
    - Ejecutar `gh run list` y confirmar que el workflow "Test and Publish" se ha iniciado para el tag.

## 5. Manejo de Errores Comunes

- **Linting falló en CI**: Ejecuta `pre-commit run --all-files` localmente y commitea los fixes de estilo.
- **Tag ya existe**: Si fallaste en el release, borra el tag local (`git tag -d vX.Y.Z`) y remoto (`git push origin :refs/tags/vX.Y.Z`) antes de reintentar.
- **Conflictos de Merge**: Haz rebase con main (`git pull --rebase origin main`) antes de pushear.
