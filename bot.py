import os
import requests
import pytz
import time
from datetime import datetime, timezone
from flask import Flask, request
import telebot
from threading import Thread

# 🔐 Token y configuración
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = -1002641253969  # Reemplaza con tu ID de grupo
THREAD_ID = 31            # Reemplaza con el ID del hilo si lo usas

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 🧠 Caché simple para eficiencia
CACHE_EXPIRATION = 600  # segundos
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
        print(f"[{key}] Error: {e}")
        return f"⚠️ No se pudo obtener datos de {key}"

# 📊 Indicadores

def obtener_dominancia_btc():
    def fetch():
        url = "https://api.coingecko.com/api/v3/global"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        btc = data["data"]["market_cap_percentage"]["btc"]
        return f"📊 *Dominancia BTC*: {btc:.2f}%"
    return fetch_with_cache("dominancia", fetch)

def obtener_codicia():
    def fetch():
        url = "https://api.alternative.me/fng/"
        data = requests.get(url, timeout=10).json()["data"][0]
        fecha = datetime.utcfromtimestamp(int(data["timestamp"])).strftime('%Y-%m-%d')
        return f"😱 *Índice Miedo/Codicia*: {data['value']} ({data['value_classification']})\n📅 Fecha: {fecha}"
    return fetch_with_cache("codicia", fetch)

def obtener_allseason():
    def fetch():
        url = "https://www.bitformance.com/api/altcoin-season-index"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        index = data.get("current_value")
        if index is None:
            raise ValueError("Índice no disponible")
        return f"🌕 *Altseason Index*: {index}\nEvaluación basada en los últimos 90 días comparando altcoins con BTC."
    return fetch_with_cache("allseason", fetch)

def obtener_corrupcion():
    def fetch():
        url = "https://api.worldbank.org/v2/country/ES/indicator/CC.EST?format=json"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        valor = data[1][0]["value"]
        fecha = data[1][0]["date"]
        return f"🕵️ *Control de Corrupción (España)*: {valor:.2f}\n📅 Año: {fecha}\nFuente: Banco Mundial"
    return fetch_with_cache("corrupcion", fetch)

# 💬 Comandos

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.reply_to(msg, "🤖 Bot operativo vía Webhook")

@bot.message_handler(commands=["dominancia"])
def cmd_dominancia(msg):
    bot.reply_to(msg, obtener_dominancia_btc(), parse_mode="Markdown")

@bot.message_handler(commands=["codicia"])
def cmd_codicia(msg):
    bot.reply_to(msg, obtener_codicia(), parse_mode="Markdown")

@bot.message_handler(commands=["allseason"])
def cmd_allseason(msg):
    bot.reply_to(msg, obtener_allseason(), parse_mode="Markdown")

@bot.message_handler(commands=["corrupcion"])
def cmd_corrupcion(msg):
    bot.reply_to(msg, obtener_corrupcion(), parse_mode="Markdown")

# ⏰ Envío automático

def envio_programado():
    tz = pytz.timezone("Europe/Madrid")
    ya_enviado = set()

    while True:
        ahora = datetime.now(tz)
        hora_actual = ahora.strftime("%H:%M")

        if hora_actual in {"09:00", "16:00"} and hora_actual not in ya_enviado:
            print(f"🕘 Enviando indicadores programados ({hora_actual})...")
            try:
                bot.send_message(CHAT_ID, obtener_dominancia_btc(), thread_id=THREAD_ID, parse_mode="Markdown")
                bot.send_message(CHAT_ID, obtener_codicia(), thread_id=THREAD_ID, parse_mode="Markdown")
                bot.send_message(CHAT_ID, obtener_allseason(), thread_id=THREAD_ID, parse_mode="Markdown")
                bot.send_message(CHAT_ID, obtener_corrupcion(), thread_id=THREAD_ID, parse_mode="Markdown")
                ya_enviado.add(hora_actual)
            except Exception as e:
                print(f"Error al enviar indicadores: {e}")
            time.sleep(60)

        if hora_actual not in {"09:00", "16:00"}:
            ya_enviado.clear()

        time.sleep(30)

Thread(target=envio_programado, daemon=True).start()

# 🌐 Webhook

@app.route(f"/{TOKEN}", methods=["POST"])
def recibir_update():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/")
def home():
    return "Bot activo vía Webhook", 200

WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# 🏁 Lanzar Flask
if __name__ == "__main__":
    print("🔥 Webhook activo. Escuchando Telegram...")
    app.run(host="0.0.0.0", port=10000)

