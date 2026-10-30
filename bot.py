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
        # Android client bypasses most cloud bot-blocks
        cmd = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android,web",
            "--no-warnings",
            "-g",
            "-f", "b/best",
            url
        ]
        
        # Agar cookies file maujood hai to include karein
        if os.path.exists("cookies.txt"):
            cmd.extend(["--cookies", "cookies.txt"])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 45 second ka timeout taaki stuck na ho
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=45)
        direct_url = stdout.decode().strip()

        if direct_url.startswith("http"):
            # Multiple stream URLs aane par pehla/combined handle karein
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
            # Agar koi error message ho to dikhayein
            clean_err = err.split('\n')[-1] if err else "Stream link generate nahi ho paya."
            await status_msg.edit_text(f"Error aayi:\n`{clean_err}`", parse_mode="Markdown")

    except asyncio.TimeoutError:
        await status_msg.edit_text("Request timed out! Server ne bohot samay lagaya.")
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
