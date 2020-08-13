import time
from modules.base_module import Module

class_name = "ClanRequest"


class ClanRequest(Module):
    prefix = "crq"

    def __init__(self, server):
        self.server = server
        self.clan = server.modules["cln"]
        self.commands = {"lrui": self.load_requests,
                         "lrci": self.load_clan_requests,
                         "crr": self.create_request,
                         "dlr": self.delete_request,
                         "alr": self.approve_request}

    async def load_requests(self, msg, client):
        cid = await self.server.redis.get(f"uid:{client.uid}:req")
        if not cid:
            return await client.send(["crq.lrq", {"rqls": []}])
        await client.send(["crq.lrq", {"rqls": [{"uid": client.uid, "crd": 1,
                                                 "src": 0,
                                                 "rid": int(client.uid),
                                                 "cid": cid}]}])

    async def load_clan_requests(self, msg, client):
        r = self.server.redis
        cid = await r.get(f"uid:{client.uid}:clan")
        role = int(await r.get(f"clans:{cid}:m:{client.uid}:role"))
        if role < 2:
            return
        requests = []
        for rid in await r.smembers(f"clans:{cid}:req"):
            requests.append({"uid": int(rid), "crd": 1, "src": 0,
                             "rid": int(rid), "cid": int(cid)})
        await client.send(["crq.lrq", {"rqls": requests}])

    async def create_request(self, msg, client):
        r = self.server.redis
        if await r.get(f"uid:{client.uid}:clan"):
            return
        if await r.get(f"uid:{client.uid}:req"):
            return
        cid = msg[2]["cid"]
        if str(cid) not in await r.smembers("clans"):
            return
        await r.sadd(f"clans:{cid}:req", client.uid)
        await r.set(f"uid:{client.uid}:req", cid)
        await client.send(["crq.crr", {"scs": True,
                                       "rqst": {"uid": client.uid,
                                                "crd": int(time.time()),
                                                "src": 0, "cid": cid,
                                                "rid": int(client.uid)}}])
        clan = await self.clan.get_clan(cid)
        for uid in clan["members"]:
            if clan["members"][uid]["role"] < 2:
                continue
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await tmp.send(["crq.dlr", {"rid": client.uid}])
                await tmp.send(["crq.crr", {"scs": True,
                                            "rqst": {"uid": client.uid,
                                                     "crd": int(time.time()),
                                                     "src": 0, "cid": cid,
                                                     "rid": int(client.uid)}}])

    async def delete_request(self, msg, client):
        r = self.server.redis
        rid = msg[2]["rid"]
        if str(rid) == client.uid:
            cid = await r.get(f"uid:{client.uid}:req")
        else:
            cid = await r.get(f"uid:{client.uid}:clan")
        if not cid:
            return
        if str(rid) != client.uid:
            role = int(await r.get(f"clans:{cid}:m:{client.uid}:role"))
            if role < 2:
                return
        if str(rid) not in await r.smembers(f"clans:{cid}:req"):
            return
        await r.srem(f"clans:{cid}:req", rid)
        await r.delete(f"uid:{rid}:req")
        if str(rid) in self.server.online:
            tmp = self.server.online[str(rid)]
            await tmp.send(["crq.dlr", {"rid": rid}])
        clan = await self.clan.get_clan(cid)
        for uid in clan["members"]:
            if clan["members"][uid]["role"] < 2:
                continue
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await tmp.send(["crq.dlr", {"rid": rid}])

    async def approve_request(self, msg, client):
        r = self.server.redis
        uid = str(msg[2]["rid"])
        cid = await r.get(f"uid:{client.uid}:clan")
        role = int(await r.get(f"clans:{cid}:m:{client.uid}:role"))
        if role < 2:
            return
        if uid not in await r.smembers(f"clans:{cid}:req"):
            return
        await r.srem(f"clans:{cid}:req", uid)
        await r.delete(f"uid:{uid}:req")
        await self.clan.join_clan(cid, uid)
        cn = self.server.modules["cn"]
        await cn.add_action(cid, f"{uid}_0")
