import feedparser
import re
from functools import reduce
import json
import requests as _req
import time

NOTION_PARA_BLOCK_LIMIT = 2000
now = time.time()


def parse_rss(rss_info: dict):
    entries = []
    try:
        res = _req.get(
            rss_info.get("url"),
            headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.34"},
        )
        feed = feedparser.parse(res.text)
    except Exception:
        print("Feedparser error")
        return []
    for entry in feed.entries:
        if now - time.mktime(entry.published_parsed) < (7 * 24 * 3600):
            entries.append(
                {
                    "title": entry.title,
                    "link": entry.link,
                    "time": time.strftime("%Y-%m-%dT%H:%M:%S%z", entry.published_parsed),
                    "summary": re.sub(r"<.*?>|\n*", "", entry.summary)[:NOTION_PARA_BLOCK_LIMIT],
                    "synced": False,
                    "rss": rss_info,
                }
            )
    # 读取前 100 条
    return entries[:100]


def deep_get(dictionary, keys, default=None):
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )


class NotionAPI:
    NOTION_API_HOST = "https://api.notion.com/v1"

    def __init__(self, sec, rss, coll) -> None:
        self._sec = sec
        self._rss_id = rss
        self._col_id = coll
        self.HEADERS = {
            "Authorization": f"Bearer {self._sec}",
            "Notion-Version": "2021-08-16",
            "Content-Type": "application/json",
        }
        self.session = _req.Session()
        self.session.headers.update(self.HEADERS)

    def query_open_rss(self):
        api = self.NOTION_API_HOST + f"/databases/{self._rss_id}/query"
        res = self.session.post(
            api,
            json={"filter": {"property": "Enable", "checkbox": {"equals": True}}},
        )
        results = res.json().get("results")
        rss_list = [
            {
                "url": deep_get(r, "properties.URL.url"),
                "title": deep_get(r, "properties.Name.title")[0].get("text").get("content"),
            }
            for r in results
        ]
        return rss_list

    def save_page(self, entry):
        api = self.NOTION_API_HOST + "/pages"

        title = entry.get("title")
        summary = entry.get("summary")

        data = {
            "parent": {"database_id": self._col_id},
            "properties": {
                "标题": {"title": [{"text": {"content": title}}]},
                "URL": {"url": entry.get("link")},
                "来源": {"rich_text": [{"text": {"content": entry.get("rss").get("title")}}]},
                "发布时间": {"date": {"start": entry.get("time")}},
            },
            "children": [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": summary,
                                },
                            }
                        ]
                    },
                },
            ],
        }

        res = self.session.post(api, data=json.dumps(data))
        return res.json()
