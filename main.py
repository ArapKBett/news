import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
import discord
from discord.ext import commands
from news_fetcher import NewsFetcher
from config import (TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID,
                    DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID)

# Initialize bots with proper intents
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Configure Discord intents properly
intents = discord.Intents.default()
intents.message_content = True  # Essential for reading message content
discord_bot = commands.Bot(command_prefix="!", intents=intents)

news_fetcher = NewsFetcher()

# ========== Telegram Handlers ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 Welcome to the News Bot!\n"
        "I fetch the latest news on cybersecurity, cryptocurrency, and forex.\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📋 Available Commands:\n"
        "/start - Get welcome message\n"
        "/help - List commands\n"
        "/cybersecurity - Cybersecurity news\n"
        "/cryptocurrency - Cryptocurrency news\n"
        "/forex - Forex news\n"
        "/allnews - All topics"
    )
    await update.message.reply_text(help_text)

async def handle_news_command(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    try:
        articles = await news_fetcher.fetch_news(topic)
        messages = news_fetcher.format_news({topic: articles})
        for msg in messages:
            await update.message.reply_text(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error fetching news: {str(e)}")

async def cybersecurity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_news_command(update, context, "cybersecurity")

async def cryptocurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_news_command(update, context, "cryptocurrency")

async def forex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_news_command(update, context, "forex")

async def allnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        news = await news_fetcher.get_all_news()
        messages = news_fetcher.format_news(news)
        for msg in messages:
            await update.message.reply_text(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error fetching news: {str(e)}")

# ========== Posting Functions ==========
async def post_to_telegram(messages):
    bot = telegram_app.bot
    for msg in messages:
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            await asyncio.sleep(1)
        except TelegramError as e:
            print(f"Telegram Error: {str(e)}")
        except Exception as e:
            print(f"Unexpected Telegram error: {str(e)}")

async def post_to_discord(messages):
    try:
        channel = await discord_bot.fetch_channel(DISCORD_CHANNEL_ID)
        for msg in messages:
            while len(msg) > 0:
                chunk = msg[:1900]
                msg = msg[1900:]
                await channel.send(chunk)
                await asyncio.sleep(1)
    except discord.NotFound:
        print("❌ Discord channel not found")
    except discord.Forbidden:
        print("❌ Bot doesn't have channel permissions")
    except Exception as e:
        print(f"Discord Error: {str(e)}")

# ========== Scheduler ==========
async def fetch_and_post_news():
    print("🔄 Fetching news...")
    try:
        news = await news_fetcher.get_all_news()
        messages = news_fetcher.format_news(news)
        if messages:
            await post_to_telegram(messages)
            await post_to_discord(messages)
            print("✅ News posted successfully")
        else:
            print("⚠️ No news to post")
    except Exception as e:
        print(f"❌ News posting failed: {str(e)}")

async def scheduler():
    while True:
        await fetch_and_post_news()
        await asyncio.sleep(3600)  # 1 hour

# ========== Discord Setup ==========
@discord_bot.event
async def on_ready():
    print(f"🔗 Discord bot connected as {discord_bot.user}")

# ========== Main Function ==========
async def run_bots():
    # Add Telegram handlers
    handlers = [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("cybersecurity", cybersecurity),
        CommandHandler("cryptocurrency", cryptocurrency),
        CommandHandler("forex", forex),
        CommandHandler("allnews", allnews)
    ]
    for handler in handlers:
        telegram_app.add_handler(handler)

    # Start components
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

    # Start Discord bot
    discord_task = discord_bot.start(DISCORD_BOT_TOKEN)

    # Run tasks
    await asyncio.gather(
        discord_task,
        scheduler()
    )

    # Cleanup
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(run_bots())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    finally:
        asyncio.get_event_loop().close()
