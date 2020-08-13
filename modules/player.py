from modules.base_module import Module
from modules.location import gen_plr

class_name = "Player"


class Player(Module):
    prefix = "pl"

    def __init__(self, server):
        self.server = server
        self.commands = {"gid": self.players_by_id,
                         "gsid": self.players_by_id,
                         "flw": self.follow,
                         "gos": self.get_online_statuses}

    async def players_by_id(self, msg, client):
        players = []
        for uid in msg[2]["uids"]:
            plr = await gen_plr(uid, self.server)
            if not plr:
                continue
            players.append(plr)
        await client.send(["pl.get", {"plrs": players,
                                      "clid": msg[2]["clid"]}])

    async def follow(self, msg, client):
        uid = msg[2]["uid"]
        if uid in self.server.online:
            user_data = await self.server.get_user_data(client.uid)
            if await self.server.redis.get(f"uid:{uid}:loc_disabled") and \
               user_data["role"] < 3:
                scs = "locationNotAllowed"
                locinfo = None
            else:
                try:
                    user = self.server.online[uid]
                except KeyError:
                    scs = "userOffline"
                    locinfo = None
                    await client.send(["pl.flw", {"scs": scs,
                                                  "locinfo": locinfo}])
                    return
                scs = "success"
                locinfo = {"st": 0, "s": "127.0.0.1", "at": None, "d": 0,
                           "x": -1.0, "y": -1.0, "shlc": True, "pl": "",
                           "l": user.room}
        else:
            scs = "userOffline"
            locinfo = None
        await client.send(["pl.flw", {"scs": scs, "locinfo": locinfo}])

    async def get_online_statuses(self, msg, client):
        online = {}
        for uid in msg[2]["uids"]:
            if isinstance(uid, int):
                uid = str(uid)
            if uid in self.server.online:
                online[uid] = True
            else:
                online[uid] = False
        await client.send(["pl.gos", {"clid": msg[2]["clid"], "onl": online}])
