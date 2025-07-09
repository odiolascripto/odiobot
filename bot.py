import os
import time
import threading
import requests
from datetime import datetime
import pytz
import telebot
from keep_alive import keep_alive

# --- Configuración básica ----------------------------------------------------
TOKEN      = os.getenv("BOT_TOKEN")
CHAT_ID    = -1002641253969   # ID del canal tipo foro "Odio las Cripto"
THREAD_ID  = 31               # Tema "Pulso Diario"

bot = telebot.TeleBot(TOKEN)

# --- Funciones de utilidad ----------------------------------------------------
def obtener_dominancia_btc() -> str:
    """Devuelve la dominancia BTC formateada o un mensaje de error."""
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        btc_dom = data["data"]["market_cap_percentage"]["btc"]
        return f"📊 *Dominancia BTC*: {btc_dom:.2f}%"
    except Exception as e:
        print("Error al obtener dominancia BTC:", e)
        return "⚠️ No se pudo obtener la dominancia BTC."

# --- Handlers ----------------------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(msg):
    bot.reply_to(msg, "Bot activo 🚀")

@bot.message_handler(commands=['id'])
def send_chat_id(msg):
    bot.reply_to(msg, f"Chat ID: {msg.chat.id}")

@bot.message_handler(commands=['dominancia'])
def enviar_dominancia_manual(msg):
    bot.reply_to(msg, obtener_dominancia_btc(), parse_mode="Markdown")

# (Eco opcional para ver IDs en otros grupos)
@bot.message_handler(func=lambda m: True)
def echo_all(msg):
    bot.reply_to(msg, f"Chat ID de este grupo: {msg.chat.id}")

# --- Envío automático diario a las 09:00 -------------------------------------
def tarea_dominancia_diaria():
    tz_madrid = pytz.timezone("Europe/Madrid")
    while True:
        ahora = datetime.now(tz_madrid)
        if ahora.hour == 9 and ahora.minute == 0:
            try:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=obtener_dominancia_btc(),
                    message_thread_id=THREAD_ID,
                    parse_mode="Markdown",
                )
                # Evita doble envío en el mismo minuto
                time.sleep(60)
            except Exception as e:
                print("Error enviando dominancia diaria:", e)
        # Revisa cada 30 s
        time.sleep(30)

def iniciar_hilo_programado():
    hilo = threading.Thread(target=tarea_dominancia_diaria, daemon=True)
    hilo.start()

# --- Arranque ----------------------------------------------------------------
keep_alive()            # Mantiene vivo en Render
iniciar_hilo_programado()
bot.polling(none_stop=True, interval=0, timeout=20)

