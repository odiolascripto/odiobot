import os
import time
import threading
import requests
from datetime import datetime, timedelta
import pytz
import telebot

# ✅ NUEVO TOKEN de @BotFather
TOKEN = "7988846618:AAFe8L0b4joR_XjT7RNWah8MsjnkFPqm_30"
CHAT_ID = -1002641253969
THREAD_ID = 31

bot = telebot.TeleBot(TOKEN)

CACHE_EXPIRATION = timedelta(minutes=10)

cache = {
    'dominancia': {'data': None, 'last_fetch': None},
    'codicia': {'data': None, 'last_fetch': None},
    'corrupcion': {'data': None, 'last_fetch': None},
    'allseason': {'data': None, 'last_fetch': None}
}

def fetch_with_cache(key, fetch_func):
    now = datetime.utcnow()
    cached = cache[key]
    if cached['data'] is not None and cached['last_fetch'] and (now - cached['last_fetch']) < CACHE_EXPIRATION:
        return cached['data']
    try:
        data = fetch_func()
        cache[key] = {'data': data, 'last_fetch': now}
        return data
    except Exception as e:
        print(f"Error fetching {key}: {e}")
        if cached['data'] is not None:
            return cached['data'] + " (⚠️ Datos posiblemente desactualizados)"
        else:
            return f"⚠️ No se pudo obtener datos de {key}."

# --- Datos de mercado ---

def obtener_dominancia_btc():
    def fetch():
        resp = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        btc_dom = data["data"]["market_cap_percentage"]["btc"]
        return f"📊 *Dominancia BTC*: {btc_dom:.2f}%"
    return fetch_with_cache('dominancia', fetch)

def obtener_indice_codicia():
    def fetch():
        resp = requests.get("https://api.alternative.me/fng/", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        value = data['data'][0]['value']
        classification = data['data'][0]['value_classification']
        date_str = data['data'][0]['timestamp']
        date = datetime.utcfromtimestamp(int(date_str)).strftime('%Y-%m-%d')
        return f"😱 *Índice Miedo/Codicia*: {value} ({classification})\n📅 Fecha: {date}"
    return fetch_with_cache('codicia', fetch)

def obtener_corrupcion():
    return "⚠️ Comando /corrupcion no configurado aún."

def obtener_allseason():
    def fetch():
        resp = requests.get("https://api.allcoinseason.com/v1/allcoinseason", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        index = data.get('index', 'N/D')
        description = data.get('description', '')
        return f"🌕 *Altseason Index*: {index}\n{description}"
    return fetch_with_cache('allseason', fetch)

# --- Comandos Telegram ---

@bot.message_handler(commands=['start'])
def send_welcome(msg):
    bot.reply_to(msg, "🤖 Bot operativo. Usa /dominancia, /codicia, /corrupcion o /allseason")

@bot.message_handler(commands=['dominancia'])
def cmd_dominancia(msg):
    bot.reply_to(msg, obtener_dominancia_btc(), parse_mode="Markdown")

@bot.message_handler(commands=['codicia'])
def cmd_codicia(msg):
    bot.reply_to(msg, obtener_indice_codicia(), parse_mode="Markdown")

@bot.message_handler(commands=['corrupcion'])
def cmd_corrupcion(msg):
    bot.reply_to(msg, obtener_corrupcion(), parse_mode="Markdown")

@bot.message_handler(commands=['allseason'])
def cmd_allseason(msg):
    bot.reply_to(msg, obtener_allseason(), parse_mode="Markdown")

# --- Envío automático diario 9:00h Madrid ---

def tarea_dominancia_diaria():
    tz_madrid = pytz.timezone("Europe/Madrid")
    while True:
        ahora = datetime.now(tz_madrid)
        if ahora.hour == 9 and ahora.minute == 0:
            print(f"[{ahora}] 🕘 Enviando indicadores diarios...")
            try:
                bot.send_message(chat_id=CHAT_ID, text=obtener_dominancia_btc(), message_thread_id=THREAD_ID, parse_mode="Markdown")
                bot.send_message(chat_id=CHAT_ID, text=obtener_indice_codicia(), message_thread_id=THREAD_ID, parse_mode="Markdown")
                print("✅ Mensajes enviados correctamente")
                time.sleep(60)
            except Exception as e:
                print(f"❌ Error al enviar: {e}")
        time.sleep(30)

def iniciar_hilo_programado():
    hilo = threading.Thread(target=tarea_dominancia_diaria, daemon=True)
    hilo.start()

# --- Arranque principal ---

bot.remove_webhook()  # 🔧 Limpia cualquier webhook residual
iniciar_hilo_programado()
bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)


