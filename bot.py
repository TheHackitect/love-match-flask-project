import logging
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Chat, ChatMember, ChatMemberUpdated, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ChatMemberHandler
from flask import Flask
from models import db, Participant  # Import the db instance from models
from telegram.constants import ParseMode
from typing import Optional, Tuple

# Initialize Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure the database is initialized with the app context
with app.app_context():
    db.init_app(app)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Website URL
WEBSITE_URL = "https://queerhtxsingles.com/"
BOT_URL = "https://t.me/queerhtxsinglesBot"


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    args = context.args

    with app.app_context():
        existing_user = Participant.query.filter_by(telegram_user_id=user.id).first()

    if args and args[0] == "GetId":
        await update.message.reply_text(f"Your User ID is: {user.id} 😊")
        return

    if existing_user:
        await update.message.reply_html(
            f"Welcome back, {existing_user.name}! 🎉\n"
            f"Username: {existing_user.username}\n"
            f"Email: {existing_user.email}\n"
            f"Dating Preference: {existing_user.dating_preference}\n"
            f"Bio: {existing_user.bio}\n"
            f"📅 Joined on: {existing_user.time.strftime('%Y-%m-%d')}"
        )
    else:
        await update.message.reply_html(
            f"Hi {user.mention_html()}! Welcome to QueerHTX Singles! 🌈✨\n"
            "Please register on our website to get started.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Register Here", url=WEBSITE_URL)]
            ])
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help! How can we assist you? 😊")

# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Echo the user message."""
#     await update.message.reply_text(update.message.text)



async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    await update.effective_chat.send_message(
                f"Welcome, {member_name}! 🎉\n\n"
                
                f"To participate, Please send a message here\n"
                f"<a href='{BOT_URL}'>Send a message to bot</a> 🌈\n\n"

                "Please register on our website to join the fun!\n"
                f"<a href='{WEBSITE_URL}'>Register Here</a> 🌈\n\n",
            parse_mode=ParseMode.HTML,
        )

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7478636127:AAH628CWYez8rfiJ1S26bqpLhvAvikPf3jw").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Welcome new users to the group chat
    # application.add_handler(ChatMemberHandler(welcome_chat_member, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
