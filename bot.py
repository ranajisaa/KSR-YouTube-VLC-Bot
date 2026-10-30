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

def get_video_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url:
        parsed = urllib.parse.urlparse(url)
        return urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
    elif "live/" in url:
        return url.split("live/")[1].split("?")[0]
    return None

def fetch_direct_stream(video_id):
    # Official YouTube TV Client API (Datacenter friendly, bypasses bot check)
    api_url = "https://www.youtube.com/youtubei/v1/player"
    payload = {
        "videoId": video_id,
        "context": {
            "client": {
                "clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER",
                "clientVersion": "2.0",
                "hl": "en",
                "gl": "US"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (SMART-TV; Linux; Tizen 5.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/5.0 TV Safari/538.1"
    }

    try:
        req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Check for direct formats
            streaming_data = data.get("streamingData", {})
            
            # 1. Progressive streams (Video + Audio combined)
            formats = streaming_data.get("formats", [])
            for f in formats:
                if f.get("url"):
                    return f.get("url")
            
            # 2. HLS Manifest (Perfect for VLC stream)
            if streaming_data.get("hlsManifestUrl"):
                return streaming_data.get("hlsManifestUrl")
                
            # 3. Adaptive formats
            adaptive = streaming_data.get("adaptiveFormats", [])
            for f in adaptive:
                if f.get("url") and "video" in f.get("mimeType", ""):
                    return f.get("url")
    except Exception as e:
        logging.error(f"TV Client error: {e}")

    # Fallback: Android client API
    payload_android = {
        "videoId": video_id,
        "context": {
            "client": {
                "clientName": "ANDROID_TESTSUITE",
                "clientVersion": "1.9",
                "androidSdkVersion": 30,
                "hl": "en",
                "gl": "US"
            }
        }
    }
    try:
        req = urllib.request.Request(api_url, data=json.dumps(payload_android).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode('utf-8'))
            streaming_data = data.get("streamingData", {})
            formats = streaming_data.get("formats", [])
            for f in formats:
                if f.get("url"):
                    return f.get("url")
            if streaming_data.get("hlsManifestUrl"):
                return streaming_data.get("hlsManifestUrl")
    except Exception as e:
        logging.error(f"Android fallback error: {e}")

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

    video_id = get_video_id(url)
    if not video_id:
        await status_msg.edit_text("URL se Video ID nahi mil paya. Kripya valid YouTube link bhejein.")
        return

    loop = asyncio.get_event_loop()
    direct_url = await loop.run_in_executor(None, fetch_direct_stream, video_id)

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
        await status_msg.edit_text("YouTube ne is video ki direct stream allow nahi ki. Kripya koi doosra video try karein.")

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
