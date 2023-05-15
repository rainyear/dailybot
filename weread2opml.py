"""
This is a script to convert WeRead's exported note file to OPML file.
"""


import sys

if len(sys.argv) < 2:
    print("Usage: python3 weread2opml.py <path/to/weread_exported_file>")
else:
  raw_content = sys.argv[1:]
  print(raw_content)