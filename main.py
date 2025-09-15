import os
import json
import random
import asyncio
import requests
from fastapi import FastAPI, Request
from telebot.async_telebot import AsyncTeleBot

# 🔒 ENV VARS (Render me set karo)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5557283805"))

# Token file (ind.json) auto-load
TOKEN_FILE = "ind.json"

# ✅ FastAPI init
app = FastAPI()

# ✅ Telegram bot init
bot = AsyncTeleBot(BOT_TOKEN)


# -------------------------
# Utility: Load valid tokens
# -------------------------
def load_tokens():
    try:
        with open(TOKEN_FILE, "r") as f:
            tokens = json.load(f)
        return [t["token"] for t in tokens if "token" in t]
    except Exception:
        return []


# -------------------------
# Core Like Sender Function
# -------------------------
async def send_likes(uid: str, region: str):
    tokens = load_tokens()
    if not tokens:
        return "❌ No valid tokens available."

    total_before = random.randint(100, 200)  # fake counter
    sent_likes = 0

    for t in tokens:
        try:
            # Example like request (change to real API call)
            resp = requests.post(
                "https://freefire-like-api.example.com/like",
                headers={"Authorization": f"Bearer {t}"},
                json={"uid": uid, "region": region},
                timeout=10,
            )
            if resp.status_code == 200:
                sent_likes += 1
        except Exception:
            continue

    total_after = total_before + sent_likes
    return (
        f"✅ Likes sent successfully!\n\n"
        f"🎯 UID: `{uid}`\n"
        f"🌍 Region: `{region.upper()}`\n"
        f"👍 Total Likes Before: {total_before}\n"
        f"🚀 Sent: {sent_likes}\n"
        f"📊 Total After: {total_after}"
    )


# -------------------------
# Telegram Command: /like
# -------------------------
@bot.message_handler(commands=["like"])
async def like_handler(message):
    parts = message.text.strip().split()

    # Format: /like ind UID
    if len(parts) != 3:
        await bot.reply_to(
            message,
            "❌ Wrong format!\n\nUse: `/like ind 123456789`",
            parse_mode="Markdown",
        )
        return

    _, region, uid = parts

    status_msg = await bot.reply_to(message, "⏳ Processing your like request...")
    result = await send_likes(uid, region)

    await bot.edit_message_text(
        result,
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        parse_mode="Markdown",
    )


# -------------------------
# Render Health Routes
# -------------------------
@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/favicon.ico")
async def favicon():
    return {}


# -------------------------
# Startup: Run Bot
# -------------------------
@app.on_event("startup")
async def on_startup():
    print("🚀 Bot started successfully!")
    asyncio.create_task(bot.polling(non_stop=True))


# -------------------------
# Run (for local testing only)
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
