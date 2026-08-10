# BotcchiV2

Bot de musica para Discord escrito en Python. Usa `discord.py` para comandos y voz,
`yt-dlp` como implementacion mantenida de youtube-dl, FFmpeg para transmitir audio y
Spotify Web API para convertir canciones o playlists de Spotify en busquedas de YouTube.

## Arquitectura

```text
.
|-- main.py                    # Unico punto de entrada y carga del bot
|-- botcchi/
|   |-- bot.py                 # Cliente Discord, intents y errores globales
|   |-- config.py              # Variables de entorno tipadas
|   |-- cogs/                  # Controladores de comandos
|   |-- models/                # Modelos inmutables de pistas y usuarios
|   |-- services/              # YouTube, Spotify, resolucion, colas y FFmpeg
|   |-- ui/                    # Fabrica central de embeds
|   `-- utils/                 # Formato de duraciones y textos
|-- tests/
|-- run.sh / run.bat
|-- Dockerfile
`-- .github/workflows/ci.yml
```

Cada servidor tiene su propia cola y reproductor. Las operaciones bloqueantes de yt-dlp y
Spotipy se ejecutan fuera del event loop. La URL de audio se obtiene cuando la pista va a
comenzar, para que no expire mientras espera en la cola. Cuando la cola termina, el bot se
desconecta automáticamente del canal de voz después de un minuto de inactividad.

## Configuracion de Discord

1. Crea una aplicacion y un bot en el [Developer Portal](https://discord.com/developers/applications).
2. En **Bot > Privileged Gateway Intents**, activa **Message Content Intent**.
3. Invita el bot con los permisos `View Channels`, `Send Messages`, `Embed Links`,
   `Connect` y `Speak`.
4. Copia `.env.example` como `.env` y completa al menos `BOT_TOKEN` y `BOT_PREFIX`.

```dotenv
BOT_TOKEN=
BOT_PREFIX=--
APP_ID=
PUBLIC_KEY=
BOT_URL_INVITACION=
BOT_SERVIDORES_PERMITIDOS=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
COOKIES_BROWSER=
COOKIES_FILE=
```

`BOT_SERVIDORES_PERMITIDOS` acepta IDs separados por comas o punto y coma. Si queda vacio,
el bot responde en todos los servidores donde este instalado. Las credenciales de Spotify
son opcionales, pero ambas son necesarias para aceptar URLs de Spotify.

Para videos que exijan sesion, usa `COOKIES_FILE=./cookies.txt` o un navegador local como
`COOKIES_BROWSER=firefox`. En Docker se recomienda exclusivamente un archivo de cookies y
el volumen definido en `docker-compose.yml`.

## Ejecucion

Requisitos locales: Python 3.10 o superior y FFmpeg disponible en `PATH`.

Linux/macOS:

```bash
chmod +x run.sh
./run.sh
```

Windows:

```bat
run.bat
```

Docker:

```bash
docker compose up --build -d
docker compose logs -f botcchi
```

## Comandos

Con un prefijo `--`: `--comandos`, `--ping`, `--play <busqueda o URL>`,
`--playlist <URL>`, `--skip`, `--stop`, `--clear`, `--queue`, `--np` y
`--lyrics` (WIP). Todas las respuestas visibles se envian como embeds.

## CI/CD

El workflow de GitHub Actions ejecuta Ruff, pytest y compilacion de bytecode en cada pull
request y push a `main`. Tras pasar las pruebas, construye Docker; los pushes a `main`
publican `latest` y una etiqueta por SHA en GitHub Container Registry (`ghcr.io`).
