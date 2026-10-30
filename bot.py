import os
import asyncio
import logging
import json
import urllib.request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def get_cobalt_stream(url):
    # Public Cobalt instances jo YouTube cipher aur datacenter block bypass karte hain
    instances = [
        "https://cobalt-api.kwiatekm.tokyo",
        "https://api.cobalt.tools",
        "https://cobalt.api.sc",
        "https://capi.wuk.sh"
    ]
    
    payload = {
        "url": url,
        "videoQuality": "720",
        "audioFormat": "mp3",
        "downloadMode": "auto"
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    for inst in instances:
        try:
            req = urllib.request.Request(
                inst,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res = json.loads(response.read().decode('utf-8'))
                if res.get("url"):
                    return res.get("url")
                if res.get("stream"):
                    return res.get("stream")
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

    loop = asyncio.get_event_loop()
    direct_url = None

    # Step 1: Cobalt bypass (Works on Music videos & avoids datacenter block)
    try:
        direct_url = await loop.run_in_executor(None, get_cobalt_stream, url)
    except Exception as e:
        logging.error(f"Cobalt error: {e}")

    # Step 2: yt-dlp fallback
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
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
            out = stdout.decode().strip()
            if out.startswith("http"):
                direct_url = out.split('\n')[0]
        except Exception as e:
            logging.error(f"yt-dlp fallback error: {e}")

    # Final Result
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
            "Video stream link generate nahi ho saka. Kripya doosra link try karein."
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
