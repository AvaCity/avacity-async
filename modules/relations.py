import time
from modules.base_module import Module
from modules.location import refresh_avatar

class_name = "Relations"


class Relations(Module):
    prefix = "rl"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get_relations,
                         "crt": self.create_relation,
                         "adcr": self.admin_create_relation,
                         "rmv": self.remove_relation,
                         "crs": self.change_relation_status,
                         "wwtns": self.wedding_witness,
                         "strtw": self.start_wedding,
                         "apprw": self.wedding_approve,
                         "rings": self.rings,
                         "ednt": self.edit_note}
        self.statuses = self.server.parser.parse_relations()
        self.progresses = self.server.parser.parse_relation_progresses()

    async def get_relations(self, msg, client):
        data = ["rl.get", {"uid": client.uid, "rlts": {}}]
        relations = await self.server.redis.smembers(f"rl:{client.uid}")
        for rl in relations:
            relation = await self._get_relation(client.uid, rl)
            data[1]["rlts"][relation["uid"]] = relation["rlt"]
        await client.send(data)

    async def create_relation(self, msg, client):
        confirms = self.server.modules["cf"].confirms
        privileges = self.server.modules["cp"].privileges
        user_data = await self.server.get_user_data(client.uid)
        if client.uid not in confirms and \
           user_data["role"] < privileges["RELATION_TEST_PANEL"]:
            return
        if client.uid in confirms and \
           not confirms[client.uid]["completed"]:
            return
        relation = msg[2]
        if await self.get_link(client.uid, relation["uid"]):
            return
        await self._create_relation(f"{client.uid}:{relation['uid']}",
                                    relation)
        if client.uid in confirms:
            del confirms[client.uid]

    async def remove_relation(self, msg, client):
        uid = msg[2]["uid"]
        if uid == client.uid:
            return
        link = None
        for rl in await self.server.redis.smembers(f"rl:{client.uid}"):
            if uid in rl:
                link = rl
                break
        if not link:
            return
        await self._remove_relation(link)

    async def admin_create_relation(self, msg, client):
        privileges = self.server.modules["cp"].privileges
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < privileges["RELATION_TEST_PANEL"]:
            return
        relation = msg[2]
        if client.uid == relation["uid"]:
            return
        link = await self.get_link(client.uid, relation["uid"])
        if not link:
            await self._create_relation(f"{client.uid}:{relation['uid']}",
                                        relation)
        else:
            await self._update_relation(link, relation)

    async def change_relation_status(self, msg, client):
        relation = msg[2]
        link = await self.get_link(client.uid, relation["uid"])
        if not link:
            return
        rl = (await self._get_relation(client.uid, link))["rlt"]
        status = self.statuses[rl["s"]]
        if relation["s"] not in status["transition"]:
            privileges = self.server.modules["cp"].privileges
            user_data = await self.server.get_user_data(client.uid)
            if user_data["role"] < privileges["RELATION_TEST_PANEL"]:
                return
        if "t" in relation:
            inv = self.server.inv[client.uid]
            if "er" in relation["t"]:
                if not await self.buy_ring(relation["t"]["er"], client.uid):
                    return
            elif "mr" in relation["t"]:
                if not await inv.take_item(relation["t"]["er"]):
                    return
        await self._update_relation(link, relation)

    async def wedding_witness(self, msg, client):
        uid = msg[2]["wwid"]
        link = await self.get_link(client.uid, msg[2]["uid"])
        if not link:
            return
        rl = (await self._get_relation(client.uid, link))["rlt"]
        if rl["s"] // 10 != 6:
            return
        confirms = self.server.modules["cf"].confirms
        if client.uid not in confirms:
            return
        if confirms[client.uid]["uid"] != uid:
            return
        if confirms[client.uid]["at"] != "weddingWitness":
            return
        await client.send(["rl.apprw", {"uid": msg[2]["uid"]}])

    async def start_wedding(self, msg, client):
        uid = msg[2]["uid"]
        link = await self.get_link(client.uid, msg[2]["uid"])
        if not link:
            return
        rl = (await self._get_relation(client.uid, link))["rlt"]
        if rl["s"] // 10 != 6:
            return
        await client.send(["rl.strtw", {"uid": uid}])
        # if uid in self.server.online:
        #    tmp = self.server.online[uid]
        #    await tmp.send(["rl.strtw", {"uid": client.uid}])

    async def wedding_approve(self, msg, client):
        uid = msg[2]["uid"]
        link = await self.get_link(client.uid, uid)
        if not link:
            return
        rl = (await self._get_relation(client.uid, link))["rlt"]
        if rl["s"] // 10 != 6:
            return
        await client.send(["rl.rings", {"uid": uid}])

    async def rings(self, msg, client):
        uid = msg[2]["uid"]
        link = await self.get_link(client.uid, uid)
        if not link:
            return
        rl = (await self._get_relation(client.uid, link))["rlt"]
        if rl["s"] // 10 != 6:
            return
        await self.server.redis.set(f"rl:{link}:ring", msg[2]["wrid"])
        await self._update_relation(link, {"s": 70})

    async def edit_note(self, msg, client):
        uid = msg[2]["uid"]
        link = await self.get_link(client.uid, uid)
        await self.server.redis.set(f"uid:{client.uid}:note:{uid}",
                                    msg[2]["nt"])
        rlt = (await self._get_relation(client.uid, link))["rlt"]
        await client.send(["rl.ednt", {"uid": uid, "rlt": rlt}])

    async def _create_relation(self, link, relation):
        pipe = self.server.redis.pipeline()
        for uid in link.split(":"):
            pipe.sadd(f"rl:{uid}", link)
        pipe.set(f"rl:{link}:p", 0)
        pipe.set(f"rl:{link}:st", int(time.time()))
        pipe.set(f"rl:{link}:ut", int(time.time()))
        pipe.set(f"rl:{link}:s", relation["s"])
        await pipe.execute()
        for uid in link.split(":"):
            rl = await self._get_relation(uid, link)
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await refresh_avatar(tmp, self.server)
                await tmp.send(["rl.new", rl])

    async def _update_relation(self, link, relation):
        pipe = self.server.redis.pipeline()
        pipe.set(f"rl:{link}:p", 0)
        pipe.set(f"rl:{link}:st", int(time.time()))
        pipe.set(f"rl:{link}:ut", int(time.time()))
        pipe.set(f"rl:{link}:s", relation["s"])
        if "t" in relation:
            if relation["t"]["er"]:
                pipe.set(f"rl:{link}:ring", relation["t"]["er"])
            elif relation["t"]["mr"]:
                pipe.set(f"rl:{link}:ring", relation["t"]["mr"])
        await pipe.execute()
        for uid in link.split(":"):
            rl = await self._get_relation(uid, link)
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await refresh_avatar(tmp, self.server)
                await tmp.send(["rl.crs", rl])

    async def _remove_relation(self, link):
        pipe = self.server.redis.pipeline()
        pipe.delete(f"rl:{link}:p")
        pipe.delete(f"rl:{link}:st")
        pipe.delete(f"rl:{link}:ut")
        pipe.delete(f"rl:{link}:s")
        pipe.delete(f"rl:{link}:t")
        for uid in link.split(":"):
            pipe.srem(f"rl:{uid}", link)
        await pipe.execute()
        for uid in link.split(":"):
            if link.split(":")[0] == uid:
                second_uid = link.split(":")[1]
            else:
                second_uid = link.split(":")[0]
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await refresh_avatar(tmp, self.server)
                await tmp.send(["rl.rmv", {"uid": second_uid}])

    async def add_progress(self, action, link):
        value = self.progresses[action]
        s = int(await self.server.redis.get(f"rl:{link}:s"))
        p = int(await self.server.redis.get(f"rl:{link}:p"))
        if 100 in self.statuses[s]["progress"]:
            max_value = 100
        else:
            max_value = 0
        if -100 in self.statuses[s]["progress"]:
            min_value = -100
        else:
            min_value = 0
        total = p + value
        if total >= max_value:
            total = 100
        elif min_value < min_value:
            total = -100
        if total in self.statuses[s]["progress"]:
            await self.server.redis.set(f"rl:{link}:p", 0)
            await self.server.redis.set(f"rl:{link}:s",
                                        self.statuses[s]["progress"][total])
            command = "rl.crs"
        else:
            await self.server.redis.set(f"rl:{link}:p", total)
            command = "rl.urp"
        for uid in link.split(":"):
            rl = await self._get_relation(uid, link)
            rl["chprr"] = action
            if uid in self.server.online:
                tmp = self.server.online[uid]
                if command == "rl.crs":
                    await refresh_avatar(tmp, self.server)
                await tmp.send([command, rl])

    async def get_link(self, uid1, uid2):
        rlts = await self.server.redis.smembers(f"rl:{uid1}")
        if f"{uid1}:{uid2}" in rlts:
            return f"{uid1}:{uid2}"
        elif f"{uid2}:{uid1}" in rlts:
            return f"{uid2}:{uid1}"
        else:
            return None

    async def _get_relation(self, uid, link):
        if link.split(":")[0] == uid:
            second_uid = link.split(":")[1]
        else:
            second_uid = link.split(":")[0]
        pipe = self.server.redis.pipeline()
        for item in ["p", "st", "ut", "s", "ring"]:
            pipe.get(f"rl:{link}:{item}")
        pipe.get(f"uid:{uid}:note:{second_uid}")
        result = await pipe.execute()
        try:
            rl = {"uid": second_uid, "rlt": {"p": int(result[0]),
                                             "st": int(result[1]),
                                             "ut": int(result[2]),
                                             "s": int(result[3]),
                                             "t": None}}
        except TypeError:
            await self.server.redis.srem(f"rl:{uid}", link)
            return
        if result[4]:
            if rl["rlt"]["s"] // 10 == 6:
                rl["rlt"]["t"] = {"er": result[4]}
            else:
                rl["rlt"]["t"] = {"mr": result[4], "wt": 1}
        if result[5]:
            rl["rlt"]["nt"] = result[5]
        return rl

    async def buy_ring(self, ring, uid):
        user_data = await self.server.get_user_data(uid)
        rings = {"engRing1": {"slvr": 15000, "gld": 0},
                 "engRing2": {"slvr": 0, "gld": 100},
                 "engRing3": {"slvr": 0, "gld": 300},
                 "mrRing1": {"slvr": 15000, "gld": 0},
                 "mrRing2": {"slvr": 0, "gld": 100},
                 "mrRing3": {"slvr": 0, "gld": 300}}
        price = rings[ring]
        if price["slvr"] > user_data["slvr"] or \
           price["gld"] > user_data["gld"]:
            return False
        r = self.server.redis
        await r.set(f"uid:{uid}:slvr", user_data["slvr"] - price["slvr"])
        await r.set(f"uid:{uid}:gld", user_data["gld"] - price["gld"])
        return True
