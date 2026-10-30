import os
import asyncio
import logging
import urllib.parse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "KSR YouTube VLC Player Bot online hai! Link bhejiye direct VLC stream pane ke liye."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya valid YouTube video link bhejiye.")
        return

    status_msg = await update.message.reply_text("Server stream link extract kar raha hai...")

    # yt-dlp with cookies on hosting server
    cmd = [
        "yt-dlp",
        "--no-cache-dir",
        "--cookies", "cookies.txt",
        "-f", "best[ext=mp4]/18/best",
        "-g",
        url
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode().strip()

        if output.startswith("http"):
            stream_url = output.split('\n')[0]
            reply_text = (
                f"🎬 **VLC Playable Stream URL:**\n\n"
                f"`{stream_url}`\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"▶️ **Play karne ka tareeqa:**\n"
                f"1. Upar wale link par tap karke copy karein.\n"
                f"2. VLC app -> **More** -> **New stream** par paste karein.\n"
                f"3. Play dabayein, video server stream se chalegi."
            )
            await status_msg.edit_text(reply_text, parse_mode="Markdown")
        else:
            logging.error(f"yt-dlp stderr: {stderr.decode()}")
            await status_msg.edit_text("Error: Stream extract nahi ho saki. Cookies file refresh karke check karein.")

    except asyncio.TimeoutError:
        proc.kill()
        await status_msg.edit_text("Server timeout ho gaya.")
    except Exception as e:
        await status_msg.edit_text(f"Error: {str(e)}")

def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN nahi mila!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("KSR Bot running on FadeHost...")
    app.run_polling()

if __name__ == "__main__":
    main()
