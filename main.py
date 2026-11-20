import os
import logging
import threading
import requests
from flask import Flask, request

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ["WA_TOKEN"]            # token de acceso de Meta
PHONE_ID = os.environ["WA_PHONE_ID"]      # ID del número de WhatsApp Business
VERIFY_TOKEN = os.environ["WA_VERIFY"]    # cadena que tú eliges para el webhook
API_URL = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"  # revisa la versión vigente

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
destino = None  # número con el que chateas (formato internacional, sin +)


@app.get("/webhook")
def verificar():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge", ""), 200
    return "Forbidden", 403


@app.post("/webhook")
def recibir():
    global destino
    data = request.get_json(silent=True) or {}
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if msg.get("type") == "text":
                    destino = msg["from"]
                    print(f"\n[{msg['from']}] {msg['text']['body']}\n> ", end="", flush=True)
    return "ok", 200


def enviar(numero, texto):
    r = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": texto},
        },
        timeout=10,
    )
    if not r.ok:
        print(f"Error {r.status_code}: {r.text}")


def main():
    global destino
    threading.Thread(
        target=lambda: app.run(port=5000), daemon=True
    ).start()
    print("Escribe '/para 34600111222' para elegir contacto. Ctrl+C para salir.")
    while True:
        linea = input("> ").strip()
        if linea.startswith("/para "):
            destino = linea.split()[1]
        elif not destino:
            print("Aún no hay destinatario.")
        elif linea:
            enviar(destino, linea)


if __name__ == "__main__":
    main()