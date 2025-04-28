import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "newsapi": {
        "key": os.getenv("NEWS_API_KEY"),
        "url": "https://newsapi.org/v2/"
    },
    "gnews": {
        "key": os.getenv("GNEWS_API_KEY"),
        "url": "https://gnews.io/api/v4/"
    },
    "guardian": {
        "key": os.getenv("GUARDIAN_API_KEY"),
        "url": "https://content.guardianapis.com/"
    },
    "telegram": {
        "token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "channel": int(os.getenv("TELEGRAM_CHANNEL_ID"))
    },
    "discord": {
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "channel": int(os.getenv("DISCORD_CHANNEL_ID"))
    }
}