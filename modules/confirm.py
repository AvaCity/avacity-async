from modules.base_module import Module

class_name = "UserConfirm"


class UserConfirm(Module):
    prefix = "cf"

    def __init__(self, server):
        self.server = server
        self.commands = {"uc": self.user_confirm,
                         "uca": self.user_confirm_approve,
                         "ucd": self.user_confirm_decline}
        self.confirms = {}

    async def user_confirm(self, msg, client):
        if msg[2]["uid"] == client.uid:
            return
        if msg[2]["uid"] in self.server.online:
            tmp = self.server.online[msg[2]["uid"]]
            self.confirms[client.uid] = {"uid": msg[2]["uid"],
                                         "at": msg[2]["at"],
                                         "completed": False}
            await tmp.send(["cf.uc", {"uid": client.uid, "at": msg[2]["at"]}])

    async def user_confirm_approve(self, msg, client):
        if msg[2]["uid"] in self.server.online and \
           msg[2]["uid"] in self.confirms:
            tmp = self.server.online[msg[2]["uid"]]
            if self.confirms[tmp.uid]["at"] != msg[2]["at"]:
                return
            if self.confirms[tmp.uid]["uid"] != client.uid:
                return
            self.confirms[tmp.uid]["completed"] = True
            await tmp.send(["cf.uca", {"uid": client.uid, "at": msg[2]["at"]}])

    async def user_confirm_decline(self, msg, client):
        if msg[2]["uid"] in self.server.online and \
           msg[2]["uid"] in self.confirms:
            tmp = self.server.online[msg[2]["uid"]]
            if self.confirms[tmp.uid]["at"] != msg[2]["at"]:
                return
            if self.confirms[tmp.uid]["uid"] != client.uid:
                return
            del self.confirms[tmp.uid]
            await tmp.send(["cf.ucd", {"uid": client.uid, "at": msg[2]["at"]}])
