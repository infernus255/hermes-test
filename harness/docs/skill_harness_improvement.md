# Skill: Auto-Optimización y Evolución del Harness de Orquestación

## 1. Propósito
Permitir que el motor de ejecución autónoma (el Harness que vincula Linux/Codespaces, Docker, Telegram y GitHub) analice su propio rendimiento y se modifique a sí mismo, incrementando la velocidad de procesamiento, mejorando el manejo del estado multi-entorno y robusteciendo la estabilidad del contenedor Docker.

## 2. Áreas de Optimización Obligatoria

### A. Gestión Eficiente del Estado (Git Syncing)
* El Harness debe estructurar las actualizaciones en commits atómicos y descriptivos.
* Implementar un sistema de marcas de tiempo y hashes de entorno en el repositorio para evitar conflictos cuando múltiples nodos locales (Compu A, Compu B, entorno Codespaces en la Web) sincronicen cambios en paralelo.

### B. Robustez del Entorno Docker (Pruebas de Contenedorización)
* **Regla de Oro:** El agente tiene permitido mutar el `Dockerfile` y los archivos de configuración de Docker Compose, pero **NUNCA** puede realizar un push directo a la rama principal (`main`) sin haber ejecutado con éxito una validación local:

```bash
  docker compose build --no-cache && docker compose run --rm test-suite
```

Si el build de prueba falla, el Harness debe capturar el stderr del contenedor, revertir los cambios locales al último commit estable (`git stash` / `git checkout -- .`) y reevaluar su estrategia de Prompt Engineering.

### C. Unificación de Canales de Entrada (Telegram vs. VS Code Client)
El Harness debe procesar los comandos de Telegram y las solicitudes del panel de chat de Copilot usando la misma capa lógica para evitar condiciones de carrera (dos IAs intentando escribir el mismo archivo al mismo tiempo).

Cuando se reciba un comando prioritario por Telegram, el Harness pausará momentáneamente las tareas en segundo plano que esté ejecutando el Autopilot de Copilot en VS Code.

## 3. Métricas de Eficiencia del Sistema

El Harness evaluará su éxito basándose en la reducción progresiva de:
* El tiempo total de ejecución por tarea compleja (Latencia).
* La cantidad de tokens consumidos para estabilizar un bug en Docker (Costo).
* Los errores de sincronización entre entornos distribuidos (Múltiple Entorno).
