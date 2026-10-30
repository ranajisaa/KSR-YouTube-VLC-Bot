import os
import socket
import logging
import urllib.parse
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Network socket ko hang hone se rokne ke liye strict 5-second timeout
socket.setdefaulttimeout(5)

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
        "Namaste! Koi bhi YouTube link bhejiye, main VLC ke liye direct playable MP4 stream links taiyar kar dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()
    
    if not ("http://" in raw_text or "https://" in raw_text):
        await update.message.reply_text("Kripya ek valid YouTube link bhejiye.")
        return

    video_id = extract_video_id(raw_text)
    if not video_id:
        await update.message.reply_text("Video ID detect nahi hua. Normal YouTube link bhejein.")
        return

    # Direct Tunneled Media Streams (local=true Google ka IP lock aur redirect dono bypass karta hai)
    stream_sd = f"https://yewtu.be/latest_version?id={video_id}&itag=18&local=true"
    stream_backup = f"https://invidious.nerdvpn.de/latest_version?id={video_id}&itag=18&local=true"
    stream_audio = f"https://yewtu.be/latest_version?id={video_id}&itag=140&local=true"

    reply_html = (
        "🎬 <b>VLC Direct Stream Links:</b>\n\n"
        "🔹 <b>Stream 1 (Direct Video MP4):</b>\n"
        f"<code>{stream_sd}</code>\n\n"
        "🔹 <b>Stream 2 (Backup Video MP4):</b>\n"
        f"<code>{stream_backup}</code>\n\n"
        "🎵 <b>Stream 3 (Audio Only):</b>\n"
        f"<code>{stream_audio}</code>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "▶️ <b>Play karne ka tarika:</b>\n"
        "1. Upar <code>code box</code> wale link par <b>sirf ek baar tap karein</b> (pura link ek baar mein copy ho jayega).\n"
        "2. VLC app kholein ➡️ <b>More</b> ➡️ <b>New stream</b> par paste karein.\n"
        "3. Orange arrow dabayein, video seedha play hogi!"
    )

    await update.message.reply_text(reply_html, parse_mode=ParseMode.HTML)

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
