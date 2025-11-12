"""
Telegram Bot for Milk Sell Bot
Integrates the milk consultation chatbot with Telegram
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
from telegram.constants import ChatAction, ParseMode
from dotenv import load_dotenv
import os
import sys
import logging
from datetime import datetime

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.core.agent.client import AgentWithMCP
from src.utils.loader.mcp_loader import load_mcp_client
from jinja2 import Template
from src.core.memory.memory_manager import MemoryManager

load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Global bot components
agent = None
memory_manager = None
system_prompt = None

async def initialize_milk_bot():
    """Initialize the milk sell bot with MCP tools"""
    global agent, memory_manager, system_prompt
    
    try:
        logger.info("Initializing Milk Sell Bot...")
        
        # Load system prompt
        system_prompt = Template(open("src/module/milk_sell_bot/prompts/sql_query.j2").read()).render()
        
        # Initialize memory manager
        memory_manager = MemoryManager()
        
        # Load MCP clients
        logger.info("Loading MCP clients...")
        mcp_client = await load_mcp_client({
            "search_tools": {
                "transport": "streamable_http",
                "url": "http://localhost:9000/mcp"
            },
            "auto_sale_tools": {
                "transport": "streamable_http",
                "url": "http://localhost:9002/mcp"  
            },
        })
        
        tools = await mcp_client.get_tools()
        logger.info(f"✓ Loaded {len(tools)} MCP tools")
        
        # Initialize agent
        agent = AgentWithMCP(tools, system_prompt)
        logger.info("✓ Milk Sell Bot initialized successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize milk bot: {e}")
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_text = f"""
🍼 **Chào mừng {user.first_name} đến với Milk Sell Bot!**

Tôi là trợ lý AI chuyên tư vấn sữa cho trẻ em. Tôi có thể giúp bạn:

🔍 **Tìm kiếm sản phẩm** - Tìm sữa theo tên, thương hiệu
💰 **Lọc theo giá** - Tìm sữa phù hợp với ngân sách  
👶 **Tư vấn theo tuổi** - Gợi ý sữa phù hợp với độ tuổi
🏷️ **Sản phẩm khuyến mãi** - Xem sữa đang giảm giá
📊 **Thống kê** - Xem tổng quan database
🛒 **Đặt hàng** - Mua sản phẩm trực tiếp

**Hãy thử hỏi tôi:**
• "Tôi muốn tìm sữa Vinamilk"
• "Sữa nào rẻ nhất?"
• "Con tôi 15 tháng, sữa nào phù hợp?"
• "Có sữa nào đang giảm giá không?"
"""
    
    # Create quick action buttons
    keyboard = [
        [
            InlineKeyboardButton("🔍 Tìm sản phẩm", callback_data="search_products"),
            InlineKeyboardButton("💰 Sản phẩm rẻ", callback_data="cheap_products")
        ],
        [
            InlineKeyboardButton("🏷️ Giảm giá", callback_data="discounted"),
            InlineKeyboardButton("📊 Thống kê", callback_data="stats")
        ],
        [
            InlineKeyboardButton("👶 Tư vấn theo tuổi", callback_data="age_advice"),
            InlineKeyboardButton("🏢 Thương hiệu", callback_data="brands")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🆘 **Hướng dẫn sử dụng Milk Sell Bot**

**Các câu hỏi bạn có thể hỏi:**

🔍 **Tìm kiếm:**
• "Tôi muốn tìm sữa [tên thương hiệu]"
• "Có sữa [tên sản phẩm] không?"

💰 **Theo giá:**
• "Sữa nào rẻ nhất?"
• "Tôi muốn sữa dưới 200k"
• "Sữa từ 300k đến 500k"

👶 **Theo tuổi:**
• "Con tôi [X] tháng tuổi, sữa nào phù hợp?"
• "Sữa cho trẻ sơ sinh"
• "Sữa cho bé 2 tuổi"

🏷️ **Khuyến mãi:**
• "Có sữa nào đang giảm giá không?"
• "Sản phẩm khuyến mãi"

🛒 **Đặt hàng:**
• "Tôi muốn mua sản phẩm ID [số], số lượng [X]"
• "Đặt hàng [tên sản phẩm]"

📊 **Thông tin:**
• "Thống kê database"
• "Có những thương hiệu nào?"
• "Các loại sữa có sẵn"

**Lệnh bot:**
/start - Bắt đầu sử dụng bot
/help - Xem hướng dẫn này
/status - Kiểm tra trạng thái bot
"""
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    global agent, memory_manager
    
    if agent and memory_manager:
        status_text = """
✅ **Bot Status: ACTIVE**

🤖 Agent: Initialized
💾 Memory: Connected  
🔧 MCP Tools: Loaded
🗄️ Database: Connected

Bot sẵn sàng phục vụ! Hãy hỏi tôi về sữa nhé 🍼
"""
    else:
        status_text = """
❌ **Bot Status: NOT INITIALIZED**

Bot chưa được khởi tạo. Vui lòng liên hệ admin.
"""
    
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    # Map button callbacks to questions
    button_questions = {
        "search_products": "Có những loại sữa nào?",
        "cheap_products": "Sữa nào rẻ nhất?",
        "discounted": "Có sữa nào đang giảm giá không?",
        "stats": "Cho tôi thống kê database",
        "age_advice": "Tư vấn sữa cho bé 12 tháng tuổi",
        "brands": "Có những thương hiệu nào?"
    }
    
    question = button_questions.get(query.data, "Xin chào!")
    
    # Process the question as if user typed it
    await process_message(query.message, question, query.from_user.id)

async def process_message(message, text: str, user_id: int):
    """Process user message with the milk bot"""
    global agent, memory_manager
    
    if not agent or not memory_manager:
        await message.reply_text(
            "Bot chưa được khởi tạo. Vui lòng thử lại sau hoặc liên hệ admin.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Show typing indicator
    await message.chat.send_action(ChatAction.TYPING)
    
    try:
        # Use user_id as both user_id and session_id for Telegram
        session_id = f"tg_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        # Get conversation history from memory
        conversation = memory_manager.get_memory_as_conversation(
            str(user_id), session_id, top_k=6
        )
        
        # Get response from agent
        response = await agent.run(conversation, text)
        
        # Save to memory
        memory_manager.save_memory(
            user_id=str(user_id),
            session_id=session_id,
            question=text,
            answer=str(response)  # Ensure response is string
        )
        
        # Send response to user
        # Split long messages if needed
        if len(response) > 4096:
            # Split into chunks
            chunks = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for chunk in chunks:
                await message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.reply_text(
            f"Xin lỗi, đã có lỗi xảy ra: {str(e)}\n\nVui lòng thử lại hoặc liên hệ admin."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"User {user.id} ({user.first_name}): {message_text}")
    
    await process_message(update.message, message_text, user.id)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "Đã có lỗi xảy ra. Vui lòng thử lại sau."
        )

def main():
    """Main function to run the Telegram bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Create application
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    logger.info("Starting Milk Sell Telegram Bot...")
    
    # Initialize the milk bot in a separate thread to avoid event loop conflicts
    async def pre_init():
        init_success = await initialize_milk_bot()
        if not init_success:
            logger.error("Failed to initialize milk bot. Bot will not work properly.")
    
    # Run initialization
    try:
        asyncio.get_event_loop().run_until_complete(pre_init())
    except RuntimeError:
        # If no event loop, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(pre_init())
        loop.close()
    
    # Run the bot
    logger.info("Telegram Bot is running...")
    logger.info("Press Ctrl+C to stop the bot")
    
    # Use the simpler run_polling method  
    try:
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

