import asyncio
import schedule
import time
from telegram import Bot
from telegram.error import TelegramError
import discord
from discord.ext import commands
from news_fetcher import NewsFetcher
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID

# Initialize Telegram bot
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Initialize Discord bot
discord_bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

# Initialize NewsFetcher
news_fetcher = NewsFetcher()

async def post_to_telegram(messages):
    for message in messages:
        try:
            await telegram_bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
        except TelegramError as e:
            print(f"Error posting to Telegram: {e}")

async def post_to_discord(messages):
    channel = discord_bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("Discord channel not found")
        return
    for message in messages:
        try:
            # Discord has a 2000-character limit per message
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

@discord_bot.event
async def on_ready():
    print(f"Discord bot logged in as {discord_bot.user}")

async def run_bots():
    # Start Discord bot
    discord_task = asyncio.create_task(discord_bot.start(DISCORD_BOT_TOKEN))
    
    # Run scheduler
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)  # Check schedule every minute

if __name__ == "__main__":
    asyncio.run(run_bots())
