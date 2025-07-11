import telebot
import requests
import schedule
import time
from flask import Flask, request
import pytz
from datetime import datetime

TOKEN = "TU_TOKEN_AQUÍ"
WEBHOOK_URL = "https://odiobot.onrender.com/" + TOKEN

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 🌍 Zona horaria
tz_madrid = pytz.timezone("Europe/Madrid")

# 🔥 Activar Webhook
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# 🕹️ Comando /start
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.reply_to(msg, "✅ Bot activo y operativo. ¡Hola, Angel!")

# 📊 Comando /dominancia
@bot.message_handler(commands=["dominancia"])
def cmd_dominancia(msg=None):
    r = requests.get("https://api.coinlore.net/api/global/")
    if r.status_code == 200:
        dominancia = r.json()[0]["btc_d"]
        texto = f"🔗 Dominancia actual de Bitcoin: {dominancia}%"
        if msg: bot.reply_to(msg, texto)
        else: return texto

# 😱 Comando /codicia
@bot.message_handler(commands=["codicia"])
def cmd_codicia(msg=None):
    r = requests.get("https://api.alternative.me/fng/")
    if r.status_code == 200:
        valor = int(r.json()["data"][0]["value"])
        emoji = "🤑" if valor >= 80 else "😐" if valor >= 50 else "😱"
        texto = f"{emoji} Índice de Miedo/Codicia: {valor}"
        if msg: bot.reply_to(msg, texto)
        else: return texto

# 📈 Comando /allseason
@bot.message_handler(commands=["allseason"])
def cmd_allseason(msg=None):
    r = requests.get("https://api.bitformance.io/v1/data/altseason/index")
    if r.status_code == 200:
        estado = r.json()["data"]["state"]
        traduccion = {
            "Altcoin Season": "🚀 ¡Es temporada de altcoins!",
            "Not Altcoin Season": "🌒 No es temporada de altcoins",
            "Halfway": "⚖️ Estamos a mitad de camino"
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

# 📌 Comando /ayuda — PASO 12
@bot.message_handler(commands=["ayuda"])
def cmd_ayuda(msg):
    ayuda = (
        "📌 *Lista de comandos disponibles:*\n\n"
        "👉 `/start` — Verifica si el bot está operativo\n"
        "👉 `/dominancia` — Dominancia actual de BTC\n"
        "👉 `/codicia` — Índice de Miedo/Codicia\n"
        "👉 `/allseason` — Estado del mercado altcoins\n"
        "👉 `/corrupcion` — Índice oficial de España\n"
        "👉 `/ayuda` — Este menú\n"
        "👉 `/precio` — Precio BTC\n"
        "👉 `/precio eth`, `/precio sol`, etc — Otras criptos\n\n"
        "📡 *Mensajes automáticos:* 09:00h y 16:00h (Madrid)\n"
        "📆 *Eventos semanales:* Lunes a las 09:30h\n"
        "🔍 *Subgrupos:* Noticias, Datos OnChain"
    )
    bot.reply_to(msg, ayuda, parse_mode="Markdown")

# ⏰ Mensaje automático
def enviar_indicadores_programados():
    hora = datetime.now(tz_madrid).strftime("%H:%M")
    chat_id = "TU_CHAT_ID_AQUÍ"  # Reemplaza con tu ID de grupo
    print(f"🕘 Enviando indicadores programados ({hora})")
    texto = (
        f"{cmd_dominancia()}\n"
        f"{cmd_codicia()}\n"
        f"{cmd_allseason()}\n"
        f"{cmd_corrupcion()}"
    )
    bot.send_message(chat_id, texto)

# 🗓️ Programar tareas
schedule.every().day.at("09:00").do(enviar_indicadores_programados)
schedule.every().day.at("16:00").do(enviar_indicadores_programados)

# 🌐 Flask para Webhook
@app.route("/" + TOKEN, methods=["POST"])
def recibir_webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def estado():
    return "✅ Bot activo vía Webhook"

# 🧃 Bucle continuo
def ciclo_bot():
    while True:
        schedule.run_pending()
        time.sleep(10)

import threading
threading.Thread(target=ciclo_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
