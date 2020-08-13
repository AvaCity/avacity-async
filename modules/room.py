from modules.base_module import Module

class_name = "Room"


class Room(Module):
    prefix = "r"

    def __init__(self, server):
        self.server = server
        self.commands = {"cnn": self.canyon}

    async def canyon(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "scl":  # switch canyon layer
            room = self.server.rooms[msg[0]].copy()
            online = self.server.online
            client.canyon_lid = msg[2]["lid"]
            cl = {"l": {"l1": [], "l2": []}}
            for uid in room:
                if uid not in online:
                    continue
                cl["l"][online[uid].canyon_lid].append(uid)
            for uid in room:
                if uid not in online:
                    continue
                await online[uid].send(["r.cnn.scl", {"uid": client.uid,
                                                      "lid": client.canyon_lid,
                                                      "cl": cl}])
