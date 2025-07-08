import os
import telebot
from keep_alive import keep_alive

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot activo 🚀")

# Handler para obtener el chat ID de cualquier grupo o chat donde envíes un mensaje
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"El chat ID de este grupo es: {chat_id}")

keep_alive()
bot.polling()
