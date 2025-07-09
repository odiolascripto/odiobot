import os
import telebot
from keep_alive import keep_alive

# ---------------------------
# Token del bot (variable de entorno)
# ---------------------------
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# ---------------------------
# /start  →  mensaje de bienvenida
# ---------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot activo 🚀")

# ---------------------------
# Handler genérico para obtener el chat‑ID
# (útil para saber el ID del grupo donde se use)
# ---------------------------
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"El chat ID de este grupo es: {chat_id}")

# ---------------------------
# Mantener vivo (para Render/Replit)
# ---------------------------
keep_alive()

# ---------------------------
# Arrancar polling
# ---------------------------
bot.polling()

