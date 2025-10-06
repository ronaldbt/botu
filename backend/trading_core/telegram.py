import requests

# Coloca tu token y tu chat_id (te explico luego cómo obtenerlos)
TELEGRAM_TOKEN = "TU_TELEGRAM_BOT_TOKEN"
CHAT_ID = "TU_CHAT_ID"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print("Error al enviar mensaje a Telegram:", response.text)
