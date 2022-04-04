import os
from feedtool import NotionAPI, parse_rss

NOTION_SEC = os.environ.get("NOTION_SEC")
NOTION_DB_RSS = os.environ.get("NOTION_RSS")
NOTION_DB_READER = os.environ.get("NOTION_RED")
FEISHU_BOT_API = os.environ.get("FEISHU_BOT_API")


def read_rss(api):
    for rss in api.query_open_rss():
        # !! 必须和 Notion RSS DB 保持一致
        entries = parse_rss(rss)
        print(f"Got {len(entries)} items from #{rss.get('title')}#")
        if len(entries) == 0:
            continue
        data = api.session.post(api.NOTION_API_HOST + f"/databases/{api._col_id}/query", json={"filter": {"property": "来源", "text": {"equals": entries[0].get("rss").get("title")}}})
        urls = [x.get("properties").get("URL").get("url") for x in data.json().get("results")]
        for entry in entries:
            if entry.get("link") not in urls:
                api.save_page(entry)
            else:
                print(f"Entry {entry.get('title')} already exist!")


def run():
    if NOTION_SEC is None:
        print("NOTION_SEC secrets is not set!")
        return
    api = NotionAPI(NOTION_SEC, NOTION_DB_RSS, NOTION_DB_READER)

    read_rss(api)


if __name__ == "__main__":
    run()
