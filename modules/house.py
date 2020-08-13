import time
import asyncio
from modules.location import Location, gen_plr
from inventory import Inventory
import const

class_name = "House"


class House(Location):
    prefix = "h"

    def __init__(self, server):
        super().__init__(server)
        self.kicked = {}
        self.commands.update({"minfo": self.get_my_info, "gr": self.get_room,
                              "oinfo": self.owner_info,
                              "ioinfo": self.init_owner_info})

    async def get_my_info(self, msg, client):
        if msg[2]["onl"]:
            return await client.send(["h.minfo", {"scs": True}])
        apprnc = await self.server.get_appearance(client.uid)
        if not apprnc:
            return await client.send(["h.minfo", {"has.avtr": False}])
        user_data = await self.server.get_user_data(client.uid)
        if client.uid not in self.server.inv:
            self.server.inv[client.uid] = Inventory(self.server, client.uid)
            await self.server.inv[client.uid]._get_inventory()
        inv = self.server.inv[client.uid].get()
        cs = await self.server.get_clothes(client.uid, type_=1)
        rooms = []
        for item in await self.server.redis.smembers(f"rooms:{client.uid}"):
            room = await self.server.redis.lrange(f"rooms:{client.uid}:{item}",
                                                  0, -1)
            room_items = await self.server.get_room_items(client.uid, item)
            rooms.append({"f": room_items,
                          "w": 13, "id": item, "lev": int(room[1]), "l": 13,
                          "nm": room[0]})
            await asyncio.sleep(0.1)
        ac = {}
        for item in self.server.achievements:
            ac[item] = {"p": 0, "nWct": 0, "l": 3, "aId": item}
        tr = {}
        for item in self.server.trophies:
            if item in const.PREMIUM_TROPHIES:
                if not user_data["premium"]:
                    continue
            if item in const.BLACKLIST_TROPHIES:
                continue
            tr[item] = {"trrt": 0, "trcd": 0, "trid": item}
        plr = await gen_plr(client, self.server)
        plr.update({"cs": cs, "hs": {"r": rooms, "lt": 0}, "inv": inv,
                    "onl": True, "achc": {"ac": ac, "tr": tr}})
        plr["res"] = {"slvr": user_data["slvr"], "enrg": user_data["enrg"],
                      "emd": user_data["emd"], "gld": user_data["gld"]}
        await client.send(["h.minfo", {"plr": plr, "tm": 1}])
        await self._perform_login(client)

    async def owner_info(self, msg, client):
        uid = msg[2]["uid"]
        if not uid:
            return
        if uid in self.kicked and client.uid in self.kicked[uid]:
            return await client.send(["h.oinfo", {"kc": True}])
        plr = await gen_plr(uid, self.server)
        rooms = []
        tmp = await self.server.redis.smembers(f"rooms:{uid}")
        for item in tmp:
            room = await self.server.redis.lrange(f"rooms:{uid}:{item}", 0, -1)
            room_items = await self.server.get_room_items(uid, item)
            rooms.append({"f": room_items, "w": 13, "l": 13, "id": item,
                          "lev": int(room[1]), "nm": room[0]})
            await asyncio.sleep(0.1)
        ath = False
        for room_orig in self.server.rooms:
            room = room_orig.split("_")
            if room[0] == "house" and room[1] == uid:
                if uid in self.server.rooms[room_orig]:
                    ath = True
                    break
        await client.send(["h.oinfo", {"ath": ath, "plr": plr,
                                       "hs": {"r": rooms, "lt": 0}}])

    async def init_owner_info(self, msg, client):
        uid = msg[2]["uid"]
        if not uid:
            return
        plr = await gen_plr(uid, self.server)
        ath = False
        for room_orig in self.server.rooms:
            room = room_orig.split("_")
            if room[0] == "house" and room[1] == uid:
                if uid in self.server.rooms[room_orig]:
                    ath = True
                    break
        await client.send("h.ioinfo", {"tids": [], "ath": ath, "plr": plr})

    async def get_room(self, msg, client):
        room = f"{msg[2]['lid']}_{msg[2]['gid']}_{msg[2]['rid']}"
        if client.room:
            await self.leave_room(client)
        if msg[2]["gid"] in self.kicked and \
           client.uid in self.kicked[msg[2]["gid"]]:
            return
        await self.join_room(client, room)
        if client.uid == msg[2]["gid"]:
            await self.owner_at_house(client.uid, True)
        await client.send(["h.gr", {"rid": client.room}])

    async def owner_at_house(self, owner, ath):
        for room_orig in self.server.rooms.copy():
            room = room_orig.split("_")
            if room[0] == "house" and room[1] == owner:
                for uid in self.server.rooms[room_orig].copy():
                    try:
                        tmp = self.server.online[uid]
                    except KeyError:
                        continue
                    await tmp.send(["h.oah", {"ath": ath}])

    async def room(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "info":
            rmmb = []
            try:
                room = self.server.rooms[msg[0]].copy()
            except KeyError:
                await client.send(["cp.ms.rsm", {"txt": "Произошла ошибка, "
                                                        "перезайдите в игру"}])
                return
            online = self.server.online
            for uid in room:
                try:
                    tmp = online[uid]
                except KeyError:
                    continue
                rmmb.append(await gen_plr(tmp, self.server))
            room_addr = f"rooms:{msg[2]['uid']}:{msg[2]['rid']}"
            tmp = await self.server.redis.lrange(room_addr, 0, -1)
            if not tmp:
                await client.send(["cp.ms.rsm", {"txt": "Комната не найдена, "
                                                        "напишите в "
                                                        "техподдержку"
                                                        f"({room_addr})"}])
                return
            room_items = await self.server.get_room_items(msg[2]["uid"],
                                                          msg[2]["rid"])
            room = {"f": room_items, "w": 13, "id": msg[2]["rid"],
                    "l": 13, "lev": int(tmp[1]), "nm": tmp[0]}
            evn = None
            if uid in self.server.modules["ev"].events:
                event = await self.server.modules["ev"]._get_event(uid)
                event_room = f"house_{uid}_{event['l']}"
                if event_room == msg[0]:
                    evn = event
            await client.send(["h.r.info", {"rmmb": rmmb, "rm": room,
                                            "evn": evn}])
        elif subcommand == "rfr":
            redis = self.server.redis
            room = msg[0].split("_")[-1]
            room_data = await redis.lrange(f"rooms:{client.uid}:{room}", 0, -1)
            room_items = await self.server.get_room_items(client.uid, room)
            online = self.server.online
            if msg[0] not in self.server.rooms:
                return
            room_tmp = self.server.rooms[msg[0]].copy()
            for uid in room_tmp:
                try:
                    tmp = online[uid]
                except KeyError:
                    continue
                await tmp.send(["h.r.rfr", {"rm": {"f": room_items, "w": 13,
                                                   "l": 13,
                                                   "lev": int(room_data[1]),
                                                   "nm": room_data[0]}}])
        elif subcommand == "kc":
            tmid = msg[2]["tmid"]
            owner = msg[0].split("_")[1]
            if owner != client.uid:
                return
            owner_data = await self.server.get_user_data(client.uid)
            user_data = await self.server.get_user_data(tmid)
            if user_data["role"] and not owner_data["role"]:
                return
            if owner not in self.kicked:
                self.kicked[owner] = {}
            self.kicked[owner][tmid] = time.time()
            room_tmp = self.server.rooms[msg[0]].copy()
            for uid in room_tmp:
                if uid not in self.server.online:
                    continue
                tmp = self.server.online[uid]
                if uid == tmid:
                    await tmp.send(["h.r.kc", {}])
                    await self.leave_room(tmp)
                await tmp.send([msg[0], tmid])
        else:
            await super().room(msg, client)

    async def _perform_login(self, client):
        await client.send(["cm.new", {"campaigns": const.campaigns}])
        await client.send(["cp.cht.gbl", {"blcklst": {"uids": []}}])
        await client.send(["nws.hasnews", {"gnexst": False, "gnunr": False}])

    async def _background(self):
        while True:
            for owner in self.kicked.copy():
                for uid in self.kicked[owner]:
                    if time.time() - self.kicked[owner][uid] >= 1800:
                        del self.kicked[owner][uid]
            await asyncio.sleep(60)
