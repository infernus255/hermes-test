# hermes-test

Este repositorio contiene todo lo necesario para ejecutar Hermes Agent con soporte de Telegram dentro de Docker.

Archivos principales:

- `Dockerfile` — construye la imagen Hermes con dependencias y el instalador oficial.
- `docker-compose.yml` — ejecuta Hermes en un contenedor reproducible.
- `docker-entrypoint.sh` — inyecta las variables de entorno y arranca Hermes.
- `hermes.env.example` — plantilla para tus credenciales.
- `api_budget.json` — archivo de presupuesto de tokens compartido.
- `api_key_limits.example.json` — ejemplo de límites para las API keys.
- `docs/` — documentación, planos y gobernanza de arquitectura.

## Uso rápido

1. Copia la plantilla de entorno:

```bash
cp hermes.env.example hermes.env
```

2. Rellena `hermes.env` con tus credenciales reales:

- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY` o `GOOGLE_API_KEY`
- `GATEWAY_ALLOW_ALL_USERS=true` durante pruebas

3. Construye y arranca el contenedor:

```bash
docker compose up --build -d
```

4. Verifica los logs:

```bash
docker compose logs -f
```

5. Para ejecutar comandos Hermes directamente dentro de la imagen:

```bash
docker run --rm --entrypoint /bin/bash hermes-test -lc 'hermes --version'
```

## Notas importantes

- `hermes.env` no debe ser versionado con secretos reales.
- `.dockerignore` ya excluye `hermes.env` y otros archivos de entorno.
- El contenedor necesita un token válido de Telegram antes de poder conectar la plataforma.
- El entrypoint ahora acepta comandos personalizados o, por defecto, arranca `hermes gateway run`.
- Usa las skills ligeras en `harness/` para mantener memoria, estado y el plan sincronizados.

## Validación

El Dockerfile se construyó correctamente y el contenedor puede ejecutar Hermes. Con un token real de Telegram y una API key válida de Gemini, el gateway debe iniciarse y conectar a la plataforma Telegram.

## Archivos de soporte adicionales

- `.gitignore` — para ignorar archivos de entorno local.
- `hermes-install.sh` — script de instalación reproducible para entornos Ubuntu.
- `harness/README.md` — guía de skills ligeras para memoria, estado, plan y Docker.
- `review_for_ai.md` — paquete de revisión listo para enviar a otra IA.
- `copilot_architecture_directive.md` — directivas claras para refactorizar el harness.
- `copilot_autorunner.md` — autorunner maestro para ejecutar la refactorización y validación.
- `api_key_limits.example.json` — ejemplo de configuración de límites de API keys.
- `harness/scripts/skill_commit_push.py` — skill de validación, commit y push basado en estado.
- `docs/N8N.md` — documentación de n8n para este repositorio.
- `state.json` — ahora registra el entorno actual y mantiene múltiples entornos.
- `docs/copilot-instructions.md` — instrucciones de Copilot para usar estas skills de forma determinista.
- `harness/docs/COPILOT_SKILL.md` — documentación de la skill y el comportamiento predecible.
