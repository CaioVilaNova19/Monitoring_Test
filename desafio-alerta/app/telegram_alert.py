import requests
import sys
import os

def send_telegram_alert(status, detected_at, current_count):
    """
    Envia um alerta para um chat do Telegram.
    """

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or "7773981984:AAFGY8iKoPtqMsp-Wn8BOug1mFdcKw1ky0I"
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or "1315871209"  # seu ID, testado via navegador

    message_text = (
        f"🚨 <b>ANOMALY ALERT - Transaction {status.upper()}</b>\n\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Detected at:</b> {detected_at}\n"
        f"<b>Current count:</b> {current_count}\n\n"
        f"Verify the dashboard."
    )

    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(telegram_api_url, json=payload)
        response.raise_for_status()
        print(f"✅ Alerta enviado para o Telegram: {status}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar alerta para o Telegram: {e}")
        print("Resposta:", response.text)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Uso: python telegram_alert.py <status> <detected_at> <current_count>")
        sys.exit(1)

    status_arg = sys.argv[1]
    detected_at_arg = sys.argv[2]
    current_count_arg = int(sys.argv[3])

    send_telegram_alert(status_arg, detected_at_arg, current_count_arg)