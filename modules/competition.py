import asyncio
import operator
from modules.base_module import Module

class_name = "Competition"


class Competition(Module):
    prefix = "ctmr"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get_top}
        self.top = []

    async def _background(self):
        while True:
            await self.update_snow()
            await asyncio.sleep(600)

    async def get_top(self, msg, client):
        await client.send(["ctmr.get", {"tu": {"snowboardRating": self.top}}])

    async def update_snow(self):
        users = {}
        max_uid = int(await self.server.redis.get("uids"))
        for i in range(1, max_uid+1):
            act = await self.server.redis.get(f"uid:{i}:snowscore")
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
        self.top = best_top
