from modules.base_module import Module
from modules.location import refresh_avatar

icon = "https://ava.city/files/"
class_name = "Support"


class Support(Module):
    prefix = "spt"

    def __init__(self, server):
        self.server = server
        self.commands = {"init": self.init, "gscnl": self.get_social_channels,
                         "rsnm": self.reset_avatar_name,
                         "lmdac": self.load_moderator_actions,
                         "swcr": self.show_crown, "clev": self.close_event,
                         "swlc": self.switch_location}

    async def init(self, msg, client):
        await client.send(["spt.init", {"a": False}])

    async def get_social_channels(self, msg, client):
        channels = []
        channels.append({"act": True, "prt": 1, "id": 1, "stid": "rules",
                         "dsctn": "Правила сервера",
                         "ttl": "Правила", "icnurl": icon+"rules.png",
                         "lnk": ""})
        channels.append({"act": True, "prt": 2, "id": 2, "stid": "tg",
                         "dsctn": "Группа Telegram",
                         "ttl": "Telegram", "icnurl": icon+"tg.png?1",
                         "lnk": "https://t.me/avacity_2_0"})
        channels.append({"act": True, "prt": 3, "id": 3, "stid": "rules",
                         "dsctn": "", "ttl": "Техподдержка",
                         "icnurl": icon+"support.png",
                         "lnk": "https://t.me/avacity_help"})
        channels.append({"act": True, "prt": 4, "id": 4, "stid": "faq",
                         "dsctn": "Подробный гайд по игре", "ttl": "FAQ",
                         "icnurl": icon+"faq.png",
                         "lnk": "https://medium.com/@support_a.c/"
                                "ava-city-faq-гайд-для-новичков-914414d1fe2e"})
        await client.send(["spt.gscnl", {"scls": channels}])

    async def reset_avatar_name(self, msg, client):
        privileges = self.server.modules["cp"].privileges
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < privileges["RENAME_AVATAR"]:
            return
        uid = str(msg[2]["uid"])
        name = msg[2]["n"].strip()
        if not name:
            return
        if not await self.server.redis.lindex(f"uid:{uid}:appearance", 0):
            return
        await self.server.redis.lset(f"uid:{uid}:appearance", 0, name)
        if uid in self.server.online:
            tmp = self.server.online[uid]
            await refresh_avatar(tmp, self.server)

    async def load_moderator_actions(self, msg, client):
        await client.send(["spt.lmdac", {"uid": msg[2]["uid"], "acts": []}])

    async def show_crown(self, msg, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < 2:
            return
        redis = self.server.redis
        crown = await redis.get(f"uid:{client.uid}:hide_crown")
        if not crown:
            await redis.set(f"uid:{client.uid}:hide_crown", 1)
        else:
            await redis.delete(f"uid:{client.uid}:hide_crown")
        await refresh_avatar(client, self.server)

    async def close_event(self, msg, client):
        privileges = self.server.modules["cp"].privileges
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < privileges["EVENT_BAN"]:
            return
        events = self.server.modules["ev"].events
        eid = str(msg[2]["eid"])
        if eid not in events:
            return
        del events[eid]
        msg.pop(0)
        await client.send(msg)

    async def switch_location(self, msg, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < 2:
            return
        if await self.server.redis.get(f"uid:{client.uid}:loc_disabled"):
            await self.server.redis.delete(f"uid:{client.uid}:loc_disabled")
        else:
            await self.server.redis.set(f"uid:{client.uid}:loc_disabled", 1)
        await refresh_avatar(client, self.server)
