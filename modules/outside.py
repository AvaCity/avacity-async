from modules.location import Location, gen_plr, get_cc
import const

class_name = "Outside"


class Outside(Location):
    prefix = "o"

    def __init__(self, server):
        super().__init__(server)
        self.commands.update({"r": self.room, "gr": self.get_room})

    async def disconnect(self, prefix, tmp, client):
        await tmp.send([prefix+".r.lv", {"uid": client.uid}])
        await tmp.send([client.room, client.uid], type_=17)

    async def connect(self, plr, tmp, client):
        await tmp.send(["o.r.jn", {"plr": plr}])
        await tmp.send([client.room, client.uid], type_=16)

    async def get_room(self, msg, client):
        if "rid" not in msg[2]:
            num = 1
            while True:
                room = f"{msg[2]['lid']}_{msg[2]['gid']}_{num}"
                if self._get_room_len(room) >= const.ROOM_LIMIT:
                    num += 1
                else:
                    break
        else:
            room = f"{msg[2]['lid']}_{msg[2]['gid']}_{msg[2]['rid']}"
        if client.room:
            await self.leave_room(client)
        await self.join_room(client, room)
        await client.send(["o.gr", {"rid": client.room}])

    async def room(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "info":
            rmmb = []
            room = self.server.rooms[msg[0]].copy()
            online = self.server.online
            location_name = msg[0].split("_")[0]
            cl = {"l": {"l1": [], "l2": []}}
            for uid in room:
                if uid not in online:
                    if uid in self.server.rooms[msg[0]]:
                        self.server.rooms[msg[0]].remove(uid)
                    continue
                rmmb.append(await gen_plr(online[uid], self.server))
                if location_name == "canyon":
                    cl["l"][online[uid].canyon_lid].append(uid)
            if location_name == "canyon":
                cc = await get_cc(msg[0], self.server)
            else:
                cc = None
                cl = None
            uid = msg[0].split("_")[-1]
            evn = None
            if uid in self.server.modules["ev"].events:
                event = await self.server.modules["ev"]._get_event(uid)
                event_room = f"{event['l']}_{uid}"
                if event_room == msg[0]:
                    evn = event
            await client.send(["o.r.info", {"rmmb": rmmb, "evn": evn,
                                            "cc": cc, "cl": cl}])
        else:
            await super().room(msg, client)

    def _get_room_len(self, room):
        if room not in self.server.rooms:
            return 0
        return len(self.server.rooms[room])
