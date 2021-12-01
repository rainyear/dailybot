import json
import feedparser
import os
import requests as _req

NOTION_SEC         = os.environ.get("NOTION_SEC")
NOTION_DB_RSS      = "90761665a1d141b984afca52a2b05410"
NOTION_DB_KEYWORDS = "26d213dcc8b641cd921db43eb7b23733"
NOTION_DB_READER   = "28dfbfdf24a848cd9de28302454ee3dd"

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
        api = self.api_endpoint("/databases/{self._kw_id}/query")
        res = self.session.post(
            api, json={"filter": {"property": "Open", "checkbox": {"equals": True}}}
        )
        results = res.json().get("results")
        return results

    def query_open_rss(self):
        api = self.api_endpoint("/databases/{self._rss_id}/query")
        res = self.session.post(
            api,
            json={"filter": {"property": "Enable", "checkbox": {"equals": True}}},
        )
        results = res.json().get("results")
        return results

    def save_page(self, entry, keywords, entropy):
        api = self.api_endpoint("/pages")

        title = entry.get("title")
        summary = entry.get("summary")

        multi_selects = [{"name": kw} for kw in keywords]

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
                "Entropy": {"number": entropy},
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



def run():
    if NOTION_SEC is None: 
        print("NOTION_SEC secrets is not set!")
        return
    api = NotionAPI(NOTION_SEC, NOTION_DB_RSS, NOTION_DB_KEYWORDS, NOTION_DB_READER)
    print(api.query_keywords())

if __name__ == "__main__":
    run()