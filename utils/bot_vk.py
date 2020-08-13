import hashlib
import vk_api
import redis
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
import requests
import bot_common_sync


TOKEN = ""


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    r = redis.Redis(decode_responses=True)
    longpoll = VkBotLongPoll(vk_session, '')
    while True:
        try:
            listen(longpoll, vk, r)
        except requests.exceptions.ReadTimeout:
            continue


def listen(longpoll, vk, r):
    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW \
               and event.from_user and event.obj.message["text"]:
                keyboard = VkKeyboard()
                keyboard.add_button("Пароль", color=VkKeyboardColor.POSITIVE)
                keyboard.add_line()
                keyboard.add_button("Сброс", color=VkKeyboardColor.NEGATIVE)
                text = event.obj.message["text"]
                sid = event.obj.message["from_id"]
                print(f"{sid}: {text}")
                if text.lower() == "начать":
                    vk.messages.send(user_id=sid,
                                     random_id=get_random_id(),
                                     keyboard=keyboard.get_keyboard(),
                                     message="Список команд:")
                elif text.lower() == "пароль":
                    #passwd = r.get(f"vk:{sid}")
                    #if passwd:
                    #    vk.messages.send(user_id=sid,
                    #                     random_id=get_random_id(),
                    #                     keyboard=keyboard.get_keyboard(),
                    #                     message="Пароль можно получить "
                    #                             "только один раз")
                    #    continue
                    #else:
                    #    uid, passwd = bot_common_sync.new_account(r)
                    #    r.set(f"vk:{sid}", uid)
                    #    r.set(f"uid:{uid}:vk", sid)
                    vk.messages.send(user_id=sid,
                                     random_id=get_random_id(),
                                     keyboard=keyboard.get_keyboard(),
                                     message=f"Регистрация теперь происходит через сайт: https://avacity.xyz")
                elif text.lower() == "сброс":
                    uid = r.get(f"vk:{sid}")
                    if not uid:
                        continue
                    try:
                        int(uid)
                    except ValueError:
                        vk.messages.send(user_id=sid,
                                         random_id=get_random_id(),
                                         keyboard=keyboard.get_keyboard(),
                                         message="Сброс временно не работает")
                        continue
                    bot_common_sync.reset_account(r, uid)
                    vk.messages.send(user_id=sid,
                                     random_id=get_random_id(),
                                     keyboard=keyboard.get_keyboard(),
                                     message="Аккаунт сброшен")
                elif text.lower() == "сменить парольъъъъъыъыъъ":
                    continue
                    passwd = r.get(f"vk:{sid}")
                    if not passwd:
                        continue
                    while True:
                        new_passwd = bot_common_sync.random_string()
                        if not r.get(f"auth:{new_passwd}"):
                            break
                    uid = r.get(f"auth:{passwd}")
                    r.delete(f"auth:{passwd}")
                    r.set(f"auth:{new_passwd}", uid)
                    r.set(f"vk:{sid}", new_passwd)
                    vk.messages.send(user_id=sid,
                                     random_id=get_random_id(),
                                     keyboard=keyboard.get_keyboard(),
                                     message=f"Ваш новый пароль: {new_passwd}")
                elif text.lower() == "пин":
                    passwd = r.get(f"vk:{sid}")
                    if not passwd:
                        continue
                    uid = r.get(f"auth:{passwd}")
                    clan = r.get(f"uid:{uid}:clan")
                    if not clan:
                        continue
                    owner = r.get(f"clans:{clan}:owner")
                    if owner != uid:
                        continue
                    pin = r.get(f"clans:{clan}:pin")
                    vk.messages.send(user_id=sid,
                                     random_id=get_random_id(),
                                     keyboard=keyboard.get_keyboard(),
                                     message=f"Ваш пин: {pin}")
                else:
                    vk.messages.send(user_id=sid,
                                     random_id=get_random_id(),
                                     keyboard=keyboard.get_keyboard(),
                                     message="Неизвестная команда")
        except Exception as ex:
            print(ex)


if __name__ == '__main__':
    main()
