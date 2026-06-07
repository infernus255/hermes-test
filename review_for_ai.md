# Paquete de Revisión para Otra IA

Este archivo reúne las rutas y el propósito clave para que otra IA analice el repositorio.

## Fecha de generación
- 2026-06-07T08:53:46.842744+00:00

## Archivos clave para revisión

- `README.md`
- `copilot_improvements.md`
- `docs/copilot-instructions.md`
- `harness/docs/COPILOT_SKILL.md`
- `docs/HERMES_TELEGRAM_INSTALL_PLAN.md`
- `harness_evolution_blueprint.md`
- `harness/README.md`
- `harness/scripts/skill_state.py`
- `harness/scripts/skill_plan.py`
- `harness/scripts/skill_docker.py`
- `harness/scripts/skill_commit_push.py`
- `harness/scripts/utils/state_loader.py`
- `Dockerfile`
- `docker-compose.yml`
- `api_budget.json`

## Puntos de enfoque para la IA

- Revisa la arquitectura del harness y los scripts en `harness/scripts/`.
- Comprueba el uso de `state.json`, bloqueo de archivos y portabilidad.
- Verifica la gobernanza de claves API y la configuración de `api_budget.json`.
- Evalúa la consistencia entre documentación y código.
- Busca condiciones de carrera, duplicaciones y dependencias rígidas.

## Uso

1. Abre este archivo y el archivo `copilot_improvements.md`.
2. Envía estos archivos al chat o IA de revisión.
3. Pide recomendaciones específicas sobre robustez, portabilidad y gobernanza de tokens.

## Nota de seguridad

- No compartas archivos con credenciales reales (`hermes.env`, `~/.hermes/.env`, etc.).
- Usa siempre `hermes.env.example` como plantilla.
