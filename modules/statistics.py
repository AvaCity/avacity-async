from modules.base_module import Module

class_name = "Statistics"


class Statistics(Module):
    prefix = "stat"

    def __init__(self, server):
        self.server = server
        self.commands = {"urlnv": self.log_url_navigate}

    async def log_url_navigate(self, msg, client):
        return
