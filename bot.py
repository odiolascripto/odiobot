import os
import requests
import telebot
from flask import Flask, request
from datetime import datetime
import threading
import schedule
import time
from pytz import timezone  # 🕒 Ajuste de zona horaria

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

def responder(mensaje, texto, parse_mode=None):
    bot.send_message(
        chat_id=mensaje.chat.id,
        text=texto,
        message_thread_id=getattr(mensaje, "message_thread_id", None),
        parse_mode=parse_mode
    )

# ✅ /start
@bot.message_handler(commands=["start"])
def handle_start(message):
    responder(message, "✅ Bot Cripto Inteligente activo y operativo.")

# 📊 /dominancia
@bot.message_handler(commands=["dominancia"])
def handle_dominancia(message):
    r = requests.get("https://api.coinlore.net/api/global/").json()
    dom = r[0]["btc_d"]
    responder(message, f"📊 Dominancia BTC: {dom}%")

# 😱 /codicia
@bot.message_handler(commands=["codicia"])
def handle_codicia(message):
    r = requests.get("https://api.alternative.me/fng/").json()
    val = r["data"][0]["value"]
    tipo = r["data"][0]["value_classification"]
    responder(message, f"😱 Miedo/Codicia: {val} ({tipo})")

# 🌈 /allseason
@bot.message_handler(commands=["allseason"])
def handle_allseason(message):
    r = requests.get("https://www.blockchaincenter.net/api/altcoin-season-index/").json()
    idx = r["altcoinSeasonIndex"]
    responder(message, f"🌈 Altseason Index: {idx}")

# 🚨 /corrupcion
@bot.message_handler(commands=["corrupcion"])
def handle_corrupcion(message):
    r = requests.get("https://raw.githubusercontent.com/datasets/corruption-index/master/data/corruption-index.csv").text
    for fila in r.splitlines():
        if "Spain" in fila:
            responder(message, f"🚨 Corrupción en España:\n{fila}")
            break

# 🧾 /ayuda
@bot.message_handler(commands=["ayuda"])
def handle_ayuda(message):
    texto = """🧾 *Comandos disponibles:*

/start → Verifica estado del bot  
/dominancia → Dominancia actual del BTC  
/codicia → Índice Miedo/Codicia  
/allseason → Altcoin Season Index  
/corrupcion → Índice de Corrupción España  
/ayuda → Este menú

⏰ Indicadores automáticos: 09:00h y 16:00h (hora España)
"""
    responder(message, texto, parse_mode="Markdown")

# 🔁 Indicadores automáticos
def indicadores_programados():
    ahora = datetime.now(timezone("Europe/Madrid")).strftime("%H:%M")  # 🕒 Hora ajustada
    mensaje = f"⏰ Indicadores Cripto ({ahora})\n"

    r1 = requests.get("https://api.coinlore.net/api/global/").json()
    dom = r1[0]["btc_d"]
    mensaje += f"📊 Dominancia BTC: {dom}%\n"

    r2 = requests.get("https://api.alternative.me/fng/").json()
    val = r2["data"][0]["value"]
    tipo = r2["data"][0]["value_classification"]
    mensaje += f"😱 Miedo/Codicia: {val} ({tipo})"

    bot.send_message(chat_id=int(CHAT_ID), text=mensaje)

# 🕰️ Horarios fijos (UTC)
schedule.every().day.at("09:00").do(indicadores_programados)
schedule.every().day.at("16:00").do(indicadores_programados)

def ciclo_schedule():
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=ciclo_schedule).start()

# 📬 Webhook Telegram
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    bot.process_new_updates([
        telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    ])
    return "ok", 200

# 🔂 Ping anti-sueño
@app.route("/", methods=["GET", "HEAD"])
def ping():
    return "✅ Bot activo"

# 🟢 Arranque Flask
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://odiobot.onrender.com/{BOT_TOKEN}")
    print("🔧 Webhook conectado")
    app.run(host="0.0.0.0", port=10000)



