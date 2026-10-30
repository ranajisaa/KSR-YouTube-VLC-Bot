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
        process = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", "cookies.txt",
            "-g",
            "-f", "b",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            direct_url = stdout.decode().strip()
            reply_text = (
                f"**Stream Link:**\n`{direct_url}`\n\n"
                "**VLC mein chalane ke liye:**\n"
                "1. VLC app kholein.\n"
                "2. 'More' -> 'New stream' par jayein.\n"
                "3. Ye URL paste karke play dabayein."
            )
            await status_msg.edit_text(reply_text, parse_mode="Markdown")
        else:
            err = stderr.decode().strip()
            await status_msg.edit_text(f"Error aayi:\n`{err}`", parse_mode="Markdown")

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
