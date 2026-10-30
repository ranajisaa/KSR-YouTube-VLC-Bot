import os
import re
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 KSR YouTube VLC Player\n\n"
        "YouTube link bhejo, main stream URL nikaalunga."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    match = re.search(
        r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/\S+",
        text
    )

    if not match:
        await update.message.reply_text("❌ Valid YouTube link bhejo.")
        return

    url = match.group(0).rstrip(".,!?)]}")

    status = await update.message.reply_text("⏳ Stream URL nikaal raha hoon...")

    try:
        process = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--js-runtimes", "node",
            "--remote-components", "ejs:github",
            "-g",
            "-f", "b",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=90
        )

        if process.returncode != 0 or not stdout.strip():
            error = stderr.decode(errors="replace").strip()
            await status.edit_text(
                f"❌ yt-dlp error:\n{error[:2500]}"
            )
            return

        stream_url = stdout.decode().strip().splitlines()[0]

        await status.edit_text("✅ Stream URL ready!")
        await update.message.reply_text(
            stream_url,
            disable_web_page_preview=True
        )

    except asyncio.TimeoutError:
        await status.edit_text("⏳ Timeout! Dobara try karo.")

    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)[:2000]}")


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN set nahi hai.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
    )

    print("KSR Stream Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
