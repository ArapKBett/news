import asyncio
import schedule
import time
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
import discord
from discord.ext import commands
from news_fetcher import NewsFetcher
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID

# Initialize Telegram bot application
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Initialize Discord bot
discord_bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

# Initialize NewsFetcher
news_fetcher = NewsFetcher()

# Telegram command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 Welcome to the News Bot!\n"
        "I fetch the latest news on cybersecurity, cryptocurrency, and forex.\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Available Commands:\n"
        "/start - Get a welcome message\n"
        "/help - List all commands\n"
        "/cybersecurity - Get latest cybersecurity news\n"
        "/cryptocurrency - Get latest cryptocurrency news\n"
        "/forex - Get latest forex news\n"
        "/allnews - Get news for all topics"
    )

async def cybersecurity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await news_fetcher.fetch_news("cybersecurity")
    messages = news_fetcher.format_news({"cybersecurity": articles})
    for message in messages:
        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

async def cryptocurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await news_fetcher.fetch_news("cryptocurrency")
    messages = news_fetcher.format_news({"cryptocurrency": articles})
    for message in messages:
        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

async def forex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = await news_fetcher.fetch_news("forex")
    messages = news_fetcher.format_news({"forex": articles})
    for message in messages:
        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

async def allnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news_by_topic = await news_fetcher.get_all_news()
    messages = news_fetcher.format_news(news_by_topic)
    for message in messages:
        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

# Scheduled posting functions
async def post_to_telegram(messages):
    telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for message in messages:
        try:
            await telegram_bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except TelegramError as e:
            print(f"Error posting to Telegram: {e}")

async def post_to_discord(messages):
    channel = discord_bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("Discord channel not found")
        return
    for message in messages:
        try:
            if len(message) > 2000:
                message = message[:1997] + "..."
            await channel.send(message)
        except Exception as e:
            print(f"Error posting to Discord: {e}")

async def fetch_and_post_news():
    print("Fetching news...")
    news_by_topic = await news_fetcher.get_all_news()
    messages = news_fetcher.format_news(news_by_topic)
    if messages:
        await post_to_telegram(messages)
        await post_to_discord(messages)
        print("News posted successfully")
    else:
        print("No news to post")

# Schedule news fetching every hour
schedule.every(1).hours.do(lambda: asyncio.run(fetch_and_post_news()))

# Discord bot event
@discord_bot.event
async def on_ready():
    print(f"Discord bot logged in as {discord_bot.user}")

# Main function to run both bots
async def run_bots():
    # Add Telegram command handlers
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("cybersecurity", cybersecurity))
    telegram_app.add_handler(CommandHandler("cryptocurrency", cryptocurrency))
    telegram_app.add_handler(CommandHandler("forex", forex))
    telegram_app.add_handler(CommandHandler("allnews", allnews))

    # Start Telegram bot polling
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

    # Start Discord bot
    discord_task = asyncio.create_task(discord_bot.start(DISCORD_BOT_TOKEN))

    # Run scheduler
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)  # Check schedule every minute

    # Cleanup (not typically reached)
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

if __name__ == "__main__":
    asyncio.run(run_bots())
