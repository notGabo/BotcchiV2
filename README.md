# 🎵 Botcchi (Python + FFmpeg + yt-dlp + DAVE)

Repositorio re escritura de codigo para el bot Botcchi escrito en python. Sin depender del proyecto Vulkan.

--

Un bot de música modular, robusto y estéticamente pulido para Discord, desarrollado en Python (`discord.py`), con soporte para YouTube, listas de reproducción de Spotify, encriptación DAVE (End-to-End Voice Protocol) y despliegue automatizado con Docker y CI/CD.

---

## 🚀 Características Principales

- **Respuestas 100% en Embeds**: Todos los comandos responden con tarjetas estéticas de Discord.
- **Soporte DAVE Protocol**: Incluye la librería `davey` para compatibilidad completa con el protocolo de voz cifrado punto a punto de Discord.
- **Soporte YouTube & Spotify**: Reproduce canciones individuales o playlists completas.
- **Arquitectura Modular (Cog-Service-Handler)**: Código limpio y mantenible separado en servicios, cogs de comandos y builders de embeds.
- **Dockerizado & Multiplataforma**: Incluye `Dockerfile`, `docker-compose.yml`, además de scripts `.run` para Windows (`run.bat`) y Linux (`run.sh`).
- **Pipeline de CI/CD**: Workflow de GitHub Actions preconfigurado para testing, compilación e integración continua en VPS.

---

## 🛠️ Requisitos Previos

1. **Python 3.11+**
2. **FFmpeg** instalado y agregado al PATH del sistema.
3. **Token de Bot de Discord** con los siguientes Intents activados en el Discord Developer Portal:
   - `MESSAGE CONTENT INTENT`
   - `SERVER MEMBERS INTENT`

---

## 📋 Configuración del Archivo `.env`

Crea un archivo llamado `.env` en la raíz del proyecto (basado en el template entregado):

```env
BOT_TOKEN=tu_token_de_discord_aqui
BOT_PREFIX=--
APP_ID=tu_app_id
PUBLIC_KEY=tu_public_key
BOT_URL_INVITACION=https://discord.com/api/oauth2/authorize?...
BOT_SERVIDORES_PERMITIDOS=123456789012345678,987654321098765432
SPOTIFY_CLIENT_ID=tu_spotify_client_id
SPOTIFY_CLIENT_SECRET=tu_spotify_client_secret
COOKIES_BROWSER=
COOKIES_FILE=data/cookies.txt
```

---

## 💻 Comandos Disponibles

| Comando | Descripción |
| :--- | :--- |
| `🔹comandos` | Muestra la lista de comandos disponibles. |
| `🔹ping` | Responde con 'Pong!' y la latencia actual del bot. |
| `🔹play [canción o url]` | Reproduce una canción de YouTube o busca por palabras clave. |
| `🔹playlist [url]` | Carga y añade a la cola una lista de reproducción de YouTube o Spotify. |
| `🔹skip` | Salta a la siguiente canción en la cola. |
| `🔹stop` | Detiene la música, limpia la cola y desconecta al bot del canal de voz. |
| `🔹clear` | Limpia la cola de reproducción en caso de problemas. |
| `🔹queue` | Muestra las canciones en la cola de reproducción. |
| `🔹np` | Muestra la canción que se está reproduciendo actualmente. |
| `🔹lyrics` | [WIP] Muestra la letra de la canción en reproducción. |

---

## ⚙️ Instrucciones de Instalación y Ejecución

### Opción A: Localmente (Linux / macOS)
```bash
chmod +x run.sh
./run.sh
```

### Opción B: Localmente (Windows)
Ejecuta con doble clic el archivo `run.bat` o desde CMD:
```cmd
run.bat
```

### Opción C: Con Docker y Docker Compose
```bash
docker compose up -d --build
```

---

## 🏗️ Arquitectura del Proyecto

```text
bot-musica/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── .env
├── .gitignore
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.sh
├── run.bat
├── main.py
├── data/
│   └── .gitkeep
└── src/
    ├── config.py
    ├── cogs/
    │   ├── general.py
    │   └── music.py
    ├── services/
    │   ├── yt_handler.py
    │   ├── spotify_handler.py
    │   └── lyrics_handler.py
    └── utils/
        └── embed_builder.py
```
