from flask import Flask, request
import requests
import threading
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# 🔹 Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE = "https://marco-cp-api.vercel.app"

# --- Flask App (for Render Health Check) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram Classplus Token Bot is running on Render!"

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Send your email to get Classplus OTP.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n/start - Begin\nSend your email and then the OTP step by step.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    # Step 1: Email Input
    if "email" not in user_data:
        user_data["email"] = text
        try:
            res = requests.post(f"{API_BASE}/send-otp", json={"email": text})
            data = res.json()
            if data.get("success"):
                await update.message.reply_text("📩 OTP sent to your email. Now send me the OTP.")
            else:
                await update.message.reply_text(f"❌ Failed to send OTP: {data}")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error sending OTP: {e}")

    # Step 2: OTP Input
    elif "otp" not in user_data:
        user_data["otp"] = text
        email = user_data["email"]
        try:
            res = requests.post(f"{API_BASE}/verify-otp", json={"email": email, "otp": text})
            data = res.json()
            if "token" in data:
                await update.message.reply_text(f"✅ Your Token:\n\n`{data['token']}`", parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ Verification failed: {data}")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error verifying OTP: {e}")
        user_data.clear()

# --- Telegram Bot Setup ---
def run_bot():
    print("🤖 Telegram bot thread started...")
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_cmd))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.run_polling(drop_pending_updates=True)

# --- Main Entry Point ---
if __name__ == '__main__':
    print("🚀 Starting Flask + Telegram bot on Render...")
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
    bot_thread.join()
