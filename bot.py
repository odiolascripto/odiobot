import os
import requests
import telebot
from flask import Flask, request
from dotenv import load_dotenv
from datetime import datetime
import threading
import schedule
import time

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 🧭 /start
@bot.message_handler(commands=["start"])
def enviar_start(message):
    bot.send_message(message.chat.id, "✅ Bot está operativo y escuchando comandos.")

# 📈 /dominancia
@bot.message_handler(commands=["dominancia"])
def enviar_dominancia(message):
    url = "https://api.coinlore.net/api/global/"
    data = requests.get(url).json()
    btc_dominance = data[0]["btc_d"]
    bot.send_message(message.chat.id, f"💪 Dominancia BTC: {btc_dominance}%")

# 😱 /codicia
@bot.message_handler(commands=["codicia"])
def enviar_codicia(message):
    url = "https://api.alternative.me/fng/"
    data = requests.get(url).json()
    valor = data["data"][0]["value"]
    tipo = data["data"][0]["value_classification"]
    bot.send_message(message.chat.id, f"📊 Miedo/Codicia: {valor} ({tipo})")

# 🌈 /allseason
@bot.message_handler(commands=["allseason"])
def enviar_allseason(message):
    url = "https://www.blockchaincenter.net/api/altcoin-season-index/"
    data = requests.get(url).json()
    valor = data["altcoinSeasonIndex"]
    bot.send_message(message.chat.id, f"🌈 Altseason Index: {valor}")

# 🚨 /corrupcion
@bot.message_handler(commands=["corrupcion"])
def enviar_corrupcion(message):
    url = "https://raw.githubusercontent.com/datasets/corruption-index/master/data/corruption-index.csv"
    respuesta = requests.get(url).text
    for fila in respuesta.splitlines():
        if "Spain" in fila or "España" in fila:
            bot.send_message(message.chat.id, f"🚨 Corrupción en España:\n{fila}")
            break

# 🧾 /ayuda
@bot.message_handler(commands=["ayuda"])
def enviar_ayuda(message):
    texto = """📘 *Comandos disponibles:*

/start → Estado del bot
/dominancia → Dominancia BTC
/codicia → Índice de Miedo/Codicia
/allseason → Altcoin Season Index
/corrupcion → Corrupción en España
/ayuda → Este menú

📡 Envíos automáticos a las 09:00 y 16:00h
"""
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

# 🕒 Tareas automáticas
def enviar_indicadores():
    ahora = datetime.now().strftime("%H:%M")
    mensaje = f"⏰ Indicadores automáticos ({ahora})\n"
    
    # BTC Dominancia
    dom_url = "https://api.coinlore.net/api/global/"
    dom_data = requests.get(dom_url).json()
    btc_dominance = dom_data[0]["btc_d"]
    mensaje += f"💪 Dominancia BTC: {btc_dominance}%\n"
    
    # Fear & Greed
    fng_url = "https://api.alternative.me/fng/"
    fng_data = requests.get(fng_url).json()
    valor = fng_data["data"][0]["value"]
    tipo = fng_data["data"][0]["value_classification"]
    mensaje += f"📊 Miedo/Codicia: {valor} ({tipo})"

    bot.send_message(CHAT_ID, mensaje)

# ⏲️ Programación horaria
schedule.every().day.at("09:00").do(enviar_indicadores)
schedule.every().day.at("16:00").do(enviar_indicadores)

def ciclo_schedule():
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=ciclo_schedule).start()

# 🔁 Webhook Telegram
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def recibir_actualizacion():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

# 🧭 Ping anti-sueño
@app.route("/", methods=["GET", "HEAD"])
def ping():
    return "✅ Bot operativo"

# 🟢 Arranque
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://odiobot.onrender.com/{BOT_TOKEN}")
    print("🔧 Webhook registrado correctamente")
    app.run(host="0.0.0.0", port=10000)

