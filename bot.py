import os
import telebot
from keep_alive import keep_alive
import threading
import time

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Cambia aquí por el chat ID real de tu grupo de alertas
ALERT_GROUP_CHAT_ID = -1002641253969  # ejemplo, pon el tuyo real

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot activo 🚀")

@bot.message_handler(commands=['id'])
def send_chat_id(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"El chat ID de este grupo o chat es:\n{chat_id}")

# Para cualquier otro mensaje, devuelve el chat ID (útil para pruebas)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"El chat ID de este grupo es: {chat_id}")

# Función para enviar mensajes automáticos periódicos
def enviar_alertas_periodicas():
    while True:
        try:
            # Aquí metes los datos que quieres enviar (ejemplo dominancia)
            mensaje = "📊 Dominancia BTC: 45.3%\n📅 Próximos eventos económicos: Lunes 12:00 - Informe X"
            bot.send_message(ALERT_GROUP_CHAT_ID, mensaje)
        except Exception as e:
            print(f"Error enviando mensaje automático: {e}")
        # Espera el tiempo que quieras entre mensajes (ejemplo 1 hora = 3600 seg)
        time.sleep(3600)

# Levantamos el hilo en background para las alertas periódicas
def start_background_thread():
    thread = threading.Thread(target=enviar_alertas_periodicas)
    thread.daemon = True
    thread.start()

keep_alive()
start_background_thread()
bot.polling(none_stop=True, interval=0, timeout=20)
