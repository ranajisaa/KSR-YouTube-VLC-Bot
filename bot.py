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

def fetch_stream_tunnel(url, video_id):
    # 1. Cobalt Tunnel Nodes (Direct proxied media stream - NO IP Lock)
    cobalt_nodes = [
        "https://cobalt-api.kwiatekm.tokyo/",
        "https://capi.wuk.sh/",
        "https://cobalt.canine.tools/",
        "https://dl.khub.win/",
        "https://cobalt.shyim.net/",
        "https://cobalt.slpy.one/"
    ]
    
    payload = json.dumps({"url": url}).encode('utf-8')
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for node in cobalt_nodes:
        try:
            req = urllib.request.Request(node, data=payload, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get("url"):
                    return data["url"]
                if data.get("picker") and len(data["picker"]) > 0:
                    return data["picker"][0].get("url")
        except Exception as e:
            logging.warning(f"Cobalt error on {node}: {e}")

    # 2. Piped Proxy Backends (Fallback: Reverse-proxied video streams)
    if video_id:
        piped_nodes = [
            f"https://pipedapi.adminforge.de/streams/{video_id}",
            f"https://api.piped.private.coffee/streams/{video_id}",
            f"https://pipedapi.tokhmi.xyz/streams/{video_id}",
            f"https://piped-api.lunar.icu/streams/{video_id}"
        ]
        for p_url in piped_nodes:
            try:
                p_req = urllib.request.Request(p_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(p_req, timeout=6) as p_resp:
                    p_data = json.loads(p_resp.read().decode('utf-8'))
                    for stream in p_data.get("videoStreams", []):
                        if not stream.get("videoOnly") and stream.get("url"):
                            return stream["url"]
                    if p_data.get("hls"):
                        return p_data["hls"]
            except Exception as e:
                logging.warning(f"Piped error on {p_url}: {e}")

    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Koi bhi YouTube link bhejiye, main VLC ke liye direct playable stream URL generate karke dunga."
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

    status_msg = await update.message.reply_text("VLC Playable Direct Stream URL generate ho raha hai, intezar karein...")

    loop = asyncio.get_event_loop()
    stream_url = await loop.run_in_executor(None, fetch_stream_tunnel, url, video_id)

    if stream_url and stream_url.startswith("http"):
        reply_text = (
            f"🎬 **VLC Direct Playable Stream URL:**\n\n"
            f"`{stream_url}`\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"▶️ **Play karne ka tarika:**\n"
            f"1. Upar link par ek baar tap karke copy karein.\n"
            f"2. VLC app kholein -> **More** -> **New stream** par jayein.\n"
            f"3. Paste karke play dabayein, video direct stream ho jayegi!"
        )
        await status_msg.edit_text(reply_text, parse_mode="Markdown")
    else:
        await status_msg.edit_text(
            "Stream link generate nahi ho saka. Kripya 1 minute baad dobara koshish karein."
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
