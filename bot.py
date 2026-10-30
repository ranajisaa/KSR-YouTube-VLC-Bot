import os
import asyncio
import logging
import json
import urllib.request
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

def fetch_stream_url(url, video_id):
    # Method 1: Piped Streaming API (VLC ke liye sabse fast HLS/Direct stream)
    if video_id:
        piped_instances = [
            "https://pipedapi.adminforge.de",
            "https://api.piped.private.coffee",
            "https://pipedapi.smnz.de"
        ]
        for inst in piped_instances:
            try:
                req = urllib.request.Request(
                    f"{inst}/streams/{video_id}",
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    # HLS link VLC mein sabse smooth chalta hai
                    if data.get("hls"):
                        return data["hls"]
                    for stream in data.get("videoStreams", []):
                        if not stream.get("videoOnly") and stream.get("url"):
                            return stream["url"]
            except Exception as e:
                logging.warning(f"Piped error on {inst}: {e}")

    # Method 2: Cobalt v10 API (Bypasses music signature ciphers)
    cobalt_instances = [
        "https://cobalt-api.kwiatekm.tokyo/",
        "https://api.cobalt.tools/",
        "https://capi.wuk.sh/",
        "https://cobalt.canine.tools/"
    ]
    cobalt_payload = json.dumps({"url": url}).encode('utf-8')
    cobalt_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    for inst in cobalt_instances:
        try:
            req = urllib.request.Request(inst, data=cobalt_payload, headers=cobalt_headers, method='POST')
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get("url"):
                    return data["url"]
        except Exception as e:
            logging.warning(f"Cobalt error on {inst}: {e}")

    # Method 3: Invidious Direct Gateway
    if video_id:
        invidious_instances = [
            "https://invidious.nerdvpn.de",
            "https://inv.nadeko.net",
            "https://invidious.flokinet.to"
        ]
        for inst in invidious_instances:
            try:
                req = urllib.request.Request(
                    f"{inst}/api/v1/videos/{video_id}",
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    formats = data.get("formatStreams", [])
                    if formats and formats[-1].get("url"):
                        return formats[-1]["url"]
                    if data.get("hlsContentUrl"):
                        return data["hlsContentUrl"]
            except Exception as e:
                logging.warning(f"Invidious error on {inst}: {e}")

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
    loop = asyncio.get_event_loop()
    stream_url = await loop.run_in_executor(None, fetch_stream_url, url, video_id)

    if stream_url and stream_url.startswith("http"):
        reply_text = (
            f"**Stream Link:**\n`{stream_url}`\n\n"
            "**VLC mein chalane ke liye:**\n"
            "1. VLC app kholein.\n"
            "2. 'More' -> 'New stream' par jayein.\n"
            "3. Ye URL paste karke play dabayein."
        )
        await status_msg.edit_text(reply_text, parse_mode="Markdown")
    else:
        await status_msg.edit_text(
            "Video stream link extract nahi ho saka. Kripya doosra link try karein ya thodi der baad koshish karein."
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
