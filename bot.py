import os
import telebot
import requests
import time
from flask import Flask, request
import pytz
from datetime import datetime, timedelta

# 🔐 Configuración
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

# 📊 Comando /dominancia
@bot.message_handler(commands=["dominancia"])
def cmd_dominancia(msg=None):
    r = requests.get("https://api.coinlore.net/api/global/")
    if r.status_code == 200:
        dominancia = float(r.json()[0]["btc_d"])
        emoji = "🧱" if dominancia >= 55 else "📊" if dominancia >= 45 else "🌪️"
        texto = f"{emoji} Dominancia actual de Bitcoin: {dominancia}%"
        if msg: bot.reply_to(msg, texto)
        else: return texto, dominancia

# 😱 Comando /codicia
@bot.message_handler(commands=["codicia"])
def cmd_codicia(msg=None):
    r = requests.get("https://api.alternative.me/fng/")
    if r.status_code == 200:
        valor = int(r.json()["data"][0]["value"])
        emoji = "🤑" if valor >= 80 else "😐" if valor >= 50 else "😱"
        texto = f"{emoji} Índice de Miedo/Codicia: {valor}"
        if msg: bot.reply_to(msg, texto)
        else: return texto, valor

# 📈 Comando /allseason
@bot.message_handler(commands=["allseason"])
def cmd_allseason(msg=None):
    r = requests.get("https://api.coinlore.net/api/global/")
    if r.status_code == 200:
        dominancia = float(r.json()[0]["btc_d"])
        if dominancia < 45:
            estado = f"🚀 Temporada de altcoins (Dominancia BTC: {dominancia:.1f}%)"
        elif dominancia < 55:
            estado = f"⚖️ Estamos a medio camino (Dominancia BTC: {dominancia:.1f}%)"
        else:
            estado = f"🌒 No es temporada de altcoins (Dominancia BTC: {dominancia:.1f}%)"
        if msg: bot.reply_to(msg, estado)
        else: return estado

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
        "👉 `/dominancia` — Dominancia actual de BTC\n"
        "👉 `/codicia` — Índice de Miedo/Codicia\n"
        "👉 `/allseason` — Estado altcoins\n"
        "👉 `/corrupcion` — Índice España\n"
        "👉 `/ayuda` — Este menú\n"
        "📡 *Auto-envíos:* 09:00h y 16:00h\n"
        "📆 *Resumen semanal:* lunes a las 09:30h y 11:00h\n"
        "🔍 *Subgrupos:* Noticias, OnChain, Eventos"
    )
    bot.reply_to(msg, ayuda, parse_mode="Markdown")
# ⏰ Envío diario automático
def enviar_indicadores_programados():
    hora = datetime.now(tz_madrid).strftime("%H:%M")
    print(f"📡 Enviando indicadores programados ({hora})")
    texto_dominancia, valor_dominancia = cmd_dominancia()
    texto_codicia, valor_codicia = cmd_codicia()
    texto_allseason = cmd_allseason()
    texto_corrupcion = cmd_corrupcion()
    mensaje = f"{texto_dominancia}\n{texto_codicia}\n{texto_allseason}\n{texto_corrupcion}"
    alertas = []
    if valor_codicia >= 80:
        alertas.append("⚠️ Codicia extrema — posible sobrecompra del mercado")
    if valor_dominancia <= 40:
        alertas.append("⚠️ Dominancia baja — altcoins podrían estar tomando el control")
    if alertas:
        mensaje += "\n\n" + "\n".join(alertas)
    bot.send_message(CHAT_ID, mensaje, message_thread_id=THREAD_ID)

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

# ✅ Nuevo ciclo con hora real local
def ciclo_bot():
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

        time.sleep(30)

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
