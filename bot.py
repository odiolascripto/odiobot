import os
import telebot
from keep_alive import keep_alive

# Usamos una variable de entorno para el token del bot
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot activo 🚀")

keep_alive()
bot.polling()
