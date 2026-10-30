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
        "Namaste! Mujhe koi bhi YouTube video ya live stream link bhejiye, main aapko direct VLC play link generate karke dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya ek valid URL bhejiye.")
        return

    status_msg = await update.message.reply_text("Stream link nikal raha hoon, thoda intezar karein...")

    try:
        # TV client cloud datacenter IPs par sign-in block nahi karta
        cmd = [
            "yt-dlp",
            "--no-cache-dir",
            "--extractor-args", "youtube:player_client=tv,android_creator",
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
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=40)
        direct_url = stdout.decode().strip()

        if direct_url.startswith("http"):
            stream_link = direct_url.split('\n')[0]
            reply_text = (
                f"**Stream Link:**\n`{stream_link}`\n\n"
                "**VLC mein chalane ke liye:**\n"
                "1. VLC app kholein.\n"
                "2. 'More' -> 'New stream' par jayein.\n"
                "3. Ye URL paste karke play dabayein."
            )
            await status_msg.edit_text(reply_text, parse_mode="Markdown")
        else:
            err = stderr.decode().strip()
            err_line = [l for l in err.split('\n') if "ERROR" in l]
            clean_err = err_line[-1] if err_line else (err.split('\n')[-1] if err else "Stream link generate nahi ho saka.")
            await status_msg.edit_text(f"Error aayi:\n`{clean_err}`", parse_mode="Markdown")

    except asyncio.TimeoutError:
        try:
            process.kill()
        except:
            pass
        await status_msg.edit_text("Request timed out! YouTube ne response dene mein zyada samay liya.")
    except Exception as e:
        await status_msg.edit_text(f"Kuch gadbad hui: {str(e)}")

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
