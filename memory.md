# Hermes Memory

Este archivo registra cada aprendizaje, mejora o decisión de configuración importante para que el proyecto evolucione con poco gasto de tokens.

## Aprendizajes y mejoras

- 2026-06-07: Configuración de Hermes con proveedor `gemini` y modelo `gemini-3.5-flash` para Google Gemini directo.
- 2026-06-07: Dockerfile ajustado para incluir `xz-utils` y permitir que el instalador de Hermes descargue y desempaquete su runtime interno.
- 2026-06-07: Se crearon los artefactos reproducibles: `Dockerfile`, `docker-compose.yml`, `docker-entrypoint.sh`, `hermes.env.example`, `hermes-install.sh`.
- 2026-06-07: Se añadió la primera estructura de `state.json` para registrar estado de Hermes, OS y git de manera automatizada.
