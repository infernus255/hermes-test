# Auditoría Técnica: Copilot Harness y Optimización de Token

## 1. Duplicación de Procesamiento de Contexto

El repositorio actual todavía tiene puntos de duplicación de contexto y lectura de estado que deben eliminarse.

### Líneas exactas de código duplicadas

1. `harness/scripts/skill_state.py`
   - `15: KEY_LIMITS_FILE = loader.repo_root / "api_key_limits.json"`
   - `38: def load_env_file(path):`
   - `49: def parse_key_limits(value):`
   - `113-116: lectura de hermes.env y ~/.hermes/.env`
   - `174: "limits_source": "api_key_limits.json or API_KEY_LIMITS env"`
   - `203: config_output = run_command(["hermes", "config", "show"]) or ""`
   - `244-246: uso de dpkg-query y shutil.which("dpkg-query")`
   - `320-339: guardado de state.json con loader.save_state(state)` y estado de ambiente local

2. `harness/scripts/skill_plan.py`
   - `18-21: carga de estado con loader.load_state(force_reload=True)`
   - `103-131: generación de una sección Markdown de estado y autorunner`

3. `harness/scripts/skill_docker.py`
   - `41-44: carga de estado con loader.load_state(force_reload=True)`
   - `49: state = load_state()` y extracción de required_packages
   - `48-53: lectura/escritura directa de Dockerfile`

4. `harness/scripts/skill_commit_push.py`
   - `43-44: carga de estado con loader.load_state(force_reload=True)`
   - `80-90: comprobación de Hermes con hermes config show`
   - `112-179: validaciones de documentación, API keys, n8n y Docker`
   - `139: git_add_commit_push()` ejecuta cambios de git dentro del mismo flujo

5. `harness/scripts/skill_env_control.py`
   - `74-78: carga de estado con loader.load_state()`
   - `82-116: escritura de state.json y sincronización de plan Markdown`

### Observaciones

- Aunque `StateLoader` existe, varios scripts siguen invocando `load_state(force_reload=True)` de forma independiente, lo que produce lecturas repetidas de `state.json`.
- `skill_state.py` sigue usando `hermes config show` con parseo por regex en la línea 203 en lugar de un formato API/JSON estructurado.
- `skill_commit_push.py` valida el repositorio y el estado en la misma ejecución; esto puede duplicar el uso de contexto cuando otro script ya actualizó `state.json`.
- `skill_env_control.py` ya contiene buena intención para centralizar la sincronización, pero mantiene una implementación parcial y reutiliza un `env_id` fijo que no es portable.

## 2. Plan para Conectar Roo Code con Gemini 3.5 Flash

### Objetivo
Minimizar el gasto de tokens y controlar los créditos de Copilot usando `gemini-3.5-flash` para la edición profunda.

### Propuesta

1. Registrar explícitamente un alias dedicado para Roo Code:
   - `ROO_CODE_GEMINI_API_KEY`
   - `ROO_CODE_GEMINI_ALIAS=roo`
   - `HEREMES_MODEL_DEFAULT=gemini-3.5-flash`

2. Extender la carga de claves en `harness/scripts/skill_state.py` para aceptar:
   - `ROO_GEMINI_API_KEY`
   - `ROO_GEMINI_API_KEYS`
   - `GEMINI_API_KEY` / `GEMINI_API_KEYS`
   - `GOOGLE_API_KEY` / `GOOGLE_API_KEYS`

3. Hacer que `state.json` documente `keys[]` con alias y límites:
   - `alias`
   - `provider` (gemini/google)
   - `key_id` hash
   - `limit` y `limit_source`
   - `source`

4. Enviar solo el contexto mínimo a Copilot/Roo Code:
   - archivos modificados desde el último sync (`git diff --name-only HEAD^..HEAD`)
   - un resumen condensado de `state.json` con metadata relevante
   - archivos de gobernanza clave: `docs/copilot-instructions.md`, `harness/docs/COPILOT_SKILL.md`, `docs/HERMES_TELEGRAM_INSTALL_PLAN.md`

5. Forzar la política de modelo en Hermes:
   - `provider=gemini`
   - `model.default=gemini-3.5-flash`
   - `model.base_url=https://generativelanguage.googleapis.com/v1beta/openai`

6. Usar `api_budget.json` para bloqueo de gasto:
   - el harness debe leer `api_budget.json` antes de ejecutar cambios sensibles
   - si el presupuesto se acerca a `0`, detener operaciones automáticas y pedir revisión manual

### Beneficios esperados

- reducción de tokens de prompt en cada ciclo de edición profunda.
- menor riesgo de que Roo Code use un modelo más caro equivocadamente.
- control explícito de límites por clave y ambiente.
- visibilidad de consumo de crédito por alias y proveedor.

## 3. Refactorización Propuesta para el Script de Control del Entorno

### Observaciones clave

- `skill_env_control.py` ya existe como controlador parcial, pero debe convertirse en el punto único de orquestación.
- El harness debe dejar de tratar `skill_plan.py`, `skill_docker.py` y `skill_commit_push.py` como consumidores independientes sin un flujo coordinado.
- La gestión de concurrencia entre Hermes/Telegram y Copilot/Roo Code falta en `skill_env_control.py`.

### Refactorización propuesta

1. `skill_env_control.py` debe convertirse en el controlador maestro:
   - `load_repository_state()`
   - `discover_changed_files()`
   - `acquire_harness_lock()`
   - `release_harness_lock()`
   - `emit_structured_telemetry()`

2. Consolidar todas las lecturas y escrituras de `state.json` en `harness/scripts/utils/state_loader.py`.
   - `StateLoader.acquire_lock()` / `release_lock()` ya están implementados.
   - Todos los scripts deben compartir este mecanismo.
   - `StateLoader.load_state(force_reload=True)` debe ser la única entrada de estado.

3. Generar telemetría estructurada en lugar de Markdown cuando sea posible:
   - `skill_env_control.py` puede registrar `hermes` como objeto JSON con campos `installed`, `version`, `provider`, `model_default`, `base_url`, `gateway`.
   - Exponer `system.os_name`, `system.os_version`, y `system.driver_extensions` de forma portable.
   - Incluir un `changed_files` array en el estado para prompts incrementales.

4. Implementar un flujo incremental de archivos modificados:
   - `git diff --name-only HEAD~1..HEAD`
   - `git status --porcelain` para detectar cambios no rastreados
   - reaccionar solo sobre ese subconjunto en el prompt de edición profunda

5. Evitar hardcodeos de Linux y variables rígidas:
   - `repo_root` debe respetar `REPO_ROOT_OVERRIDE`
   - `Path.home()` y `os.getenv("HOME")` deben usarse para rutas de usuario
   - `skill_state.py` no debe asumir `/etc/os-release`, `dpkg-query`, `lsb_release` ni `docker` como siempre presentes
   - `skill_env_control.py` no debe usar `env_id` fijo como `codespaces-16ec44`

6. Mejorar la robustez del Dockerfile:
   - `Dockerfile` líneas `5-15`: consolidar instalación en una sola capa y marcar paquetes estrictos.
   - `Dockerfile` línea `19`: validar `PATH` y asegurar que `~/.hermes` se pueda montar como volumen externo.
   - Añadir documentación de volúmenes persistentes para estado de Hermes y `state.json`.

### Recomendación específica de implementación

- Mantener `skill_state.py` como productor de estado y telemetría.
- `skill_plan.py` solo debe materializar plan/markdown desde el estado central.
- `skill_docker.py` debe ser un actualizador de `Dockerfile` basado en `state.json`.
- `skill_commit_push.py` debe validar y publicar, pero no regenerar estado.
- `skill_env_control.py` debe orquestar el ciclo completo: `state -> plan -> docker -> commit`.

## 4. Rutas de auditoría y artefacto histórico

- Archivo de diagnóstico principal: `copilot_improvements.md`
- Archivo histórico de auditoría: `tests/copilot_deep_audit.md`

> Este diagnóstico se genera como el entregable técnico para asistentes de código (Copilot/Roo Code). Mantiene el foco en reducción de contexto, portabilidad multi-entorno, y bloqueo de concurrencia entre Hermes y la edición profunda.
