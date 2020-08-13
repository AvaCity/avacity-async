import time
import random
import asyncio
from modules.base_module import Module

class_name = "Event"


class Event(Module):
    prefix = "ev"

    def __init__(self, server):
        self.server = server
        self.commands = {"get": self.get_events, "gse": self.get_self_event,
                         "crt": self.create_event,
                         "cse": self.close_self_event,
                         "evi": self.get_event_info}
        self.events = {}

    async def get_events(self, msg, client):
        friends_only = msg[2]["fof"]
        category = msg[2]["c"]
        evts = []
        tmp = list(self.events.keys())
        random.shuffle(tmp)
        i = 0
        for uid in tmp:
            if i == 50:
                break
            if friends_only:
                rl = self.server.modules["rl"]
                if not await rl.get_link(client.uid, uid):
                    continue
            if category != -1:
                if uid not in self.events or \
                   category != self.events[uid]["category"]:
                    continue
            apprnc = await self.server.get_appearance(uid)
            if not apprnc:
                continue
            try:
                evts.append(await self._get_event(uid))
                i += 1
            except KeyError:
                if uid in self.events:
                    del self.events[uid]
        await client.send(["ev.get", {"c": category, "tg": "", "evlst": evts,
                                      "evtg": [], "fof": friends_only}])

    async def get_self_event(self, msg, client):
        if client.uid not in self.events:
            return await client.send(["ev.gse", {}])
        ev = await self._get_event(client.uid)
        await client.send(["ev.gse", {"ev": ev}])

    async def create_event(self, msg, client):
        if client.uid in self.events:
            return
        ev = msg[2]["ev"]
        duration = int(msg[2]["evdrid"].split("eventDuration")[1])
        if ev["c"] == 3:  # support event
            user_data = await self.server.get_user_data(client.uid)
            if user_data["role"] < 2:
                return
        event = {"name": ev["tt"], "description": ev["ds"],
                 "start": int(time.time()), "uid": client.uid,
                 "finish": int(time.time()+duration*60),
                 "min_lvl": ev["ml"], "category": ev["c"], "active": ev["ac"],
                 "rating": ev["r"]}
        if not ev["l"]:
            event["location"] = "livingroom"
        else:
            try:
                int(ev["l"])
                ev["l"] = f"room{ev['l']}"
            except ValueError:
                pass
            event["location"] = ev["l"]
        self.events[client.uid] = event
        user_data = await self.server.get_user_data(client.uid)
        event = await self._get_event(client.uid)
        await client.send(["ev.crt", {"ev": event,
                                      "res": {"gld": user_data["gld"],
                                              "slvr": user_data["slvr"],
                                              "enrg": user_data["enrg"],
                                              "emd": user_data["emd"]},
                                      "evtg": []}])
        if ev["c"] == 2:  # wedding
            await client.send(["nt.wevt", {"uid": client.uid, "evt": event}])
            rl = self.server.modules["rl"]
            relations = await self.server.redis.smembers(f"rl:{client.uid}")
            for link in relations:
                relation = await rl._get_relation(client.uid, link)
                if relation["rlt"]["s"] // 10 == 6:
                    uid = relation["uid"]
                    rlt = relation["rlt"]
                    relation["rlt"]["t"]["we"] = True
                    await client.send(["nt.wevt", {"uid": uid, "evt": event}])
                    await client.send(['rl.urt', {'uid': uid, 'rlt': rlt}])
                    if uid not in self.server.online:
                        continue
                    tmp = self.server.online[uid]
                    await tmp.send(["nt.wevt", {"uid": client.uid,
                                                "evt": event}])
                    await tmp.send(['rl.urt', {'uid': client.uid, 'rlt': rlt}])

    async def close_self_event(self, msg, client):
        if client.uid not in self.events:
            return
        del self.events[client.uid]
        await client.send(["ev.cse", {}])

    async def get_event_info(self, msg, client):
        id_ = str(msg[2]["id"])
        if id_ not in self.events:
            return
        event = await self._get_event(id_)
        apprnc = await self.server.get_appearance(id_)
        clths = await self.server.get_clothes(id_, type_=2)
        await client.send(["ev.evi", {"ev": event,
                                      "plr": {"uid": id_, "apprnc": apprnc,
                                              "clths": clths},
                                      "id": int(id_)}])

    async def _get_event(self, uid):
        event = self.events[uid]
        apprnc = await self.server.get_appearance(uid)
        if event["location"] == "livingroom" or \
           event["location"].startswith("room"):
            type_ = 0
        else:
            type_ = 1
        return {"tt": event["name"], "ds": event["description"],
                "st": event["start"], "ft": event["finish"], "uid": uid,
                "l": event["location"], "id": int(uid), "unm": apprnc["n"],
                "ac": event["active"], "c": event["category"],
                "ci": 0, "fo": False, "r": event["rating"], "lg": 30,
                "tp": type_, "ml": event["min_lvl"]}

    async def _background(self):
        while True:
            for uid in self.events.copy():
                if time.time() - self.events[uid]["finish"] > 0:
                    del self.events[uid]
            await asyncio.sleep(60)
