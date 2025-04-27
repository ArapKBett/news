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
            "pageSize": 5
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()
                    
                    if response.status != 200 or data.get("status") != "ok":
                        error_msg = data.get("message", "Unknown error")
                        print(f"News API error ({topic}): {error_msg}")
                        return []
                        
                    return data.get("articles", [])
                    
        except aiohttp.ClientError as e:
            print(f"HTTP error ({topic}): {e}")
            return []
        except Exception as e:
            print(f"Unexpected error ({topic}): {e}")
            return []

    async def get_all_news(self):
        tasks = [self.fetch_news(topic) for topic in self.topics]
        results = await asyncio.gather(*tasks)
        return dict(zip(self.topics, results))

    def format_news(self, news_by_topic):
        formatted_messages = []
        for topic, articles in news_by_topic.items():
            if not articles:
                continue
            
            for i in range(0, len(articles), 3):
                chunk = articles[i:i+3]
                message = f"📰 *Latest {topic.capitalize()} News*\n\n"
                for article in chunk:
                    title = article.get("title", "No Title").replace("*", "").strip()
                    source = article.get("source", {}).get("name", "Unknown")
                    url = article.get("url", "#")
                    message += f"• {title}\n   Source: {source}\n   [Read more]({url})\n\n"
                formatted_messages.append(message)
        return formatted_messages
