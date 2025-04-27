import aiohttp
import asyncio
from config import NEWS_API_KEY

class NewsFetcher:
    def __init__(self):
        self.base_url = "https://newsapi.org/v2/everything"
        self.api_key = NEWS_API_KEY
        self.topics = ["cybersecurity", "cryptocurrency", "forex"]

    async def fetch_news(self, topic):
        params = {
            "q": topic,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 5  # Fetch 5 articles per topic
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("articles", [])
                    else:
                        print(f"Error fetching {topic} news: {response.status}")
                        return []
            except Exception as e:
                print(f"Exception fetching {topic} news: {e}")
                return []

    async def get_all_news(self):
        news_by_topic = {}
        for topic in self.topics:
            articles = await self.fetch_news(topic)
            news_by_topic[topic] = articles
        return news_by_topic

    def format_news(self, news_by_topic):
        formatted_messages = []
        for topic, articles in news_by_topic.items():
            if not articles:
                continue
            message = f"📰 *Latest {topic.capitalize()} News*\n\n"
            for article in articles:
                title = article.get("title", "No Title")
                source = article.get("source", {}).get("name", "Unknown")
                url = article.get("url", "#")
                message += f"*{title}*\nSource: {source}\nLink: {url}\n\n"
            formatted_messages.append(message)
        return formatted_messages
