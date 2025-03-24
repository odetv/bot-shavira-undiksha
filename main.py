import asyncio
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from aiohttp import ClientSession


# Environment variable
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TOKEN_BOT_TELEGRAM")
API_URL = os.getenv("API_SHAVIRA_URL")
API_AUTH_TOKEN = os.getenv("API_SHAVIRA_AUTHTOKEN")


# Logging
logging.basicConfig(level=logging.INFO)


# Send a question to the chatbot API and returns the answer
async def call_chat_api(question: str) -> str:
    headers = {"Authorization": f"Bearer {API_AUTH_TOKEN}", "Content-Type": "application/json"}
    payload = {"question": question}
    async with ClientSession() as session:
        try:
            async with session.post(API_URL, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("data", [{}])[0].get("answer", "Maaf, saya tidak dapat memahami pertanyaan Anda!")
        except Exception as e:
            logging.error(f"Error: {e}")
            return "Terjadi kesalahan saat menghubungi server. Coba lagi nanti!"


# Function to keep sending "typing..." until API response is received
async def keep_typing(chat_id, bot):
    try:
        while True:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass


# Handler command /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Salam Harmoni🙏\nAku Shavira, ada yang bisa dibantu?")


async def handle_chat(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    chat_id = update.effective_chat.id
    typing_task = asyncio.create_task(keep_typing(chat_id, context.bot))
    bot_response = await call_chat_api(user_message)
    typing_task.cancel()
    await update.message.reply_text(bot_response, parse_mode="Markdown")


# Handler error
async def error_handler(update: object, context: CallbackContext) -> None:
    logging.error(f"Update {update} caused error {context.error}")


# Configuration bot
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat))
app.add_error_handler(error_handler)


# Run bot
if __name__ == "__main__":
    logging.info("Bot is running...")
    app.run_polling()
