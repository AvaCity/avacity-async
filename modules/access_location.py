from modules.base_module import Module

class_name = "AccessLocation"


class AccessLocation(Module):
    prefix = "al"

    def __init__(self, server):
        self.server = server
        self.commands = {"catcl": self.check_access_to_canyon_location}

    async def check_access_to_canyon_location(self, msg, client):
        num = 1
        while True:
            room = f"{msg[2]['lid']}_{msg[2]['gid']}_{num}"
            if self._get_room_len(room) >= 8:
                num += 1
            else:
                break
        await client.send(["al.catcl", {"scc": True, 'rid': room}])

    def _get_room_len(self, room):
        if room not in self.server.rooms:
            return 0
        return len(self.server.rooms[room])
