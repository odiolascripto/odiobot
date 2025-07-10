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
CHAT_ID    = -1002641253969   # Grupo "Odio las Cripto"
THREAD_ID  = 31               # Subgrupo "Pulso Diario"

bot = telebot.TeleBot(TOKEN)

# --- Funciones de utilidad ----------------------------------------------------
def obtener_dominancia_btc() -> str:
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        btc_dom = data["data"]["market_cap_percentage"]["btc"]
        return f"📊 *Dominancia BTC*: {btc_dom:.2f}%"
    except Exception as e:
        print("Error al obtener dominancia BTC:", e)
        return "⚠️ No se pudo obtener la dominancia BTC."

def obtener_indice_codicia() -> str:
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        d = resp.json()["data"][0]
        return (f"📈 *Índice Codicia & Miedo*: {d['value']} ({d['value_classification']})")
    except Exception as e:
        print("Error al obtener índice codicia:", e)
        return "⚠️ No se pudo obtener el índice Codicia & Miedo."

# --- Handlers de comandos manuales -------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(msg):
    bot.reply_to(msg, "Bot activo 🚀")

@bot.message_handler(commands=['id'])
def send_chat_id(msg):
    bot.reply_to(msg, f"Chat ID: {msg.chat.id}")

@bot.message_handler(commands=['dominancia'])
def enviar_dominancia_manual(msg):
    bot.reply_to(msg, obtener_dominancia_btc(), parse_mode="Markdown")

@bot.message_handler(commands=['codicia'])
def enviar_codicia_manual(msg):
    bot.reply_to(msg, obtener_indice_codicia(), parse_mode="Markdown")

# --- Envío automático diario --------------------------------------------------
def tarea_alerta_diaria():
    tz_madrid = pytz.timezone("Europe/Madrid")
    while True:
        ahora = datetime.now(tz_madrid)
        if ahora.hour == 9 and ahora.minute == 0:
            try:
                mensaje = f"{obtener_dominancia_btc()}\n\n{obtener_indice_codicia()}"
                bot.send_message(
                    chat_id=CHAT_ID,
                    message_thread_id=THREAD_ID,
                    text=mensaje,
                    parse_mode="Markdown"
                )
                time.sleep(60)  # Evita reenvío en el mismo minuto
            except Exception as e:
                print("Error enviando alerta diaria:", e)
        time.sleep(30)

def iniciar_hilo_programado():
    hilo = threading.Thread(target=tarea_alerta_diaria, daemon=True)
    hilo.start()

# --- Arranque ----------------------------------------------------------------
keep_alive()
iniciar_hilo_programado()
bot.polling(none_stop=True, interval=0, timeout=20)

