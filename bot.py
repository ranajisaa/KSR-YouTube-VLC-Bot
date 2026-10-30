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

def fetch_working_vlc_link(video_id):
    # Tested, active Invidious instances jo directly playable formatStreams deti hain
    instances = [
        "https://invidious.jing.rocks",
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://iv.melmac.space"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for inst in instances:
        try:
            req_url = f"{inst}/api/v1/videos/{video_id}"
            req = urllib.request.Request(req_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode())
                
                # FormatStreams me direct playable video+audio mp4 URLs hote hain
                streams = data.get("formatStreams", [])
                if streams:
                    # Sabse best combined format URL return karein
                    for st in reversed(streams):
                        if st.get("url"):
                            return st["url"]
                
                # Agar formats na mile to HLS stream check karein
                if data.get("hlsContentUrl"):
                    return data["hlsContentUrl"]
        except Exception as e:
            logging.warning(f"Error on {inst}: {e}")
            continue

    # Secondary Gateway: Direct Piped Instance
    try:
        piped_req = urllib.request.Request(
            f"https://pipedapi.adminforge.de/streams/{video_id}",
            headers=headers
        )
        with urllib.request.urlopen(piped_req, timeout=5) as p_res:
            p_data = json.loads(p_res.read().decode())
            for stream in p_data.get("videoStreams", []):
                if not stream.get("videoOnly") and stream.get("url"):
                    return stream["url"]
    except Exception as e:
        logging.warning(f"Piped error: {e}")

    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Koi bhi YouTube link bhejiye, main VLC ke liye direct playable stream URL generate kar dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya ek valid YouTube URL bhejiye.")
        return

    video_id = extract_video_id(url)
    if not video_id:
        await update.message.reply_text("Video ID pehchan nahi paya. Valid link bhejiye.")
        return

    status_msg = await update.message.reply_text("VLC Playable Stream URL nikal raha hoon, kripya intezar karein...")

    loop = asyncio.get_event_loop()
    stream_url = await loop.run_in_executor(None, fetch_working_vlc_link, video_id)

    if stream_url:
        reply_text = (
            f"🎬 **VLC Playable Direct Stream URL:**\n\n"
            f"`{stream_url}`\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"▶️ **Play karne ka tarika:**\n"
            f"1. Upar link par tap karke copy karein.\n"
            f"2. VLC app kholein -> **More** -> **New stream** par jayein.\n"
            f"3. Paste karke play dabayein, video direct buffer hokar chalegi!"
        )
        await status_msg.edit_text(reply_text, parse_mode="Markdown")
    else:
        await status_msg.edit_text(
            "Stream extract nahi ho saki. Kripya 30 second baad dobara koshish karein."
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
