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
        "Namaste! Koi bhi YouTube link bhejiye, main VLC ke liye direct playable stream URL nikal kar dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya ek valid YouTube link bhejiye.")
        return

    status_msg = await update.message.reply_text("VLC Playable Stream URL nikal raha hoon, thoda intezar karein...")

    # YouTube Studio Creator Client (Datacenter IP par bot-block bypass karta hai)
    cmd = [
        "yt-dlp",
        "--no-cache-dir",
        "--no-check-certificates",
        "--extractor-args", "youtube:player_client=android_creator,web_creator",
        "-f", "best[ext=mp4]/18/b/best",
        "-g",
        url
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=40)
        output = stdout.decode().strip()

        if output.startswith("http"):
            stream_url = output.split('\n')[0]
            reply_text = (
                f"🎬 **VLC Playable Stream URL:**\n\n"
                f"`{stream_url}`\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"▶️ **Play karne ka tareeqa:**\n"
                f"1. Upar diye gaye link par tap karke copy karein.\n"
                f"2. VLC app kholein -> **More** -> **New stream** par jayein.\n"
                f"3. Link paste karke play karein."
            )
            await status_msg.edit_text(reply_text, parse_mode="Markdown")
        else:
            err_msg = stderr.decode().strip()
            logging.error(f"yt-dlp error: {err_msg}")
            # Secondary fallback: TV Embedded Client
            cmd_tv = [
                "yt-dlp",
                "--no-cache-dir",
                "--extractor-args", "youtube:player_client=tv_embedded",
                "-f", "18/b/best",
                "-g",
                url
            ]
            proc_tv = await asyncio.create_subprocess_exec(
                *cmd_tv,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_tv, _ = await asyncio.wait_for(proc_tv.communicate(), timeout=30)
            output_tv = stdout_tv.decode().strip()

            if output_tv.startswith("http"):
                stream_url = output_tv.split('\n')[0]
                reply_text = (
                    f"🎬 **VLC Playable Stream URL:**\n\n"
                    f"`{stream_url}`\n\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"▶️ **Play karne ka tareeqa:**\n"
                    f"1. Upar link par tap karke copy karein.\n"
                    f"2. VLC app kholein -> **More** -> **New stream** par jayein.\n"
                    f"3. Paste karke play dabayein."
                )
                await status_msg.edit_text(reply_text, parse_mode="Markdown")
            else:
                await status_msg.edit_text("Stream link extract nahi ho saka. Kripya doosra link try karein.")

    except asyncio.TimeoutError:
        try:
            process.kill()
        except:
            pass
        await status_msg.edit_text("Server timeout ho gaya. Kripya 30 second baad dobara try karein.")
    except Exception as e:
        await status_msg.edit_text(f"Error: {str(e)}")

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
