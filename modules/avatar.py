import logging
from modules.base_module import Module
# from modules.location import refresh_avatar
from inventory import Inventory
import const

class_name = "Avatar"


class Avatar(Module):
    prefix = "a"

    def __init__(self, server):
        self.server = server
        self.commands = {"apprnc": self.appearance, "clths": self.clothes}
        self.clothes_list = server.parser.parse_clothes()
        self.sets = server.parser.parse_cloth_sets()

    async def appearance(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "rnn":
            name = msg[2]["unm"].strip()
            if not name:
                return
            if len(name) > const.MAX_NAME_LEN:
                return
            await self.server.redis.lset(f"uid:{client.uid}:appearance",
                                         0, name)
            user_data = await self.server.get_user_data(client.uid)
            await client.send(["a.apprnc.rnn",
                               {"res": {"slvr": user_data["slvr"],
                                        "enrg": user_data["enrg"],
                                        "emd": user_data["emd"],
                                        "gld": user_data["gld"]},
                                "unm": name}])
        elif subcommand == "save":
            apprnc = msg[2]["apprnc"]
            current_apprnc = await self.server.get_appearance(client.uid)
            if not current_apprnc:
                await self.update_appearance(apprnc, client)
                self.server.inv[client.uid] = Inventory(self.server,
                                                        client.uid)
                await self.server.inv[client.uid]._get_inventory()
                inv = self.server.inv[client.uid]
                await self.server.redis.set(f"uid:{client.uid}:wearing",
                                            "casual")
                if apprnc["g"] == 1:
                    weared = ["boyShoes8", "boyPants10", "boyShirt14"]
                    available = ["boyUnderdress1"]
                else:
                    weared = ["girlShoes14", "girlPants9", "girlShirt12"]
                    available = ["girlUnderdress1", "girlUnderdress2"]
                for item in weared+available:
                    await inv.add_item(item, "cls")
                user_data = await self.server.get_user_data(client.uid)
                if user_data["premium"]:
                    for item in const.PREMIUM_BUBBLES:
                        await inv.add_item(item, "gm")
                if user_data["role"] >= 2:
                    await inv.add_item("moderatorChatBubbleDecor", "gm")
                for item in weared:
                    await inv.change_wearing(item, True)
                for item in const.room_items:
                    await self.server.modules["frn"].add_item(item,
                                                              "livingroom",
                                                              client.uid)
                    for i in range(1, 6):
                        await self.server.modules["frn"].add_item(item,
                                                                  f"room{i}",
                                                                  client.uid)
            else:
                if apprnc["g"] != current_apprnc["g"]:
                    logging.info("gender doesn't match!")
                    return
                await self.update_appearance(apprnc, client)
            apprnc = await self.server.get_appearance(client.uid)
            await client.send(["a.apprnc.save", {"apprnc": apprnc}])

    async def clothes(self, msg, client):
        subcommand = msg[1].split(".")[2]
        try:
            if subcommand == "wear":
                await self.wear_cloth(msg, client)
            elif subcommand == "buy":
                clothes = [{"tpid": msg[2]["tpid"], "clid": ""}]
                await self.buy_clothes(msg[1], clothes, msg[2]["ctp"], client)
            elif subcommand in ["bcc", "bac"]:
                await self.buy_clothes(msg[1], msg[2]["clths"], msg[2]["ctp"],
                                       client)
            elif subcommand == "bst":
                await self.buy_clothes_suit(msg[2]["tpid"], msg[2]["ctp"],
                                            client)
            else:
                logging.warning(f"Command {msg[1]} not found")
        except KeyError:
            client.writer.close()

    async def change_ctp(self, uid, new_ctp):
        ctp = await self.server.redis.get(f"uid:{uid}:wearing")
        if ctp == new_ctp:
            return
        await self.server.redis.set(f"uid:{uid}:wearing", new_ctp)
        await self.server.inv[uid]._get_inventory()

    async def wear_cloth(self, msg, client):
        ctp = msg[2]["ctp"]
        if ctp not in ["casual", "club", "official", "swimwear", "underdress"]:
            return
        user_data = await self.server.get_user_data(client.uid)
        if ctp != "casual" and not user_data["premium"]:
            await client.send(["cp.ms.rsm", {"txt": "Сохренение и покупка "
                                                    "одежды доступна только в "
                                                    "слот 'повседневная'. "
                                                    "Чтобы сохранять и "
                                                    "покупать одежду в других "
                                                    "слотах, оформите "
                                                    "Премиум"}])
            return
        await self.change_ctp(client.uid, ctp)
        wearing = await self.server.redis.smembers(f"uid:{client.uid}:{ctp}")
        for cloth in wearing:
            await self.server.inv[client.uid].change_wearing(cloth, False)
        clths = msg[2]["clths"]
        for cloth in clths:
            if cloth["clid"]:
                tmp = f"{cloth['tpid']}_{cloth['clid']}"
            else:
                tmp = cloth["tpid"]
            await self.server.inv[client.uid].change_wearing(tmp, True)
        inv = self.server.inv[client.uid].get()
        clths = await self.server.get_clothes(client.uid, type_=2)
        ccltn = await self.server.get_clothes(client.uid, type_=3)
        await client.send(["a.clths.wear", {"inv": inv, "clths": clths,
                                            "ccltn": ccltn, "cn": "",
                                            "ctp": ctp}])

    async def buy_clothes(self, command, clothes, ctp, client):
        items = await self.server.redis.smembers(f"uid:{client.uid}:items")
        if (await self.server.get_appearance(client.uid))["g"] == 1:
            gender = "boy"
        else:
            gender = "girl"
        gold = 0
        silver = 0
        rating = 0
        to_buy = []
        user_data = await self.server.get_user_data(client.uid)
        for item in clothes:
            cloth = item["tpid"]
            clid = item["clid"]
            if clid:
                name = f"{cloth}_{clid}"
            else:
                name = cloth
            if name in items or cloth in items:
                continue
            for category in self.clothes_list[gender]:
                for item in self.clothes_list[gender][category]:
                    if item == cloth:
                        tmp = self.clothes_list[gender][category][item]
                        if not tmp["canBuy"]:
                            continue
                        if tmp["vipOnly"]:
                            if not user_data["premium"]:
                                return
                        gold += tmp["gold"]
                        silver += tmp["silver"]
                        rating += tmp["rating"]
                        if clid:
                            to_buy.append(name)
                        else:
                            to_buy.append(cloth)
                        break
        if ctp != "casual" and not user_data["premium"]:
            await client.send(["cp.ms.rsm", {"txt": "Сохренение и покупка "
                                                    "одежды доступна только в "
                                                    "слот 'повседневная'. "
                                                    "Чтобы сохранять и "
                                                    "покупать одежду в других "
                                                    "слотах, оформите "
                                                    "Премиум"}])
            return
        if not to_buy or user_data["gld"] < gold or user_data["slvr"] < silver:
            return
        pipe = self.server.redis.pipeline()
        pipe.set(f"uid:{client.uid}:gld", user_data["gld"] - gold)
        pipe.set(f"uid:{client.uid}:slvr", user_data["slvr"] - silver)
        pipe.set(f"uid:{client.uid}:crt", user_data["crt"] + rating)
        await pipe.execute()
        await self.change_ctp(client.uid, ctp)
        for cloth in to_buy:
            await self.server.inv[client.uid].add_item(cloth, "cls")
            await self.server.inv[client.uid].change_wearing(cloth, True)
        user_data = await self.server.get_user_data(client.uid)
        inv = self.server.inv[client.uid].get()
        clths = await self.server.get_clothes(client.uid, type_=2)
        ccltn = await self.server.get_clothes(client.uid, type_=1)
        ccltn = ccltn["ccltns"][ctp]
        await client.send([command, {"inv": inv,
                                     "res": {"gld": user_data["gld"],
                                             "slvr": user_data["slvr"],
                                             "emd": user_data["emd"],
                                             "enrg": user_data["enrg"]},
                                     "clths": clths, "ccltn": ccltn,
                                     "crt": user_data["crt"]}])

    async def buy_clothes_suit(self, tpid, ctp, client):
        if (await self.server.get_appearance(client.uid))["g"] == 1:
            gender = "boy"
        else:
            gender = "girl"
        if tpid not in self.sets[gender]:
            logging.info(f"Set {tpid} not found")
            return
        gold = 0
        silver = 0
        rating = 0
        items = await self.server.redis.smembers(f"uid:{client.uid}:items")
        to_buy = []
        user_data = await self.server.get_user_data(client.uid)
        for cloth in self.sets[gender][tpid]:
            if ":" in cloth:
                cloth = cloth.replace(":", "_")
            if cloth in items:
                continue
            category = self.get_category(cloth, gender)
            if not category:
                continue
            attrs = self.clothes_list[gender][category][cloth]
            if not attrs["canBuy"]:
                continue
            if attrs["vipOnly"]:
                if not user_data["premium"]:
                    continue
            gold += attrs["gold"]
            silver += attrs["silver"]
            rating += attrs["rating"]
            to_buy.append(cloth)
        if ctp != "casual" and not (user_data["role"] or user_data["premium"]):
            await client.send(["cp.ms.rsm", {"txt": "Сохренение и покупка "
                                                    "одежды доступна только в "
                                                    "слот 'повседневная'. "
                                                    "Чтобы сохранять и "
                                                    "покупать одежду в других "
                                                    "слотах, оформите "
                                                    "Премиум"}])
            return
        if user_data["gld"] < gold or user_data["slvr"] < silver:
            return
        await self.server.redis.set(f"uid:{client.uid}:gld",
                                    user_data["gld"] - gold)
        await self.server.redis.set(f"uid:{client.uid}:slvr",
                                    user_data["slvr"] - silver)
        await self.server.redis.set(f"uid:{client.uid}:crt",
                                    user_data["crt"] + rating)
        if ctp not in ["casual", "club", "official", "swimwear", "underdress"]:
            return
        await self.change_ctp(client.uid, ctp)
        for cloth in to_buy:
            await self.server.inv[client.uid].add_item(cloth, "cls")
            await self.server.inv[client.uid].change_wearing(cloth, True)
        inv = self.server.inv[client.uid].get()
        clths = await self.server.get_clothes(client.uid, type_=2)
        ccltn = await self.server.get_clothes(client.uid, type_=1)
        ccltn = ccltn["ccltns"][ctp]
        user_data = await self.server.get_user_data(client.uid)
        await client.send(["a.clths.buy", {"inv": inv,
                                           "res": {"slvr": user_data["slvr"],
                                                   "enrg": user_data["enrg"],
                                                   "emd": user_data["emd"],
                                                   "gld": user_data["gld"]},
                                           "clths": clths, "ccltn": ccltn,
                                           "crt": user_data["crt"]}])

    async def update_appearance(self, apprnc, client):
        old = await self.server.get_appearance(client.uid)
        if old:
            nick = old["n"]
        else:
            nick = apprnc["n"]
        redis = self.server.redis
        await redis.delete(f"uid:{client.uid}:appearance")
        await redis.rpush(f"uid:{client.uid}:appearance", nick,
                          apprnc["nct"], apprnc["g"], apprnc["sc"],
                          apprnc["ht"], apprnc["hc"], apprnc["brt"],
                          apprnc["brc"], apprnc["et"], apprnc["ec"],
                          apprnc["fft"], apprnc["fat"], apprnc["fac"],
                          apprnc["ss"], apprnc["ssc"], apprnc["mt"],
                          apprnc["mc"], apprnc["sh"], apprnc["shc"],
                          apprnc["rg"], apprnc["rc"], apprnc["pt"],
                          apprnc["pc"], apprnc["bt"], apprnc["bc"])

    async def update_crt(self, uid):
        redis = self.server.redis
        clothes = []
        for tmp in await redis.smembers(f"uid:{uid}:items"):
            if await redis.lindex(f"uid:{uid}:items:{tmp}", 0) == "cls":
                if "_" in clothes:
                    clothes.append(tmp.split("_")[0])
                else:
                    clothes.append(tmp)
        appearance = await self.server.get_appearance(uid)
        if not appearance:
            return 0
        gender = "boy" if appearance["g"] == 1 else "girl"
        crt = 0
        for cloth in clothes:
            for _category in self.clothes_list[gender]:
                for item in self.clothes_list[gender][_category]:
                    if item == cloth:
                        item = self.clothes_list[gender][_category][cloth]
                        crt += item["rating"]
                        break
        await self.server.redis.set(f"uid:{uid}:crt", crt)
        return crt

    def get_category(self, cloth, gender):
        if "_" in cloth:
            cloth = cloth.split("_")[0]
        for category in self.clothes_list[gender]:
            for item in self.clothes_list[gender][category]:
                if item == cloth:
                    return category
        return None
