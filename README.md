# 使用Notion订阅内容

该[Notion模板](https://functional-crown-0ab.notion.site/RSS-Template-1f69adf675c44599af2d11721febdbb3)
匹配了简悦的[导入到 Notion 辅助增强](https://github.com/Kenshin/simpread/discussions/3572)功能。读取到的内容可以放入同一个收藏夹。
## 环境变量
需要用到Notion机器人的token，Notion模板中两个数据库**收集**和**订阅入口**的ID。

在项目的**Secret**中添加对应的环境变量。
```Python
NOTION_SEC = os.environ.get("NOTION_SEC")
NOTION_DB_RSS = os.environ.get("NOTION_FED")
NOTION_DB_READER = os.environ.get("NOTION_RED")
```
## 创建类`NotionAPI`
```Python
api = NotionAPI(NOTION_SEC, NOTION_DB_READER, NOTION_DB_FEEDS)
```
## 删除过期的内容
```Python
def delete_rss(self)
```
## 读取Feed列表
```Python
def query_open_rss(self):
```
## 读取Notion中已有的内容
按照**创建时间**（从新到旧）和与Feed名称对应的**来源**筛选和读取Notion中已有的Feed对应的内容
```Python
data = requests.request(
    "POST",
    url=f"{api.NOTION_API_database}/{api.reader_id}/query",
    headers=api.headers,
    json={
        "filter": {
            "property": "Origin",
            "select": {"equals": f"{entries[0].get('rss').get('title')}"},
        },
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "descending",
            }
        ],
    },
)
```
虽然这会导致有多少个feed就要**query**多少次database。但是Notion每次**query**只会返回100个项目，只一次查询，很可能导致项目重复添加。
## 创建**URL列表**
```Python
urls = [x.get("properties").get("URL").get("url") for x in data.json().get("results")]
```
## 利用Feed列表读取内容
```Python
entries = parse_rss(rss)
```

## 保存内容到Notion
判断内容的‘link’在URL列表中是否存在，将不存在的内容保存到Notion
```Python
def save_page(self, entry)
```

## 灵感来源
[rainyear/chuandashi: 赛博传达室老大爷 (github.com)](https://github.com/rainyear/chuandashi)

原项目中还包含关键词、白名单和飞书机器人的功能，不过被我删了。
