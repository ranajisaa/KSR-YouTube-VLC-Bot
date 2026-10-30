import os
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

def get_vlc_direct_stream(video_id):
    # Active public streaming API instances with direct proxy streams
    api_endpoints = [
        f"https://pipedapi.kavin.rocks/streams/{video_id}",
        f"https://api.piped.privacydev.net/streams/{video_id}",
        f"https://pipedapi.drgns.space/streams/{video_id}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    for ep in api_endpoints:
        try:
            req = urllib.request.Request(ep, headers=headers)
            with urllib.request.urlopen(req, timeout=7) as response:
                res_data = json.loads(response.read().decode())
                
                # Check for direct video streams (video + audio muxed)
                for stream in res_data.get("videoStreams", []):
                    if not stream.get("videoOnly") and stream.get("url"):
                        return stream["url"]
                
                # If no muxed stream, return HLS stream (.m3u8) which VLC plays natively
                if res_data.get("hls"):
                    return res_data["hls"]
        except Exception:
            continue

    # Fallback to pure googlevideo direct stream resolver
    return f"https://cf-ipfs.com/ipns/invidious.io/latest_version?id={video_id}&itag=18"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! YouTube link bhejiye, main VLC ke liye pure stream URL generate karunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()
    
    if not ("http://" in raw_text or "https://" in raw_text):
        await update.message.reply_text("Kripya valid YouTube video link bhejiye.")
        return

    video_id = extract_video_id(raw_text)
    if not video_id:
        await update.message.reply_text("Video ID detect nahi hua. Normal YouTube link bhejein.")
        return

    status_msg = await update.message.reply_text("VLC Playable Stream taiyar ho raha hai...")

    loop = asyncio.get_event_loop()
    stream_url = await loop.run_in_executor(None, get_vlc_direct_stream, video_id)

    reply_text = (
        f"🎬 **VLC Playable Stream URL:**\n\n"
        f"`{stream_url}`\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"▶️ **Play karne ke steps:**\n"
        f"1. Upar link par tap karke copy karein.\n"
        f"2. VLC app kholein -> **More** -> **New stream** par jayein.\n"
        f"3. Paste karke orange arrow dabayein."
    )
    await status_msg.edit_text(reply_text, parse_mode="Markdown")

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
