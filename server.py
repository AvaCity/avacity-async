import importlib
import asyncio
import logging
from datetime import datetime
import time
import json
import os.path
import aioredis
import exceptions
import websockets
import const
from client import Client
from inventory import Inventory
from xml_parser import Parser

modules = ["client_error", "house", "outside", "user_rating", "mail", "avatar",
           "location_game", "relations", "social_request", "user_rating",
           "competition", "furniture", "billing", "component", "support",
           "passport", "player", "statistics", "shop", "mobile", "confirm",
           "craft", "profession", "inventory", "event", "chat_decor", "hs",
           "clan", "clan_request", "clan_member", "descriptor",
           "clan_activity", "clan_news", "access_location", "room",
           "clan_location", "work", "photosalon"]


class Server():
    def __init__(self, host="0.0.0.0", port=8123):
        self.online = {}
        self.slots = []
        self.rooms = {}
        self.inv = {}
        self.msgmeter = {}
        self.parser = Parser()
        self.conflicts = self.parser.parse_conflicts()
        self.achievements = self.parser.parse_achievements()
        self.trophies = self.parser.parse_trophies()
        self.game_items = self.parser.parse_game_items()
        self.appearance = self.parser.parse_appearance()
        self.modules = {}
        for item in modules:
            module = importlib.import_module(f"modules.{item}")
            class_ = getattr(module, module.class_name)
            self.modules[class_.prefix] = class_(self)
        self.kicked = []

    async def listen(self):
        self.redis = await aioredis.create_redis_pool("redis://localhost",
                                                      encoding="utf-8")
        loop = asyncio.get_event_loop()
        for prefix in self.modules:
            module = self.modules[prefix]
            if hasattr(module, "_background"):
                loop.create_task(module._background())
                print(f"{prefix} background")
        self.server = await asyncio.start_server(self.new_conn,
                                                 "0.0.0.0", 8123)
        loop.create_task(self._background())
        await websockets.server.serve(self.handle_websocket,
                                      "localhost", 8765)
        logging.info("Сервер готов принимать соединения")

    async def stop(self):
        logging.info("Выключение...")
        for uid in self.online.copy():
            try:
                await self.online[uid].send([6, "Restart", {}], type_=2)
            except Exception:
                continue
        self.server.close()
        await self.server.wait_closed()

    async def handle_websocket(self, websocket, path):
        data = json.loads(await websocket.recv())
        if data["action"] == "get_online":
            await websocket.send(json.dumps({"action": "online",
                                             "online": len(self.online)}))

    async def new_conn(self, reader, writer):
        loop = asyncio.get_event_loop()
        loop.create_task(Client(self).handle(reader, writer))

    async def process_data(self, data, client):
        if not client.uid:
            if data["type"] != 1:
                return client.writer.close()
            return await self.auth(data["msg"], client)
        if data["type"] == 2:
            return client.writer.close()
        elif data["type"] == 17:
            await client.send([data["msg"][0], client.uid], type_=17)
            if data["msg"][0].split("_")[0] == "game":
                await self.modules["lg"].exit_game(data["msg"][0], client)
        elif data["type"] == 34:
            if data["msg"][1] == "clerr":
                return
            if client.uid in self.msgmeter:
                self.msgmeter[client.uid] += 1
                if self.msgmeter[client.uid] > 160:
                    if client.uid in self.kicked:
                        return client.writer.close()
                    self.kicked.append(client.uid)
                    logging.debug(f"Кик {client.uid} за превышение лимитов")
                    await client.send(["cp.ms.rsm", {"txt": "Вы были кикнуты "
                                                            "за превышение "
                                                            "лимитов"}])
                    await client.send([5, "Limits kick", {}], type_=2)
                    return client.writer.close()
            else:
                self.msgmeter[client.uid] = 1
            client.last_msg = time.time()
            prefix = data["msg"][1].split(".")[0]
            if prefix not in self.modules:
                logging.warning(f"Command {data['msg'][1]} not found")
                return
            if not client.drop:
                if client.debug:
                    logging.debug(f"uid: {client.uid}, {data}")
                await self.modules[prefix].on_message(data["msg"], client)
            # asyncio.create_task(self.modules[prefix].on_message(data["msg"],
            #                                                    client))

    async def auth(self, msg, client):
        uid = await self.redis.get(f"auth:{msg[2]}")
        if not uid:
            await client.send([5, "Key is invalid", {}], type_=2)
            client.writer.close()
            return
        cfghash = msg[3]["cfghsh"]
        if not os.path.exists(f"files/data/config_all_ru_{cfghash}.zip"):
            print(f"КОНФИГ ЛЕВЫЙ - {uid}")
            banned = await self.redis.get(f"uid:{uid}:banned")
            if not banned and uid != "38046":
                await self.redis.set(f"uid:{uid}:banned", 0)
                await self.redis.set(f"uid:{uid}:ban_time", int(time.time()))
                await self.redis.set(f"uid:{uid}:ban_end", 0)
                await self.redis.set(f"uid:{uid}:ban_reason", "Читы")
                message = f"{uid} получил автобан\nПричина: читы"
                await self.modules["cp"].send_tg(message)
        banned = await self.redis.get(f"uid:{uid}:banned")
        if banned:
            ban_time = int(await self.redis.get(f"uid:{uid}:ban_time"))
            ban_end = int(await self.redis.get(f"uid:{uid}:ban_end"))
            reason = await self.redis.get(f"uid:{uid}:ban_reason")
            if not reason:
                reason = ""
            category = await self.redis.get(f"uid:{uid}:ban_category")
            if category:
                category = int(category)
            else:
                category = 4
            if ban_end == 0:
                time_left = 0
            else:
                time_left = ban_end - int(time.time()*1000)
            if time_left < 0 and ban_end != 0:
                await self.redis.delete(f"uid:{uid}:banned")
                await self.redis.delete(f"uid:{uid}:ban_time")
                await self.redis.delete(f"uid:{uid}:ban_end")
                await self.redis.delete(f"uid:{uid}:ban_reason")
            else:
                await client.send([10, "User is banned",
                                   {"duration": 999999, "banTime": ban_time,
                                    "notes": reason, "reviewerId": banned,
                                    "reasonId": category, "unbanType": "none",
                                    "leftTime": time_left, "id": None,
                                    "reviewState": 1, "userId": uid,
                                    "moderatorId": banned}], type_=2)
                client.writer.close()
                return
        if uid in self.online:
            try:
                await self.online[uid].send([6, {}], type_=3)
                self.online[uid].writer.close()
            except OSError:
                pass
        user_data = await self.get_user_data(uid)
        if not user_data:
            pipe = self.redis.pipeline()
            pipe.set(f"uid:{uid}:slvr", 1000)
            pipe.set(f"uid:{uid}:gld", 6)
            pipe.set(f"uid:{uid}:enrg", 100)
            pipe.set(f"uid:{uid}:exp", 493500)
            pipe.set(f"uid:{uid}:emd", 0)
            pipe.set(f"uid:{uid}:lvt", 0)
            await pipe.execute()
            user_data = await self.get_user_data(uid)
        role = user_data["role"]
        if len(self.slots) >= 1700 and uid not in self.slots and not role and \
           not user_data["premium"]:
            await client.send([10, "User is banned",
                               {"duration": 999999, "banTime": 1,
                                "notes": "Сервер переполнен, пожалуйста, "
                                         "попытайтесь войти чуть позже. "
                                         "Игроки купившие премиум могут "
                                         "входить на переполненный сервер "
                                         "без ограничений!",
                                "reviewerId": "1", "reasonId": 4,
                                "unbanType": "none", "leftTime": 0,
                                "id": None, "reviewState": 1, "userId": uid,
                                "moderatorId": "1"}], type_=2)
            client.writer.close()
            return
        if uid not in self.slots:
            self.slots.append(uid)
        client.uid = uid
        client.user_data["id"] = uid
        email = await self.redis.get(f"uid:{uid}:email")
        if email:
            client.user_data["email"] = email
        self.online[uid] = client
        await self.redis.set(f"uid:{uid}:lvt", int(time.time()))
        await self.check_new_act(client, user_data["lvt"])
        await self.redis.set(f"uid:{uid}:ip", client.addr)
        if uid not in self.inv:
            self.inv[uid] = Inventory(self, uid)
            await self.inv[uid]._get_inventory()
        else:
            self.inv[uid].expire = 0
        if user_data["prem_time"] != 0 and \
           time.time() - user_data["prem_time"] > 0:
            await self.remove_premium(uid)
        await client.send([client.uid, "", True, False, False], type_=1)
        client.checksummed = True

    async def check_new_act(self, client, lvt):
        now = datetime.now()
        old = datetime.fromtimestamp(lvt)
        give = False
        if now.day - old.day == 1:
            give = True
        else:
            delta = now - old
            if now.day != old.day:
                if delta.days <= 1:
                    give = True
                else:
                    await self.redis.delete(f"uid:{client.uid}:days")
        if give:
            strik = await self.redis.get(f"uid:{client.uid}:days")
            if not strik:
                strik = 1
            else:
                strik = int(strik)
                if strik >= 5:
                    user_data = await self.get_user_data(client.uid)
                    if user_data["premium"] and strik < 8:
                        strik += 1
                else:
                    strik += 1
            await self.redis.incrby(f"uid:{client.uid}:act", strik)
            await self.redis.set(f"uid:{client.uid}:days", strik)

    async def remove_premium(self, uid):
        clothes = self.modules["a"].clothes_list
        apprnc = await self.redis.lindex(f"uid:{uid}:appearance", 2)
        if not apprnc:
            return
        if apprnc == "1":
            gender = "boy"
        else:
            gender = "girl"
        items = await self.redis.smembers(f"uid:{uid}:items")
        crt = int(await self.redis.get(f"uid:{uid}:crt"))
        for category in clothes[gender]:
            for item in clothes[gender][category]:
                if not clothes[gender][category][item]["vipOnly"]:
                    continue
                for tmp in items:
                    if item not in tmp:
                        continue
                    await self.inv[uid].take_item(item)
                    crt -= clothes[gender][category][item]["rating"]
                    for ctp in ["casual", "club", "official", "swimwear",
                                "underdress"]:
                        await self.redis.srem(f"uid:{uid}:{ctp}", item)
                    break
        await self.redis.set(f"uid:{uid}:crt", crt)
        await self.redis.set(f"uid:{uid}:wearing", "casual")
        for item in const.PREMIUM_BUBBLES:
            await self.inv[uid].take_item(item)
        await self.redis.delete(f"uid:{uid}:trid")
        await self.redis.delete(f"uid:{uid}:bubble")
        await self.redis.delete(f"uid:{uid}:premium")

    async def get_user_data(self, uid):
        pipe = self.redis.pipeline()
        pipe.get(f"uid:{uid}:slvr")
        pipe.get(f"uid:{uid}:enrg")
        pipe.get(f"uid:{uid}:gld")
        pipe.get(f"uid:{uid}:exp")
        pipe.get(f"uid:{uid}:emd")
        pipe.get(f"uid:{uid}:lvt")
        pipe.get(f"uid:{uid}:trid")
        pipe.get(f"uid:{uid}:crt")
        pipe.get(f"uid:{uid}:hrt")
        pipe.get(f"uid:{uid}:act")
        pipe.get(f"uid:{uid}:role")
        pipe.get(f"uid:{uid}:premium")
        result = await pipe.execute()
        if not result[0]:
            return None
        if result[5]:
            lvt = int(result[5])
        else:
            lvt = 0
        if result[7]:
            crt = int(result[7])
        else:
            crt = await self.modules["a"].update_crt(uid)
        if result[8]:
            hrt = int(result[8])
        else:
            hrt = await self.modules["frn"].update_hrt(uid)
        if result[9]:
            act = int(result[9])
        else:
            act = 0
        if result[10]:
            role = int(result[10])
        else:
            role = 0
        premium = False
        if result[11]:
            prem_time = int(result[11])
            if prem_time == 0 or prem_time - time.time() > 0:
                premium = True
        else:
            prem_time = 0
        return {"uid": uid, "slvr": int(result[0]), "enrg": int(result[1]),
                "gld": int(result[2]), "exp": int(result[3]),
                "emd": int(result[4]), "lvt": lvt, "crt": crt, "act": act,
                "hrt": hrt, "trid": result[6], "role": role,
                "premium": premium, "prem_time": prem_time}

    async def get_appearance(self, uid):
        apprnc = await self.redis.lrange(f"uid:{uid}:appearance", 0, -1)
        if not apprnc:
            return False
        return {"n": apprnc[0], "nct": int(apprnc[1]), "g": int(apprnc[2]),
                "sc": int(apprnc[3]), "ht": int(apprnc[4]),
                "hc": int(apprnc[5]), "brt": int(apprnc[6]),
                "brc": int(apprnc[7]), "et": int(apprnc[8]),
                "ec": int(apprnc[9]), "fft": int(apprnc[10]),
                "fat": int(apprnc[11]), "fac": int(apprnc[12]),
                "ss": int(apprnc[13]), "ssc": int(apprnc[14]),
                "mt": int(apprnc[15]), "mc": int(apprnc[16]),
                "sh": int(apprnc[17]), "shc": int(apprnc[18]),
                "rg": int(apprnc[19]), "rc": int(apprnc[20]),
                "pt": int(apprnc[21]), "pc": int(apprnc[22]),
                "bt": int(apprnc[23]), "bc": int(apprnc[24])}

    async def get_clothes(self, uid, type_):
        clothes = []
        cur_ctp = await self.redis.get(f"uid:{uid}:wearing")
        for item in await self.redis.smembers(f"uid:{uid}:{cur_ctp}"):
            if "_" in item:
                id_, clid = item.split("_")
                clothes.append({"id": id_, "clid": clid})
            else:
                clothes.append({"id": item, "clid": ""})
        if type_ == 1:
            ctps = ["casual", "club", "official", "swimwear", "underdress"]
            clths = {"cc": cur_ctp, "ccltns": {}}
            clths["ccltns"][cur_ctp] = {"cct": [], "cn": "", "ctp": cur_ctp}
            for item in clothes:
                if item["clid"]:
                    clths["ccltns"][cur_ctp]["cct"].append(f"{item['id']}:"
                                                           f"{item['clid']}")
                else:
                    clths["ccltns"][cur_ctp]["cct"].append(item["id"])
            ctps.remove(cur_ctp)
            for ctp in ctps:
                clths["ccltns"][ctp] = {"cct": [], "cn": "", "ctp": ctp}
                clothes = []
                for item in await self.redis.smembers(f"uid:{uid}:{ctp}"):
                    if "_" in item:
                        id_, clid = item.split("_")
                        clothes.append({"id": id_, "clid": clid})
                    else:
                        clothes.append({"id": item, "clid": ""})
                for item in clothes:
                    if item["clid"]:
                        clths["ccltns"][ctp]["cct"].append(f"{item['id']}:"
                                                           f"{item['clid']}")
                    else:
                        clths["ccltns"][ctp]["cct"].append(item["id"])
        elif type_ == 2:
            clths = {"clths": []}
            for item in clothes:
                clths["clths"].append({"tpid": item["id"],
                                       "clid": item["clid"]})
        elif type_ == 3:
            clths = {"cct": [], "cn": "", "ctp": cur_ctp}
            for item in clothes:
                if item["clid"]:
                    clths["cct"].append(f"{item['id']}:{item['clid']}")
                else:
                    clths["cct"].append(item["id"])
        return clths

    async def get_room_items(self, uid, room):
        if "_" in room:
            raise exceptions.WrongRoom()
        names = []
        pipe = self.redis.pipeline()
        spipe = self.redis.pipeline()
        for name in await self.redis.smembers(f"rooms:{uid}:{room}:items"):
            pipe.lrange(f"rooms:{uid}:{room}:items:{name}", 0, -1)
            spipe.smembers(f"rooms:{uid}:{room}:items:{name}:options")
            names.append(name)
        result = await pipe.execute()
        options = await spipe.execute()
        i = 0
        items = []
        for name in names:
            name, lid = name.split("_")
            item = result[i]
            option = options[i]
            try:
                tmp = {"tpid": name, "x": float(item[0]),
                       "y": float(item[1]), "z": float(item[2]),
                       "d": int(item[3]), "lid": int(lid)}
            except IndexError:
                await self.redis.srem(f"rooms:{uid}:{room}:items",
                                      f"{name}_{lid}")
                await self.redis.delete(f"rooms:{uid}:{room}:items:"
                                        f"{name}_{lid}")
                continue
            for kek in option:
                if kek == "clrs":
                    item = await self.redis.smembers(f"rooms:{uid}:{room}:"
                                                     f"items:{name}_{lid}:"
                                                     f"{kek}")
                else:
                    item = await self.redis.get(f"rooms:{uid}:{room}:items:"
                                                f"{name}_{lid}:{kek}")
                tmp[kek] = item
            items.append(tmp)
            i += 1
        return items

    async def _background(self):
        while True:
            logging.info(f"Игроков онлайн: {len(self.online)}")
            logging.info(f"Кикнуто за превышение лимитов: {len(self.kicked)}")
            self.msgmeter = {}
            self.kicked = []
            for uid in self.inv.copy():
                inv = self.inv[uid]
                if uid not in self.online and time.time() - inv.expire > 0:
                    del self.inv[uid]
            for uid in self.slots.copy():
                if uid not in self.online:
                    self.slots.remove(uid)
            for uid in self.online.copy():
                if uid not in self.online:
                    continue
                if time.time() - self.online[uid].last_msg > 420:
                    client = self.online[uid]
                    user_data = await self.get_user_data(uid)
                    if user_data["role"] or user_data["premium"]:
                        continue
                    # logging.debug(f"Кик {client.uid} за афк")
                    await client.send(["cp.ms.rsm", {"txt": "Вы были кикнуты "
                                                            "за афк"}])
                    await client.send([3, {}], type_=3)
                    client.writer.close()
                    if uid in self.slots:
                        self.slots.remove(uid)
            await asyncio.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)-8s [%(asctime)s]  %(message)s",
                        datefmt="%H:%M:%S", level=logging.DEBUG)
    logging.getLogger("websockets").setLevel(logging.INFO)
    server = Server()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.listen())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(server.stop())
    loop.close()
