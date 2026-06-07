# hermes-test

Este repositorio contiene todo lo necesario para ejecutar Hermes Agent con soporte de Telegram dentro de Docker.

Archivos principales:

- `Dockerfile` — construye la imagen Hermes con dependencias y el instalador oficial.
- `docker-compose.yml` — ejecuta Hermes en un contenedor reproducible.
- `docker-entrypoint.sh` — inyecta las variables de entorno y arranca Hermes.
- `hermes.env.example` — plantilla para tus credenciales.
- `HERMES_TELEGRAM_INSTALL_PLAN.md` — plan de instalación, diagnóstico y despliegue.

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

## Validación

El Dockerfile se construyó correctamente y el contenedor puede ejecutar Hermes. Con un token real de Telegram y una API key válida de Gemini, el gateway debe iniciarse y conectar a la plataforma Telegram.

## Archivos de soporte adicionales

- `.gitignore` — para ignorar archivos de entorno local.
- `hermes-install.sh` — script de instalación reproducible para entornos Ubuntu.
