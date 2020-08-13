import hashlib
import string
import random


def random_string(string_length=20):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(string_length))


def new_account(redis):
    redis.incr("uids")
    uid = redis.get("uids")
    passwd = random_string()
    pipe = redis.pipeline()
    m = hashlib.sha256()
    m.update(f"{uid}_{passwd}".encode())
    hash_ = m.hexdigest()
    pipe.set(f"auth:{hash_}", uid)
    pipe.set(f"uid:{uid}:lvt", 0)
    pipe.sadd(f"rooms:{uid}", "livingroom")
    pipe.rpush(f"rooms:{uid}:livingroom", "#livingRoom", 1)
    for i in range(1, 6):
        pipe.sadd(f"rooms:{uid}", f"room{i}")
        pipe.rpush(f"rooms:{uid}:room{i}", f"Комната {i}", 2)
    pipe.execute()
    return (uid, passwd)


def reset_account(redis, uid):
    pipe = redis.pipeline()
    pipe.set(f"uid:{uid}:slvr", 1000)
    pipe.set(f"uid:{uid}:gld", 6)
    pipe.set(f"uid:{uid}:enrg", 100)
    pipe.delete(f"uid:{uid}:trid")
    pipe.delete(f"uid:{uid}:crt")
    pipe.delete(f"uid:{uid}:hrt")
    pipe.delete(f"uid:{uid}:wearing")
    for item in ["casual", "club", "official", "swimwear",
                 "underdress"]:
        pipe.delete(f"uid:{uid}:{item}")
    pipe.delete(f"uid:{uid}:appearance")
    for item in redis.smembers(f"uid:{uid}:items"):
        pipe.delete(f"uid:{uid}:items:{item}")
    pipe.delete(f"uid:{uid}:items")
    for room in redis.smembers(f"rooms:{uid}"):
        for item in redis.smembers(f"rooms:{uid}:{room}:items"):
            pipe.delete(f"rooms:{uid}:{room}:items:{item}")
        pipe.delete(f"rooms:{uid}:{room}:items")
        pipe.delete(f"rooms:{uid}:{room}")
    pipe.delete(f"rooms:{uid}")
    pipe.sadd(f"uid:{uid}:items", "blackMobileSkin")
    pipe.rpush(f"uid:{uid}:items:blackMobileSkin", "gm", 1)
    pipe.sadd(f"rooms:{uid}", "livingroom")
    pipe.rpush(f"rooms:{uid}:livingroom", "#livingRoom", 1)
    for i in range(1, 6):
        pipe.sadd(f"rooms:{uid}", f"room{i}")
        pipe.rpush(f"rooms:{uid}:room{i}", f"Комната {i}", 2)
    pipe.execute()
