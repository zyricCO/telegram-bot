import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, 
    Filters, ConversationHandler, CallbackContext
)
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db
import re

# ===== YOUR CONFIG (Replace with env vars in production!) =====
BOT_TOKEN = "7968587228:AAFGSue0OxSI7Yh51eLBuz9rYwetdQX7-xY"  # From BotFather
ADMIN_ID = "1841079821"  # Your Telegram User ID

# Firebase Config (Realtime Database)
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyC9yCEe4a9KC0Ph64gMkrDn_Cfah0TxlMw",
    "authDomain": "swiftgain.firebaseapp.com",
    "databaseURL": "https://swiftgain-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "swiftgain",
    "storageBucket": "swiftgain.firebasestorage.app",
    "messagingSenderId": "751911092919",
    "appId": "1:751911092919:web:bd0ab90ca8b4432f0d4332"
}

# Initialize Firebase (Realtime DB)
cred = credentials.Certificate("serviceAccountKey.json")  # Download from Firebase Console
firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_CONFIG['databaseURL']
})
ref = db.reference('kyc_submissions')  # Root path for KYC data

# ===== BOT SETUP =====
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)

# States
CHOOSING, LOGIN_USERNAME, LOGIN_PASSWORD, KYC_NAME, KYC_EMAIL, KYC_PHONE = range(6)

# --- Helper Functions ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_phone(phone):
    return re.match(r"^\+?[\d\s-]{7,}$", phone)

# --- Menu & Handlers ---
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
        query.edit_message_text(
            "**Zyricco Services:**\n"
            "- AI Indicator: Real-time trend detection\n"
            "- GainX: Earn up to 12% daily\n"
            "- Funded Accounts: Trade with Zyricco capital\n"
            "- Account Management: Let our pros grow your account\n"
            "- AI Signals: Smart trading insights from our AI\n\n"
            "Contact support for more info.",
            parse_mode='Markdown'
        )
        return main_menu(update, context)
    elif query.data == 'support':
        query.edit_message_text("For support, contact us on Telegram: @zyricco_support")
        return main_menu(update, context)
    elif query.data == 'cancel':
        query.edit_message_text("Goodbye!")
        return ConversationHandler.END

# --- KYC Flow (Firebase Realtime DB) ---
def kyc_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("Email address?")
    return KYC_EMAIL

def kyc_email(update: Update, context: CallbackContext) -> int:
    email = update.message.text
    if not is_valid_email(email):
        update.message.reply_text("❌ Invalid email. Try again.")
        return KYC_EMAIL
    context.user_data['email'] = email
    update.message.reply_text("Phone number? (e.g., +1234567890)")
    return KYC_PHONE

def kyc_phone(update: Update, context: CallbackContext) -> int:
    phone = update.message.text
    if not is_valid_phone(phone):
        update.message.reply_text("❌ Invalid phone. Use format: +1234567890")
        return KYC_PHONE

    # Save to Firebase Realtime DB
    user_data = {
        "name": context.user_data['name'],
        "email": context.user_data['email'],
        "phone": phone,
        "chat_id": update.message.chat_id,
        "timestamp": datetime.now().isoformat()
    }
    ref.push().set(user_data)  # Stores under a unique key

    update.message.reply_text("✅ KYC submitted! We'll contact you soon.")
    context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"New KYC:\nName: {user_data['name']}\nEmail: {user_data['email']}\nPhone: {user_data['phone']}"
    )
    return main_menu(update, context)

# --- Timeout & Cancel ---
def timeout(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("⌛ Session timed out. Type /start to begin again.")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Action cancelled.")
    return main_menu(update, context)

# --- Conversation Handler ---
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
    fallbacks=[
        CommandHandler('cancel', cancel),
        MessageHandler(Filters.all, timeout)
    ],
    conversation_timeout=timedelta(minutes=5),  # 5-minute timeout
)

dispatcher.add_handler(conv_handler)

# --- Webhook ---
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)