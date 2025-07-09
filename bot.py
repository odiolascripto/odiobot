import os
import telebot
from keep_alive import keep_alive

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# ID del grupo "Alerta Cripto. Datos y Eventos"
GROUP_CHAT_ID = -1002641253969

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot activo 🚀")

# Enviar mensaje automático al iniciar
def notify_group_start():
    try:
        bot.send_message(GROUP_CHAT_ID, "🤖 Bot activo. ¡Listo para enviar datos cripto!")
    except Exception as e:
        print("Error enviando mensaje al grupo:", e)

# Mantener vivo con Flask
keep_alive()

# Notifica en el grupo al arrancar
notify_group_start()

# Inicia polling
bot.polling(none_stop=True, interval=0, timeout=20)
