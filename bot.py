import os
import requests
import telebot
from flask import Flask, request
from datetime import datetime, timedelta
import threading
import schedule
import time
from pytz import timezone
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
FINNHUB_TOKEN = os.environ.get("FINNHUB_TOKEN")
BITQUERY_API_KEY = os.environ.get("BITQUERY_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

def responder(mensaje, texto, parse_mode=None):
    bot.send_message(
        chat_id=mensaje.chat.id,
        text=texto,
        message_thread_id=getattr(mensaje, "message_thread_id", None),
        parse_mode=parse_mode
    )

@bot.message_handler(commands=["start"])
def handle_start(message):
    responder(message, "✅ Bot Cripto Inteligente activo y operativo.")

@bot.message_handler(commands=["dominancia"])
def handle_dominancia(message):
    r = requests.get("https://api.coinlore.net/api/global/").json()
    dom = r[0]["btc_d"]
    responder(message, f"📊 Dominancia BTC: {dom}%")

@bot.message_handler(commands=["codicia"])
def handle_codicia(message):
    r = requests.get("https://api.alternative.me/fng/").json()
    val = r["data"][0]["value"]
    tipo = r["data"][0]["value_classification"]
    responder(message, f"😱 Miedo/Codicia: {val} ({tipo})")

@bot.message_handler(commands=["radar"])
def handle_radar(message):
    print("[Radar] Comando recibido")
    responder(message, "🛰️ Activando radar manual...")
    try:
        publicar_radar()
    except Exception as e:
        print(f"[Radar] Error ejecutando radar: {e}")

@bot.message_handler(commands=["noticias"])
def noticias_handler(message):
    resumen = get_crypto_news()
    bot.send_message(message.chat.id, resumen)

@bot.message_handler(commands=["ayuda"])
def handle_ayuda(message):
    texto = """🧾 *Comandos disponibles:*

/start → Verifica estado del bot  
/dominancia → Dominancia actual del BTC  
/codicia → Índice Miedo/Codicia  
/radar → Activar radar manual  
/noticias → Titulares vía Cryptolytical  
/ayuda → Este menú

⏰ Indicadores automáticos: 09:00h y 16:00h  
📆 Eventos macro: 09:30h  
📰 Noticias: cada hora a y media  
🔓 Desbloqueos: lunes a las 10:00h
"""
    responder(message, texto, parse_mode="Markdown")

def get_crypto_news():
    url = "https://cryptolytical.netlify.app/.netlify/functions/news"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        noticias = data.get("data", [])[:5]
        resumen = ""
        for noticia in noticias:
            resumen += f"📰 {noticia['title']}\n🔗 {noticia['url']}\n\n"
        return resumen or "No se encontraron noticias recientes."
    except Exception as e:
        return f"Error al obtener noticias: {e}"

def indicadores_programados():
    ahora = datetime.now(timezone("Europe/Madrid")).strftime("%H:%M")
    print(f"[Indicadores] Ejecutados automáticamente a las {ahora}")
    mensaje = f"⏰ Indicadores Cripto ({ahora})\n"
    r1 = requests.get("https://api.coinlore.net/api/global/").json()
    dom = r1[0]["btc_d"]
    mensaje += f"📊 Dominancia BTC: {dom}%\n"
    r2 = requests.get("https://api.alternative.me/fng/").json()
    val = r2["data"][0]["value"]
    tipo = r2["data"][0]["value_classification"]
    mensaje += f"😱 Miedo/Codicia: {val} ({tipo})"
    bot.send_message(chat_id=int(CHAT_ID), text=mensaje)

def publicar_eventos_macro():
    try:
        url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_TOKEN}"
        r = requests.get(url, timeout=10).json()
        eventos = r.get("economicCalendar", [])
        hoy = datetime.now(timezone("Europe/Madrid")).date().isoformat()
        relevantes = []
        for e in eventos:
            if e.get("date") != hoy or e.get("impact") != "high":
                continue
            tipo = e.get("event")
            pais = e.get("country")
            hora = e.get("time", "—")
            emoji = "📉" if "CPI" in tipo else "🏦" if "FOMC" in tipo else "📈" if "GDP" in tipo else "🔊"
            texto = f"{emoji} *{tipo}* ({pais}) — {hora}"
            relevantes.append(texto)
        if relevantes:
            mensaje = "📆 *Eventos macroeconómicos hoy:*\n" + "\n".join(relevantes)
            bot.send_message(chat_id=int(CHAT_ID), text=mensaje, parse_mode="Markdown")
        else:
            print("[Macro] Sin eventos relevantes para hoy.")
    except Exception as e:
        print(f"[Macro] Error al obtener eventos: {e}")

def publicar_radar():
    url = "https://www.criptonoticias.com/"
    archivo = "/tmp/noticias_enviadas.txt"
    if not os.path.exists(archivo):
        open(archivo, "w").close()
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("div.post-card")
        titulares = []
        for card in cards[:10]:
            enlace_tag = card.select_one("a.post-card__title-link")
            titulo = enlace_tag.text.strip() if enlace_tag else ""
            enlace = enlace_tag["href"] if enlace_tag and enlace_tag.has_attr("href") else ""
            if titulo and enlace:
                titulares.append((titulo, enlace))
    except Exception as e:
        print(f"[Radar] Error al obtener titulares: {e}")
        return
    try:
        with open(archivo, "r") as f:
            previas = f.read().splitlines()
    except Exception as e:
        print(f"[Radar] Error leyendo archivo: {e}")
        previas = []
    nuevas = []
    for t, link in titulares:
        if t not in previas:
            nuevas.append((t, link))
    if nuevas:
        for t, link in nuevas:
            mensaje = f"📰 *Titular detectado:*\n{t}\n🔗 {link}"
            bot.send_message(chat_id=int(CHAT_ID), text=mensaje, parse_mode="Markdown")
        with open(archivo, "a") as f:
            for t, _ in nuevas:
                f.write(t + "\n")
    else:
        print("[Radar] Sin titulares nuevos en esta pasada.")

def publicar_desbloqueos_bitquery():
    url = "https://streaming.bitquery.io/graphql"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY
    }
    hoy = datetime.utcnow().date()
    dentro_7 = hoy + timedelta(days=7)
    query = {
        "query": f"""
        {{
          ethereum {{
            smartContractEvents(
              options: {{desc: "block.height", limit: 100}}
              smartContractEvent: {{signature: "Unlock(address,uint256)"}}
              date: {{after: "{hoy}", before: "{dentro_7}"}}
            ) {{
              block {{ timestamp {{ iso8601 }} }}
              smartContract {{ address {{ address }} }}
              arguments {{ argument value }}
            }}
          }}
        }}
        """
    }
    try:
        r = requests.post(url, json=query, headers=headers, timeout=15)
        data = r.json()
        eventos = data.get("data", {}).get("ethereum", {}).get("smartContractEvents", [])
        if not eventos:
            mensaje = "📭 No hay desbloqueos significativos esta semana."
        else:
            mensaje = "🔓 *Desbloqueos de tokens esta semana:*\n\n"
            for e in eventos[:8]:
                fecha = e["block"]["timestamp"]["iso8601"][:10]
                token = e["smartContract"]["address"]["address"]
                monto = e["arguments"][1]["value"] if len(e["arguments"]) > 1 else "?"
                mensaje += f"• `{fecha}` — `{token}` desbloquea `{monto}` tokens\n"
            mensaje += "\n📡 *Fuente:* Bitquery API"
        bot.send_message(chat_id=int(CHAT_ID), text=mensaje, parse_mode="Markdown")
    except Exception as e:
        print(f"[Desbloqueos] Error: {e}")

# ⏰ Programación automática
schedule.every().day.at("09:00").do(indicadores_programados)
schedule.every().day.at("16:00").do(indicadores_programados)
schedule.every().day.at("09:30").do(publicar_eventos_macro)
schedule.every().hour.at(":30").do(publicar_radar)
schedule.every().monday.at("10:00").do(publicar_desbloqueos_bitquery)
schedule.every().day.at("10:00").do(indicadores_programados)

def ciclo_schedule():
    print("🕒 Ciclo automático activo")
    while True:
        schedule.run_pending()
        time.sleep(30)

# Iniciar hilo del scheduler ANTES del webhook
threading.Thread(target=ciclo_schedule, daemon=True).start()

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    bot.process_new_updates([
        telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    ])
    return "ok", 200

@app.route("/", methods=["GET", "HEAD"])
def ping():
    return "✅ Bot activo"

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://odiobot.onrender.com/{BOT_TOKEN}")
    print("🔧 Webhook conectado")
    app.run(host="0.0.0.0", port=10000)




