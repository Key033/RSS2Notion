import os
from feedtool import NotionAPI, parse_rss
import requests

NOTION_SEC = os.environ.get("NOTION_SEC")
NOTION_DB_READER = os.environ.get("NOTION_RED")
NOTION_DB_FEEDS = os.environ.get("NOTION_FED")


def read_rss(api: NotionAPI):
    for rss in api.query_open_rss():
        entries = parse_rss(rss)
        if len(entries) == 0:
            continue
        data = requests.request(
            "POST",
            url=f"{api.NOTION_API_database}/{api.reader_id}/query",
            headers=api.headers,
            json={
                "filter": {
                    "property": "来源",
                    "rich_text": {"equals": f"{entries[0].get('rss').get('title')}"},
                },
                "sorts": [
                    {
                        "timestamp": "created_time",
                        "direction": "descending",
                    }
                ],
            },
        )
        urls = [x.get("properties").get("URL").get("url") for x in data.json().get("results")]
        repeat_flag = 0
        for entry in entries:
            if entry.get("link") not in urls:
                api.save_page(entry)
            else:
                repeat_flag += 1
        print(f"从 {rss.get('title')} 读取到 {len(entries)} 篇内容，其中重复 {repeat_flag} 篇。")


def run():
    if NOTION_SEC is None:
        print("NOTION_SEC secrets is not set!")
        return
    api = NotionAPI(NOTION_SEC, NOTION_DB_READER, NOTION_DB_FEEDS)

    read_rss(api)


if __name__ == "__main__":
    run()
