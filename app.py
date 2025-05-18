from flask import Flask, request from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup from telegram.ext import (Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext) import os

Telegram Bot Token

TOKEN = os.environ.get("BOT_TOKEN") bot = Bot(token=TOKEN)

Admin Telegram ID

ADMIN_ID = 1841079821

Flask app

app = Flask(name) dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1, use_context=True)

States for conversation

CHOOSING, LOGIN_USERNAME, LOGIN_PASSWORD, KYC_NAME, KYC_EMAIL, KYC_PHONE = range(6)

In-memory KYC storage (for demo purposes)

kyc_submissions = []

Main Menu

def main_menu(update: Update, context: CallbackContext) -> int: keyboard = [ [InlineKeyboardButton("Login", callback_data='login')], [InlineKeyboardButton("Signup (KYC)", callback_data='signup')], [InlineKeyboardButton("Our Services", callback_data='services')], [InlineKeyboardButton("Support", callback_data='support')], [InlineKeyboardButton("Cancel", callback_data='cancel')] ] reply_markup = InlineKeyboardMarkup(keyboard)

if update.message:
    update.message.reply_text(
        "Welcome to *Zyricco* – Your AI-Powered Trading Partner!\n\nChoose an option:",
        reply_markup=reply_markup, parse_mode='Markdown')
elif update.callback_query:
    update.callback_query.edit_message_text(
        "Welcome to *Zyricco* – Your AI-Powered Trading Partner!\n\nChoose an option:",
        reply_markup=reply_markup, parse_mode='Markdown')
return CHOOSING

Handle Menu Buttons

def handle_buttons(update: Update, context: CallbackContext) -> int: query = update.callback_query query.answer()

if query.data == 'login':
    context.bot.send_message(chat_id=query.message.chat_id, text="Enter your username:")
    return LOGIN_USERNAME
elif query.data == 'signup':
    context.bot.send_message(chat_id=query.message.chat_id, text="Starting KYC...\nWhat is your full name?")
    return KYC_NAME
elif query.data == 'services':
    services_text = (
        "*Zyricco Services:*\n"
        "- AI Indicator: Smart trend detection\n"
        "- GainX: Earn up to 12% daily\n"
        "- Funded Accounts: Trade using Zyricco capital\n"
        "- Account Management: We grow your account\n"
        "- AI Signals: Smart trading alerts\n\n"
        "Message @zyricco_support for custom plans."
    )
    query.edit_message_text(services_text, parse_mode='Markdown')
    return CHOOSING
elif query.data == 'support':
    query.edit_message_text("Contact support via @zyricco_support")
    return CHOOSING
elif query.data == 'cancel':
    query.edit_message_text("Thank you for using Zyricco. Goodbye!")
    return ConversationHandler.END

Login Handlers

def login_username(update: Update, context: CallbackContext) -> int: context.user_data['username'] = update.message.text update.message.reply_text("Now enter your password:") return LOGIN_PASSWORD

def login_password(update: Update, context: CallbackContext) -> int: update.message.reply_text("Login failed: Incorrect username or password.") return main_menu(update, context)

KYC Handlers

def kyc_name(update: Update, context: CallbackContext) -> int: context.user_data['name'] = update.message.text update.message.reply_text("Thanks! Now your email address:") return KYC_EMAIL

def kyc_email(update: Update, context: CallbackContext) -> int: context.user_data['email'] = update.message.text update.message.reply_text("Finally, your phone number:") return KYC_PHONE

def kyc_phone(update: Update, context: CallbackContext) -> int: context.user_data['phone'] = update.message.text user = context.user_data summary = ( f"Name: {user['name']}\nEmail: {user['email']}\nPhone: {user['phone']}" ) kyc_submissions.append(summary) update.message.reply_text("KYC submitted. We'll review and contact you soon.") context.bot.send_message(chat_id=ADMIN_ID, text=f"New KYC Submission:\n{summary}") return main_menu(update, context)

Admin Panel

def admin_panel(update: Update, context: CallbackContext): if update.effective_user.id != ADMIN_ID: update.message.reply_text("Access denied.") return

if not kyc_submissions:
    update.message.reply_text("No KYC submissions yet.")
else:
    message = "*KYC Submissions:*\n\n"
    for i, entry in enumerate(kyc_submissions, 1):
        message += f"{i}. {entry}\n\n"
    update.message.reply_text(message, parse_mode='Markdown')

Cancel Command

def cancel(update: Update, context: CallbackContext) -> int: update.message.reply_text("Operation cancelled.") return main_menu(update, context)

Webhook route

@app.route("/", methods=["POST"]) def webhook(): update = Update.de_json(request.get_json(force=True), bot) dispatcher.process_update(update) return "ok"

@app.route("/", methods=["GET"]) def home(): return "Zyricco Bot is live."

Handlers

conv_handler = ConversationHandler( entry_points=[CommandHandler('start', main_menu), CommandHandler('menu', main_menu)], states={ CHOOSING: [CallbackQueryHandler(handle_buttons)], LOGIN_USERNAME: [MessageHandler(Filters.text & ~Filters.command, login_username)], LOGIN_PASSWORD: [MessageHandler(Filters.text & ~Filters.command, login_password)], KYC_NAME: [MessageHandler(Filters.text & ~Filters.command, kyc_name)], KYC_EMAIL: [MessageHandler(Filters.text & ~Filters.command, kyc_email)], KYC_PHONE: [MessageHandler(Filters.text & ~Filters.command, kyc_phone)], }, fallbacks=[CommandHandler('cancel', cancel)] )

dispatcher.add_handler(conv_handler) dispatcher.add_handler(CommandHandler("admin

