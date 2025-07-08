import os
import telebot
from keep_alive import keep_alive

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot activo 🚀")

keep_alive()

bot.delete_webhook()          # <-- Añade esta línea para evitar conflicto de polling
bot.polling(non_stop=True)    # <-- Mejor usar non_stop=True para que sea más estable
