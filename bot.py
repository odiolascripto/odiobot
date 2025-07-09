import os, telebot
from keep_alive import keep_alive

TOKEN = os.getenv("BOT_TOKEN")
bot   = telebot.TeleBot(TOKEN)

# 🔑  Línea esencial: evita el conflicto 409
bot.delete_webhook(drop_pending_updates=True)

@bot.message_handler(commands=['start'])
def send_welcome(m):
    bot.reply_to(m, "Bot activo 🚀")

# Handler temporal para obtener el chat‑ID
@bot.message_handler(func=lambda m: True)
def echo_all(m):
    bot.reply_to(m, f"El chat ID de este grupo es: {m.chat.id}")

keep_alive()
bot.polling(none_stop=True, interval=0, timeout=20)

