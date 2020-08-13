import configparser
import aioredis
from aiogram import Bot, Dispatcher, executor, types
import bot_common
config = configparser.ConfigParser()
config.read('bot.ini')
TOKEN = config["bot"]["tg_token"]
issues_link = "https://github.com/AvaCity/avacity-2.0/issues"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


async def on_startup(dispatcher, url=None, cert=None):
    global r
    r = await aioredis.create_redis_pool("redis://localhost",
                                         encoding="utf-8")


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("Привет!\nЯ бот для выдачи паролей для AvaCity!\n"
                        "Чтобы получить пароль, введите команду /password\n"
                        "Смена пароля - /change_password\nСброс аккаунта - "
                        f"/reset\nПриятной игры!")


@dp.message_handler(commands=["password"])
async def password(message: types.Message):
    passwd = await r.get(f"tg:{message.from_user.id}")
    if passwd:
        uid = await r.get(f"auth:{passwd}")
    else:
        uid, passwd = await bot_common.new_account(r)
        await r.set(f"tg:{message.from_user.id}", passwd)
        await r.set(f"uid:{uid}:tg", message.from_user.id)
    await message.reply(f"Ваш логин: {uid}\nВаш пароль: {passwd}")


@dp.message_handler(commands=["change_password"])
async def change_password(message: types.Message):
    passwd = await r.get(f"tg:{message.from_user.id}")
    if not passwd:
        return await message.reply("Ваш аккаунт не создан")
    while True:
        new_passwd = bot_common.random_string()
        if await r.get(f"auth:{new_passwd}"):
            continue
        break
    uid = await r.get(f"auth:{passwd}")
    await r.delete(f"auth:{passwd}")
    await r.set(f"auth:{new_passwd}", uid)
    await r.set(f"tg:{message.from_user.id}", new_passwd)
    await message.reply(f"Ваш новый пароль: {new_passwd}")


@dp.message_handler(commands=["reset"])
async def reset(message: types.Message):
    passwd = await r.get(f"tg:{message.from_user.id}")
    if not passwd:
        return await message.reply("Ваш аккаунт не создан")
    uid = await r.get(f"auth:{passwd}")
    await bot_common.reset_account(r, uid)
    await message.reply(f"Ваш аккаунт был сброшен")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
