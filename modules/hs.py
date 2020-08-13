import random
from modules.base_module import Module

class_name = "House"


class House(Module):
    prefix = "hs"

    def __init__(self, server):
        self.server = server
        self.commands = {"ac": self.action}
        self.actions = {"chgCh": self.change_channel,
                        "turnOff": self.turn_off,
                        "turnOn": self.turn_on,
                        "chgTxt": self.change_text,
                        "trnWhl": self.turn_wheel,
                        "chgClr": self.change_colors}

    async def action(self, msg, client):
        room = msg.pop(0)
        rid = room.split("_")[-1]
        uid = client.uid
        if msg[1]["act"] in self.actions:
            if room.split("_")[1] != uid:
                return
            oid = str(msg[1]["oid"])
            r = self.server.redis
            room_addr = f"rooms:{uid}:{rid}:items"
            items = await r.smembers(room_addr)
            for item in items:
                if item.split("_")[-1] == oid:
                    addr = room_addr+f":{item}"
                    await self.actions[msg[1]["act"]](msg[1], addr, r)
        for uid in self.server.rooms[room].copy():
            try:
                tmp = self.server.online[uid]
            except KeyError:
                continue
            await tmp.send(msg)

    async def change_channel(self, msg, addr, r):
        tr = msg["tid"]["cnl"]
        await r.sadd(addr+":options", "tr")
        await r.sadd(addr+":options", "st")
        await r.set(addr+":tr", tr)
        await r.set(addr+":st", 1)

    async def turn_off(self, msg, addr, r):
        await r.srem(addr+":options", "st")
        await r.delete(addr+":st")

    async def turn_on(self, msg, addr, r):
        await r.sadd(addr+":options", "st")
        await r.set(addr+":st", 1)

    async def change_text(self, msg, addr, r):
        txt = msg["tid"]["txt"]
        await r.sadd(addr+":options", "txt")
        await r.set(addr+":txt", txt)

    async def turn_wheel(self, msg, addr, r):
        colors = await r.smembers(addr+":clrs")
        clr = random.choice(colors)
        await r.set(addr+":rsClr", clr)
        msg["tid"] = {"clr": clr, "oid": msg["aid"], "sid": msg["aid"]}

    async def change_colors(self, msg, addr, r):
        colors = msg["tid"]["clr"]
        await r.delete(addr+":clrs")
        for item in colors:
            await r.sadd(addr+":clrs", item)
        msg["tid"].update({"oid": msg["aid"], "sid": msg["aid"]})
