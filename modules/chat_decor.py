from modules.base_module import Module
from modules.location import refresh_avatar
import modules.notify as notify

class_name = "ChatDecor"


class ChatDecor(Module):
    prefix = "chtdc"

    def __init__(self, server):
        self.server = server
        self.commands = {"schtm": self.save_chat_decor_model}

    async def save_chat_decor_model(self, msg, client):
        r = self.server.redis
        if msg[2]["chtnwbd"]:  # new bubble
            bubble = msg[2]["chtdc"]["bdc"]
            if not bubble:
                await r.delete(f"uid:{client.uid}:bubble")
            elif not await self.server.inv[client.uid].get_item(bubble):
                if not await self.buy_decor(bubble, client):
                    return
            if bubble:
                await r.set(f"uid:{client.uid}:bubble", bubble)
        if msg[2]["chtnwtc"]:  # new text color
            text_color = msg[2]["chtdc"]["tcl"]
            if not text_color:
                await r.delete(f"uid:{client.uid}:tcl")
            elif not await self.server.inv[client.uid].get_item(text_color):
                if not await self.buy_decor(text_color, client):
                    return
            if text_color:
                await r.set(f"uid:{client.uid}:tcl", text_color)
        bubble = await r.get(f"uid:{client.uid}:bubble")
        text_color = await r.get(f"uid:{client.uid}:tcl")
        spks = ["bushStickerPack", "froggyStickerPack", "doveStickerPack",
                "jackStickerPack", "catStickerPack", "sharkStickerPack"]
        await client.send(["ntf.chtdcm", {"chtdc": {"bdc": bubble,
                                                    "spks": spks,
                                                    "tcl": text_color}}])
        await client.send(["chtdc.schtm", {}])
        await refresh_avatar(client, self.server)

    async def buy_decor(self, item, client):
        items = self.server.game_items["game"]
        if item not in items:
            return False
        price = items[item]["gold"]
        if not price:
            return False
        user_data = await self.server.get_user_data(client.uid)
        if user_data["gld"] < price:
            return False
        r = self.server.redis
        await r.set(f"uid:{client.uid}:gld", user_data["gld"]-price)
        await self.server.inv[client.uid].add_item(item, "gm")
        await client.send(["ntf.inv", {"it": {"c": 1, "iid": "",
                                              "tid": item}}])
        await notify.update_resources(client, self.server)
        return True
