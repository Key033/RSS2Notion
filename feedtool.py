import feedparser
import re
import json
import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser

NOTION_PARA_BLOCK_LIMIT = 2000
now = datetime.now(timezone.utc)
delete_time = now - timedelta(7)  # 删除7天前的内容
load_time = 2  # 导入2天内的内容


def parse_rss(rss_info: dict):
    entries = []
    try:
        res = requests.get(
            rss_info.get("url"),
            headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.34"},
        )
        feed = feedparser.parse(res.text)
    except requests.exceptions.ProxyError:
        print(f"加载 {rss_info.get('title')} 失败")
        return []
    for entry in feed.entries:
        published_time = parser.parse(entry.get("published"))
        if not published_time.tzinfo:
            published_time = published_time.replace(tzinfo=timezone(timedelta(hours=8)))
        if now - published_time < timedelta(load_time):
            entries.append(
                {
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "time": published_time.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "summary": re.sub(r"<.*?>|\n*", "", entry.get("summary"))[:NOTION_PARA_BLOCK_LIMIT],
                    "rss": rss_info,
                }
            )
    # 读取前 100 条
    return entries[:100]


class NotionAPI:
    NOTION_API_pages = "https://api.notion.com/v1/pages"
    NOTION_API_database = "https://api.notion.com/v1/databases"

    def __init__(self, sec, red, fed) -> None:
        self.reader_id = red
        self.feeds_id = fed
        self.headers = {
            "Authorization": f"Bearer {sec}",
            "Notion-Version": "2022-02-22",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.delete_rss()
        self.data = requests.request(
            "POST",
            url=f"{self.NOTION_API_database}/{self.reader_id}/query",
            headers=self.headers,
            json={
                "sorts": [
                    {
                        "timestamp": "created_time",
                        "direction": "descending",
                    }
                ]
            },
        )
        self.urls = [x.get("properties").get("URL").get("url") for x in self.data.json().get("results")]

    def query_open_rss(self):
        res = requests.request(
            "POST",
            url=f"{self.NOTION_API_database}/{self.feeds_id}/query",
            headers=self.headers,
            json={
                "filter": {
                    "property": "Enable",
                    "checkbox": {"equals": True},
                }
            },
        )
        results = res.json().get("results")
        rss_list = [
            {
                "url": r.get("properties").get("URL").get("url"),
                "title": r.get("properties").get("Name").get("title")[0].get("text").get("content"),
            }
            for r in results
        ]
        return rss_list

    def save_page(self, entry):
        data = {
            "parent": {"database_id": self.reader_id},
            "properties": {
                "标题": {
                    "title": [
                        {
                            "text": {"content": entry.get("title")},
                        }
                    ]
                },
                "URL": {"url": entry.get("link")},
                "来源": {
                    "rich_text": [
                        {
                            "text": {"content": entry.get("rss").get("title")},
                        }
                    ]
                },
                "发布时间": {"date": {"start": entry.get("time")}},
            },
            "children": [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": entry.get("summary")},
                            }
                        ]
                    },
                }
            ],
        }
        res = requests.request("POST", url=self.NOTION_API_pages, headers=self.headers, data=json.dumps(data))
        return res.json()

    def delete_rss(self):
        filter_json = {
            "filter": {
                "and": [
                    {
                        "property": "已读",
                        "checkbox": {"equals": True},
                    },
                    {
                        "property": "发布时间",
                        "date": {"before": delete_time.strftime("%Y-%m-%dT%H:%M:%S%z")},
                    },
                ]
            }
        }
        results = requests.request("POST", url=f"{self.NOTION_API_database}/{self.reader_id}/query", headers=self.headers, json=filter_json).json().get("results")
        payload = {"archived": True}
        responses = []
        for result in results:
            responses += [requests.request("PATCH", url=f"{self.NOTION_API_pages}/{result.get('id')}", json=payload, headers=self.headers).json()]
        return responses
