import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "KSR YouTube VLC Player Bot online hai! YouTube video link bhejiye."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya valid YouTube video link bhejiye.")
        return

    status_msg = await update.message.reply_text("Stream extract ho rahi hai...")

    # Cookies check karein
    has_cookies = os.path.exists("cookies.txt") and os.path.getsize("cookies.txt") > 0

    cmd = [
        "yt-dlp",
        "--no-cache-dir",
        "--no-check-certificates",
        "-f", "best[ext=mp4]/18/best",
        "-g"
    ]

    if has_cookies:
        cmd.extend(["--cookies", "cookies.txt"])
    else:
        # Web hosting IP block bypass karne ke liye Android TV embedded client
        cmd.extend(["--extractor-args", "youtube:player_client=android_embedded,tv"])

    cmd.append(url)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=35)
        output = stdout.decode().strip()

        if output.startswith("http"):
            stream_url = output.split('\n')[0]
            reply_text = (
                f"🎬 **VLC Playable Stream URL:**\n\n"
                f"`{stream_url}`\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"▶️ **Play karne ka tareeqa:**\n"
                f"1. Upar link par tap karke copy karein.\n"
                f"2. VLC app kholein -> **More** -> **New stream** par paste karein.\n"
                f"3. Play dabayein."
            )
            await status_msg.edit_text(reply_text, parse_mode="Markdown")
        else:
            err_text = stderr.decode()
            logging.error(f"yt-dlp error: {err_text}")
            await status_msg.edit_text("Stream extract nahi ho saki. Hosting server par cookies setup karein ya dusra link check karein.")

    except asyncio.TimeoutError:
        try:
            proc.kill()
        except:
            pass
        await status_msg.edit_text("Server timeout ho gaya. 30 second baad dobara koshish karein.")
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
