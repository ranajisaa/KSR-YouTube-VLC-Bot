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
    try:
        url = url.strip()
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0].split("&")[0]
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

def get_direct_stream(video_id):
    # Working backend APIs jo VLC ke liye direct playable mp4/hls deti hain
    backends = [
        f"https://pipedapi.adminforge.de/streams/{video_id}",
        f"https://api.piped.private.coffee/streams/{video_id}",
        f"https://pipedapi.tokhmi.xyz/streams/{video_id}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for endpoint in backends:
        try:
            req = urllib.request.Request(endpoint, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode())
                
                # 1. Sabse pehle combined video+audio direct MP4 link check karein (VLC ke liye best)
                video_streams = data.get("videoStreams", [])
                for stream in video_streams:
                    # Video + Audio dono ho aur direct link ho
                    if not stream.get("videoOnly") and stream.get("url"):
                        return stream.get("url")
                
                # 2. Agar combined na mile to HLS (.m3u8) link VLC seedha play karta hai
                if data.get("hls"):
                    return data.get("hls")
        except Exception as e:
            logging.error(f"Failed backend {endpoint}: {e}")
            continue

    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Koi bhi YouTube link bhejiye, main aapko direct VLC play link generate karke dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya valid YouTube link bhejiye.")
        return

    status_msg = await update.message.reply_text("VLC Playable Stream nikal raha hoon, intezar karein...")

    video_id = extract_video_id(url)
    if not video_id:
        await status_msg.edit_text("Video ID nahi mil paya. Kripya valid YouTube link bhejiye.")
        return

    loop = asyncio.get_event_loop()
    stream_url = await loop.run_in_executor(None, get_direct_stream, video_id)

    if stream_url:
        reply_text = (
            f"🎬 **VLC Playable Stream Link:**\n\n"
            f"`{stream_url}`\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"▶️ **Play karne ka tareeqa:**\n"
            f"1. Upar wale link par ek baar tap karke copy karein.\n"
            f"2. VLC app kholein -> **More** -> **New stream** par jayein.\n"
            f"3. Paste karke play dabayein, video turant chalegi!"
        )
        await status_msg.edit_text(reply_text, parse_mode="Markdown")
    else:
        await status_msg.edit_text("Error: YouTube streaming server busy hai, kripya 1 minute baad dobara bhejein.")

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
