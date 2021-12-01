import feedparser
import re
from datetime import datetime
from functools import reduce
import json
import requests as _req

NOTION_PARA_BLOCK_LIMIT = 2000


TIMESTAMP = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
DATESTAMP = lambda: datetime.now().strftime("%Y-%m-%d")

"""
rss = {
    "title"  : "文章标题",
    "link"   : "文章链接",
    "summary": "文章摘要",
    "synced" : False,
    "date"   : "文章时间 | 抓取时间",
    "rss"    : {
        "title"      : "RSS 标题",
        "uri"        : "RSS 地址",
        "isWhiteList": "是否白名单"
    }
}
"""

def parse_rss(rss_info: dict):
    entries = []
    try:
        res = _req.get(rss_info.get("uri"), headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.34"})
        feed = feedparser.parse(res.text)
    except:
        print("Feedparser error")
        return []
    for entry in feed.entries:
        entries.append(
            {
                "title": entry.title,
                "link": entry.link,
                "date": entry.get("updated", TIMESTAMP()),
                "summary": re.sub(r"<.*?>|\n*", "", entry.summary)[
                    :NOTION_PARA_BLOCK_LIMIT
                ],
                "synced": False,
                "rss": rss_info,
            }
        )
    # 读取前 20 条
    return entries[:20]

def deep_get(dictionary, keys, default=None):
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )

class NotionAPI:
    NOTION_API_HOST = "https://api.notion.com/v1"
    def __init__(self, sec, rss, keyword, coll) -> None:
        self._sec    = sec
        self._rss_id = rss
        self._kw_id  = keyword
        self._col_id = coll
        self.HEADERS = {
            "Authorization": f"Bearer {self._sec}",
            "Notion-Version": "2021-08-16",
            "Content-Type"  : "application/json",
        }
        self.session = _req.Session()
        self.session.headers.update(self.HEADERS)
    def api_endpoint(self, path):
        return "{}{}".format(self.NOTION_API_HOST, path)

    def query_keywords(self):
        api = self.api_endpoint(f"/databases/{self._kw_id}/query")
        res = self.session.post(
            api, json={"filter": {"property": "Open", "checkbox": {"equals": True}}}
        )
        results = res.json().get("results")
        keyword_list = [
            deep_get(k, "properties.KeyWords.title")[0].get("text").get("content")
            for k in results
        ]
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
                "isWhiteList" : deep_get(r, "properties.Whitelist.checkbox"),
                "uri"         : deep_get(r, "properties.URI.url"),
                "title"       : deep_get(r, "properties.Name.title")[0].get("text").get("content")
            }
            for r in results
        ]
        return rss_list

    def is_page_exist(self, uri):
        api = self.api_endpoint(f"/databases/{self._col_id}/query")
        res = self.session.post(
            api,
            json={"filter": {"property": "URI", "text": {"equals": uri}}}
        )
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
                "Title": {"title": [{"text": {"content": title}}]},
                "URI": {"url": entry.get("link")},
                "Key Words": {"multi_select": multi_selects},
                "Entropy": {"number": entry.get("entropy", 0.0)},
                "Source": {
                    "rich_text": [{"text": {"content": entry.get("rss").get("title")}}]
                },
                "白名单": {"checkbox": entry.get("rss").get("isWhiteList")},
            },
            "children": [
                {
                    "type": "heading_3",
                    "heading_3": {
                        "text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Summary",
                                },
                            }
                        ]
                    },
                },  # H3
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