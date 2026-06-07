# n8n Documentation

Este documento describe cómo verificar y documentar la instalación de n8n dentro del repositorio.

## Qué verifica el skill de commit/push

- `n8n` está disponible en el PATH (`n8n --version`).
- El proceso debe estar levantado cuando se solicita validación de ejecución.
- Existe documentación dedicada en `docs/N8N.md`.
- El estado de Docker se puede validar con `docker compose config`.

## Instalación mínima

```bash
npm install -g n8n
```

## Ejecución mínima

```bash
n8n start
```

## Notas

Este repositorio usa herramientas deterministas para validar estado y documentación. El commit/push skill usa `state.json` y estos archivos de documentación como puntos de comprobación.
