# Hermes Skills

Estos scripts son las "skills" ligeras para mantener memoria, estado, plan y Docker sincronizados.

- `bash harness/scripts/skill_memory.sh "Texto de aprendizaje"`
  - Agrega una nueva entrada en `memory.md`.

- `python3 harness/scripts/skill_state.py`
  - Escanea Hermes, el sistema operativo y el repositorio git.
  - Genera o actualiza `state.json`.
  - Herramienta determinista para capturar el estado real del entorno.
  - Registra cada entorno como una entrada independiente en `state.json`.
  - Detecta múltiples claves API y sus límites configurados.

- `python3 harness/scripts/skill_plan.py`
  - Usa `state.json` para actualizar `docs/HERMES_TELEGRAM_INSTALL_PLAN.md`.
  - Inserta la sección de estado actual y el autorunner de bajo tier.
  - No inventa cambios: refleja el estado detectado.

- `python3 harness/scripts/skill_docker.py`
  - Revisa `state.json` y sincroniza la lista de paquetes en `Dockerfile`.
  - Asegura que el Dockerfile sea coherente con el estado del sistema.

- `python3 harness/scripts/skill_commit_push.py "Mensaje de commit"`
  - Valida el estado, la documentación, Hermes, Copilot, n8n y Docker.
  - Hace commit y push solo si todas las comprobaciones pasan.
