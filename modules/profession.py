from modules.base_module import Module

class_name = "Profession"


class Profession(Module):
    prefix = "prf"

    def __init__(self, server):
        self.server = server
        self.commands = {"vsgprp": self.visage_propose,
                         "vsgapprv": self.visage_approve}
        self.colors = {"sh": "shc", "pt": "pc", "ss": "ssc", "fat": "fac"}
        self.propose = {}

    async def visage_propose(self, msg, client):
        second_client = None
        if msg[2]["uid"] in self.server.online:
            second_client = self.server.online[msg[2]["uid"]]
            if second_client.room != client.room:
                return
        else:
            return
        new_apprnc = {"sh": msg[2]["apprnc"]["sh"],
                      "shc": msg[2]["apprnc"]["shc"],
                      "pt": msg[2]["apprnc"]["pt"],
                      "pc": msg[2]["apprnc"]["pc"],
                      "ss": msg[2]["apprnc"]["ss"],
                      "ssc": msg[2]["apprnc"]["ssc"],
                      "fat": msg[2]["apprnc"]["fat"],
                      "fac": msg[2]["apprnc"]["fac"]}
        apprnc = await self.server.get_appearance(msg[2]["uid"])
        price = self._calculate_price(apprnc, new_apprnc)
        if await self.server.inv[client.uid].get_item("vsgstBrush") < price:
            return
        apprnc.update(new_apprnc)
        self.propose[second_client.uid] = {"uid": client.uid, "apprnc": apprnc,
                                           "price": price}
        await second_client.send(["prf.vsgapprv", {"uid": client.uid,
                                                   "apprnc": apprnc}])

    async def visage_approve(self, msg, client):
        if client.uid not in self.propose:
            return
        if not msg[2]["apprvd"]:
            del self.propose[client.uid]
            return
        price = self.propose[client.uid]["price"]
        sender = self.propose[client.uid]["uid"]
        if not await self.server.inv[sender].take_item("vsgstBrush", price):
            return
        apprnc = self.propose[client.uid]["apprnc"]
        del self.propose[client.uid]
        await self.server.modules["a"].update_appearance(apprnc, client)
        apprnc = await self.server.get_appearance(client.uid)
        await client.send(["a.apprnc.save", {"apprnc": apprnc}])
        if sender in self.server.online:
            tmp = self.server.online[sender]
            amount = await self.server.inv[sender].get_item("vsgstBrush")
            await tmp.send(["ntf.inv", {"it": {"c": amount, "iid": "",
                                               "tid": "vsgstBrush"}}])

    def _calculate_price(self, old_apprnc, new_apprnc):
        gender = "boy" if old_apprnc["g"] == 1 else "girl"
        brush = 0
        for item in ["sh", "pt", "ss", "fat"]:
            if new_apprnc[item] == old_apprnc[item]:
                color = self.colors[item]
                if new_apprnc[color] == old_apprnc[color]:
                    continue
            id_ = new_apprnc[item]
            if "brush" in self.server.appearance[gender][item][id_]:
                brush += self.server.appearance[gender][item][id_]["brush"]
        return brush
