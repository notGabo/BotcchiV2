from os import getenv
from dotenv import load_dotenv

# Variables de entorno
load_dotenv()
BOT_TOKEN = getenv('BOT_TOKEN')
BOT_URL = getenv('BOT_URL')
BOT_URL_INVITACION = getenv('BOT_URL_INVITACION')
BOT_SERVIDORES_PERMITIDOS = getenv('BOT_SERVIDORES_PERMITIDOS').split(',')
BOT_APP_ID = getenv("APP_ID")

#Configuraciones bot
BOT_PREFIX = '--'
BOT_NAME= 'BotcchiV2'
BOT_DESCRIPTION = 'Nuevo bot de musica escrito desde 0 con un engine propio'

# Misc
SPOTIFY_REGEX = r"^(https?://)?(www\.)?(spotify\.com|open\.spotify\.com)/.+$"


