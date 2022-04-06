# 使用Notion订阅RSS
 ## 读取环境变量
```Python
NOTION_SEC = os.environ.get("NOTION_SEC")
NOTION_DB_RSS = os.environ.get("NOTION_FED")
NOTION_DB_READER = os.environ.get("NOTION_RED")
```
## 创建类`NotionAPI`
```Python
api = NotionAPI(NOTION_SEC, NOTION_DB_READER, NOTION_DB_FEEDS)
```
## 删除过期的RSS
```Python
def delete_rss(self)
```
## 读取已有的RSS
按照创建时间（**从新到旧**前100个）读取Feed对应的RSS
```Python
self.data = requests.request("POST", url=f"{self.NOTION_API_database}/{self.reader_id}/query", headers=self.headers, json={"sorts": [{"timestamp": "created_time", "direction": "descending"}]})
```
创建**URL列表**
```Python
self.urls = [x.get("properties").get("URL").get("url") for x in self.data.json().get("results")]
```
## 读取Feed列表
```Python
def query_open_rss(self):
```
## 利用Feed列表读取RSS
```Python
entries = parse_rss(rss)
```

## 保存RSS到Notion
判断RSS的‘link’在URL列表中是否存在，将不存在的RSS保存到Notion
```Python
def save_page(self, entry)
```

## 灵感来源
[rainyear/chuandashi: 赛博传达室老大爷 (github.com)](https://github.com/rainyear/chuandashi)

原项目中还包含关键词、白名单和飞书机器人的功能，不过被我删了。
