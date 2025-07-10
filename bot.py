import telebot
import requests
import pytz
from flask import Flask, request
from datetime import datetime
from threading import Thread
import os
import time

# Lee el token desde las variables de entorno (Render.com → Environment)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Configuración de Flask
app = Flask(__name__)

# Zona horaria correcta para España
tz = pytz.timezone("Europe/Madrid")

# IDs de envío automático
CHAT_ID = "-1002641253969"
THREAD_ID = "31"

# === Funciones de obtención de datos ===

def obtener_dominancia_btc():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/global")
        data = response.json()
        dominancia = data["data"]["market_cap_percentage"]["btc"]
        return f"🧠 *Dominancia BTC*: {dominancia:.2f}%"
    except Exception as e:
        return f"Error al obtener dominancia BTC: {e}"

def obtener_indice_codicia():
    try:
        response = requests.get("https://api.alternative.me/fng/")
        data = response.json()
        valor = data["data"][0]["value"]
        clasificacion = data["data"][0]["value_classification"]
        return f"🧠 *Índice Miedo/Codicia*: {valor} - {clasificacion}"
    except Exception as e:
        return f"Error al obtener índice de codicia: {e}"

def obtener_indice_corrupcion():
    # Puedes sustituir por una API real si existe más adelante
    return "🚨 *Índice de Corrupción Cripto*: sin fuente oficial aún."

def obtener_allseason():
    try:
        response = requests.get("https://www.blockchaincenter.net/api/altcoin-season-index/")
        data = response.json()
        valor = data["values"][-1]["value"]
        return f"📊 *Altcoin Season Index*: {valor:.0f}"
    except Exception as e:
        return f"Error al obtener Altcoin Season Index: {e}"

# === Comandos manuales ===

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message, "Hola, soy tu bot cripto. Comandos disponibles:\n"
                          "/dominancia\n"
                          "/codicia\n"
                          "/corrupcion\n"
                          "/allseason")

@bot.message_handler(commands=["dominancia"])
def enviar_dominancia_manual(msg):
    bot.reply_to(msg, obtener_dominancia_btc(), parse_mode="Markdown")

@bot.message_handler(commands=["codicia"])
def enviar_codicia_manual(msg):
    bot.reply_to(msg, obtener_indice_codicia(), parse_mode="Markdown")

@bot.message_handler(commands=["corrupcion"])
def enviar_corrupcion_manual(msg):
    bot.reply_to(msg, obtener_indice_corrupcion(), parse_mode="Markdown")

@bot.message_handler(commands=["allseason"])
def enviar_allseason_manual(msg):
    bot.reply_to(msg, obtener_allseason(), parse_mode="Markdown")

# === Envío automático programado ===

def enviar_datos_programados():
    while True:
        ahora = datetime.now(tz)
        if ahora.hour == 9 and ahora.minute == 0:
            try:
                texto = f"{obtener_dominancia_btc()}\n{obtener_indice_codicia()}"
                bot.send_message(chat_id=CHAT_ID, message_thread_id=int(THREAD_ID), text=texto, parse_mode="Markdown")
            except Exception as e:
                print(f"Error en envío automático: {e}")
            time.sleep(60)  # Evita duplicar envío
        time.sleep(20)

# === Flask para mantener vivo ===

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "Bot activo"

def keep_alive():
    app.run(host="0.0.0.0", port=8080)

# === Lanzamiento del bot ===

if __name__ == "__main__":
    Thread(target=keep_alive).start()
    Thread(target=enviar_datos_programados).start()
    bot.polling(none_stop=True, interval=0, timeout=20)
