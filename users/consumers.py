import jwt
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .models import Users
from asgiref.sync import sync_to_async


async def fetch_user_from_headers(headers: dict):
    cookie_header = headers.get(b"cookie", b"").decode("utf-8")
    jwt_cookie = None
    if cookie_header:
        cookies = cookie_header.split("; ")
        for cookie in cookies:
            if cookie.startswith("jwt="):
                jwt_cookie = cookie.split("jwt=")[1]
                break
    payload = jwt.decode(jwt_cookie, "secrets", algorithms=["HS256"])
    return await sync_to_async(Users.objects.get)(user_id=payload["user_id"])


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        try:
            user = await fetch_user_from_headers(dict(self.scope.get("headers")))
            group_name = user.group_name
            await self.channel_layer.group_add(
                group_name,
                self.channel_name,
            )
            await self.accept()
            print("CONNECTED GROUP", group_name)

        except Exception as e:
            print(e)

    async def disconnect(self, close_code):
        try:
            user = await fetch_user_from_headers(dict(self.scope.get("headers")))
            group_name = user.group_name
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name,
            )
            await self.close()

        except Exception as e:
            print(e)

    async def send_log(self, event):
        message = event["log_data"]
        await self.send(text_data=message)

    async def send_message(self, data):
        await self.send(text_data=data["action"])

