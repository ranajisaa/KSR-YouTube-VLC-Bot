import os
import asyncio
import logging
import urllib.parse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def extract_video_id(url):
    try:
        url = url.strip()
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0].split("&")[0].split("/")[0]
        elif "watch?v=" in url:
            parsed = urllib.parse.urlparse(url)
            return urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
        elif "shorts/" in url:
            return url.split("shorts/")[1].split("?")[0].split("&")[0]
        elif "live/" in url:
            return url.split("live/")[1].split("?")[0].split("&")[0]
    except Exception:
        pass
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Koi bhi YouTube link bhejiye, main aapko direct VLC play streams generate karke dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya valid YouTube video link bhejiye.")
        return

    video_id = extract_video_id(url)
    if not video_id:
        await update.message.reply_text("URL se Video ID nahi mila. Kripya valid YouTube link bhejein.")
        return

    # Ye direct media playback endpoints hain jo VLC player direct stream karta hai
    stream_hq = f"https://yewtu.be/latest_version?id={video_id}&itag=22"
    stream_sd = f"https://yewtu.be/latest_version?id={video_id}&itag=18"
    stream_audio = f"https://yewtu.be/latest_version?id={video_id}&itag=140"
    backup_stream = f"https://vid.puffyan.us/latest_version?id={video_id}&itag=18"

    reply_text = (
        f"🎬 **VLC Playable Stream URLs:**\n\n"
        f"🔹 **HD Video Stream (720p - itag 22):**\n"
        f"`{stream_hq}`\n\n"
        f"🔹 **SD Video Stream (360p - itag 18):**\n"
        f"`{stream_sd}`\n\n"
        f"🔹 **Backup Stream:**\n"
        f"`{backup_stream}`\n\n"
        f"🎵 **Audio Only Stream:**\n"
        f"`{stream_audio}`\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"▶️ **Play karne ka tarika:**\n"
        f"1. Kisi bhi ek link par tap karke copy karein.\n"
        f"2. VLC app kholein -> **More** -> **New stream** par jayein.\n"
        f"3. Paste karke play dabayein, video bina ruki direct chalu ho jayegi."
    )

    await update.message.reply_text(reply_text, parse_mode="Markdown")

def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN environment variable nahi mila!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("KSR Stream Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
