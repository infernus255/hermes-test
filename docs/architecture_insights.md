# Guía de Insights de Arquitectura para la Auto-Evolución del Sistema
> **Nota para los Agentes de IA:** Lee este documento detenidamente antes de modificar cualquier línea de código del repositorio. Define las restricciones físicas y operativas de este ecosistema híbrido.

---

## 1. Topología del Entorno Operativo
Este sistema funciona bajo un esquema descentralizado con una única fuente de verdad:

[ Telegram Input ] -----v[ VS Code / Copilot ] --> [ Harness en Codespaces (Linux/Docker) ] --> [ GitHub Repo (Truth) ]^[ Nodos Locales (A/B) ] -/

* **Entorno de Ejecución Actual:** GitHub Codespaces ejecutando una distribución de Linux en la nube.
* **Advertencia de Docker en la Nube:** Al correr dentro de Codespaces, Docker opera bajo un esquema de *Docker-in-Docker* (DinD) o sockets compartidos. Los agentes deben asegurar que los volúmenes configurados para persistencia de estados locales utilicen rutas relativas que no se destruyan al reiniciar o expirar el Codespace web.

---

## 2. Peligros Críticos del Modo Autopilot (Preview) con Raptor Mini
El modo Autopilot de Copilot tiene permisos para autoevaluar herramientas, responder preguntas de bloqueo internas y continuar iterando sin confirmación humana directa.

* **El Riesgo del "Bucle de Dinero/Créditos Quemados":** Al emparejar a Raptor Mini (optimizado para ediciones masivas multi-archivo) con un bucle autónomo que se autogestiona, existe el riesgo de que una mala interpretación gramatical en el Prompt Engineering provoque que la IA reescriba 50 archivos de forma cíclica, evaporando el remanente de los créditos gratuitos en minutos.
* **Mitigación:** Todo script generado para automatizar el bucle debe incluir un mecanismo de *Rate Limiting* por hardware o tiempo (ej. máximo 5 iteraciones seguidas antes de forzar un `sleep` de 60 segundos).

---

## 3. Estrategia Multientorno y Flota de Agentes
Cuando este repositorio se clone en diferentes entornos físicos (Computadora personal A, Computadora de pruebas B, Servidor en la nube):

* Cada máquina debe inyectar una variable de entorno local llamada `AGENCY_NODE_ID` (ej: `DESKTOP-EROS-01`, `CODESPACE-WEB`).
* Los cambios locales en los Skills que dependan de optimizaciones específicas de hardware o sistemas operativos locales se manejarán a través de ramas (*branches*) separadas.
* La consolidación de conocimientos de los diferentes entornos se gestionará de manera limpia mediante Pull Requests (PRs). Los agentes pueden abrir PRs de forma autónoma con los archivos `.md` de nuevos aprendizajes en la carpeta `/skills`, pero la fusión final a `main` requiere control de calidad o validación integral de tests del sistema.

---

## 4. Instrucciones de Uso

1. Crea una carpeta llamada `harness/` y guarda allí los dos primeros archivos (`skill_token_management.md` y `skill_harness_improvement.md`).
2. Guarda el tercer archivo (`architecture_insights.md`) en la raíz del repositorio.
3. Abre el chat de Copilot en modo Autopilot Preview (con Raptor Mini seleccionado) o invoca a Hermes y diles:

"Lean los archivos en `harness/` y el archivo `architecture_insights.md`. En base a esas directivas, programen el script de automatización en Python o Node para inicializar la base de `config/api_budget.json` y configuren el interceptor de tokens para las API keys de Gemini 3.5 Flash".

A partir de ahí, ambos modelos entenderán perfectamente las reglas de juego, los límites de costos y cómo optimizarse mutuamente sin pisarse los cables.
