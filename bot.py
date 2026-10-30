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
        "Namaste! Koi bhi YouTube link bhejiye, main direct VLC playable googlevideo stream link generate karke dunga."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Kripya ek valid URL bhejiye.")
        return

    status_msg = await update.message.reply_text("VLC Direct Stream URL nikal raha hoon, kripya intezar karein...")

    cmd = [
        "yt-dlp",
        "--no-cache-dir",
        "--extractor-args", "youtube:player_client=ios",
        "-g",
        "-f", "18/b/best",
        url
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=35)
        raw_output = stdout.decode().strip()

        if raw_output.startswith("http"):
            stream_link = raw_output.split('\n')[0]
            reply_text = (
                f"✅ **VLC Direct Stream URL:**\n\n"
                f"`{stream_link}`\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"▶️ **Play karne ke liye:**\n"
                f"1. Upar wale link par tap karke copy karein.\n"
                f"2. VLC app mein **More** -> **New stream** par paste karein aur play dabayein."
            )
            await status_msg.edit_text(reply_text, parse_mode="Markdown")
        else:
            # Fallback agar iOS client fail ho
            cmd_fallback = [
                "yt-dlp",
                "--no-cache-dir",
                "--extractor-args", "youtube:player_client=android",
                "-g",
                "-f", "18/b/best",
                url
            ]
            proc_fb = await asyncio.create_subprocess_exec(
                *cmd_fallback,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            out_fb, _ = await asyncio.wait_for(proc_fb.communicate(), timeout=35)
            fb_url = out_fb.decode().strip()
            if fb_url.startswith("http"):
                stream_link = fb_url.split('\n')[0]
                reply_text = (
                    f"✅ **VLC Direct Stream URL:**\n\n"
                    f"`{stream_link}`\n\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"▶️ **Play karne ke liye:**\n"
                    f"1. Upar wale link par tap karke copy karein.\n"
                    f"2. VLC app mein **More** -> **New stream** par paste karein aur play dabayein."
                )
                await status_msg.edit_text(reply_text, parse_mode="Markdown")
            else:
                await status_msg.edit_text("Stream extract nahi ho saki. Kripya doosra link try karein.")

    except asyncio.TimeoutError:
        try:
            process.kill()
        except:
            pass
        await status_msg.edit_text("Request timeout ho gayi. Kripya dobara try karein.")
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
