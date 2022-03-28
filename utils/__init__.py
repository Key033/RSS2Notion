import feedparser
import re
from functools import reduce
import json
import requests as _req
import time

NOTION_PARA_BLOCK_LIMIT = 2000
now = time.time()

"""
entry = {
    "title"  : "文章标题",
    "link"   : "文章链接",
    "summary": "文章摘要",
    "synced" : False,
    "time"   : "发布时间",
    "rss"    : {
        "title"      : "RSS 标题",
        "url"        : "RSS 地址",
        "isWhiteList": "是否白名单"
    }
}
"""


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
        if hasattr(entry, published_parsed):
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
            else:
                entries.append(
                    {
                        "title": entry.title,
                        "link": entry.link,
                        "summary": re.sub(r"<.*?>|\n*", "", entry.summary)[:NOTION_PARA_BLOCK_LIMIT],
                        "synced": False,
                        "rss": rss_info,
                    }
                )
    # 读取前 20 条
    return entries[:20]


def html2Notion(html: str):
    pass


def deep_get(dictionary, keys, default=None):
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )


class NotionAPI:
    NOTION_API_HOST = "https://api.notion.com/v1"

    def __init__(self, sec, rss, keyword, coll) -> None:
        self._sec = sec
        self._rss_id = rss
        self._kw_id = keyword
        self._col_id = coll
        self.HEADERS = {
            "Authorization": f"Bearer {self._sec}",
            "Notion-Version": "2021-08-16",
            "Content-Type": "application/json",
        }
        self.session = _req.Session()
        self.session.headers.update(self.HEADERS)

    def api_endpoint(self, path):
        return "{}{}".format(self.NOTION_API_HOST, path)

    def query_keywords(self):
        api = self.api_endpoint(f"/databases/{self._kw_id}/query")
        res = self.session.post(api, json={"filter": {"property": "Open", "checkbox": {"equals": True}}})
        results = res.json().get("results")
        keyword_list = [deep_get(k, "properties.KeyWords.title")[0].get("text").get("content") for k in results]
        return keyword_list

    def query_open_rss(self):
        api = self.api_endpoint(f"/databases/{self._rss_id}/query")
        res = self.session.post(
            api,
            json={"filter": {"property": "Enable", "checkbox": {"equals": True}}},
        )
        results = res.json().get("results")
        rss_list = [
            {
                "isWhiteList": deep_get(r, "properties.Whitelist.checkbox"),
                "url": deep_get(r, "properties.URL.url"),
                "title": deep_get(r, "properties.Name.title")[0].get("text").get("content"),
            }
            for r in results
        ]
        return rss_list

    def is_page_exist(self, url):
        api = self.api_endpoint(f"/databases/{self._col_id}/query")
        res = self.session.post(api, json={"filter": {"property": "URL", "text": {"equals": url}}})
        return len(res.json().get("results")) > 0

    def save_page(self, entry):
        api = self.api_endpoint("/pages")

        title = entry.get("title")
        summary = entry.get("summary")

        multi_selects = [{"name": kw} for kw in entry.get("match_keywords")]

        # NOTION API 限制 Summary 长度：
        """
        body.children[1].paragraph.text[0].text.content.length should be ≤ `2000`
        """

        data = {
            "parent": {"database_id": self._col_id},
            "properties": {
                "标题": {"title": [{"text": {"content": title}}]},
                "URL": {"url": entry.get("link")},
                "关键词": {"multi_select": multi_selects},
                # "Entropy": {"number": entry.get("entropy", 0.0)},
                "来源": {"rich_text": [{"text": {"content": entry.get("rss").get("title")}}]},
                "白名单": {"checkbox": entry.get("rss").get("isWhiteList")},
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
