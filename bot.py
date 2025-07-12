import os
import telebot
import requests
import time
from flask import Flask, request
import pytz
from datetime import datetime, timedelta
import schedule

# 🔐 Configuración
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = -1002641253969
THREAD_ID = 31
WEBHOOK_URL = f"https://odiobot.onrender.com/{TOKEN}"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
tz_madrid = pytz.timezone("Europe/Madrid")

# 🧪 Métricas internas (Paso 17)
registro_metrica = {
    "noticias_enviadas": 0,
    "ultimas_ejecuciones": {},
    "alertas_enviadas": 0
}

def registrar_ejecucion(nombre):
    ahora = datetime.now(tz_madrid).strftime("%d/%m %H:%M")
    registro_metrica["ultimas_ejecuciones"][nombre] = ahora

# 🌍 Indicadores cripto diarios — Dominancia, Codicia, Altseason
def enviar_indicadores_programados():
    mensaje = ""
    alerta = ""

    try:
        r_dom = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        btc_dominancia = r_dom.json().get("data", {}).get("market_cap_percentage", {}).get("btc", 0)
        mensaje += f"🧱 Dominancia actual de Bitcoin: {btc_dominancia:.2f}%\n"

        r_codicia = requests.get("https://fear-and-greed-index-api.com/v1/fear-and-greed", timeout=10)
        codicia = int(r_codicia.json().get("value", 50))

        if codicia < 20:
            emoji_codicia = "😱"
        elif codicia < 60:
            emoji_codicia = "😐"
        else:
            emoji_codicia = "🤑"

        mensaje += f"{emoji_codicia} Índice de Miedo/Codicia: {codicia}\n"

        altseason = "No es temporada de altcoins" if btc_dominancia > 50 else "Altseason activa"
        mensaje += f"🌒 {altseason} (Dominancia BTC: {btc_dominancia:.1f}%)\n"

        if codicia >= 80:
            alerta += "🟠 ¡Codicia extrema! Riesgo de sobreoptimismo.\n"
            registro_metrica["alertas_enviadas"] += 1
        if btc_dominancia <= 40:
            alerta += "🔵 Dominancia baja: posible altseason o volatilidad.\n"
            registro_metrica["alertas_enviadas"] += 1

        mensaje_final = alerta + mensaje if alerta else mensaje
        bot.send_message(chat_id=CHAT_ID, text=mensaje_final.strip(), message_thread_id=THREAD_ID)
        registrar_ejecucion("indicadores")

    except Exception as err:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Error en indicadores: {err}", message_thread_id=THREAD_ID)

# 🧠 Clasificación temática + impacto editorial
def analizar_tematica_y_impacto(titulo, resumen):
    texto = f"{titulo} {resumen}".lower()
    categoria = "🌐 General"
    impacto = "🟢 Impacto bajo"

    temas = {
        "📈 Mercado": ["bull", "bear", "pump", "crash", "volatility", "futures", "etf", "trend", "market", "volume", "trading", "price"],
        "⚖️ Regulación": ["regulation", "ban", "sec", "law", "legal", "compliance", "crime", "sanction", "fine", "lawsuit", "court"],
        "🔐 Hackeo": ["hack", "exploit", "rug", "security", "breach", "attack", "phishing", "loss", "wallet compromised"],
        "💼 Corporativo": ["investment", "fund", "acquisition", "merger", "venture", "partner", "launch", "collaboration", "announcement"],
        "🧪 Innovación": ["blockchain", "nft", "layer 2", "protocol", "upgrade", "smart contract", "integration", "ai", "zk", "rollup"]
    }

    for label, palabras in temas.items():
        if any(p in texto for p in palabras):
            categoria = label
            break

    palabras_alto = ["sec", "etf", "crash", "ban", "lawsuit", "regulator", "hack", "exploit", "blackrock", "binance", "rug pull", "attack"]
    palabras_medio = ["trend", "pump", "new listing", "volume spike", "depeg", "launch", "investment", "venture"]

    if any(p in texto for p in palabras_alto):
        impacto = "🔴 Impacto muy alto"
    elif any(p in texto for p in palabras_medio):
        impacto = "🟠 Impacto medio"

    return categoria, impacto

# 📡 Radar cripto automático — Cointelegraph vía Apify
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
APIFY_DATASET_ID = "2xEswle6SascMv29A"

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
            "Bitcoin", "Ethereum", "XRP", "Ripple", "SOL", "Solana", "ETF", "SEC",
            "Altseason", "alt season", "dominance", "regulation", "interest rate", "hack", "crash", "pump",
            "dominancia", "regulación", "tipos de interés", "hackeo", "caída", "subida"
        ]

        enviados = cargar_enlaces_enviados()
        mensaje = ""
        nuevas = 0

        for n in noticias:
            titulo = n.get("title", "")
            resumen = n.get("summary", "")
            link = n.get("url", "")
            fecha = n.get("datePublished", "")[:10]
            contenido = f"{titulo} {resumen}".lower()

            if link not in enviados and any(p.lower() in contenido for p in palabras_clave):
                categoria, impacto = analizar_tematica_y_impacto(titulo, resumen)
                mensaje += f"*{titulo}* — {fecha}\n{impacto} — {categoria}\n✍️ {resumen}\n🔗 {link}\n\n"
                guardar_enlace_enviado(link)
                nuevas += 1

        if nuevas > 0:
            registro_metrica["noticias_enviadas"] += nuevas
            registrar_ejecucion("noticias")

        return mensaje.strip() if nuevas > 0 else None

    except Exception as e:
        return f"⚠️ Error al cargar noticias: {e}"

def enviar_noticias_cointelegraph():
    resumen = get_noticias_cointelegraph()
    if resumen:
        bot.send_message(chat_id=CHAT_ID, text="🗞️ Noticias destacadas — Cointelegraph\n\n" + resumen, message_thread_id=THREAD_ID, parse_mode="Markdown")
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
        eventos_relevantes.sort()
        mensaje = ""
        emojis_pais = {
            "US": "🇺🇸", "EU": "🇪🇺", "JP": "🇯🇵", "CN": "🇨🇳", "GB": "🇬🇧", "ES": "🇪🇸"
        }
        for fecha, pais, evento in eventos_relevantes:
            emoji = emojis_pais.get(pais, "")
            fecha_formato = fecha.strftime("%a %d/%m")
            mensaje += f"{emoji} {fecha_formato} — {evento}\n"
        return mensaje.strip() if mensaje else None
    except Exception as err:
        return f"⚠️ No se pudo cargar el calendario económico: {err}"

def enviar_evento_semanal():
    resumen = get_eventos_macro_cripto()
    if resumen:
        bot.send_message(chat_id=CHAT_ID, text="📅 Calendario económico\n\n" + resumen, message_thread_id=104)
        registrar_ejecucion("eventos_macro")

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

        eventos.sort()
        mensaje = ""
        for _, linea in eventos:
            mensaje += linea + "\n"

        return mensaje.strip() if mensaje else None
    except Exception as err:
        return f"⚠️ Error al cargar desbloqueos: {err}"

def enviar_desbloqueos_semanales():
    resumen = get_desbloqueos_tokens()
    if resumen:
        bot.send_message(chat_id=CHAT_ID, text="🔓 Desbloqueos de tokens\n\n" + resumen, message_thread_id=104)
        registrar_ejecucion("desbloqueos")

# 📦 Comando /resumen (Paso 16)
@bot.message_handler(commands=["resumen"])
def comando_resumen(message):
    texto = "📊 *Resumen cripto automático*\n\n"

    try:
        r_dom = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        btc_dominancia = r_dom.json().get("data", {}).get("market_cap_percentage", {}).get("btc", 0)
        texto += f"🧱 Dominancia BTC: {btc_dominancia:.2f}%\n"
    except:
        texto += "⚠️ Dominancia BTC no disponible\n"

    try:
        r_codicia = requests.get("https://fear-and-greed-index-api.com/v1/fear-and-greed", timeout=10)
        codicia = int(r_codicia.json().get("value", 50))
        texto += f"🤑 Codicia/Miedo: {codicia}\n"
    except:
        texto += "⚠️ Índice codicia no disponible\n"

    titulares = get_noticias_cointelegraph()
    eventos = get_eventos_macro_cripto()
    desbloqueos = get_desbloqueos_tokens()

    if titulares:
        texto += "\n🗞️ Titulares destacados:\n\n" + titulares + "\n"
    if eventos:
        texto += "\n📅 Eventos macro:\n\n" + eventos + "\n"
    if desbloqueos:
        texto += "\n🔓 Desbloqueos:\n\n" + desbloqueos + "\n"

    bot.send_message(chat_id=message.chat.id, text=texto.strip(), parse_mode="Markdown")

# 📊 Comando /stats (Paso 17)
@bot.message_handler(commands=["stats"])
def comando_stats(message):
    stats = registro_metrica
    texto = "📈 *Estado interno del bot*\n\n"
    texto += f"🗞️ Titulares enviados: {stats['noticias_enviadas']}\n"
    texto += f"⚠️ Alertas emitidas: {stats['alertas_enviadas']}\n"
    texto += f"\n🕒 Últimas ejecuciones:\n"
    for k, v in stats["ultimas_ejecuciones"].items():
        texto += f"— {k}: {v}\n"
    bot.send_message(chat_id=message.chat.id, text=texto.strip(), parse_mode="Markdown")

# ✅ Ciclo de ejecución con radar integrado
def ciclo_bot():
    schedule.every(30).minutes.do(enviar_noticias_cointelegraph)
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

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
