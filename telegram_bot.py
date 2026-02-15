import sys
import os
import logging
import asyncio

# Setup Path to include project root (parent of memora_os)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Check if we are inside memora_os or root
if os.path.basename(current_dir) == "memora_os":
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
else:
    sys.path.append(current_dir)

from memora_os.config import settings
from memora_os.pipeline.reflect.agent import ReflectAgent

# Telegram Import
try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
except ImportError:
    print("Error: 'python-telegram-bot' is not installed.")
    print("Run: pip install python-telegram-bot")
    sys.exit(1)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize Reflect Agent
print("Initializing Reflect Agent...")
reflect_agent = ReflectAgent()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start command handler
    """
    user = update.effective_user
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"👋 Hello {user.first_name}! I am MemoraOS.\n\nAsk me anything about your memories (emails, meetings, projects).\nExample: 'Who is Marcus?'"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles regular text messages by querying the Reflect Agent.
    """
    user_id = update.effective_user.id
    
    # Security Check (Optional)
    allowed_id = getattr(settings, 'TELEGRAM', {}).get('ALLOWED_USER_ID')
    if allowed_id and str(allowed_id) != "000000000" and str(user_id) != str(allowed_id):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⛔ Access Denied. Your User ID is not authorized."
        )
        return

    query = update.message.text
    if not query:
        return

    # Notify user we are thinking
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Query Graph (Synchronous call wrapped in executor if needed, but for prototype direct calls are okay if fast enough)
    # The ReflectAgent uses requests (blocking), so ideally we should run in thread.
    response = await asyncio.to_thread(reflect_agent.query, query)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response
    )

if __name__ == '__main__':
    # Load Token
    token = getattr(settings, 'TELEGRAM', {}).get('BOT_TOKEN')
    
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("❌ Error: Telegram Bot Token not set in settings.yaml")
        print("Please edit 'memora_os/config/settings.yaml' and add your token.")
        sys.exit(1)
        
    print(f"🤖 MemoraOS Telegram Bot Started! Listening...")
        
    application = ApplicationBuilder().token(token).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    
    application.run_polling()
