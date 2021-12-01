import os
import requests
from utils import NotionAPI, deep_get, parse_rss

NOTION_SEC         = os.environ.get("NOTION_SEC")
NOTION_DB_RSS      = "90761665a1d141b984afca52a2b05410"
NOTION_DB_KEYWORDS = "26d213dcc8b641cd921db43eb7b23733"
NOTION_DB_READER   = "28dfbfdf24a848cd9de28302454ee3dd"

FEISHU_BOT_API = os.environ.get("FEISHU_BOT_API")
FEISHU_BOT_SEC = os.environ.get("FEISHU_BOT_SEC")
def feishu_bot_send_msg(msg):
    if FEISHU_BOT_API:
        requests.post(FEISHU_BOT_API, json={"pass": FEISHU_BOT_SEC, "msg": msg})


def process_entry(entry:dict, keywords:list):
    entropy        = 0
    match_keywords = []
    # TODO: filter keywords -
    text = f'{entry.get("title")} {entry.get("summary")}'
    for kw in keywords:
        if kw in text:
            print(f"Keyword {kw} Matched! -> #{entry.get('title')}")
            match_keywords.append(kw)
            entropy += 1

    if len(keywords) > 0:
        entropy /= len(keywords)

    if deep_get(entry, "rss.isWhiteList"):
        entropy = 1

    entry["entropy"] = float(f"{entropy}")
    entry["match_keywords"] = match_keywords

    return entry

def read_rss(rsslist):
    for rss in rsslist:
    # !! 必须和 Notion RSS DB 保持一致
        entries = parse_rss(rss)
        print(f"Got {len(entries)} items from #{rss.get('title')}#")
        if len(entries) == 0:
            feishu_bot_send_msg("""
---
RSS Warning!
---
{title} Got 0 item!
    {uri}
""".format(title = rss.get("title"), uri=rss.get("uri")))
        for entry in entries:
            yield entry

def run():
    if NOTION_SEC is None:
        print("NOTION_SEC secrets is not set!")
        return
    api = NotionAPI(NOTION_SEC, NOTION_DB_RSS, NOTION_DB_KEYWORDS, NOTION_DB_READER)

    keywords = api.query_keywords()

    new_entries = []
    for entry in read_rss(api.query_open_rss()):
        res = process_entry(entry, keywords)
        if res.get("entropy") > 0:
            if not api.is_page_exist(entry.get("link")):
                api.save_page(entry)
                new_entries.append(entry.get("title"))
            else:
                print(f"Entry {entry.get('title')} already exist!")
    
    msg = """
---
NEW RSS
---
{lines}
""".format(lines= '\n'.join(new_entries))
    print(msg)

if __name__ == "__main__":
    run()