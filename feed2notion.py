import feedparser
import os

print(feedparser.__version__)

NOTION_SEC = os.environ.get("NOTION_SEC")
print(NOTION_SEC)
