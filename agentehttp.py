import requests
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = "8742607552:AAH6ESb97z7fLROC8aZFZzvgaOc0U3xHUZQ"
LAPTOP_IP = "100.96.246.102"  # IP de Tailscale de tu laptop
API_KEY = "fran123"             # La que probaste en PowerShell
OLLAMA_URL = "http://localhost:11434/api/generate"

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"Mensaje recibido: {user_text}")

    # Prompt con palabras clave
    prompt = (
        f"Eres un asistente llamado Otto.\n"
        f"Si el texto contiene la palabra 'abrir', responde SOLO en JSON con {{\"action\": \"abrir\", \"valor\": \"APP_O_URL\"}}.\n"
        f"Si el texto contiene 'ajustar' y 'brillo', responde SOLO en JSON con {{\"action\": \"brillo\", \"nivel\": NUMERO}}.\n"
        f"Si el texto contiene 'ajustar' y 'volumen', responde SOLO en JSON con {{\"action\": \"volumen\", \"nivel\": NUMERO}}.\n"
        f"Si NO contiene esas palabras clave, responde como un asistente conversacional normal en lenguaje natural.\n"
        f"Orden del usuario: {user_text}"
    )

    try:
        # Llamada a Ollama
        res_ollama = requests.post(OLLAMA_URL, json={
            "model": "qwen2:1.5b",
            "prompt": prompt,
            "stream": False
        })

        respuesta = res_ollama.json()['response']

        # Intentamos parsear como JSON
        try:
            datos_ia = json.loads(respuesta)
            accion = datos_ia.get("action")

            # --- Enviar orden a la laptop ---
            url_lap = f"http://{LAPTOP_IP}:7777/orden"
            headers = {"X-API-KEY": API_KEY}

            if accion == "abrir":
                payload = {"accion": "abrir", "valor": datos_ia.get("valor")}
            elif accion == "brillo":
                payload = {"accion": "brillo", "valor": datos_ia.get("nivel")}
            elif accion == "volumen":
                payload = {"accion": "volumen", "valor": datos_ia.get("nivel")}
            else:
                await update.message.reply_text("⚠️ Acción desconocida.")
                return

            r = requests.post(url_lap, json=payload, headers=headers, timeout=5)

            if r.status_code == 200:
                await update.message.reply_text(f"✅ Orden enviada: {accion}")
            else:
                await update.message.reply_text(f"❌ Error de la laptop: {r.status_code}")

        except json.JSONDecodeError:
            # Si no es JSON, tratamos la respuesta como texto normal
            await update.message.reply_text(respuesta)

    except Exception as e:
        await update.message.reply_text(f"💥 Error: {e}")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN_TELEGRAM).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    print("🚀 Bot en el VPS escuchando...")
    app.run_polling()
