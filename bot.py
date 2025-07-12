import os
import telebot
import requests
import time
from flask import Flask, request
import pytz
from datetime import datetime, timedelta
import schedule  # 🆕 para ejecutar cada 30 min

# 🔐 Configuración
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = -1002641253969
THREAD_ID = 31
WEBHOOK_URL = f"https://odiobot.onrender.com/{TOKEN}"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
tz_madrid = pytz.timezone("Europe/Madrid")

# 📡 Radar cripto automático — Cointelegraph vía Apify
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
APIFY_DATASET_ID = "2xEswle6SascMv29A"  # ⚠️ Reemplaza con tu dataset real

def cargar_enlaces_enviados():
    try:
        with open("noticias_enviadas.txt", "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def guardar_enlace_enviado(link):
    with open("noticias_enviadas.txt", "a") as f:
        f.write(f"{link}\n")

def get_noticias_cointelegraph():
    try:
        url = f"https://api.apify.com/v2/datasets/{APIFY_DATASET_ID}/items?token={APIFY_TOKEN}"
        r = requests.get(url, timeout=10)
        noticias = r.json()

        palabras_clave = [
            # Inglés
            "Bitcoin", "Ethereum", "XRP", "Ripple", "SOL", "Solana", "ETF", "SEC",
            "Altseason", "alt season", "dominance", "regulation", "interest rate", "hack", "crash", "pump",
            # Español
            "Bitcoin", "Ethereum", "XRP", "Ripple", "Sol", "Solana", "ETF", "SEC",
            "altseason", "alt season", "dominancia", "regulación", "tipos de interés", "hackeo", "caída", "subida"
        ]

        enviados = cargar_enlaces_enviados()
        mensaje = "🗞️ Noticias destacadas — Cointelegraph\n\n"
        nuevas = 0

        for n in noticias:
            titulo = n.get("title", "")
            resumen = n.get("summary", "")
            link = n.get("url", "")
            fecha = n.get("datePublished", "")[:10]
            contenido = f"{titulo} {resumen}".lower()

            if link not in enviados and any(p.lower() in contenido for p in palabras_clave):
                mensaje += f"*{titulo}* — {fecha}\n✍️ {resumen}\n🔗 {link}\n\n"
                guardar_enlace_enviado(link)
                nuevas += 1

        return mensaje.strip() if nuevas > 0 else None

    except Exception as e:
        return f"⚠️ Error al cargar noticias: {e}"

def enviar_noticias_cointelegraph():
    resumen = get_noticias_cointelegraph()
    if resumen:
        bot.send_message(chat_id=CHAT_ID, text=resumen, message_thread_id=THREAD_ID, parse_mode="Markdown")
# 📅 Calendario macroeconómico Finnhub
def get_eventos_macro_cripto():
    api_key = os.getenv("FINNHUB_API_KEY")
    url = f"https://finnhub.io/api/v1/calendar/economic?token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        eventos = data.get("economicCalendar", [])
        hoy = datetime.today().date()
        limite = hoy + timedelta(days=7)
        eventos_relevantes = []
        categorias_clave = [
            "Interest Rate Decision", "Unemployment Rate", "GDP Growth Rate",
            "CPI", "PPI", "Central Bank Speech", "FOMC Minutes",
            "Inflation Rate", "Non Farm Payrolls"
        ]
        paises_clave = ["US", "EU", "JP", "CN", "GB", "ES"]
        impactos_validos = ["medium", "high", "Medium", "High"]
        for e in eventos:
            fecha_str = e.get("date")
            try:
                fecha_evento = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except:
                continue
            if hoy <= fecha_evento <= limite:
                evento = e.get("event", "")
                impacto = e.get("impact", "").lower()
                pais = e.get("country", "").upper()
                if any(cat.lower() in evento.lower() for cat in categorias_clave):
                    if pais in paises_clave and impacto in [i.lower() for i in impactos_validos]:
                        eventos_relevantes.append((fecha_evento, pais, evento))
        if not eventos_relevantes:
            return "📅 No hay eventos macroeconómicos relevantes esta semana."
        eventos_relevantes.sort()
        mensaje = "📅 Calendario macroeconómico relevante esta semana:\n\n"
        emojis_pais = {
            "US": "🇺🇸", "EU": "🇪🇺", "JP": "🇯🇵", "CN": "🇨🇳", "GB": "🇬🇧", "ES": "🇪🇸"
        }
        for fecha, pais, evento in eventos_relevantes:
            emoji = emojis_pais.get(pais, "")
            fecha_formato = fecha.strftime("%a %d/%m")
            mensaje += f"{emoji} {fecha_formato} — {evento}\n"
        return mensaje.strip()
    except Exception as err:
        return f"⚠️ No se pudo cargar el calendario económico: {err}"

def enviar_evento_semanal():
    resumen = get_eventos_macro_cripto()
    bot.send_message(chat_id=CHAT_ID, text=resumen, message_thread_id=104)

# 🔓 Desbloqueos de tokens
def get_desbloqueos_tokens():
    try:
        r = requests.get("https://dropstab.com/api/tokenUnlocks?limit=300", headers={"accept": "application/json"})
        if r.status_code != 200:
            return "⚠️ No se pudo cargar los desbloqueos de tokens."

        data = r.json().get("items", [])
        hoy = datetime.today().date()
        limite = hoy + timedelta(days=15)
        eventos = []

        for token in data:
            nombre = token.get("token", {}).get("name", "")
            simbolo = token.get("token", {}).get("symbol", "")
            fecha_str = token.get("date")
            if not nombre or not fecha_str:
                continue
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except:
                continue
            if hoy <= fecha <= limite:
                porcentaje = token.get("percentage", 0)
                valor = token.get("value", {}).get("usd")
                linea = f"🔓 {fecha.strftime('%a %d/%m')} — {nombre} ({simbolo}) | {porcentaje:.2f}%"
                if valor:
                    linea += f" ≈ ${valor:,.0f}"
                eventos.append((fecha, linea))

        if not eventos:
            return "🔓 No hay desbloqueos relevantes en los próximos 15 días."

        eventos.sort()
        mensaje = "🔓 Desbloqueos de tokens esta quincena:\n\n"
        for _, linea in eventos:
            mensaje += linea + "\n"

        return mensaje.strip()
    except Exception as err:
        return f"⚠️ Error al cargar desbloqueos: {err}"

def enviar_desbloqueos_semanales():
    resumen = get_desbloqueos_tokens()
    bot.send_message(chat_id=CHAT_ID, text=resumen, message_thread_id=104)

# ✅ Ciclo de ejecución con radar integrado
def ciclo_bot():
    schedule.every(30).minutes.do(enviar_noticias_cointelegraph)  # 🆕 Radar cada 30 min
    ultima_hora = ""
    while True:
        ahora = datetime.now(tz_madrid).strftime("%H:%M")
        dia_semana = datetime.now(tz_madrid).strftime("%A")

        if ahora != ultima_hora:
            if ahora in ["09:00", "16:00"]:
                enviar_indicadores_programados()
            if ahora == "09:30" and dia_semana == "Monday":
                enviar_evento_semanal()
            if ahora == "11:00" and dia_semana == "Monday":
                enviar_desbloqueos_semanales()
            ultima_hora = ahora

        schedule.run_pending()
        time.sleep(10)

import threading
threading.Thread(target=ciclo_bot).start()

# 🌐 Webhook Flask
@app.route("/" + TOKEN, methods=["POST"])
def recibir_webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def ping():
    return "✅ Bot activo vía Webhook"

# 🚀 Ejecución Flask
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)

