# Auditoría Técnica: Copilot Harness y Optimización de Token

## 1. Duplicación de Procesamiento de Contexto

El repositorio actual duplica la carga y el análisis del contexto en varios scripts del harness.

### Bloques exactos de código duplicados

1. `skills/scripts/skill_state.py`
   - `11: REPO_ROOT = Path(__file__).resolve().parents[1]`
   - `12: STATE_FILE = REPO_ROOT / "state.json"`
   - `14: KEY_LIMITS_FILE = REPO_ROOT / "api_key_limits.json"`
   - `37: def load_env_file(path):`
   - `73: if KEY_LIMITS_FILE.exists():`
   - `75: data = json.loads(KEY_LIMITS_FILE.read_text(encoding="utf-8"))`
   - `112: env_values.update(load_env_file(repo_env))`
   - `115: env_values.update(load_env_file(home_env))`
   - `189: output = run_command(["hermes", "--version"]) or ""`
   - `193: config_output = run_command(["hermes", "config", "show"]) or ""`
   - `247: if Path("/etc/os-release").exists():`
   - `248: data = Path("/etc/os-release").read_text().splitlines()`

2. `skills/scripts/skill_plan.py`
   - `8: PLAN_FILE = REPO_ROOT / "docs" / "HERMES_TELEGRAM_INSTALL_PLAN.md"`
   - `16: def load_state():`
   - `19: return json.loads(STATE_FILE.read_text())`
   - `112: content = PLAN_FILE.read_text()`
   - `115-122:` manipulación directa de contenido markdown para reemplazar bloques `STATE-BEGIN` / `STATE-END` y `AUTORUNNER-BEGIN` / `AUTORUNNER-END`
   - `123: PLAN_FILE.write_text(content)`

3. `skills/scripts/skill_docker.py`
   - `8: DOCKERFILE = REPO_ROOT / "Dockerfile"`
   - `11: def load_state():`
   - `14: return json.loads(STATE_FILE.read_text())`
   - `17: def parse_dockerfile_packages(content):`
   - `18: pattern = re.compile(r"apt-get install -y(.*?)(?:\\n|$)", re.S)`
   - `46: state = load_state()`
   - `48: dockerfile_text = DOCKERFILE.read_text()`
   - `53: DOCKERFILE.write_text(updated_text)`

4. `skills/scripts/skill_commit_push.py`
   - `12: VALIDATION_FILES = [`
   - `41: def load_state():`
   - `43: return None, "No se encontró state.json. Ejecuta skills/scripts/skill_state.py primero."`
   - `84: def validate_copilot_docs():`
   - `100: def validate_n8n():`
   - `112: def validate_api_keys(state):`
   - `139: def git_add_commit_push(message):`
   - `146: state, err = load_state()`
   - `153: for path in VALIDATION_FILES:`
   - `169: ok, msg = validate_copilot_docs()`
   - `174: ok, msg = validate_api_keys(state)`
   - `179: ok, msg = validate_n8n()`
   - `199: git_add_commit_push(commit_message)`

### Observaciones de duplicación

- `state.json` se vuelve a leer en `skill_plan.py`, `skill_docker.py` y `skill_commit_push.py`.
- `skill_commit_push.py` vuelve a validar archivos que ya pueden haber sido generados por otros scripts, lo que agrega carga innecesaria.
- El parseo de la configuración de Hermes en `skill_state.py` se realiza con expresiones regulares sobre `hermes config show` en lugar de usar un formato estructurado.
- La validación de `state.json` y la generación de `HERMES_TELEGRAM_INSTALL_PLAN.md` son procesos separados, pero el prompt de Copilot idealmente debe consumir solo el estado ya formalizado.

## 2. Plan para Conectar Roo Code con Gemini 3.5 Flash

### Objetivo
Minimizar el consumo de contexto y créditos de Copilot usando el modelo `gemini-3.5-flash` como el canal preferido de inferencia para edición profunda.

### Propuesta Técnica

1. Establecer un alias de uso exclusivo para Roo Code:
   - `ROO_CODE_GEMINI_API_KEY`
   - `HEREMES_MODEL_DEFAULT=gemini-3.5-flash`
   - Opcionalmente: `ROO_CODE_GEMINI_ALIAS=roo` o `GEMINI_API_KEY_ROO`

2. Actualizar la carga de claves en el harness para exponer este alias como clave de menor costo:
   - `skills/scripts/skill_state.py` ya soporta `GEMINI_API_KEYS` y `GOOGLE_API_KEYS`.
   - Agregar un prefijo `ROO_` y permitir `ROO_GEMINI_API_KEY` como entrada explícita.

3. Limitar el contexto de Copilot a cambios detectados:
   - Ejecutar `git diff --name-only HEAD^` o un hash de `state.json`.
   - En lugar de presentar todo el repo, solo enviar:
     - archivos modificados desde la última sincronización (`git diff --name-only`)
     - `state.json` corto con metadatos relevantes
     - `docs/copilot-instructions.md` y `skills/docs/COPILOT_SKILL.md`

4. Definir la política de modelo en Hermes:
   - `provider=gemini`
   - `model.default=gemini-3.5-flash`
   - `model.base_url=https://generativelanguage.googleapis.com/v1beta/openai`

5. Añadir control de límite de uso por clave:
   - Reforzar `api_key_limits.json` y `API_KEY_LIMITS`.
   - Registrar el uso de Gemini por alias en `state.json`.
   - Proponer `api_budget.json` como fuente compartida para monitorear créditos.

### Ganancia esperada
- Menor tasa de tokens enviados en prompts de edición profunda.
- Menor riesgo de que Roo Code use el modelo más caro equivocadamente.
- Control explícito de límites por clave y ambiente.

## 3. Refactorización Propuesta para el Script de Control del Entorno

### Problema actual
El harness divide responsabilidades entre varios scripts sin un controlador centralizado. Esto causa:
- duplicación de lectura de `state.json`
- falta de bloqueo en `state.json` y en archivos generados
- dependencia de rutas Linux estáticas
- falta de un mecanismo de cambio incremental

### Propuesta: `skills/scripts/skill_env_control.py`

Debe incluir:

1. Descubrimiento de entorno portable
   - `REPO_ROOT = Path(__file__).resolve().parents[1]`
   - `HOME = Path(os.getenv('HOME', Path.home()))`
   - Permitir `REPO_ROOT` sobreescribible con `REPO_ROOT_OVERRIDE`

2. Carga de telemetría estructurada
   - Leer los logs de Hermes si existen en JSON o YAML
   - Evitar `hermes config show` sin estructura; usar JSON directo cuando el proveedor lo permita
   - Registrar en `state.json` un objeto `hermes.telemetry` con:
     - `timestamp`
     - `config_path`
     - `gateway_status`
     - `model.provider`
     - `model.default`
     - `model.base_url`

3. Control de archivos modificados
   - `changed_files = git diff --name-only HEAD..HEAD~1`
   - Solo reanalizar los archivos contenidos en `changed_files`
   - Generar un subset JSON con `changed_files` y `state.json.summary`

4. Bloqueo / lock system
   - Usar `flock` o Python `portalocker` en:
     - `state.json`
     - `docs/HERMES_TELEGRAM_INSTALL_PLAN.md`
     - `memory.md`
   - Incluir un semáforo simple en disco: `./.harness_lock`

5. Portabilidad del sistema operativo
   - Reemplazar el hardcode de `/etc/os-release` y `dpkg-query` por detección condicional:
     - `shutil.which('dpkg-query')`
     - `shutil.which('rpm')`
     - `shutil.which('uname')`
   - No asumir `lsb_release` siempre disponible.

6. Separación de estado y output
   - `state.json` debe ser la única fuente de verdad del entorno.
   - `docs/HERMES_TELEGRAM_INSTALL_PLAN.md` debe generarse desde `state.json` mediante un único paso.
   - `skill_commit_push.py` debe validar, pero no regenerar o reanalizar archivos más de lo estrictamente necesario.

### Refactorización concreta

- Unificar la carga de `state.json` en un helper compartido `utils/state_loader.py`.
- Convertir `skill_plan.py` y `skill_docker.py` en consumidores ligeros de ese helper.
- Añadir una capa `state_cache` que memoice la lectura de `state.json` dentro de una ejecución.
- Crear `skill_env_control.py` que exponga:
  - `load_repository_state()`
  - `discover_changed_files()`
  - `acquire_harness_lock()`
  - `release_harness_lock()`
  - `emit_structured_telemetry()`

## 4. Auditoría de Robustez y Portabilidad

### Hardcodeos detectados

- `Path("/etc/os-release")` en `skills/scripts/skill_state.py:247`
- `Path.home() / ".hermes" / ".env"` en `skills/scripts/skill_state.py:115`
- Uso directo de `dpkg-query` y `lsb_release` en `skill_state.py`
- Uso directo de `docker`, `pgrep`, `n8n` en `skill_commit_push.py`
- `Dockerfile` fija Ubuntu 24.04 y usa `apt-get install -y` sin cache de capas ni volúmenes persistentes

### Dockerfile relevantes

- `Dockerfile:1-8` instala paquetes básicos y Hermes sin un stage de build intermedio.
- No existe una capa explicita de volumen persistente para `~/.hermes` o `state.json`.
- El contenedor actual puede destruir el estado de aprendizaje si se reinicia sin volúmenes correctamente montados.

### Concurrencia / lock system

- No hay bloqueo de archivos en ninguno de los scripts.
- `skill_commit_push.py` puede ejecutarse al mismo tiempo que `skill_state.py` o `skill_plan.py`, lo que genera condiciones de carrera sobre `state.json` y los archivos markdown.
- No hay registro de `last_synced_commit` ni de versiones de `state.json`.

## 5. Recomendaciones Prioritarias

1. Implementar un lock simple para `state.json` y archivos generados.
2. Cambiar la telemetría de Hermes a un formato JSON estructurado en lugar de parsear texto con regex.
3. Añadir `ROO_CODE_GEMINI_API_KEY` y un alias de modelo en la configuración de Hermes.
4. Limitar el prompt de Copilot/Roo Code a archivos modificados y a un fragmento condensado de `state.json`.
5. Refactorizar el controlador de entorno hacia un único módulo reusable.

---

> Este documento se basa en la implementación actual de los scripts en `skills/scripts/*` y el `Dockerfile` del repositorio.
