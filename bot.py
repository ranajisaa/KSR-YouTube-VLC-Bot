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
        "Namaste! Koi bhi YouTube link bhejiye, main aapko VLC ke liye direct stream links generate karke dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya ek valid YouTube URL bhejiye.")
        return

    video_id = extract_video_id(url)
    if not video_id:
        await update.message.reply_text("Video ID pehchan nahi paya. Kripya valid YouTube video link bhejiye.")
        return

    # Direct VLC playable streams (Cloud IP blocks se 100% free)
    vlc_stream_1 = f"https://invidious.privacyredirect.com/latest_version?id={video_id}&itag=18"
    vlc_stream_2 = f"https://inv.nadeko.net/latest_version?id={video_id}&itag=22"
    vlc_audio = f"https://invidious.privacyredirect.com/latest_version?id={video_id}&itag=140"

    reply_text = (
        f"✅ **VLC Direct Stream Links:**\n\n"
        f"🎬 **Video Stream (Normal Quality - Itag 18):**\n"
        f"`{vlc_stream_1}`\n\n"
        f"🎬 **Video Stream (HD Quality - Itag 22):**\n"
        f"`{vlc_stream_2}`\n\n"
        f"🎵 **Audio Only Stream (Itag 140):**\n"
        f"`{vlc_audio}`\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"▶️ **VLC mein chalane ka tareeqa:**\n"
        f"1. Upar diye gaye stream link par tap karke copy karein.\n"
        f"2. VLC app kholein -> **More** -> **New stream** par jayein.\n"
        f"3. Link paste karke play dabayein, video turant bina rukawat chalegi!"
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
