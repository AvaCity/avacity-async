import random
import time
import asyncio
import logging
from modules.base_module import Module

class_name = "LocationGame"


class LocationGame(Module):
    prefix = "lg"

    def __init__(self, server):
        self.server = server
        self.commands = {"lst": self.game_list, "cg": self.create_game,
                         "gi": self.game_info, "invig": self.involve_in_game,
                         "en": self.enter_game, "f": self.fight}
        self.games = {}

    async def game_list(self, msg, client):
        await client.send(["lg.lst", {"glst": []}])

    async def create_game(self, msg, client):
        type_ = msg[2]["lgtp"]
        uid = msg[2]["gtid"]
        confirms = self.server.modules["cf"].confirms
        if client.uid not in confirms or \
           confirms[client.uid]["uid"] != uid or \
           not confirms[client.uid]["completed"]:
            return
        del confirms[client.uid]
        if uid not in self.server.online:
            logging.error("error 2")
            return
        player1 = client
        player2 = self.server.online[uid]
        if type_ == "fight":
            await self.new_fight(player1, player2)

    async def new_fight(self, player1, player2):
        while True:
            num = str(random.randint(1, 9999))
            if num not in self.games:
                break
        self.games[num] = {"first": player1.uid, "second": player2.uid,
                           "room": num, "type": "fight", "fmoves": [],
                           "smoves": [], "fready": False, "sready": False,
                           "fpoints": 0, "spoints": 0, "turn": 0, "np": "f",
                           "time": time.time()}
        cr = player1.uid
        await player1.send(["lg.f.jg", {"gmr": {"uid": cr, "fml": None,
                                                "fst": 0}}])
        await player1.send([f"game_fight_{num}", cr], type_=16)
        for user in [player1, player2]:
            await user.send(["lg.ng", {"gm": {"lgmrs": [{"uid": cr}],
                                              "lgcid": cr, "lgid": num,
                                              "lgtp": "fight"}}])
        await player1.send(["lg.cg", {"lgid": num}])

    async def game_info(self, msg, client):
        num = msg[2]["lgid"]
        if num not in self.games:
            return
        game = self.games[num]
        cr = game["first"]
        op = game["second"]
        await client.send(["lg.gi", {"gm": {"lgmrs": [{"uid": cr, "fml": None,
                                                       "fst": 0}],
                                            "fohp": 0, "lgcid": cr,
                                            "lgid": num, "lgtp": game["type"],
                                            "fchp": 0, "fmt": 5,
                                            "lgoid": op}}])

    async def involve_in_game(self, msg, client):
        num = msg[2]["lgid"]
        if num not in self.games:
            return
        game = self.games[num]
        op = self.server.online[game["second"]]
        await op.send(["lg.invig", {"uid": client.uid, "lgid": num,
                                    "rq": False}])

    async def enter_game(self, msg, client):
        num = msg[2]["lgid"]
        if num not in self.games:
            return
        game = self.games[num]
        users = [self.server.online[game["first"]],
                 self.server.online[game["second"]]]
        for user in users:
            await user.send(["lg.f.jg", {"gmr": {"uid": client.uid,
                                                 "fml": None, "fst": 0}}])
            await user.send([f"game_fight_{num}", client.uid], type_=16)
        await client.send(["lg.en", {"lgid": num}])
        for user in users:
            await user.send(["lg.eing", {"lgid": num,
                                         "gmr": {"uid": client.uid}}])

    async def exit_game(self, room, client):
        num = room.split("_")[-1]
        await client.send(["lg.lvdg", {"uid": client.uid, "lgid": num}])
        await client.send(["lg.gf", {"lgid": num}])
        if num not in self.games:
            return
        game = self.games[num]
        if client.uid == game["first"]:
            uid = game["second"]
        else:
            uid = game["first"]
        tmp = self.server.online[uid]
        user_data = await self.server.get_user_data(uid)
        await tmp.send(["lg.f.fin", {"res": {"slvr": user_data["slvr"],
                                             "enrg": user_data["enrg"],
                                             "emd": user_data["emd"],
                                             "gld": user_data["gld"]},
                                     "fohp": 0, "fwnr": None, "fchp": 0}])
        await tmp.send(["lg.f.lv", {"gtid": client.uid}])

    async def fight(self, msg, client):
        subcommand = msg[1].split(".")[-1]
        if subcommand == "rdy":
            return await self.fight_ready(msg, client)
        elif subcommand == "trnf":  # turn finished
            return await self.turn_finished(msg, client)
        else:
            print(f"Command {msg[1]} not found")

    async def fight_ready(self, msg, client):
        num = msg[0].split("_")[-1]
        if num not in self.games:
            return
        game = self.games[num]
        if client.uid == game["first"]:
            cr = True
            moves = game["fmoves"]
            game["fready"] = True
        else:
            cr = False
            moves = game["smoves"]
            game["sready"] = True
        for move in msg[2]["fml"]:
            moves.append(move["fid"])
        await client.send(["lg.f.rdy", {"scs": True}])
        if cr:
            while not (game["fready"] and game["sready"]):
                await asyncio.sleep(0.1)
            data = msg[2]
            users = [self.server.online[game["first"]],
                     self.server.online[game["second"]]]
            for user in users:
                await user.send(["lg.f.strt", {"lgcid": game["first"],
                                               "ctpy": data["ctpy"],
                                               "ctpx": data["ctpx"],
                                               "otpx": data["otpx"],
                                               "otpy": data["otpy"],
                                               "lgoid": game["second"]}])
                await self._next_turn(num)

    async def turn_finished(self, msg, client):
        num = msg[0].split("_")[-1]
        if num not in self.games:
            return
        await self._next_turn(num)

    def has_block(self, f, s):
        if (f == 1 and s == 3) or (f == 2 and s == 4):
            return True
        return False

    async def _next_turn(self, num):
        game = self.games[num]
        turn = game["turn"]
        if turn == 5:
            if game["fpoints"] > game["spoints"]:
                winner = game["first"]
                lclient = self.server.online[game["second"]]
            else:
                winner = game["second"]
                lclient = self.server.online[game["first"]]
            wclient = self.server.online[winner]
            for user in [wclient, lclient]:
                user_data = await self.server.get_user_data(user.uid)
                await user.send(["lg.f.fin", {"res": {"slvr": user_data["slvr"],
                                                      "enrg": user_data["enrg"],
                                                      "emd": user_data["emd"],
                                                      "gld": user_data["gld"]},
                                              "fohp": game["spoints"],
                                              "fgwr": {"rb": 0, "slvr": 0,
                                                       "enrg": 0, "emd": 0,
                                                       "gld": 0},
                                              "fwnr": winner,
                                              "fchp": game["fpoints"]}])
                await user.send(["lg.lvdg", {"uid": user.uid, "lgid": num}])
                await user.send(["lg.gf", {"lgid": num}])
            del self.games[num]
            return
        f = game["fmoves"][turn]
        s_orig = game["smoves"][turn]
        s = s_orig
        fp = 0
        sp = 0
        if game["np"] == "f":
            attacker = game["first"]
            if not self.has_block(f, s_orig):
                if f == 1:
                    s = 98
                    fp = 10
                elif f == 2:
                    s = 99
                    fp = 5
        else:
            attacker = game["second"]
            s = s_orig
            if not self.has_block(s, f):
                if s == 1:
                    f = 98
                    sp = 10
                elif s == 2:
                    f = 99
                    sp = 5
        game["fpoints"] += fp
        game["spoints"] += sp
        users = [self.server.online[game["first"]],
                 self.server.online[game["second"]]]
        await asyncio.sleep(3)
        for user in users:
            await user.send(["lg.f.ntrn", {"fstrn": {"fgmv": {"fid": f,
                                                              "ftrn": turn+1},
                                                     "fchp": fp},
                                           "fgcaid": attacker,
                                           "fotrn": {"fgmv": {"fid": s,
                                                              "ftrn": turn+1},
                                                     "fohp": sp}}])
        if game["np"] == "s" or s_orig in [3, 4]:
            game["turn"] += 1
            game["np"] = "f"
        else:
            game["np"] = "s"
