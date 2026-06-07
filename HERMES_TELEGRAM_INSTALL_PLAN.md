# Plan de Implementación: Instalación de Hermes Agent y Conexión con Telegram en Ubuntu (Codespaces)

Este documento contiene instrucciones paso a paso para instalar Hermes Agent, configurar un Gateway de Telegram y asegurar la replicabilidad en múltiples entornos.

---

## 1. Objetivo

Construir una instalación completa y reproducible de Hermes Agent en un entorno Ubuntu/Codespaces, con:

- Hermes Agent instalado y configurado
- Gateway de Telegram operativo
- LLM directo con Google Gemini
- Persistencia en segundo plano
- Diagnóstico y reparación de errores de proveedor
- Base para escalar a Docker / scripts / despliegues reproducibles

---

## 2. Requisitos previos

Antes de comenzar, prepara estas credenciales y datos:

- `TELEGRAM_BOT_TOKEN` — generado por `@BotFather` con `/newbot`
- `TELEGRAM_USER_ID` — tu ID de Telegram obtenido con `@userinfobot`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` — clave de Google Gemini / AI Studio
- Acceso a la terminal de Ubuntu / Codespaces
- `curl`, `git`, `python3`, `npm` disponibles

> Mantén las claves fuera de chat y en un archivo `.env` local. Nunca compartas claves reales en mensajes.

---

## 3. Preparación del entorno

Ejecuta esto para dejar el sistema listo:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git build-essential python3 python3-venv python3-pip npm
```

Verifica que `python3`, `pip`, `npm` y `curl` estén instalados:

```bash
python3 --version
pip3 --version
npm --version
curl --version
```

---

## 4. Instalación de Hermes Agent

Instala Hermes Agent con el script oficial de Nous Research:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Después de la instalación, recarga tu shell para asegurar que `~/.local/bin` esté en el `PATH`:

```bash
source ~/.bashrc
```

Verifica la instalación:

```bash
which hermes
hermes --version
```

---

## 5. Configuración segura de credenciales

Crea el archivo `~/.hermes/.env` con los valores exactos.

```bash
mkdir -p ~/.hermes
cat > ~/.hermes/.env <<'EOF'
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GATEWAY_ALLOW_ALL_USERS=true
GEMINI_API_KEY=your_gemini_api_key_here
# GOOGLE_API_KEY=your_gemini_api_key_here
EOF
```

Opcionalmente, para restringir acceso:

```bash
cat >> ~/.hermes/.env <<'EOF'
TELEGRAM_ALLOWED_USERS=123456789
EOF
```

> `GATEWAY_ALLOW_ALL_USERS=true` debe usarse sólo durante pruebas. En producción, define `TELEGRAM_ALLOWED_USERS`.

---

## 6. Configuración de Hermes para Google Gemini directo

Hermes puede usar Google Gemini directamente con el proveedor `gemini`. Para eso NO uses slugs con prefijo de proveedor, es decir:

- Correcto: `gemini-3.5-flash`
- Incorrecto para `provider: gemini`: `google/gemini-3.5-flash`

Configura Hermes así:

```bash
hermes config set model.provider gemini
hermes config set model.default gemini-3.5-flash
hermes config set model.base_url https://generativelanguage.googleapis.com/v1beta/openai
```

Verifica el estado de la configuración:

```bash
hermes config show
```

Debes ver algo como:

- `provider: gemini`
- `default: gemini-3.5-flash`
- `base_url: https://generativelanguage.googleapis.com/v1beta/openai`

---

## 7. Configuración del Gateway de Telegram

Configura el Gateway con Hermes:

```bash
hermes gateway setup
```

Pasos en el asistente:

1. Seleccionar plataforma `Telegram`
2. Ingresar el token de `TELEGRAM_BOT_TOKEN`
3. Definir el `TELEGRAM_USER_ID` en la allowlist o usar `GATEWAY_ALLOW_ALL_USERS=true`
4. Establecer el home channel si se solicita
5. Para ejecución en Codespaces, evitar systemd si no está disponible

Verifica el Gateway y configúralo:

```bash
hermes gateway status
hermes gateway list
```

---

## 8. Ejecutar Hermes Gateway en segundo plano

### Opción A: PM2 (recomendada dentro de Codespaces)

Instala PM2:

```bash
sudo npm install -g pm2
```

Arranca el dashboard:

```bash
pm2 start hermes --name "hermes-dashboard" -- dashboard --host 127.0.0.1 --port 9119 --insecure
```

Arranca el gateway:

```bash
pm2 start hermes --name "hermes-gateway" -- gateway run
```

Guarda la configuración de PM2:

```bash
pm2 save
pm2 status
```

### Opción B: Servicio systemd (si el host lo soporta)

```bash
hermes gateway install --system
sudo systemctl enable --now hermes-gateway.service
sudo systemctl status hermes-gateway.service
```

### Opción C: Docker / contenedor reproducible

Para replicar en otros entornos, puedes usar Docker con un `Dockerfile` similar a este:

```dockerfile
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y curl git python3 python3-venv python3-pip npm
RUN curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
ENV PATH="/root/.local/bin:/root/.hermes/hermes-agent/venv/bin:$PATH"
COPY hermes.env /root/.hermes/.env
RUN chmod 600 /root/.hermes/.env
CMD ["hermes", "gateway", "run"]
```

Y un archivo `hermes.env` con los valores:

```env
TELEGRAM_BOT_TOKEN=...
GATEWAY_ALLOW_ALL_USERS=true
GEMINI_API_KEY=...
```

Luego construye y ejecuta:

```bash
docker build -t hermes-gateway .
docker run --rm -p 9119:9119 --name hermes-gateway hermes-gateway
```

---

## 9. Diagnóstico y solución de errores comunes

### 9.1 El error del video: "El model provider failed after retries"

Este error suele aparecer cuando Hermes intenta usar un provider incompatible con el modelo configurado.

- Si `provider=gemini`, el modelo debe ser `gemini-...`
- Si usas `google/gemini-3.5-flash`, el provider correcto es `openrouter`

### 9.2 Verificar la configuración actual

```bash
hermes config show
hermes doctor
```

### 9.3 Verificar logs del gateway

```bash
tail -60 ~/.hermes/logs/gateway.log
grep -nEi 'error|fail|provider|openai|gemini|auth' ~/.hermes/logs/gateway.log
```

### 9.4 Migrar o actualizar la config

Si Hermes muestra advertencias de versión de config, ejecuta:

```bash
hermes doctor --fix
hermes setup
```

---

## 10. Escalabilidad y replicabilidad

### 10.1 Uso de scripts de instalación reproducibles

Crea un script `hermes-install.sh` que incluya:

- instalación de dependencias
- descarga de Hermes
- creación de `~/.hermes/.env`
- configuración de `model.provider`, `model.default`, `model.base_url`
- arranque del gateway

### 10.2 Uso de Docker y `.env` para múltiples entornos

Mantén una plantilla de `.env` borrada en el repositorio y un `Dockerfile` que sólo copie el `.env` del entorno en tiempo de despliegue.

### 10.3 Extender funcionalidades

Una vez Hermes y Telegram funcionan, puedes añadir:

- `TELEGRAM_ALLOWED_USERS` para control de acceso
- `hermes config set telegram.commands` para comandos personalizados
- `pm2` o `systemd` para que el bot se reinicie automáticamente
- un contenedor Docker que reproduzca la misma configuración en AWS, GCP, DigitalOcean o un runner local

---

## 11. Checklist final

- [ ] Hermes instalado correctamente
- [ ] `~/.hermes/.env` contiene `TELEGRAM_BOT_TOKEN` y `GEMINI_API_KEY`
- [ ] `hermes config show` indica `provider: gemini` y `default: gemini-3.5-flash`
- [ ] `hermes gateway status` muestra gateway en ejecución
- [ ] `hermes doctor` no reporta errores de provider
- [ ] Telegram responde a comandos `/new` y mensajes básicos
- [ ] El proceso se ejecuta en background con PM2, systemd o Docker

---

## 12. Nota de seguridad

Mantén siempre las claves de proveedor fuera del chat.
Usa archivos locales `.env` y permisos restringidos (`chmod 600 ~/.hermes/.env`).

---

## 13. Cómo usar este plan con un agente IA

Pide al agente IA que:

1. Ejecute todos los comandos del plan en la terminal del Codespace
2. No muestre claves sensibles en la salida
3. Verifique con `hermes doctor` y `hermes gateway status`
4. Reporte cualquier problema de provider o clave ausente

> Este plan está escrito para ser completo y minimizar la necesidad de interpretación. Cualquier modelo IA que siga los comandos debe poder implementar Hermes + Telegram en Ubuntu y dejarlo listo para escalar.

---

## 14. Estado actual y validación

El entorno actual ya incluye:

- `Dockerfile` configurado para instalar Hermes Agent en Ubuntu 24.04
- `docker-entrypoint.sh` que inyecta credenciales y arranca Hermes
- `docker-compose.yml` para ejecutar el servicio de forma reproducible
- `hermes.env.example` como plantilla segura de variables de entorno
- `.dockerignore` para excluir archivos de entorno y evitar filtrar secretos

Validación realizada:

- La imagen Docker se construyó con éxito usando `docker compose build`.
- El contenedor puede ejecutar Hermes y el binario se comprueba con `hermes --version`.
- La configuración de proveedor Gemini se aplica al arrancar el contenedor.

Notas finales de despliegue:

- Para que Telegram se conecte correctamente, `TELEGRAM_BOT_TOKEN` debe ser un token válido de BotFather.
- El uso de `GATEWAY_ALLOW_ALL_USERS=true` es útil en pruebas, pero en producción conviene definir `TELEGRAM_ALLOWED_USERS`.
- El proyecto es replicable en otros entornos siempre que se llene `hermes.env` con credenciales reales y se construya el contenedor.
