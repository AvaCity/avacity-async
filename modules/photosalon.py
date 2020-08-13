from modules.base_module import Module


class_name = "Photosalon"


class Photosalon(Module):
    prefix = "phsl"

    def __init__(self, server):
        self.server = server
        self.commands = {"bph": self.buy_photo, "shph": self.share_photo}

    async def buy_photo(self, msg, client):
        if not await self.server.inv[client.uid].take_item("film", 2):
            await client.send(["phsl.bph", {"scs": False}])
            return
        cnt = await self.server.redis.lindex(f"uid:{client.uid}:items:film", 1)
        if cnt:
            cnt = int(cnt)
        else:
            cnt = 0
        await client.send(["ntf.inv", {"it": {"c": cnt, "lid": "",
                                              "tid": "film"}}])
        await client.send(["phsl.bph", {"scs": True, "snsh": msg[2]["snsh"]}])

    async def share_photo(self, msg, client):
        snapshot = msg[2]["snsh"]
        for item in snapshot["ps"]:
            if item["uid"] == client.uid:
                continue
            if item["uid"] not in self.server.online:
                continue
            tmp = self.server.online[item["uid"]]
            await tmp.send(["phsl.shph", {"snsh": snapshot}])
