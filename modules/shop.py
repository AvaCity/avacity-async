from modules.base_module import Module
import modules.notify as notify

class_name = "Shop"


class Shop(Module):
    prefix = "sh"

    def __init__(self, server):
        self.server = server
        self.commands = {"bji": self.buy_game_item,
                         "bwr": self.buy_wedding_ring,
                         "bsrg": self.buy_game_item}

    async def buy_game_item(self, msg, client):
        item = msg[2]["tpid"]
        cnt = msg[2]["cnt"]
        await self.buy(client, item, count=cnt)

    async def buy_wedding_ring(self, msg, client):
        item = msg[2]["tpid"]
        await self.buy(client, item)

    async def buy(self, client, item, count=1, add=True):
        if item not in self.server.game_items["game"]:
            return False
        if not self.server.game_items["game"][item]["canBuy"]:
            return False
        gold = self.server.game_items["game"][item]["gold"]*count
        silver = self.server.game_items["game"][item]["silver"]*count
        user_data = await self.server.get_user_data(client.uid)
        if user_data["gld"] < gold or user_data["slvr"] < silver:
            return False
        redis = self.server.redis
        await redis.set(f"uid:{client.uid}:gld", user_data["gld"]-gold)
        await redis.set(f"uid:{client.uid}:slvr", user_data["slvr"]-silver)
        if add:
            await self.server.inv[client.uid].add_item(item, "gm", count)
            cnt = int(await redis.lindex(f"uid:{client.uid}:items:{item}", 1))
            await client.send(["ntf.inv", {"it": {"c": cnt, "lid": "",
                                                  "tid": item}}])
            await notify.update_resources(client, self.server)
        return True
