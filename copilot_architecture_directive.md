# Directiva Arquitectónica: Consolidación del Harness y Optimización de Contexto

> **Instrucciones para el Agente de IA:** Has sido provisto con este reporte de diagnóstico estratégico. Tu objetivo es transformar el conjunto actual de scripts sueltos en un pipeline formal, orquestado y portable. Debes aplicar ingeniería de software estricta para resolver problemas de concurrencia, duplicación de I/O y volatilidad del entorno Docker.

---

## 1. Mapeo de Brechas Técnicas (Deuda a Resolver)

Tras auditar el estado actual de `hermes-test`, se han identificado 4 fallas críticas que debes corregir de forma prioritaria en este ciclo de refactorización:

1. **Fragmentación Operativa:** El diseño actual es "event-driven manual". Cada script (`skill_state.py`, `skill_plan.py`, `skill_docker.py`) actúa como un consumidor aislado, forzando lecturas redundantes en disco de `state.json` y duplicando el análisis del entorno.
2. **Riesgo de Concurrencia (Efecto Choque):** No existe exclusión mutua coordinada. Si Hermes inyecta telemetría desde el OS vía Telegram al mismo tiempo que tú (Copilot) aplicas una refactorización profunda sobre el repositorio, el archivo `state.json` o los archivos Markdown (`HERMES_TELEGRAM_INSTALL_PLAN.md`) pueden sufrir corrupción de datos.
3. **Inflación del Contexto de Prompt (Gasto de Tokens):** El flujo carece de un filtro incremental. Al no procesar únicamente los archivos mutados (`git diff --name-only`), se inyecta el repositorio completo en la ventana de contexto, provocando una fuga masiva de créditos y tokens de API.
4. **Estado Efímero (Amnesia de Docker):** El `Dockerfile` y `docker-compose.yml` carecen de una estrategia explícita de volúmenes persistentes para carpetas críticas como `~/.hermes`, haciendo que cualquier reinicio del contenedor destruya el aprendizaje acumulado por el agente.

---

## 2. El Pipeline de Orquestación Objetivo

Debes refactorizar la lógica para transicionar hacia este flujo de datos secuencial y atómico, controlado por un único punto de entrada:

```text
[Ejecución Central] -> skill_env_control.py (Adquiere Lock Global)
                             │
                             ├──> 1. utils/state_loader.py (Carga única + OS Discovery)
                             ├──> 2. harness/scripts/skill_state.py (Captura Hermes/API Keys)
                             ├──> 3. harness/scripts/skill_docker.py (Sincronización Idempotente)
                             ├──> 4. harness/scripts/skill_plan.py (Inyección Atómica en MD)
                             └──> 5. harness/scripts/skill_commit_push.py (Validación y Push)
                             │
                      [Libera Lock Global] -> state.json actualizado de forma segura
```

---

## 3. Plan de Acción Quirúrgico por Componente

### Tarea A: Implementación del Guardián del Estado (`harness/scripts/utils/state_loader.py`)

- Crea o consolida este módulo para encapsular el acceso al disco mediante un patrón Singleton y un semáforo de bloqueo basado en filesystem.
- Regla de Concurrencia: Si un script secundario intenta acceder a `state.json` y el archivo `.harness_lock` existe, debe esperar un máximo de 15 segundos antes de abortar con una excepción, evitando bucles de espera infinitos.
- Detección Portable: Reemplaza la lectura estática de `/etc/os-release` por condicionales que validen la existencia de binarios (`shutil.which('uname')`, `dpkg-query`, etc.) para asegurar el funcionamiento nativo en entornos Windows locales o nubes Linux.

### Tarea B: Centralización del Control (`harness/scripts/skill_env_control.py`)

- Convierte este script en el Controlador Maestro del ecosistema.
- Debe encargarse de:
  - Adquirir el bloqueo global al iniciar y liberarlo al finalizar.
  - Capturar el manifiesto de cambios incrementales ejecutando `git diff --name-only HEAD`.
  - Inyectar en `state.json` el objeto de telemetría estructurada `harness_telemetry` con el conteo y la lista reducida de archivos modificados.

### Tarea C: Desacoplamiento de Scripts Secundarios

Refactura `skill_plan.py`, `skill_docker.py` y `skill_commit_push.py` bajo las siguientes reglas:

- Prohibido: El uso de `json.loads(Path("state.json").read_text())`. Todos deben importar y consumir obligatoriamente `StateLoader().load_state()`.
- Parsing Seguro de Docker: Refactora la lógica de `skill_docker.py`. Reemplaza las expresiones regulares frágiles sobre el Dockerfile por un mecanismo de verificación de bloques comentados estáticos (ej: `# PACKAGES-BEGIN` / `# PACKAGES-END`) o generación limpia de capas.
- Separación de Validación: Modifica `skill_commit_push.py`. Debe limitarse a leer las métricas de éxito ya asentadas en `state.json` por los scripts previos. Si la validación pasa, ejecuta el empaquetado; si falla, frena el push y reporta el log de errores.

### Tarea D: Robustez de Persistencia en Docker

Optimiza la capa de infraestructura para garantizar que el entorno sea agnóstico y el aprendizaje persistente:

- Modifica `docker-compose.yml` para mapear explícitamente el directorio de configuración del host hacia el contenedor:

```yaml
volumes:
  - ~/.hermes:/root/.hermes
  - ./state.json:/workspaces/hermes-test/state.json
```

- Asegura que el Dockerfile utilice variables de entorno relativas basadas en el directorio de trabajo, eliminando cualquier ruta absoluta dependiente de la sesión de Codespaces.

---

## 4. Políticas de Gobierno para la Inferencia de IA

- **Ahorro de Tokens:** Cuando operes en modo de edición profunda (como Autopilot o bucles autónomos de Roo Code), tienes estrictamente prohibido escanear de forma pasiva todo el árbol de archivos. Debes consultar el objeto `harness_telemetry.changed_files_manifest` dentro de `state.json` y limitar tus lecturas y escrituras estrictamente a ese subconjunto de rutas mutadas.
- **Soporte de Alias de API Keys:** El sistema de gestión de credenciales en `skill_state.py` debe reconocer y priorizar el alias `ROO_CODE_GEMINI_API_KEY` o `ROO_GEMINI_API_KEY`, mapeándolo automáticamente hacia el proveedor de bajo costo `gemini-3.5-flash` con URL base `https://generativelanguage.googleapis.com/v1beta/openai` para minimizar el consumo de créditos.
