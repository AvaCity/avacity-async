import random
from modules.base_module import Module
from modules.location import get_city_info
import modules.notify as notify
import const

class_name = "Inventory"


class Inventory(Module):
    prefix = "tr"

    def __init__(self, server):
        self.server = server
        self.commands = {"sale": self.sale_item, "opgft": self.open_gift}

    async def sale_item(self, msg, client):
        items = self.server.game_items["game"]
        tpid = msg[2]["tpid"]
        cnt = msg[2]["cnt"]
        if tpid not in items or "saleSilver" not in items[tpid]:
            return
        if not await self.server.inv[client.uid].take_item(tpid, cnt):
            return
        price = items[tpid]["saleSilver"]
        user_data = await self.server.get_user_data(client.uid)
        redis = self.server.redis
        await redis.set(f"uid:{client.uid}:slvr", user_data["slvr"]+price*cnt)
        ci = await get_city_info(client.uid, self.server)
        await client.send(["ntf.ci", {"ci": ci}])
        inv = self.server.inv[client.uid].get()
        await client.send(["ntf.inv", {"inv": inv}])
        await notify.update_resources(client, self.server)

    async def open_gift(self, msg, client):
        await client.send(["cp.ms.rsm", {"txt": "Открытие подарков не "
                                                " работает"}])
        return
        gift = msg[2]["tpid"]
        if gift != "srGft3":
            return
        type_ = random.choice(["gld", "slvr"])
        if type_ == "gld":
            max_num = random.choice([100, 250, 500])
        else:
            max_num = 10000
        num = random.randint(0, max_num)
        user_data = await self.server.get_user_data(client.uid)
        amount = user_data[type_]
        await self.server.redis.set(f"uid:{client.uid}:{type_}", amount+num)
        res = {"gld": 0, "slvr": 0, "enrg": 0}
        res[type_] = num
        appearance = await self.server.get_appearance(client.uid)
        gender = "boy" if appearance["g"] == 1 else "girl"
        if gender == "boy":
            resources = const.bigng_common+const.bigng_boy+const.bigng_loot
        else:
            resources = const.bigng_common+const.bigng_girl+const.bigng_loot
        await client.send(["tr.opgft", {"res": res, "ctid": "skiResortGifts",
                                        "lt": {"id": None, "it": loot}}])

    #async def _get_gift_items(self, gift, uid):
