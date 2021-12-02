from fastapi import FastAPI
import requests as _req
import time
import json

from requests.api import head


app = FastAPI()

APP_ID = "飞书 APP ID"
APP_SEC = "飞书 APP SEC"
API_PASS = " 和 GITHUB SEC 一致"
CHAT_ID = " 如何获取消息 ID"

class TToken:
    def __init__(self) -> None:
        self.session = _req.Session()
        self.session.headers.update({
            "content-type": "application/json; charset=utf-8"
        })
        self.Token = None
        self.Expire = int(time.time())

    def get_token(self):
        if self.Token is None or int(time.time()) > self.Expire:
            res = self.session.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": APP_ID,
                    "app_secret": APP_SEC
                })

            msg = res.json()
            print(msg)
            if "ok" == msg.get("msg"):
                self.Token = msg.get("tenant_access_token")
                self.Expire = int(time.time()) + msg.get("expire")
        return self.Token

ttoken = TToken()
@app.post("/feishu")
def bot(msg: dict):
    return {"challenge": msg.get("challenge")}

@app.post("/feishu_send")
def send_msg(msg: dict):
    if msg.get("pass") != API_PASS:
        return {"msg": "Bye!"}
    with open("msg_card.json", "r") as f:
        msg_data = json.load(f)
    msg_content = msg.get("msg")
    # Msg Card Title
    msg_data["elements"][0]["content"] = "**{}**".format(msg_content.get("title"))
    # Msg Card Content
    msg_data["elements"][2]["content"] = msg_content.get("content")
    print(msg_data)
    token = ttoken.get_token()
    api = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    res = _req.post(api, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json; charset=utf-8'
    }, json={
        "receive_id": CHAT_ID,
        "content": json.dumps(msg_data),
        "msg_type": "interactive"
    })
    print(res.json())