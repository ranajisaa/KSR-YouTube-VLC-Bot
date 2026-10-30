import os
import logging
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
        "👋 Namaste! KSR YouTube VLC Player Bot active hai.\n\n"
        "Koi bhi YouTube video link bhejiye, main VLC ke liye direct clean stream links taiyar kar dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()
    
    if not ("http://" in raw_text or "https://" in raw_text):
        await update.message.reply_text("⚠️ Kripya ek valid YouTube video link bhejiye.")
        return

    video_id = extract_video_id(raw_text)
    if not video_id:
        await update.message.reply_text("❌ Link se Video ID extract nahi ho saka. Kripya normal YouTube link bhejein.")
        return

    # 1. Clean Canonical Stream URL (VLC internal media engine ke liye sabse reliable)
    vlc_clean_stream = f"https://www.youtube.com/watch?v={video_id}"
    
    # 2. Direct Media Invidious Stream (Proxy routed)
    vlc_proxy_stream = f"https://inv.nadeko.net/latest_version?id={video_id}&itag=18"

    reply_text = (
        f"🎬 **KSR VLC Stream Ready!**\n\n"
        f"🔗 **Direct VLC Network Stream Link:**\n"
        f"`{vlc_clean_stream}`\n\n"
        f"⚡ **Alternate Proxy Stream Link:**\n"
        f"`{vlc_proxy_stream}`\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"▶️ **Play Karne Ka Tarika:**\n"
        f"1. Upar diye gaye pehle link (`{vlc_clean_stream}`) par ek baar tap karke copy karein.\n"
        f"2. VLC app kholein -> Neeche **More** -> **New stream** par jayein.\n"
        f"3. Link paste karke orange arrow (Play) dabayein.\n\n"
        f"💡 *VLC ise aapke mobile network se direct fetch karega, jisse na koi IP block aayega aur na 403 error.*"
    )

    await update.message.reply_text(reply_text, parse_mode="Markdown")

def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN environment variable nahi mila!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("KSR Stream Bot running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
