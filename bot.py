import os
import telebot
import requests
import schedule
import time
from flask import Flask, request
import pytz
from datetime import datetime

# 🔐 Token y configuración
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = -1002641253969
THREAD_ID = 31
WEBHOOK_URL = f"https://odiobot.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
tz_madrid = pytz.timezone("Europe/Madrid")

# 🔌 Webhook
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# ✅ Comando /start
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.reply_to(msg, "✅ Bot activo y operativo. ¡Hola, Angel!")

# 📊 Comando /dominancia — con emojis dinámicos 🎭
@bot.message_handler(commands=["dominancia"])
def cmd_dominancia(msg=None):
    r = requests.get("https://api.coinlore.net/api/global/")
    if r.status_code == 200:
        dominancia = float(r.json()[0]["btc_d"])
        if dominancia >= 55:
            emoji = "🧱"
        elif dominancia >= 45:
            emoji = "📊"
        else:
            emoji = "🌪️"
        texto = f"{emoji} Dominancia actual de Bitcoin: {dominancia}%"
        if msg: bot.reply_to(msg, texto)
        else: return texto, dominancia

# 😱 Comando /codicia — con emojis
@bot.message_handler(commands=["codicia"])
def cmd_codicia(msg=None):
    r = requests.get("https://api.alternative.me/fng/")
    if r.status_code == 200:
        valor = int(r.json()["data"][0]["value"])
        emoji = "🤑" if valor >= 80 else "😐" if valor >= 50 else "😱"
        texto = f"{emoji} Índice de Miedo/Codicia: {valor}"
        if msg: bot.reply_to(msg, texto)
        else: return texto, valor

# 📈 Comando /allseason — traducción agregada ✅
@bot.message_handler(commands=["allseason"])
def cmd_allseason(msg=None):
    r = requests.get("https://api.bitformance.io/v1/data/altseason/index")
    if r.status_code == 200:
        estado = r.json()["data"]["state"]
        traduccion = {
            "Altcoin Season": "🚀 Temporada de altcoins",
            "Not Altcoin Season": "🌒 No es temporada de altcoins",
            "Halfway": "⚖️ Estamos a medio camino"
        }
        texto = traduccion.get(estado, estado)
        if msg: bot.reply_to(msg, texto)
        else: return texto

# 🏦 Comando /corrupcion
@bot.message_handler(commands=["corrupcion"])
def cmd_corrupcion(msg=None):
    r = requests.get("https://raw.githubusercontent.com/datasets/corruption-index/master/data/corruption-index.csv")
    if r.status_code == 200:
        lineas = r.text.splitlines()
        for fila in lineas:
            if "Spain" in fila:
                año, pais, indice = fila.split(",")
                texto = f"🇪🇸 Índice de corrupción en España ({año}): {indice}"
                if msg: bot.reply_to(msg, texto)
                else: return texto
                break

# 📌 Comando /ayuda
@bot.message_handler(commands=["ayuda"])
def cmd_ayuda(msg):
    ayuda = (
        "📌 *Lista de comandos disponibles:*\n\n"
        "👉 `/start` — Verifica si el bot está operativo\n"
        "👉 `/dominancia` — Dominancia actual de BTC con emoji\n"
        "👉 `/codicia` — Índice de Miedo/Codicia\n"
        "👉 `/allseason` — Estado altcoins traducido\n"
        "👉 `/corrupcion` — Índice España\n"
        "👉 `/ayuda` — Este menú\n"
        "👉 `/precio` — Precio BTC\n"
        "👉 `/precio eth`, `/precio sol`, etc — Más criptos\n\n"
        "📡 *Auto-envíos:* 09:00h y 16:00h\n"
        "📆 *Resumen semanal:* lunes a las 09:30h\n"
        "🔍 *Subgrupos:* Noticias, OnChain, Eventos"
    )
    bot.reply_to(msg, ayuda, parse_mode="Markdown")

# ⏰ Envío automático con alertas — PASO 15 integrado 💥
def enviar_indicadores_programados():
    hora = datetime.now(tz_madrid).strftime("%H:%M")
    print(f"🕘 Enviando indicadores programados ({hora})")
    
    texto_dominancia, valor_dominancia = cmd_dominancia()
    texto_codicia, valor_codicia = cmd_codicia()
    texto_allseason = cmd_allseason()
    texto_corrupcion = cmd_corrupcion()
    
    mensaje = f"{texto_dominancia}\n{texto_codicia}\n{texto_allseason}\n{texto_corrupcion}"

    # 🚨 Revisar alertas por umbral
    alertas = []
    if valor_codicia >= 80:
        alertas.append("⚠️ Codicia extrema — posible sobrecompra del mercado")
    if valor_dominancia <= 40:
        alertas.append("⚠️ Dominancia baja — altcoins podrían estar tomando el control")
    
    if alertas:
        mensaje += "\n\n" + "\n".join(alertas)

    bot.send_message(CHAT_ID, mensaje, message_thread_id=THREAD_ID)

# 📅 Programación diaria
schedule.every().day.at("09:00").do(enviar_indicadores_programados)
schedule.every().day.at("16:00").do(enviar_indicadores_programados)

# 🌐 Flask Webhook
@app.route("/" + TOKEN, methods=["POST"])
def recibir_webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def ping():
    return "✅ Bot activo vía Webhook"

# 🧃 Ciclo continuo
def ciclo_bot():
    while True:
        schedule.run_pending()
        time.sleep(10)

import threading
threading.Thread(target=ciclo_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

