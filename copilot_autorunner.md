## Pipeline de Ejecución Automatizada: Consolidación de Arquitectura

Este autorunner define las tres fases estrictas y secuenciales para aplicar la refactorización profunda, asegurar la persistencia del entorno y validar el pipeline unificado del harness.

### FASE 1: Trigger de Refactorización de Código (Enviar a Copilot / Roo Code)

Copia y pega la siguiente directiva exacta en el chat de tu asistente de desarrollo para automatizar la **Tarea C** de reestructuración:

Plaintext

```
Lee el archivo de gobernanza @copilot_architecture_directive.md y ejecuta de inmediato la "Tarea C: Desacoplamiento de Scripts Secundarios":

1. Reescribe por completo 'harness/scripts/skill_docker.py' y 'harness/scripts/skill_plan.py'. Elimina cualquier llamada directa de lectura a 'state.json' mediante Path o json.loads crudo.
2. Importa e integra obligatoriamente el módulo reutilizable 'StateLoader' y consume los datos usando 'StateLoader().load_state()'.
3. Modifica la estrategia de parcheo en 'skill_docker.py': elimina las expresiones regulares frágiles y reemplázalas por un sistema idempotente basado en la detección de bloques comentados fijos: '# PACKAGES-BEGIN' y '# PACKAGES-END' dentro del Dockerfile.
4. Verifica que los archivos queden guardados respetando las rutas de la topología portable.
```

### FASE 2: Parche de Infraestructura (Actualización de Persistencia Docker)

Asegura la memoria a largo plazo de Hermes aplicando esta configuración exacta en tu archivo `docker-compose.yml`. Esto previene la amnesia del contenedor ante reinicios:

YAML

```
version: '3.8'

services:
  hermes:
    build: .
    container_name: hermes_agent_main
    env_file:
      - hermes.env
    volumes:
      # Sincronización de volumen persistente para la configuración y tokens de Hermes
      - ~/.hermes:/root/.hermes
      # Mapeo del estado único del repositorio compartido con el host de Linux
      - ./state.json:/workspaces/hermes-test/state.json
    ports:
      - "9119:9119"
    restart: unless-stopped
```

### FASE 3: Secuencia de Comandos en Terminal (Validación del Circuito Unificado)

Una vez que la IA termine la refactorización y los volúmenes estén mapeados, ejecuta esta secuencia de comandos de forma ordenada en la terminal de tu GitHub Codespace para consolidar el estado de producción:

Bash

```
# Paso 1: Ejecutar el controlador maestro para levantar la telemetría portable del OS y Git
python3 harness/scripts/skill_env_control.py

# Paso 2: Validar que la telemetría incremental se haya inyectado correctamente en el state.json
cat state.json | grep -A 5 "harness_telemetry"

# Paso 3: Ejecutar las pruebas, verificar n8n y realizar el push determinista al repositorio público
python3 harness/scripts/skill_commit_push.py "Harness Evolution: Implementación exitosa de arquitectura multi-entorno y mitigación de tokens"
```
