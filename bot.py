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

def get_stream_from_piped(video_id):
    # Piped API endpoints jo datacenter IP restrictions ko bypass karte hain
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.private.coffee",
        "https://pipedapi.tokhmi.xyz"
    ]
    for inst in instances:
        try:
            req_url = f"{inst}/streams/{video_id}"
            req = urllib.request.Request(
                req_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode())
                # Combined video streams check karein
                streams = data.get("videoStreams", [])
                for s in streams:
                    if not s.get("videoOnly") and s.get("url"):
                        return s.get("url")
                # HLS stream link (VLC mein live aur video dono smoothly play hoti hain)
                if data.get("hls"):
                    return data.get("hls")
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

    direct_url = None

    # Step 1: yt-dlp with android_vr (VR client par YouTube koi bot sign-in nahi maangta)
    try:
        cmd = [
            "yt-dlp",
            "--no-cache-dir",
            "--extractor-args", "youtube:player_client=android_vr,mweb",
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
        logging.error(f"yt-dlp VR error: {e}")

    # Step 2: Fallback to Piped API agar yt-dlp block ho
    if not direct_url:
        video_id = extract_video_id(url)
        if video_id:
            try:
                loop = asyncio.get_event_loop()
                direct_url = await loop.run_in_executor(None, get_stream_from_piped, video_id)
            except Exception as e:
                logging.error(f"Piped fallback error: {e}")

    # Result response
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
            "Video stream extract nahi ho saka. Kripya thodi der baad dobara koshish karein ya doosra link bhejein."
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
