from flask import Flask, request
import requests
import threading
import time
import os
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 🔹 Telegram bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE = "https://marco-cp-api.vercel.app"

# Flask app for Render web service
app = Flask(__name__)

# --- Telegram bot setup ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send your email to get Classplus OTP.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    if "email" not in user_data:
        user_data["email"] = text
        res = requests.post(f"{API_BASE}/send-otp", json={"email": text})
        data = res.json()
        if data.get("success"):
            await update.message.reply_text("📩 OTP sent to your email. Now send the OTP.")
        else:
            await update.message.reply_text(f"❌ Failed to send OTP: {data}")
    elif "otp" not in user_data:
        user_data["otp"] = text
        email = user_data["email"]
        res = requests.post(f"{API_BASE}/verify-otp", json={"email": email, "otp": text})
        data = res.json()
        if "token" in data:
            await update.message.reply_text(f"✅ Your Token:\n\n`{data['token']}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Verification failed: {data}")
        user_data.clear()

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n/start - Begin\nJust send your email and OTP step by step.")

# --- Telegram Bot Runner ---
def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_cmd))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.run_polling()

# --- Flask route for Render health check ---
@app.route('/')
def home():
    return "✅ Telegram Classplus Token Bot is running on Render!"

# --- Keep bot thread alive ---
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
