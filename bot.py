import os
import requests
import pytz
from datetime import datetime, timezone
from flask import Flask, request
import telebot

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = -1002641253969
THREAD_ID = 31

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

CACHE_EXPIRATION = 600  # en segundos
cache = {}

def fetch_with_cache(key, fetch_func):
    now = datetime.now(timezone.utc).timestamp()
    cached = cache.get(key, {})
    if cached.get("data") and (now - cached.get("last_fetch", 0)) < CACHE_EXPIRATION:
        return cached["data"]
    try:
        data = fetch_func()
        cache[key] = {"data": data, "last_fetch": now}
        return data
    except Exception as e:
        print(f"Error fetching {key}: {e}")
        return cached.get("data", f"⚠️ No se pudo obtener datos de {key}")

# Indicadores

def obtener_dominancia_btc():
    def fetch():
        url = "https://api.coingecko.com/api/v3/global"
        data = requests.get(url, timeout=10).json()
        btc = data["data"]["market_cap_percentage"]["btc"]
        return f"📊 *Dominancia BTC*: {btc:.2f}%"
    return fetch_with_cache("dominancia", fetch)

def obtener_codicia():
    def fetch():
        url = "https://api.alternative.me/fng/"
        data = requests.get(url, timeout=10).json()["data"][0]
        return f"😱 *Índice Miedo/Codicia*: {data['value']} ({data['value_classification']})\n📅 Fecha: {datetime.utcfromtimestamp(int(data['timestamp'])).strftime('%Y-%m-%d')}"
    return fetch_with_cache("codicia", fetch)

def obtener_allseason():
    def fetch():
        url = "https://api.allcoinseason.com/v1/allcoinseason"
        data = requests.get(url, timeout=10).json()
        return f"🌕 *Altseason Index*: {data.get('index', 'N/D')}\n{data.get('description', '')}"
    return fetch_with_cache("allseason", fetch)

# Comandos

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    bot.reply_to(msg, "🤖 Bot operativo vía Webhook")

@bot.message_handler(commands=['dominancia'])
def cmd_dominancia(msg):
    bot.reply_to(msg, obtener_dominancia_btc(), parse_mode="Markdown")

@bot.message_handler(commands=['codicia'])
def cmd_codicia(msg):
    bot.reply_to(msg, obtener_codicia(), parse_mode="Markdown")

@bot.message_handler(commands=['allseason'])
def cmd_allseason(msg):
    bot.reply_to(msg, obtener_allseason(), parse_mode="Markdown")

@bot.message_handler(commands=['corrupcion'])
def cmd_corrupcion(msg):
    bot.reply_to(msg, "⚠️ Comando /corrupcion aún no configurado")

# Webhook – Telegram enviará los mensajes aquí

@app.route(f"/{TOKEN}", methods=["POST"])
def recibir_update():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/")
def home():
    return "Bot activo vía Webhook", 200

# Enviar indicadores automáticos a las 9:00h

from threading import Thread
import time

def enviar_diario():
    tz = pytz.timezone("Europe/Madrid")
    while True:
        ahora = datetime.now(tz)
        if ahora.hour == 9 and ahora.minute == 0:
            print("🕘 Enviando pulso diario...")
            try:
                bot.send_message(CHAT_ID, obtener_dominancia_btc(), thread_id=THREAD_ID, parse_mode="Markdown")
                bot.send_message(CHAT_ID, obtener_codicia(), thread_id=THREAD_ID, parse_mode="Markdown")
            except Exception as e:
                print(f"Error al enviar: {e}")
            time.sleep(60)
        time.sleep(30)

Thread(target=enviar_diario, daemon=True).start()

# Registrar el Webhook

WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"

bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# Lanzar Flask app

if __name__ == "__main__":
    print("🔥 Webhook activo. Escuchando Telegram...")
    app.run(host="0.0.0.0", port=10000)

