import requests
import os
from datetime import datetime, timedelta
import schedule
import time

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
            "Interest Rate Decision", "Unemployment Rate",
            "GDP Growth Rate", "CPI", "PPI", "Central Bank Speech",
            "FOMC Minutes", "Inflation Rate", "Non Farm Payrolls"
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
            "US": "🇺🇸", "EU": "🇪🇺", "JP": "🇯🇵",
            "CN": "🇨🇳", "GB": "🇬🇧", "ES": "🇪🇸"
        }

        for fecha, pais, evento in eventos_relevantes:
            emoji = emojis_pais.get(pais, "")
            fecha_formato = fecha.strftime("%a %d/%m")
            mensaje += f"{emoji} {fecha_formato} — {evento}\n"

        return mensaje.strip()

    except Exception as err:
        return f"⚠️ No se pudo cargar el calendario económico: {err}"

# 📤 Enviar al hilo "Eventos Semanales"
def enviar_evento_semanal():
    resumen = get_eventos_macro_cripto()
    bot.send_message(
        chat_id=-1002641253969,
        text=resumen,
        message_thread_id=104
    )

# 🕒 Programar envío automático todos los lunes
schedule.every().monday.at("09:30").do(enviar_evento_semanal)

# 🔁 Bucle para mantener vivo el programador
while True:
    schedule.run_pending()
    time.sleep(30)
