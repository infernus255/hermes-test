# Skill: Gestión Inteligente de Tokens y Rotación Dinámica de API Keys

## 1. Propósito
Optimizar de forma extrema el consumo de tokens y créditos en entornos de ejecución autónoma (Autopilot Preview / Hermes Loop). Evitar el agotamiento de cuotas gratuitas o bloqueos de API mediante la racionalización del contexto, la selección inteligente de modelos y la rotación automática de credenciales.

## 2. Archivo de Estado Central (`config/api_budget.json`)
Este archivo debe ser la única fuente de verdad para el consumo de tokens y la selección de modelos. Debe actualizarse en caliente antes y después de cada llamada pesada de orquestación.

```json
{
  "vault": {
    "gemini_35_flash_primary": { "key_env_var": "GEMINI_API_KEY_1", "provider": "google", "tier": "free", "daily_token_limit": 500000, "used_today": 0, "status": "active" },
    "gemini_35_flash_backup": { "key_env_var": "GEMINI_API_KEY_2", "provider": "google", "tier": "free", "daily_token_limit": 500000, "used_today": 0, "status": "idle" },
    "openai_fallback": { "key_env_var": "OPENAI_API_KEY", "provider": "openai", "tier": "pay_as_you_go", "daily_token_limit": 100000, "used_today": 0, "status": "idle" }
  },
  "current_strategy": "cost_saving",
  "copilot_quota_alerts": {
    "max_percentage_per_session": 5,
    "current_session_burn": 0,
    "last_checkpoint_percentage": 4
  }
}
```

## 3. Matriz de Racionalización (Reglas de Selección para Ambas IAs)

| Complejidad de la Tarea | Tipo de Ejecución | Modelo / Flujo Asignado | Estrategia de Ahorro de Tokens |
|---|---|---|---|
| Baja | Respuestas breves en Telegram, logs simples, confirmación de commits. | Raptor Mini (Si estás en VS Code) o respuestas directas sin historial. | Forzar respuestas de menos de 100 tokens. Limpiar el historial previo. |
| Media | Refactorización de código aislado, añadir habilidades (`skills/*.md`), documentación. | Gemini 3.5 Flash (Key activa con menor porcentaje de uso). | Inyección de contexto fraccionada (solo las líneas mutadas, no el archivo entero). |
| Alta | Modificaciones de la arquitectura del Harness, refactorización de Docker, fallas críticas. | Gemini 3.5 Flash (Extended Context si es necesario) / Copilot Autopilot. | Consolidar un resumen previo (summary) antes de pasar todo el árbol del repositorio. |

## 4. Algoritmo de Control de "Supervivencia"

- Pre-Fly Check (Cálculo de costo estimado): Antes de enviar un prompt extenso al endpoint, estimar el tamaño del payload. Si excede el 15% de la cuota diaria remanente de la clave activa, la tarea se fragmenta o se degrada a un modelo inferior.
- Monitoreo de Copilot Free: Al detectar un incremento en los créditos quemados en Copilot (por ejemplo, saltar del 4% al 47%), el orquestador congelará temporalmente las ejecuciones de refactorización masiva multi-archivo en segundo plano.
- Freno de Mano por Bucle Infinito: Si una misma sub-tarea autónoma falla 3 veces consecutivas, el Skill abortará la ejecución, escribirá el error en el repositorio y emitirá un ping de emergencia vía Telegram para intervención humana.
