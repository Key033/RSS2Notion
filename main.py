import os
from feedtool import NotionAPI, parse_rss

NOTION_SEC = os.environ.get("NOTION_SEC")
NOTION_DB_READER = os.environ.get("NOTION_RED")
NOTION_DB_FEEDS = os.environ.get("NOTION_FED")


def read_rss(api: NotionAPI):
    for rss in api.query_open_rss():
        # !! 必须和 Notion RSS DB 保持一致
        entries = parse_rss(rss)
        if len(entries) == 0:
            continue
        repeat_flag = 0
        for entry in entries:
            if entry.get("link") not in api.urls:
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
