import logging
import const


class Inventory():
    def __init__(self, server, uid):
        self.server = server
        self.uid = uid
        self.expire = 0
        if uid in const.DEBUG:
            self.debug = True
        else:
            self.debug = False

    def get(self):
        return self.inv

    def log(self, msg):
        if self.debug:
            logging.debug(msg)

    async def add_item(self, name, type_, amount=1):
        if "_" in name:
            tid, iid = name.split("_")
        else:
            tid = name
            iid = ""
        redis = self.server.redis
        item = await redis.lrange(f"uid:{self.uid}:items:{name}", 0, -1)
        if item:
            if type_ == "cls":
                return
            await redis.lset(f"uid:{self.uid}:items:{name}", 1,
                             int(item[1])+amount)
            for tmp in self.inv["c"][type_]["it"]:
                if tmp["tid"] == tid and tmp["iid"] == iid:
                    tmp["c"] = int(item[1])+amount
                    break
        else:
            await redis.sadd(f"uid:{self.uid}:items", name)
            await redis.rpush(f"uid:{self.uid}:items:{name}", type_, amount)
            type_items = self.inv["c"][type_]["it"]
            type_items.append({"c": amount, "tid": tid, "iid": iid})

    async def take_item(self, item, amount=1):
        redis = self.server.redis
        items = await redis.smembers(f"uid:{self.uid}:items")
        if item not in items:
            return False
        tmp = await redis.lrange(f"uid:{self.uid}:items:{item}", 0, -1)
        if not tmp:
            await redis.srem(f"uid:{self.uid}:items", item)
            return False
        type_ = tmp[0]
        have = int(tmp[1])
        del tmp
        if have < amount:
            return False
        type_items = self.inv["c"][type_]["it"]
        if have > amount:
            await redis.lset(f"uid:{self.uid}:items:{item}", 1, have - amount)
            for tmp in type_items:
                if tmp["tid"] == item:
                    tmp["c"] = have - amount
                    break
        else:
            await redis.delete(f"uid:{self.uid}:items:{item}")
            await redis.srem(f"uid:{self.uid}:items", item)
            for tmp in type_items:
                if tmp["tid"] == item:
                    type_items.remove(tmp)
                    break
        return True

    async def get_item(self, item):
        redis = self.server.redis
        items = await redis.smembers(f"uid:{self.uid}:items")
        if item not in items:
            return 0
        have = int(await redis.lindex(f"uid:{self.uid}:items:{item}", 1))
        return have

    async def change_wearing(self, cloth, wearing):
        redis = self.server.redis
        if not await redis.lindex(f"uid:{self.uid}:items:{cloth}", 0):
            not_found = True
        else:
            not_found = False
        if "_" in cloth:
            tid, iid = cloth.split("_")
        else:
            tid = cloth
            iid = ""
        type_items = self.inv["c"]["cls"]["it"]
        ctp = await redis.get(f"uid:{self.uid}:wearing")
        if wearing:
            if not_found:
                logging.info(f"Cloth {cloth} not found for {self.uid}")
                return
            if "_" in cloth:
                name = cloth.split("_")[0]
            else:
                name = cloth
            await self._check_conflicts(name)
            for item in type_items:
                if item["tid"] == tid and item["iid"] == iid:
                    type_items.remove(item)
                    break
            await redis.sadd(f"uid:{self.uid}:{ctp}", cloth)
        else:
            weared = await redis.smembers(f"uid:{self.uid}:{ctp}")
            if cloth not in weared:
                logging.info(f"Cloth {cloth} not weared for {self.uid}")
                return
            if not not_found:
                type_items.append({"c": 1, "iid": iid, "tid": tid})
            await redis.srem(f"uid:{self.uid}:{ctp}", cloth)

    def __get_expire(self):
        return self.__expire

    def __set_expire(self, value):
        self.__expire = value

    expire = property(__get_expire, __set_expire)

    async def _get_inventory(self):
        self.inv = {"c": {"frn": {"id": "frn", "it": []},
                          "act": {"id": "act", "it": []},
                          "gm": {"id": "gm", "it": []},
                          "lt": {"id": "lt", "it": []},
                          "cls": {"id": "cls", "it": []}}}
        ctp = await self.server.redis.get(f"uid:{self.uid}:wearing")
        wearing = await self.server.redis.smembers(f"uid:{self.uid}:{ctp}")
        keys = []
        pipe = self.server.redis.pipeline()
        for item in await self.server.redis.smembers(f"uid:{self.uid}:items"):
            if item in wearing:
                continue
            pipe.lrange(f"uid:{self.uid}:items:{item}", 0, -1)
            keys.append(item)
        items = await pipe.execute()
        for i in range(len(keys)):
            name = keys[i]
            item = items[i]
            if not item:
                continue
            if "_" in name:
                self.inv["c"][item[0]]["it"].append({"c": int(item[1]),
                                                     "iid": name.split("_")[1],
                                                     "tid": name.split("_")[0]}
                                                    )
            else:
                try:
                    self.inv["c"][item[0]]["it"].append({"c": int(item[1]),
                                                         "iid": "",
                                                         "tid": name})
                except IndexError:
                    r = self.server.redis
                    await r.srem(f"uid:{self.uid}:items", name)
                    await r.delete(f"uid:{self.uid}:items:{name}")

    async def _check_conflicts(self, cloth):
        apprnc = await self.server.get_appearance(self.uid)
        gender = "boy" if (apprnc)["g"] == 1 else "girl"
        category = self.server.modules["a"].get_category(cloth, gender)
        if not category:
            logging.info("Category not found")
            return
        ctp = await self.server.redis.get(f"uid:{self.uid}:wearing")
        weared = await self.server.redis.smembers(f"uid:{self.uid}:{ctp}")
        for weared_cloth in weared:
            if self._has_conflict(weared_cloth, category, gender):
                await self.change_wearing(weared_cloth, False)

    def _has_conflict(self, cloth, category, gender):
        get_category = self.server.modules["a"].get_category
        cloth_category = get_category(cloth, gender)
        if cloth_category == category:
            return True
        for conflict in self.server.conflicts:
            if (conflict[0] == category and
                conflict[1] == cloth_category) or \
               (conflict[1] == category and
               conflict[0] == cloth_category):
                return True
        return False
