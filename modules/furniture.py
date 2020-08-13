from modules.base_module import Module
from modules.location import get_city_info
import modules.notify as notify
import const

class_name = "Furniture"


class Furniture(Module):
    prefix = "frn"

    def __init__(self, server):
        self.server = server
        self.commands = {"save": self.save_layout, "buy": self.buy,
                         "rnmrm": self.room_rename,
                         "bnrm": self.buy_new_room}
        self.frn_list = server.parser.parse_furniture()

    async def save_layout(self, msg, client):
        room = msg[0].split("_")
        uid = client.uid
        if room[1] != uid:
            await client.send(["cp.ms.rsm", {"txt": "save_layout ошибка 1"}])
            return
        for item in msg[2]["f"]:
            if item["t"] == 0:
                await self.type_add(item, room, uid)
            elif item["t"] == 1:
                code = await self.type_update(item, room, uid)
                if code == 0:
                    await client.send(["cp.ms.rsm", {"txt": "Превышен лимит "
                                                            "предметов"}])
                    return
            elif item["t"] == 2:
                await self.type_remove(item, room, uid)
            elif item["t"] == 3:
                await self.type_replace_door(item, room, uid)
            elif item["t"] == 4:
                await self.type_change_color(item, room, uid)
        inv = self.server.inv[uid].get()
        room_inf = await self.server.redis.lrange(f"rooms:{uid}:{room[2]}",
                                                  0, -1)
        room_items = await self.server.get_room_items(uid, room[2])
        await self.update_hrt(uid)
        ci = await get_city_info(client.uid, self.server)
        await client.send(["frn.save", {"inv": inv, "ci": ci,
                                        "hs": {"f": room_items, "w": 13,
                                               "id": room[2], "l": 13,
                                               "lev": int(room_inf[1]),
                                               "nm": room[0]}}])
        await self.server.modules["h"].room([msg[0], "h.r.rfr"], client)

    async def type_add(self, item, room, uid):
        redis = self.server.redis
        items = await redis.smembers(f"rooms:{uid}:{room[2]}:items")
        if not await self.server.inv[uid].take_item(item["tpid"]):
            return
        if any(ext in item["tpid"].lower() for ext in ["wll", "wall"]):
            walls = []
            for wall in ["wall", "wll"]:
                for room_item in items:
                    if wall in room_item.lower():
                        await self.del_item(room_item, room[2], uid)
                        tmp = room_item.split("_")[0]
                        if tmp not in walls:
                            walls.append(tmp)
                            await self.server.inv[uid].add_item(tmp, "frn")
            item["x"] = 0.0
            item["y"] = 0.0
            item["z"] = 0.0
            item["d"] = 3
            await self.add_item(item, room[2], uid)
            item["x"] = 13.0
            item["d"] = 5
            item["oid"] += 1
            await self.add_item(item, room[2], uid)
        elif any(ext in item["tpid"].lower() for ext in ["flr", "floor"]):
            for floor in ["flr", "floor"]:
                for room_item in items:
                    if floor in room_item.lower():
                        await self.del_item(room_item, room[2], uid)
                        tmp = room_item.split("_")[0]
                        await self.server.inv[uid].add_item(tmp, "frn")
            item["x"] = 0.0
            item["y"] = 0.0
            item["z"] = 0.0
            item["d"] = 5
            await self.add_item(item, room[2], uid)

    async def type_update(self, item, room, uid):
        redis = self.server.redis
        items = await redis.smembers(f"rooms:{uid}:{room[2]}:items")
        if len(items) >= 70:
            prem = await redis.get(f"uid:{uid}:premium")
            if not prem:
                return 0
            elif len(items) >= 120:
                return 0
        name = f"{item['tpid']}_{item['oid']}"
        if name in items:
            await self.update_pos_and_params(name, room[2], uid, item)
        else:
            if not await self.server.inv[uid].take_item(item["tpid"]):
                return 1
            await self.add_item(item, room[2], uid)
            if item["tpid"] in ["colorSmallCarpet", "colorBigCarpet"]:
                item["clr"] = "red"
                await self.type_change_color(item, room, uid)
            if item["tpid"] == "colorWheel":
                await self.init_wheel(item, room, uid)
        return 1

    async def type_remove(self, item, room, uid):
        redis = self.server.redis
        items = await redis.smembers(f"rooms:{uid}:{room[2]}:items")
        name = f"{item['tpid']}_{item['oid']}"
        if name not in items:
            return
        await self.del_item(name, room[2], uid)
        await self.server.inv[uid].add_item(item["tpid"], "frn")

    async def type_replace_door(self, item, room, uid):
        redis = self.server.redis
        items = await redis.smembers(f"rooms:{uid}:{room[2]}:items")
        found = None
        for tmp in items:
            oid = int(tmp.split("_")[1])
            if oid == item["oid"]:
                found = tmp
                break
        if not found:
            return
        if not await self.server.inv[uid].take_item(item["tpid"]):
            return
        data = await redis.lrange(f"rooms:{uid}:{room[2]}:items:{found}",
                                  0, -1)
        options = await redis.smembers(f"rooms:{uid}:{room[2]}:items:{found}:"
                                       "options")
        if "rid" in options:
            rid = await redis.get(f"rooms:{uid}:{room[2]}:items:{found}:rid")
        else:
            rid = None
        await self.del_item(found, room[2], uid)
        await self.server.inv[uid].add_item(found.split("_")[0], "frn")
        item.update({"x": float(data[0]), "y": float(data[1]),
                     "z": float(data[2]), "d": int(data[3]),
                     "rid": rid})
        await self.add_item(item, room[2], uid)

    async def type_change_color(self, item, room, uid):
        redis = self.server.redis
        items = await redis.smembers(f"rooms:{uid}:{room[2]}:items")
        name = f"{item['tpid']}_{item['oid']}"
        if name not in items:
            return
        await redis.sadd(f"rooms:{uid}:{room[2]}:items:{name}:options", "clr")
        await redis.set(f"rooms:{uid}:{room[2]}:items:{name}:clr", item["clr"])

    async def init_wheel(self, item, room, uid):
        redis = self.server.redis
        name = f"colorWheel_{item['oid']}"
        await redis.sadd(f"rooms:{uid}:{room[2]}:items:{name}:options",
                         "rsClr")
        await redis.sadd(f"rooms:{uid}:{room[2]}:items:{name}:options", "clrs")
        for item in ["violet", "yellow", "blue", "red", "green", "orange"]:
            await redis.sadd(f"rooms:{uid}:{room[2]}:items:{name}:clrs", item)

    async def buy(self, msg, client):
        item = msg[2]["tpid"]
        amount = msg[2]["cnt"]
        uid = client.uid
        if item not in self.frn_list:
            return
        user_data = await self.server.get_user_data(uid)
        gold = self.frn_list[item]["gold"]*amount
        silver = self.frn_list[item]["silver"]*amount
        if user_data["gld"] < gold or user_data["slvr"] < silver:
            return
        redis = self.server.redis
        await redis.set(f"uid:{uid}:gld", user_data["gld"] - gold)
        await redis.set(f"uid:{uid}:slvr", user_data["slvr"] - silver)
        await self.server.inv[uid].add_item(item, "frn", amount)
        amount = int(await redis.lindex(f"uid:{uid}:items:{item}", 1))
        await client.send(["ntf.inv", {"it": {"c": amount, "iid": "",
                                              "tid": item}}])
        await notify.update_resources(client, self.server)

    async def room_rename(self, msg, client):
        id_ = msg[2]["id"]
        redis = self.server.redis
        rooms = await redis.smembers(f"rooms:{client.uid}")
        if id_ not in rooms:
            await client.send(["cp.ms.rsm", {"txt": "Комната не найдена"}])
            return
        await redis.lset(f"rooms:{client.uid}:{id_}", 0, msg[2]["nm"])
        await client.send(["frn.rnmrm", {"id": id_, "nm": msg[2]["nm"]}])

    async def add_item(self, item, room, uid):
        redis = self.server.redis
        await redis.sadd(f"rooms:{uid}:{room}:items",
                         f"{item['tpid']}_{item['oid']}")
        if "rid" in item:
            await redis.sadd(f"rooms:{uid}:{room}:items:"
                             f"{item['tpid']}_{item['oid']}:options", "rid")
            if item["rid"]:
                await redis.set(f"rooms:{uid}:{room}:items:"
                                f"{item['tpid']}_{item['oid']}:rid",
                                item["rid"])
        await redis.rpush(f"rooms:{uid}:{room}:items:"
                          f"{item['tpid']}_{item['oid']}", item["x"],
                          item["y"], item["z"], item["d"])

    async def update_pos_and_params(self, name, room, uid, new_item):
        redis = self.server.redis
        await redis.delete(f"rooms:{uid}:{room}:items:{name}")
        await redis.rpush(f"rooms:{uid}:{room}:items:{name}",
                          new_item["x"], new_item["y"], new_item["z"],
                          new_item["d"])

    async def del_item(self, item, room, uid):
        redis = self.server.redis
        items = await redis.smembers(f"rooms:{uid}:{room}:items")
        if item not in items:
            return
        options = await redis.smembers(f"rooms:{uid}:{room}:items:{item}"
                                       ":options")
        for op in options:
            await redis.delete(f"rooms:{uid}:{room}:items:{item}:{op}")
        await redis.delete(f"rooms:{uid}:{room}:items:{item}:options")
        await redis.srem(f"rooms:{uid}:{room}:items", item)
        await redis.delete(f"rooms:{uid}:{room}:items:{item}")

    async def buy_new_room(self, msg, client):
        user_data = await self.server.get_user_data(client.uid)
        r = self.server.redis
        i = 0
        available = await r.get(f"uid:{client.uid}:rooms")
        if available:
            available = int(available)
        else:
            available = 0
        rooms = await r.smembers(f"rooms:{client.uid}")
        for room in rooms:
            if await r.get(f"rooms:{client.uid}:{room}:premium"):
                i += 1
        if user_data["premium"]:
            if i >= 4:
                if len(rooms)-i-6 >= available:
                    return
        else:
            if len(rooms)-i-6 >= available:
                return
        room = client.room.split("_")
        if room[1] != client.uid:
            return
        rid = f"room{len(rooms)}"
        item = msg[2]["ltml"]
        item["tpid"] = "door1"
        item["rid"] = rid
        item["oid"] = item["lid"]
        await self.add_item(item, room[2], client.uid)
        await r.sadd(f"rooms:{client.uid}", rid)
        await r.rpush(f"rooms:{client.uid}:{rid}",
                      msg[2]["nm"], 2)
        if user_data["premium"] and i < 4:
            print("set premium room")
            await r.set(f"rooms:{client.uid}:{rid}:premium", 1)
        for item in const.room_items:
            if item["tpid"] == "door4":
                item["rid"] = room[2]
            await self.add_item(item, rid, client.uid)
        await client.send(["frn.bnrm", {"r": {"f": [],
                                              "w": 13, "id": rid,
                                              "lev": 2, "l": 13,
                                              "nm": msg[2]["nm"]}}])


    async def update_hrt(self, uid):
        redis = self.server.redis
        hrt = 0
        for room in await redis.smembers(f"rooms:{uid}"):
            for item in await redis.smembers(f"rooms:{uid}:{room}:items"):
                item = item.split("_")[0]
                if item not in self.frn_list:
                    continue
                hrt += self.frn_list[item]["rating"]
        await redis.set(f"uid:{uid}:hrt", hrt)
        return hrt
