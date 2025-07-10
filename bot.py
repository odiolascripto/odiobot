import time
import threading
import requests
from datetime import datetime, timedelta
import pytz
import telebot
from keep_alive import keep_alive

TOKEN = "tu_token_actual"    # Usa el token que tienes ya configurado en tu script
CHAT_ID = -1002641253969     # Igual que tienes configurado
THREAD_ID = 31               # Igual que tienes configurado

bot = telebot.TeleBot(TOKEN)

cache = {
    "dominancia": {"valor": None, "expiry": datetime.min},
    "codicia": {"valor": None, "expiry": datetime.min},
    "allseason": {"valor": None, "expiry": datetime.min},
}

CACHE_DURATION = timedelta(minutes=30)

def obtener_dominancia_btc():
    ahora = datetime.now()
    if cache["dominancia"]["valor"] and ahora < cache["dominancia"]["expiry"]:
        return cache["dominancia"]["valor"]
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        btc_dom = data["data"]["market_cap_percentage"]["btc"]
        texto = f"📊 *Dominancia BTC*: {btc_dom:.2f}%"
        cache["dominancia"] = {"valor": texto, "expiry": ahora + CACHE_DURATION}
        return texto
    except Exception as e:
        print("Error al obtener dominancia BTC:", e)
        return "⚠️ No se pudo obtener la dominancia BTC."

def obtener_indice_codicia():
    ahora = datetime.now()
    if cache["codicia"]["valor"] and ahora < cache["codicia"]["expiry"]:
        return cache["codicia"]["valor"]
    try:
        resp = requests.get("https://api.alternative.me/fng/", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        valor = data["data"][0]["value"]
        estado = data["data"][0]["value_classification"]
        texto = f"😱😎 *Índice de Miedo y Codicia*: {valor} ({estado})"
        cache["codicia"] = {"valor": texto, "expiry": ahora + CACHE_DURATION}
        return texto
    except Exception as e:
        print("Error al obtener índice de codicia:", e)
        return "⚠️ No se pudo obtener el índice de miedo y codicia."

def obtener_allseason():
    ahora = datetime.now()
    if cache["allseason"]["valor"] and ahora < cache["allseason"]["expiry"]:
        return cache["allseason"]["valor"]
    try:
        # URL de ejemplo que tenías; si falla, devolverá aviso
        resp = requests.get("https://allcoinseason.com/api/v1/season", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        season = data.get("season", "Desconocido")
        score = data.get("score", "N/A")
        texto = f"🌈 *All Coin Season Index*: {season} (Score: {score})"
        cache["allseason"] = {"valor": texto, "expiry": ahora + CACHE_DURATION}
        return texto
    except Exception as e:
        print("Error al obtener All Season Index:", e)
        return "⚠️ No se pudo obtener el índice All Season."

def obtener_corrupcion():
    return "🚧 El comando /corrupcion aún no está configurado."

@bot.message_handler(commands=['dominancia'])
def enviar_dominancia_manual(msg):
    bot.reply_to(msg, obtener_dominancia_btc(), parse_mode="Markdown")

@bot.message_handler(commands=['codicia'])
def enviar_codicia_manual(msg):
    bot.reply_to(msg, obtener_indice_codicia(), parse_mode="Markdown")

@bot.message_handler(commands=['allseason'])
def enviar_allseason_manual(msg):
    bot.reply_to(msg, obtener_allseason(), parse_mode="Markdown")

@bot.message_handler(commands=['corrupcion'])
def enviar_corrupcion_manual(msg):
    bot.reply_to(msg, obtener_corrupcion(), parse_mode="Markdown")

def tarea_envio_diario():
    tz_madrid = pytz.timezone("Europe/Madrid")
    while True:
        ahora = datetime.now(tz_madrid)
        if ahora.hour == 9 and ahora.minute == 0:
            try:
                mensajes = [
                    obtener_dominancia_btc(),
                    obtener_indice_codicia(),
                    obtener_allseason(),
                    obtener_corrupcion()
                ]
                texto_final = "\n\n".join(mensajes)
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=texto_final,
                    message_thread_id=THREAD_ID,
                    parse_mode="Markdown",
                )
                time.sleep(60)
            except Exception as e:
                print("Error enviando mensajes diarios:", e)
        time.sleep(30)

def iniciar_hilo_programado():
    hilo = threading.Thread(target=tarea_envio_diario, daemon=True)
    hilo.start()

keep_alive()
iniciar_hilo_programado()
bot.polling(none_stop=True, interval=0, timeout=20)
