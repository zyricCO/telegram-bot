from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import os

# States
CHOOSING, LOGIN_USERNAME, LOGIN_PASSWORD, KYC_NAME, KYC_EMAIL, KYC_PHONE, SUPPORT_CHOOSING_SERVICE = range(7)

# Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("No BOT_TOKEN environment variable found!")
bot = Bot(token=TOKEN)

# Flask app
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1, use_context=True)

# --- Services Definition ---
SERVICES_LIST = [
    ("AI Indicator", "support_ai_indicator", "Real-time trend detection"),
    ("GainX", "support_gainx", "Earn up to 12% daily"),
    ("Funded Accounts", "support_funded", "Trade with Zyricco capital"),
    ("Account Management", "support_acct_mgmt", "Let our pros grow your account"),
    ("AI Signals", "support_ai_signals", "Smart trading insights from our AI")
]

# --- Main Menu ---
def main_menu(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Login", callback_data='login')],
        [InlineKeyboardButton("Signup (KYC)", callback_data='signup')],
        [InlineKeyboardButton("Our Services", callback_data='services_overview')], # Changed callback_data
        [InlineKeyboardButton("Support", callback_data='support_start')],         # Changed callback_data
        [InlineKeyboardButton("Cancel Interaction", callback_data='cancel_interaction')], # Changed callback_data for clarity
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = "Welcome to Zyricco – Your AI-Powered Trading Partner!\n\nChoose an option:"

    if update.callback_query: # If called from a button press
        query = update.callback_query
        try:
            query.edit_message_text(text=welcome_text, reply_markup=reply_markup)
        except Exception as e: # Handle "message is not modified" error if text and markup are identical
            if "Message is not modified" in str(e):
                query.answer() # Acknowledge the callback
            else:
                print(f"Error editing message: {e}")
                # Fallback: send a new message if edit fails for other reasons
                if query.message:
                     context.bot.send_message(chat_id=query.message.chat_id, text=welcome_text, reply_markup=reply_markup)
    elif update.message: # If called from a command like /start
        update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return CHOOSING

# --- Handle Top-Level Button Clicks (CHOOSING State) ---
def handle_main_menu_buttons(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer() # Acknowledge the callback

    if query.data == 'login':
        context.bot.send_message(chat_id=query.message.chat_id, text="Please enter your username:")
        return LOGIN_USERNAME
    elif query.data == 'signup':
        context.bot.send_message(chat_id=query.message.chat_id, text="Let's begin your KYC registration.\nWhat is your full name?")
        return KYC_NAME
    elif query.data == 'services_overview':
        services_text_parts = ["**Zyricco Services:**"]
        for name, _, description in SERVICES_LIST:
            services_text_parts.append(f"- {name}: {description}")
        services_text_parts.append("\nFor more details or to get started with a service, please contact Support.")
        final_text = "\n".join(services_text_parts)

        keyboard = [[InlineKeyboardButton("« Back to Main Menu", callback_data='main_menu_show')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=final_text, parse_mode='Markdown', reply_markup=reply_markup)
        return CHOOSING # Stay in CHOOSING to handle 'main_menu_show'

    elif query.data == 'support_start':
        keyboard = []
        for service_name, callback_data_val, _ in SERVICES_LIST:
            keyboard.append([InlineKeyboardButton(service_name, callback_data=callback_data_val)])
        keyboard.append([InlineKeyboardButton("Other Issue", callback_data='support_other')])
        keyboard.append([InlineKeyboardButton("« Back to Main Menu", callback_data='main_menu_show')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "Please select the service you need support for, or choose 'Other Issue':",
            reply_markup=reply_markup
        )
        return SUPPORT_CHOOSING_SERVICE

    elif query.data == 'cancel_interaction':
        query.edit_message_text("Action cancelled. Goodbye!")
        return ConversationHandler.END

    elif query.data == 'main_menu_show': # Generic callback to show main menu
        return main_menu(update, context)

    return CHOOSING # Default return if no specific transition


# --- Handle Support Service Selection (SUPPORT_CHOOSING_SERVICE State) ---
def handle_support_service_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    chosen_service_callback = query.data

    if chosen_service_callback == 'main_menu_show':
        return main_menu(update, context)

    service_name_display = "the selected service" # Default
    if chosen_service_callback == 'support_other':
        service_name_display = "your query"
    else:
        for name, cb_data, _ in SERVICES_LIST:
            if cb_data == chosen_service_callback:
                service_name_display = name
                break

    support_message = (
        f"Thank you for reaching out regarding {service_name_display}.\n\n"
        "Please be patient. One of our customer care executives will assist you soon.\n\n"
        "You will be contacted via Telegram by @zyricco_support or an assigned agent." # Added clarification
    )
    # Notify admin (optional, but good for support requests)
    admin_notification_text = f"Support Request: User {query.from_user.username} (ID: {query.from_user.id}) needs help with: {service_name_display}"
    try:
        context.bot.send_message(chat_id=1841079821, text=admin_notification_text) # Your admin ID
    except Exception as e:
        print(f"Failed to send support notification to admin: {e}")


    keyboard = [[InlineKeyboardButton("« Main Menu", callback_data='main_menu_show')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=support_message, reply_markup=reply_markup)

    return CHOOSING # After showing the message, allow going back to main menu via CHOOSING state


# --- Login Flow ---
def login_username(update: Update, context: CallbackContext) -> int:
    context.user_data['username'] = update.message.text
    update.message.reply_text("Now, please enter your password:")
    return LOGIN_PASSWORD

def login_password(update: Update, context: CallbackContext) -> int:
    # password = update.message.text # You'd typically validate this
    # For now, always fail as per original logic
    update.message.reply_text(
        "Login failed: Incorrect username or password. Please try again or contact support."
    )
    return main_menu(update, context)


# --- Signup (KYC) Flow ---
def kyc_name(update: Update, context: CallbackContext) -> int:
    context.user_data['kyc_name'] = update.message.text.strip()
    update.message.reply_text("Great! What is your email address?")
    return KYC_EMAIL

def kyc_email(update: Update, context: CallbackContext) -> int:
    context.user_data['kyc_email'] = update.message.text.strip()
    # Basic email validation (optional, can be more sophisticated)
    if '@' not in context.user_data['kyc_email'] or '.' not in context.user_data['kyc_email']:
        update.message.reply_text("That doesn't look like a valid email. Please enter a valid email address:")
        return KYC_EMAIL
    update.message.reply_text("And your phone number (e.g., +1234567890)?")
    return KYC_PHONE

def kyc_phone(update: Update, context: CallbackContext) -> int:
    context.user_data['kyc_phone'] = update.message.text.strip()
    user_info = context.user_data
    telegram_user = update.message.from_user
    summary = (
        f"🔔 New KYC Submission:\n\n"
        f"Telegram User: @{telegram_user.username} (ID: {telegram_user.id})\n"
        f"Full Name: {user_info.get('kyc_name', 'N/A')}\n"
        f"Email: {user_info.get('kyc_email', 'N/A')}\n"
        f"Phone: {user_info.get('kyc_phone', 'N/A')}"
    )
    update.message.reply_text(
        "Thank you! Your KYC information has been submitted successfully. "
        "We will review it and be in touch soon."
    )
    try:
        context.bot.send_message(chat_id=1841079821, text=summary)  # Your admin ID
    except Exception as e:
        print(f"Failed to send KYC summary to admin: {e}")
        update.message.reply_text("There was an issue notifying admin, but your submission is recorded.")

    return main_menu(update, context)

# --- Cancel Command (Fallback) ---
def cancel(update: Update, context: CallbackContext) -> int:
    if update.message:
        update.message.reply_text("Action cancelled. Returning to the main menu.")
    elif update.callback_query:
        query = update.callback_query
        query.answer()
        query.edit_message_text("Action cancelled. Returning to the main menu.")
    return main_menu(update, context) # Go back to main menu

# --- Conversation Handler Setup ---
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', main_menu), CommandHandler('menu', main_menu)],
    states={
        CHOOSING: [CallbackQueryHandler(handle_main_menu_buttons)],
        LOGIN_USERNAME: [MessageHandler(Filters.text & ~Filters.command, login_username)],
        LOGIN_PASSWORD: [MessageHandler(Filters.text & ~Filters.command, login_password)],
        KYC_NAME: [MessageHandler(Filters.text & ~Filters.command, kyc_name)],
        KYC_EMAIL: [MessageHandler(Filters.text & ~Filters.command, kyc_email)],
        KYC_PHONE: [MessageHandler(Filters.text & ~Filters.command, kyc_phone)],
        SUPPORT_CHOOSING_SERVICE: [CallbackQueryHandler(handle_support_service_choice)],
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
        CallbackQueryHandler(lambda u,c: main_menu(u,c) if u.callback_query.data == 'main_menu_show' else cancel(u,c)) # Ensure main_menu_show is handled in fallbacks too
        ],
    map_to_parent={ # Example if this were a nested conversation
        ConversationHandler.END: ConversationHandler.END,
        CHOOSING: CHOOSING
    }
)

dispatcher.add_handler(conv_handler)

# --- Flask Webhook Routes ---
@app.route("/webhook", methods=["POST"]) # Standard webhook path often uses /webhook
def webhook():
    try:
        json_update = request.get_json(force=True)
        update = Update.de_json(json_update, bot)
        dispatcher.process_update(update)
    except Exception as e:
        print(f"Error in webhook: {e}")
        # You might want to log the json_update here for debugging
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Zyricco Bot is running!", 200

# --- Run Flask App ---
if __name__ == "__main__":
    # Ensure the BOT_TOKEN is set before running
    if TOKEN is None:
        print("Error: BOT_TOKEN environment variable not set.")
        exit()
    port = int(os.environ.get("PORT", 8080)) # Changed default to 8080 often used by cloud platforms
    print(f"Starting Flask app on port {port}...")
    # For local development with ngrok or similar, you might set a webhook:
    # from telegram.utils.request import Request
    # req = Request(connect_timeout=0.5, read_timeout=1.0)
    # bot_instance = Bot(token=TOKEN, request=req)
    # bot_instance.set_webhook(url=f"YOUR_HTTPS_NGROK_URL/webhook") # Replace with your ngrok URL
    app.run(host='0.0.0.0', port=port, debug=True) # debug=True is useful for development
