import os
import requests

TOKEN = os.getenv("BOT_TOKEN")
url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"

response = requests.post(url)
print(response.json())
