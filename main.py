import os
import json
import requests
import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import threading
import time

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5557283805"))
API_URL = os.getenv("API_URL", "https://lordlike.onrender.com/like")

USAGE_FILE = "usage.json"
VIP_FILE = "vip.json"
GROUPS_FILE = "groups.json"

# --- Utility ---
def load_file(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
    with open(file, "r") as f:
        return json.load(f)

def save_file(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# --- Core API ---
def send_likes(uid: str, region: str, retries=1):
    """Send likes using API. Retries once if network error."""
    try:
        resp = requests.get(f"{API_URL}?uid={uid}&region={region.upper()}", timeout=30)
        return resp.json()
    except Exception as e:
        if retries > 0:
            time.sleep(2)  # wait before retry
            return send_likes(uid, region, retries=retries-1)
        return {"status": 0, "error": str(e)}

# --- Telegram Commands ---
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    if str(update.effective_user.id) != str(OWNER_ID):
        groups = load_file(GROUPS_FILE, {})
        if chat_id not in groups:
            await update.message.reply_text("❌ This group is not allowed to use this bot.")
            return

    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /like <region> <uid>")
        return

    region, uid = context.args[0].lower(), context.args[1]
    usage = load_file(USAGE_FILE, {})
    vip = load_file(VIP_FILE, {})

    today = str(datetime.date.today())
    if user_id not in usage or usage[user_id]["date"] != today:
        usage[user_id] = {"date": today, "uids": []}

    # VIP bypass limit
    if str(user_id) not in vip:
        if uid in usage[user_id]["uids"]:
            await update.message.reply_text("❌ Already used likes on this UID today.")
            return
        if len(usage[user_id]["uids"]) >= 3:
            await update.message.reply_text("❌ Daily limit reached (3 UIDs). Contact @MrDearUser for VIP.")
            return

    result = send_likes(uid, region)

    # --- Friendly messages ---
    if result.get("status") == 1:
        usage[user_id]["uids"].append(uid)
        save_file(USAGE_FILE, usage)

        player = result.get("player", {})
        likes = result.get("likes", {})

        nickname = player.get("nickname", "Unknown")
        player_uid = player.get("uid", uid)
        region = player.get("region", region.upper())
        before = likes.get("before", 0)
        after = likes.get("after", 0)
        added = likes.get("added_by_api", 0)

        msg = (
            f"✅ Likes Sent!\n\n"
            f"👤 Player: {nickname}\n"
            f"🆔 UID: {player_uid}\n"
            f"🌍 Region: {region}\n"
            f"💙 Added: {added}\n"
            f"📊 Before: {before}\n"
            f"📈 After: {after}\n"
            f"🔰 Credits: @MrDearUser\n"
            f"ℹ️ Remaining Today: {3 - len(usage[user_id]['uids'])}/3"
        )
    elif result.get("status") == 2:
        msg = "❌ Likes could not be added. UID may have reached the daily limit or API limit."
    elif result.get("status") == 0:
        msg = f"❌ Failed: Could not reach Like API. Error: {result.get('error')}"
    else:
        msg = f"❌ Failed: {result}"

    await update.message.reply_text(msg)

async def allow_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(OWNER_ID):
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /allowgroup <chat_id>")
        return
    groups = load_file(GROUPS_FILE, {})
    groups[context.args[0]] = True
    save_file(GROUPS_FILE, groups)
    await update.message.reply_text(f"✅ Group {context.args[0]} allowed.")

async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(OWNER_ID):
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /vip <user_id>")
        return
    vip = load_file(VIP_FILE, {})
    vip[context.args[0]] = True
    save_file(VIP_FILE, vip)
    await update.message.reply_text(f"✅ User {context.args[0]} promoted to VIP.")

# --- Flask keep-alive ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Free Fire Like Bot is running on Render!"

@flask_app.route('/favicon.ico')
def favicon():
    return '', 204

# --- Start Telegram bot ---
def start_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("like", like_command))
    bot_app.add_handler(CommandHandler("allowgroup", allow_group))
    bot_app.add_handler(CommandHandler("vip", add_vip))
    bot_app.run_polling()

# --- Main ---
if __name__ == "__main__":
    # Start Flask in background
    threading.Thread(
        target=lambda: flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080))),
        daemon=True
    ).start()

    # Start Telegram bot
    start_bot()
