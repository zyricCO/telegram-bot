from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import os

# States
NAME, EMAIL, PHONE = range(3)

# Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Flask app
app = Flask(__name__)

# Dispatcher setup
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1, use_context=True)

# Bot functions
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Welcome! What is your full name?")
    return NAME

def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("Thanks! Now, what's your email address?")
    return EMAIL

def get_email(update: Update, context: CallbackContext) -> int:
    context.user_data['email'] = update.message.text
    update.message.reply_text("Great! Lastly, please enter your phone number.")
    return PHONE

def get_phone(update: Update, context: CallbackContext) -> int:
    context.user_data['phone'] = update.message.text
    user_data = context.user_data
    summary = f"New Registration:\nName: {user_data['name']}\nEmail: {user_data['email']}\nPhone: {user_data['phone']}"
    update.message.reply_text("Thank you! Your data has been recorded.")
    context.bot.send_message(chat_id=1841079821, text=summary)
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Registration cancelled.")
    return ConversationHandler.END

# Add handlers
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
        EMAIL: [MessageHandler(Filters.text & ~Filters.command, get_email)],
        PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

dispatcher.add_handler(conv_handler)

# Webhook route
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Home route
@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(port=5000)