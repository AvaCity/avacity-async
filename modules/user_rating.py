import asyncio
import operator
from modules.base_module import Module

class_name = "UserRating"


class UserRating(Module):
    prefix = "ur"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get, "gar": self.get_activity}
        self.top_act = []
        self.top_hrt = []

    async def get(self, msg, client):
        await client.send(["ur.get", {"bt": self.top_hrt}])

    async def get_activity(self, msg, client):
        await client.send(["ur.gar", {"bt": self.top_act}])

    async def _background(self):
        while True:
            await self.update_act()
            await self.update_hrt()
            await asyncio.sleep(600)

    async def update_act(self):
        users = {}
        max_uid = int(await self.server.redis.get("uids"))
        for i in range(1, max_uid+1):
            act = await self.server.redis.get(f"uid:{i}:act")
            if not act or not await self.server.get_appearance(i):
                continue  # check for not created avatar
            users[i] = int(act)
        sorted_users = sorted(users.items(), key=operator.itemgetter(1),
                              reverse=True)
        best_top = []
        i = 1
        for user in sorted_users:
            best_top.append(user[0])
            if i == 10:
                break
            i += 1
        self.top_act = best_top

    async def update_hrt(self):
        users = {}
        max_uid = int(await self.server.redis.get("uids"))
        for i in range(1, max_uid+1):
            hrt = await self.server.redis.get(f"uid:{i}:hrt")
            if not hrt or not await self.server.get_appearance(i):
                continue  # check for not created avatar
            users[i] = int(hrt)
        sorted_users = sorted(users.items(), key=operator.itemgetter(1),
                              reverse=True)
        best_top = []
        i = 1
        for user in sorted_users:
            cr = int(await self.server.redis.get(f"uid:{user[0]}:crt"))
            best_top.append({"uid": user[0], "hr": user[1], "cr": cr})
            if i == 10:
                break
            i += 1
        self.top_hrt = best_top
