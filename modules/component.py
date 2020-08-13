import time
import json
import aiohttp
import urllib.parse
import logging
import random
import traceback
import asyncio
from modules.base_module import Module
from modules.location import refresh_avatar, get_city_info
import utils.bot_common

class_name = "Component"
tg_link = "https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}"
token = ""
channel = ""


def get_exp(lvl):
    expSum = 0
    i = 0
    while i < lvl-1:
        i += 1
        expSum += i * 50
    return expSum


class Component(Module):
    prefix = "cp"

    def __init__(self, server):
        self.server = server
        self.commands = {"cht": self.chat, "m": self.moderation,
                         "ms": self.message}
        self.privileges = self.server.parser.parse_privileges()
        self.help_cooldown = {}
        self.ban_reasons = {1: "нецензурные выражения",
                            5: "клевета в адрес администрации/игроков",
                            6: "клевета в адрес компании/игры",
                            7: "спам или флуд",
                            8: "реклама или ссылки",
                            9: "запрещённые описания и названия",
                            10: "мат и/или оскорбления"}
        self.warning_reasons = {"1": "Манипуляции с игровым аккаунтом",
                                "2": "Махинации с игровой валютой",
                                "3": "Использование игровых ботов",
                                "4": "Использование багов игры",
                                "5": "Клевета в адрес представителей "
                                     "администрации",
                                "6": "Клевета в адрес игры",
                                "7": "Спам или флуд",
                                "8": "Реклама или ссылки",
                                "9": "Запрещённые названия",
                                "10": "Мат или оскорбления",
                                "11": "Умышленное создание трудностей",
                                "12": "Вредоносные файлы",
                                "13": "Выдача за сотрудника",
                                "14": "Попытка доступа к чужому аккаунту",
                                "15": "Введение в заблуждение администрации",
                                "16": "Обман на подарки",
                                "17": "Мошенничество",
                                "18": "Избыточное форматирование",
                                "19": "Иностранный язык"}
        self.mute = {}

    async def chat(self, msg, client):
        if not client.room:
            return
        subcommand = msg[1].split(".")[2]
        if subcommand == "sm":  # send message
            msg.pop(0)
            if client.uid in self.mute:
                time_left = self.mute[client.uid]-time.time()
                if time_left > 0:
                    await client.send(["cp.ms.rsm", {"txt": "У вас мут ещё на "
                                                            f"{int(time_left)}"
                                                            " секунд"}])
                    return
                else:
                    del self.mute[client.uid]
            if msg[1]["msg"]["cid"]:
                if msg[1]["msg"]["cid"].startswith("clan"):
                    r = self.server.redis
                    cid = await r.get(f"uid:{client.uid}:clan")
                    for uid in await r.smembers(f"clans:{cid}:m"):
                        if uid in self.server.online:
                            await self.server.online[uid].send(msg)
                else:
                    for uid in msg[1]["msg"]["cid"].split("_"):
                        if uid in self.server.online:
                            await self.server.online[uid].send(msg)
            else:
                if "msg" in msg[1]["msg"]:
                    message = msg[1]["msg"]["msg"]
                    if message.startswith("!"):
                        try:
                            return await self.system_command(message, client)
                        except Exception:
                            print(traceback.format_exc())
                            msg = "Ошибка в команде, проверьте правильность"
                            await client.send(["cp.ms.rsm", {"txt": msg}])
                            return
                msg[1]["msg"]["sid"] = client.uid
                online = self.server.online
                room = self.server.rooms[client.room]
                for uid in room:
                    try:
                        tmp = online[uid]
                    except KeyError:
                        room.remove(uid)
                        continue
                    await tmp.send(msg)

    async def moderation(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "ar":  # access request
            user_data = await self.server.get_user_data(client.uid)
            if user_data["role"] >= self.privileges[msg[2]["pvlg"]]:
                success = True
            else:
                success = False
            await client.send(["cp.m.ar", {"pvlg": msg[2]["pvlg"],
                                           "sccss": success}])
        # elif subcommand == "bu":
            # uid = msg[2]["uid"]
            # category = msg[2]["bctr"]
            # reason = msg[2]["notes"]
            # return await self.ban_user(uid, category, reason, client)

    async def kick(self, client, uid, reason):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < 2:
            return await self.no_permission(client)
        uid_user_data = await self.server.get_user_data(uid)
        if uid_user_data["role"]:
            return
        if uid not in self.server.online:
            return await client.send(["cp.ms.rsm", {"txt": "Игрок оффлайн"}])
        tmp = self.server.online[uid]
        tmp.writer.close()
        await client.send(["cp.ms.rsm", {"txt": "Игрок был кикнут"}])
        await self.send_tg(f"{uid} получил кик от {client.uid}\n"
                           f"Причина: {reason}")

    async def ban_user(self, uid, category, reason, days, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["ALLOW_BAN_ALWAYS"]:
            return await self.no_permission(client)
        uid_user_data = await self.server.get_user_data(uid)
        if uid_user_data and uid_user_data["role"] > 2:
            return
        redis = self.server.redis
        banned = await redis.get(f"uid:{uid}:banned")
        if banned:
            await client.send(["cp.ms.rsm", {"txt": f"У UID {uid} уже есть бан"
                                                    " от администратора "
                                                    f"{banned}"}])
            return
        await redis.set(f"uid:{uid}:banned", client.uid)
        if reason:
            await redis.set(f"uid:{uid}:ban_reason", reason)
        await redis.set(f"uid:{uid}:ban_category", category)
        ban_time = int(time.time()*1000)
        if days == 0:
            ban_end = 0
            time_left = 0
        else:
            ban_end = ban_time+(days*24*60*60*1000)
            time_left = ban_end-ban_time
        await redis.set(f"uid:{uid}:ban_time", ban_time)
        await redis.set(f"uid:{uid}:ban_end", ban_end)
        if uid in self.server.online:
            tmp = self.server.online[uid]
            await tmp.send([10, "User is banned",
                            {"duration": 999999, "banTime": ban_time,
                             "notes": reason, "reviewerId": client.uid,
                             "reasonId": category, "unbanType": "none",
                             "leftTime": time_left, "id": None,
                             "reviewState": 1, "userId": uid,
                             "moderatorId": client.uid}],
                           type_=2)
            tmp.writer.close()
        if category != 4:
            if category in self.ban_reasons:
                reason = f"Меню модератора, {self.ban_reasons[category]}"
            else:
                reason = f"Меню модератора, №{category}"
        await self.send_tg(f"{uid} получил бан от {client.uid} на {days} "
                           f"дней\nПричина: {reason}")
        await client.send(["cp.ms.rsm", {"txt": f"UID {uid} получил бан"}])

    async def unban_user(self, uid, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["ALLOW_BAN_ALWAYS"]:
            return await self.no_permission(client)
        redis = self.server.redis
        banned = await redis.get(f"uid:{uid}:banned")
        if not banned:
            await client.send(["cp.ms.rsm", {"txt": f"У UID {uid} нет бана"}])
            return
        await redis.delete(f"uid:{uid}:banned")
        await redis.delete(f"uid:{uid}:ban_time")
        await self.send_tg(f"{uid} получил разбан от {client.uid}")
        await client.send(["cp.ms.rsm", {"txt": f"Снят бан UID {uid} от "
                                                f"администратора {banned}"}])

    async def message(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "smm":  # send moderator message
            user_data = await self.server.get_user_data(client.uid)
            if user_data["role"] < self.privileges["MESSAGE_TO_USER"]:
                return await self.no_permission(client)
            uid = msg[2]["rcpnts"]
            message = msg[2]["txt"]
            sccss = False
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await tmp.send(["cp.ms.rmm", {"sndr": client.uid,
                                              "txt": message}])
                sccss = True
            await client.send(["cp.ms.smm", {"sccss": sccss}])
            reason_id = message.split(":")[0]
            if reason_id == "0":
                message = message.split(":")[1]
            else:
                message = self.warning_reasons[reason_id]
            await self.send_tg(f"{uid} получил предупреждение от "
                               f"{client.uid}\n{message}")

    async def system_command(self, msg, client):
        command = msg[1:]
        if " " in command:
            command = command.split(" ")[0]
        if command == "ssm":
            if client.uid not in ["1", "2", "3"]:
                return await self.no_permission(client)
            return await self.send_system_message(msg, client)
        elif command == "mute":
            tmp = msg.split()
            tmp.pop(0)
            tmp.pop(0)
            tmp.pop(0)
            reason = " ".join(tmp)
            return await self.mute_player(msg, reason, client)
        elif command == "ban":
            tmp = msg.split()
            tmp.pop(0)
            uid = tmp.pop(0)
            days = int(tmp.pop(0))
            reason = " ".join(tmp)
            return await self.ban_user(uid, 4, reason, days, client)
        elif command == "unban":
            uid = msg.split()[1]
            return await self.unban_user(uid, client)
        elif command == "debug":
            client.debug = True
        elif command == "reset":
            uid = msg.split()[1]
            return await self.reset_user(uid, client)
        elif command == "lvl":
            lvl = int(msg.split()[1])
            return await self.change_lvl(client, lvl)
        elif command == "rename":
            return await self.rename_avatar(client, msg)
        elif command == "command":
            tmp = msg.split()
            tmp.pop(0)
            tmp = " ".join(tmp)
            to_send = json.loads(tmp)
            return await self.send_command(client, to_send)
        elif command == "kick":
            tmp = msg.split()
            tmp.pop(0)
            uid = tmp.pop(0)
            reason = " ".join(tmp)
            return await self.kick(client, uid, reason)
        elif command == "пин":
            return await self.clan_pin(client)
        elif command == "report":
            return await self.find_help(client)

    async def send_system_message(self, msg, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["SEND_SYSTEM_MESSAGE"]:
            return await self.no_permission(client)
        message = msg.split("!ssm ")[1]
        online = self.server.online
        loop = asyncio.get_event_loop()
        for uid in self.server.online.copy():
            try:
                loop.create_task(online[uid].send(["cp.ms.rsm",
                                                   {"txt": message}]))
            except KeyError:
                continue

    async def mute_player(self, msg, reason, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["CHAT_BAN"]:
            return await self.no_permission(client)
        uid = msg.split()[1]
        minutes = int(msg.split()[2])
        apprnc = await self.server.get_appearance(uid)
        if not apprnc:
            await client.send(["cp.ms.rsm", {"txt": "Игрок не найден"}])
            return
        self.mute[uid] = time.time()+minutes*60
        await self.send_tg(f"{uid} получил мут от {client.uid} на {minutes} "
                           f"минут\nПричина: {reason}")
        if uid in self.server.online:
            tmp = self.server.online[uid]
            await tmp.send(["cp.m.bccu", {"bcu": {"notes": "",
                                                  "reviewerId": "0",
                                                  "mid": "0", "id": None,
                                                  "reviewState": 1,
                                                  "userId": uid,
                                                  "mbt": int(time.time()*1000),
                                                  "mbd": minutes,
                                                  "categoryId": 14}}])
        await client.send(["cp.ms.rsm", {"txt": f"Игроку {apprnc['n']} выдан "
                                                f"мут на {minutes} минут"}])

    async def reset_user(self, uid, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < 4:
            return await self.no_permission(client)
        apprnc = await self.server.get_appearance(uid)
        if not apprnc:
            await client.send(["cp.ms.rsm", {"txt": "Аккаунт и так сброшен"}])
            return
        if uid in self.server.online:
            self.server.online[uid].writer.close()
        await utils.bot_common.reset_account(self.server.redis, uid)
        await self.send_tg(f"{client.uid} сбросил аккаунт {uid}")
        await client.send(["cp.ms.rsm", {"txt": f"Аккаунт {uid} был сброшен"}])

    async def change_lvl(self, client, lvl):
        if lvl < 10 or lvl >= 998:
            user_data = await self.server.get_user_data(client.uid)
            if user_data["role"] < 4:
                return
        exp = get_exp(lvl)
        await self.server.redis.set(f"uid:{client.uid}:exp", exp)
        ci = await get_city_info(client.uid, self.server)
        await client.send(["ntf.ci", {"ci": ci}])
        await client.send(["q.nwlv", {"lv": lvl}])
        await refresh_avatar(client, self.server)

    async def rename_avatar(self, client, msg):
        user_data = await self.server.get_user_data(client.uid)
        tmp = msg.split()
        tmp.pop(0)
        if user_data["role"] < 2:
            uid = client.uid
            name = " ".join(tmp).strip()
        else:
            uid = tmp.pop(0)
            name = " ".join(tmp).strip()
        if not await self.server.redis.lindex(f"uid:{uid}:appearance", 0):
            return
        if len(name) > 20 or not name:
            return
        await self.server.redis.lset(f"uid:{uid}:appearance", 0, name)
        if uid != client.uid:
            await self.send_tg(f"{client.uid} сменил ник {uid} на {name}")
        if uid in self.server.online:
            tmp = self.server.online[uid]
            await refresh_avatar(tmp, self.server)
        await client.send(["cp.ms.rsm", {"txt": f"Ник {uid} был изменён"}])

    async def clan_pin(self, client):
        r = self.server.redis
        cid = await r.get(f"uid:{client.uid}:clan")
        if not cid:
            await client.send(["cp.ms.rsm", {"txt": "У вас нет клуба"}])
            return
        role = await r.get(f"clans:{cid}:m:{client.uid}:role")
        if role != "3":
            await client.send(["cp.ms.rsm", {"txt": "Недостаточно прав"}])
            return
        pin = await r.get(f"clans:{cid}:pin")
        await client.send(["cp.ms.rsm", {"txt": f"Ваш пин: {pin}"}])

    async def send_command(self, client, to_send):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"] < 4:
            return
        if not isinstance(to_send, list):
            print("not list")
            print(to_send)
            return
        await client.send(to_send)

    async def find_help(self, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["role"]:
            await client.send(["cp.ms.rsm", {"txt": "ты далбаеб"}])
            return
        if client.uid in self.help_cooldown:
            if time.time() - self.help_cooldown[client.uid] < 60:
                await client.send(["cp.ms.rsm", {"txt": "Подождите перед "
                                                        "повторной "
                                                        "отправкой"}])
                return
        self.help_cooldown[client.uid] = time.time()
        uids = list(self.server.online)
        random.shuffle(uids)
        found = False
        for uid in uids:
            if await self.server.redis.get(f"uid:{uid}:role"):
                found = True
                tmp = self.server.online[uid]
                await tmp.send(["spt.clmdr", {"rid": client.room}])
                await tmp.send(["cp.ms.rsm",
                                {"txt": f"Вас позвал {client.uid}"}])
                break
        if found:
            msg = "Сообщение отправлено модератору"
        else:
            msg = "Не найдено модераторов в сети"
        await client.send(["cp.ms.rsm", {"txt": msg}])

    async def no_permission(self, client):
        await client.send(["cp.ms.rsm", {"txt": "У вас недостаточно прав, "
                                                "чтобы выполнить эту "
                                                "команду"}])

    async def send_tg(self, message):
        url = tg_link.format(token, channel, urllib.parse.quote(message))
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logging.error(f"Ошибка TG: {text}")
