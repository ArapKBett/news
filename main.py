import asyncio
import logging
from telegram.ext import Application
import discord
from discord.ext import commands
from news_fetcher import NewsFetcher
from config import CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def post_updates(telegram_messages, discord_messages):
    try:
        # Telegram Posting
        tg_app = Application.builder().token(CONFIG["telegram"]["token"]).build()
        await tg_app.initialize()
        for msg in telegram_messages:
            await tg_app.bot.send_message(
                chat_id=CONFIG["telegram"]["channel"],
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

        # Discord Posting
        intents = discord.Intents.default()
        intents.message_content = True
        dc_bot = commands.Bot(command_prefix="!", intents=intents)
        
        @dc_bot.event
        async def on_ready():
            try:
                channel = await dc_bot.fetch_channel(CONFIG["discord"]["channel"])
                for msg in discord_messages:
                    await channel.send(msg)
            finally:
                await dc_bot.close()
        
        await dc_bot.start(CONFIG["discord"]["token"])
        
    except Exception as e:
        logger.error(f"Posting error: {str(e)}")
    finally:
        await tg_app.shutdown()

async def news_cycle():
    logger.info("Starting news collection...")
    fetcher = NewsFetcher()
    news_data = await fetcher.get_all_news()
    
    telegram_msgs = fetcher.format_for_platform(news_data, "telegram")
    discord_msgs = fetcher.format_for_platform(news_data, "discord")
    
    if telegram_msgs and discord_msgs:
        logger.info(f"Posting {len(telegram_msgs)} updates")
        await post_updates(telegram_msgs, discord_msgs)
    else:
        logger.warning("No news to post")

async def scheduler():
    """Run every 2 hours"""
    while True:
        await news_cycle()
        await asyncio.sleep(7200)

if __name__ == "__main__":
    try:
        asyncio.run(scheduler())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")