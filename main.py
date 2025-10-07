import os
import json
import requests
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 🔑 Env vars se secure values
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5557283805"))  # default tumhara id
API_URL = os.getenv("API_URL", "https://lordlike.onrender.com/like")  # apni API URL

USAGE_FILE = "usage.json"
VIP_FILE = "vip.json"
GROUPS_FILE = "groups.json"

# --- Utility: file handling ---
def load_file(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
    with open(file, "r") as f:
        return json.load(f)

def save_file(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# --- Core Like Sending ---
def send_likes(uid: str, region: str):
    try:
        resp = requests.get(
            f"{API_URL}?uid={uid}&region={region.upper()}",
            timeout=15
        )
        return resp.json()
    except Exception as e:
        return {"status": 0, "error": str(e)}

# --- Command: /like ind uid ---
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    # Owner bypass
    if str(update.effective_user.id) != str(OWNER_ID):
        groups = load_file(GROUPS_FILE, {})
        if chat_id not in groups:
            await update.message.reply_text("❌ This group is not allowed to use this bot.")
            return

    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /like <region> <uid>\nExample: /like ind 1234567890")
        return

    region = context.args[0].lower()
    uid = context.args[1]

    # Load usage + VIP
    usage = load_file(USAGE_FILE, {})
    vip = load_file(VIP_FILE, {})

    today = str(datetime.date.today())
    if user_id not in usage:
        usage[user_id] = {"date": today, "uids": []}

    if usage[user_id]["date"] != today:
        usage[user_id] = {"date": today, "uids": []}

    # VIP bypass limit
    if str(user_id) not in vip:
        if uid in usage[user_id]["uids"]:
            await update.message.reply_text("❌ You already used likes on this UID today.")
            return
        if len(usage[user_id]["uids"]) >= 3:
            await update.message.reply_text("❌ Daily limit reached (3 UIDs). Contact @Mrdearuser for VIP.")
            return

    # API call
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
        f"✅ Likes Sent Successfully!\n\n"
        f"👤 Player: {nickname}\n"
        f"🆔 UID: {player_uid}\n"
        f"🌍 Region: {region}\n"
        f"💙 Added: {added}\n"
        f"📊 Before: {before}\n"
        f"📈 After: {after}\n"
        f"🔰 Credits: @MrDearUser\n"
        f"ℹ️ Remaining Today: {3 - len(usage[user_id]['uids'])}/3"
    )
else:
    msg = f"❌ Failed: {result}"
    await update.message.reply_text(msg)

# --- Owner commands ---
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

# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("like", like_command))
    app.add_handler(CommandHandler("allowgroup", allow_group))
    app.add_handler(CommandHandler("vip", add_vip))

    app.run_polling()

if __name__ == "__main__":
    main()
