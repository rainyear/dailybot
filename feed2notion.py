import os
import requests
from utils import NotionAPI, deep_get, parse_rss

NOTION_SEC = os.environ.get("NOTION_SEC")
NOTION_DB_RSS = "90761665a1d141b984afca52a2b05410"
NOTION_DB_KEYWORDS = "26d213dcc8b641cd921db43eb7b23733"
NOTION_DB_READER = "bcc40eb17dc54258866faf765b151840"
# https://www.notion.so/v2xr/bcc40eb17dc54258866faf765b151840?v=4719f35c57024c5eb54c996846b2cae4&pvs=4
FEISHU_BOT_API = os.environ.get("FEISHU_BOT_API")
FEISHU_BOT_SEC = os.environ.get("FEISHU_BOT_SEC")


def feishu_bot_send_msg(msg):
    """
    msg = {"title": "", "content": ""}
    """
    if FEISHU_BOT_API:
        requests.post(FEISHU_BOT_API, json={"pass": FEISHU_BOT_SEC, "msg": msg})


def _wrap_rss_warning_msg_fmt(title, uri):
    content = f"{title} 读取失败！\n\t{uri}"
    feishu_bot_send_msg({"title": "❗ RSS Warning", "content": content})


def _wrap_rss_new_msg_fmt(entries):
    content = ""
    for i, entry in enumerate(entries):
        content += f"{i+1}. [{entry.get('title')}]({entry.get('link')}) | {entry.get('rss').get('title')}\n"
    msg = {"title": "🔔 NEW RSS", "content": content}

    feishu_bot_send_msg(msg)


def process_entry(entry: dict, keywords: list):
    entropy = 0
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
            # 飞书提示
            _wrap_rss_warning_msg_fmt(rss.get("title"), rss.get("uri"))
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
                new_entries.append(entry)
            else:
                print(f"Entry {entry.get('title')} already exist!")
    # 飞书提示
    if len(new_entries) > 0:
        _wrap_rss_new_msg_fmt(new_entries)


if __name__ == "__main__":
    run()
