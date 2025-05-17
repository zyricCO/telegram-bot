import os
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from telegram import Update

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=TOKEN)

NAME, EMAIL, PHONE = range(3)

dispatcher = Dispatcher(bot, None, workers=0)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! What is your full name?")
    return NAME

def get_name(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text
    update.message.reply_text("Thanks! Now, what's your email?")
    return EMAIL

def get_email(update: Update, context: CallbackContext):
    context.user_data['email'] = update.message.text
    update.message.reply_text("Lastly, your phone number?")
    return PHONE

def get_phone(update: Update, context: CallbackContext):
    context.user_data['phone'] = update.message.text
    summary = f"New Registration:\nName: {context.user_data['name']}\nEmail: {context.user_data['email']}\nPhone: {context.user_data['phone']}"
    update.message.reply_text("Thank you! Your data has been recorded.")
    context.bot.send_message(chat_id=1841079821, text=summary)
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Cancelled.")
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
        EMAIL: [MessageHandler(Filters.text & ~Filters.command, get_email)],
        PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

dispatcher.add_handler(conv_handler)

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(port=5000)