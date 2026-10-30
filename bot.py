import os
import asyncio
import logging
import urllib.parse
import urllib.request
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def extract_video_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url:
        parsed = urllib.parse.urlparse(url)
        return urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
    elif "live/" in url:
        return url.split("live/")[1].split("?")[0]
    return None

def get_stream_from_invidious(video_id):
    instances = [
        "https://inv.tux.pizza",
        "https://invidious.nerdvpn.de",
        "https://vid.puffyan.us",
        "https://invidious.jing.rocks"
    ]
    for inst in instances:
        try:
            req_url = f"{inst}/api/v1/videos/{video_id}"
            req = urllib.request.Request(req_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                # FormatStreams check karein (combined video+audio)
                formats = data.get("formatStreams", [])
                if formats:
                    # Best quality link pehle lein
                    return formats[-1].get("url")
                # Agar adaptiveFormats hain
                adaptive = data.get("adaptiveFormats", [])
                for f in adaptive:
                    if "video" in f.get("type", ""):
                        return f.get("url")
        except Exception:
            continue
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Mujhe koi bhi YouTube video ya live stream link bhejiye, main aapko direct VLC play link generate karke dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya ek valid URL bhejiye.")
        return

    status_msg = await update.message.reply_text("Stream link nikal raha hoon, thoda intezar karein...")

    video_id = extract_video_id(url)
    direct_url = None

    # Step 1: Cloud-safe API bypass method
    if video_id:
        try:
            loop = asyncio.get_event_loop()
            direct_url = await loop.run_in_executor(None, get_stream_from_invidious, video_id)
        except Exception as e:
            logging.error(f"Invidious bypass error: {e}")

    # Step 2: Fallback to yt-dlp agar API se link na mila ho
    if not direct_url:
        try:
            cmd = [
                "yt-dlp",
                "--no-cache-dir",
                "-g",
                "-f", "b/best",
                url
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=35)
            output = stdout.decode().strip()
            if output.startswith("http"):
                direct_url = output.split('\n')[0]
        except Exception as e:
            logging.error(f"yt-dlp fallback error: {e}")

    if direct_url and direct_url.startswith("http"):
        reply_text = (
            f"**Stream Link:**\n`{direct_url}`\n\n"
            "**VLC mein chalane ke liye:**\n"
            "1. VLC app kholein.\n"
            "2. 'More' -> 'New stream' par jayein.\n"
            "3. Ye URL paste karke play dabayein."
        )
        await status_msg.edit_text(reply_text, parse_mode="Markdown")
    else:
        await status_msg.edit_text(
            "Error aayi: YouTube ne is video par bot restrictions lagayi hui hain. Kripya koi doosra video try karein.",
            parse_mode="Markdown"
        )

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
