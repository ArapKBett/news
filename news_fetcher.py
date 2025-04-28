import aiohttp
import asyncio
from datetime import datetime, timedelta
from config import CONFIG
import logging
import urllib.parse

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        self.topics = {
            "cybersecurity": ["cybersecurity", "hacking", "data breach"],
            "cryptocurrency": ["cryptocurrency", "bitcoin", "blockchain"],
            "forex": ["forex", "currency exchange", "fx trading"]
        }
        self.max_articles = 3
        self.user_agent = "NewsBot/2.0 (+https://example.com/bot)"

    async def _make_request(self, service, endpoint, params=None):
        try:
            cfg = CONFIG[service]
            headers = {"User-Agent": self.user_agent}
            params = params or {}

            if service == "newsapi":
                params["apiKey"] = cfg["key"]
                params["pageSize"] = self.max_articles
                params["from"] = (datetime.now() - timedelta(hours=24)).isoformat()
            elif service == "gnews":
                params["token"] = cfg["key"]
                params["max"] = self.max_articles
            elif service == "guardian":
                params["api-key"] = cfg["key"]
                params["show-fields"] = "headline,shortUrl"

            async with aiohttp.ClientSession(headers=headers) as session:
                response = await session.get(
                    f"{cfg['url']}{endpoint}", 
                    params=params
                )
                if response.status != 200:
                    return None
                return await response.json()
        except Exception as e:
            logger.error(f"{service} error: {str(e)}")
            return None

    async def fetch_topic_news(self, topic):
        all_articles = []
        seen_urls = set()

        for keyword in self.topics[topic][:2]:
            # NewsAPI
            newsapi_data = await self._make_request(
                "newsapi",
                "everything",
                {"q": keyword, "language": "en"}
            )
            for article in newsapi_data.get("articles", []) if newsapi_data else []:
                if article["url"] not in seen_urls:
                    all_articles.append({
                        "title": article.get("title", "No Title"),
                        "url": article["url"],
                        "source": article.get("source", {}).get("name", "Unknown")
                    })
                    seen_urls.add(article["url"])

            # GNews
            gnews_data = await self._make_request(
                "gnews",
                "search",
                {"q": keyword, "lang": "en"}
            )
            for article in gnews_data.get("articles", []) if gnews_data else []:
                clean_url = urllib.parse.urlsplit(article["url"])._replace(query="").geturl()
                if clean_url not in seen_urls:
                    all_articles.append({
                        "title": article.get("title", "No Title"),
                        "url": clean_url,
                        "source": article.get("source", {}).get("name", "Unknown")
                    })
                    seen_urls.add(clean_url)

            # Guardian
            guardian_data = await self._make_request(
                "guardian",
                "search",
                {"q": keyword}
            )
            for item in guardian_data.get("response", {}).get("results", []) if guardian_data else []:
                url = item.get("fields", {}).get("shortUrl") or f"https://www.theguardian.com/{item.get('id', '')}"
                if url not in seen_urls:
                    all_articles.append({
                        "title": item.get("fields", {}).get("headline", "No Title"),
                        "url": url,
                        "source": "The Guardian"
                    })
                    seen_urls.add(url)

        return all_articles[:self.max_articles]

    async def get_all_news(self):
        return {
            topic: await self.fetch_topic_news(topic)
            for topic in self.topics
        }

    def format_for_platform(self, news_data, platform):
        messages = []
        for topic, articles in news_data.items():
            if not articles:
                continue

            header = f"📰 **{topic.upper()} NEWS**" if platform == "discord" \
                else f"📰 *{topic.upper()} News*"
            
            section = [header]
            for idx, article in enumerate(articles, 1):
                if platform == "telegram":
                    entry = f"{idx}. [{article['title']}]({article['url']})\n   _{article['source']}_"
                else:  # Discord
                    entry = f"{idx}. <{article['url']}>\n   *{article['title']}* ({article['source']})"
                
                section.append(entry)
            
            messages.append("\n".join(section))
        return messages