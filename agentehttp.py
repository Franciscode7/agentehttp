import requests
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = "8742607552:AAH6ESb97z7fLROC8aZFZzvgaOc0U3xHUZQ"
LAPTOP_IP = "100.96.246.102"  # IP de Tailscale de tu laptop
API_KEY = "panchibolo123"      # La que probaste en PowerShell
OLLAMA_URL = "http://localhost:11434/api/generate"

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"Mensaje recibido: {user_text}")

    # 1. Le pedimos a Ollama que interprete la orden
    prompt = (
        f"Eres un asistente. Responde SOLO en JSON.\n"
        f"Si el usuario quiere abrir una web, devuelve: {{\"action\": \"abrir\", \"url\": \"URL_AQUÍ\"}}\n"
        f"Si quiere la calculadora, devuelve: {{\"action\": \"ejecutar\", \"cmd\": \"calc\"}}\n"
        f"Orden del usuario: {user_text}"
    )

    try:
        # Llamada a la IA
        res_ollama = requests.post(OLLAMA_URL, json={
            "model": "qwen2:1.5b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        })
        
        datos_ia = json.loads(res_ollama.json()['response'])
        accion = datos_ia.get("action")
        
        # 2. Enviar la orden a la Laptop
        url_lap = f"http://{LAPTOP_IP}:7777/orden"
        headers = {"X-API-KEY": API_KEY}
        
        if accion == "abrir":
            payload = {"accion": "abrir", "valor": datos_ia.get("url")}
        elif accion == "ejecutar":
            payload = {"accion": "ejecutar", "valor": datos_ia.get("cmd")}
        else:
            await update.message.reply_text("La IA no supo qué hacer.")
            return

        # Petición HTTP a tu laptop
        r = requests.post(url_lap, json=payload, headers=headers, timeout=5)
        
        if r.status_code == 200:
            await update.message.reply_text(f"✅ Orden enviada: {accion}")
        else:
            await update.message.reply_text(f"❌ La laptop respondió con error: {r.status_code}")

    except Exception as e:
        await update.message.reply_text(f"💥 Error: {e}")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN_TELEGRAM).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    print("🚀 Bot en el VPS escuchando...")
    app.run_polling()
