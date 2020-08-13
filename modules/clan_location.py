from modules.location import Location, gen_plr


class_name = "ClanLocation"


class ClanLocation(Location):
    prefix = "c"

    def __init__(self, server):
        super().__init__(server)
        self.kicked = {}
        self.commands.update({"gr": self.get_room})

    async def get_room(self, msg, client):
        room = f"{msg[2]['lid']}_{msg[2]['gid']}_{msg[2]['rid']}"
        if client.room:
            await self.leave_room(client)
        await self.join_room(client, room)
        await client.send(["c.gr", {"rid": client.room}])

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
            cid = msg[0].split("_")[1]
            tid = await self.server.redis.get(f"clans:{cid}:room")
            room = {"f": [], "w": 13, "id": "hall", "lev": 1, "l": 13,
                    "tid": tid, "nm": ""}
            evn = None
            await client.send(["c.r.info", {"rmmb": rmmb, "rm": room,
                                            "evn": evn}])
        else:
            await super().room(msg, client)
