import os
import json
import time
import shutil
import asyncio
import zipfile
import hashlib
import configparser
import aiohttp
from lxml import etree

download_url = "http://cdn-sp.tortugasocial.com/avataria-ru/"
# download_url = "http://static-test-avataria.tortugasocial.com/"
with open("update.json", "r") as f:
    config = json.load(f)
with open("files/versions.json", "r") as f:
    versions = json.load(f)


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url+"versions.json") as resp:
            data = await resp.json()
            print("Got versions.json")
    tasks = []
    loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession() as session:
        for item in data:
            if data[item] in item or "island" in item.lower():
                continue
            if item in config["ignore"]:
                continue
            tasks.append(loop.create_task(download_file(item, data[item],
                                                        session)))
        await asyncio.wait(tasks)
    print("Processing config")
    if "data/config_all_ru.zip" not in versions:
        print("Error - config_all_ru.zip not found")
    else:
        await process_config(versions["data/config_all_ru.zip"])
    webconfig = configparser.ConfigParser()
    webconfig.read("web.ini")
    webconfig["webserver"]["update_time"] = str(int(time.time()))
    with open("web.ini", "w") as f:
        webconfig.write(f)


async def process_config(version):
    directory = "config_all_ru"
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
    file = f"files/data/config_all_ru_{version}.zip"
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(directory)
    doc = etree.parse(f"{directory}/avatarAppearance/appearance.xml")
    root = doc.getroot()
    for el in root.xpath("//item[@clanOnly='1']"):
        del el.attrib["clanOnly"]
    for el in root.xpath("//item[@canBuy='0']"):
        del el.attrib["canBuy"]
    for el in root.xpath("//item[@library]"):
        el.getparent().remove(el)
    string = etree.tostring(root, pretty_print=True,
                            xml_declaration=True).decode()
    with open(f"{directory}/avatarAppearance/appearance.xml", "w") as f:
        f.write(string)
    for filename in ["furniture", "kitchen", "bathroom", "decor",
                     "roomLayout", "clanFurniture"]:
        doc = etree.parse(f"{directory}/inventory/{filename}.xml")
        root = doc.getroot()
        for el in root.xpath("//item[@holiday]"):
            del el.attrib["holiday"]
        for el in root.xpath("//item[@vipOnly]"):
            del el.attrib["vipOnly"]
        if filename == "clanFurniture":
            el = root.find(".//category[@logCategory1]")
            el.attrib["logCategory1"] = "furniture"
            el.attrib["typeClass"] = "furniture"
            el.attrib["id"] = "99"
            for el in root.findall(".//item[@clanCoin]"):
                el.attrib["gold"] = el.attrib["clanCoin"]
                del el.attrib["clanCoin"]
            for el in root.findall(".//item[@theme]"):
                del el.attrib["theme"]
            for el in root.findall(".//item[@minClanLevel]"):
                del el.attrib["minClanLevel"]
        else:
            for el in root.findall(".//item[@canBuy='0']"):
                del el.attrib["canBuy"]
            for el in root.findall(".//item[@library]"):
                if el.attrib["library"] in ["restaurant2019",
                                            "modernbedroom"]:
                    el.attrib["canBuy"] = "0"
        string = etree.tostring(root, pretty_print=True,
                                xml_declaration=True).decode()
        with open(f"{directory}/inventory/{filename}.xml", "w") as f:
            f.write(string)
        tasks = []
        loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession() as session:
            for el in root.findall(".//item"):
                name = el.attrib["name"]
                folder = filename
                if folder == "roomLayout":
                    if name == "RoomBase":
                        continue
                    folder = "house"
                elif folder == "decor":
                    parent = el.getparent()
                    if parent.attrib["id"] == "achievementsDecor":
                        continue
                if "library" in el.attrib:
                    folder = el.attrib["library"]
                elif "icon" in el.attrib and "@" in el.attrib["icon"]:
                    folder = el.attrib["icon"].split("@")[-1]
                url = f"{download_url}swf/furniture/{folder}/{name}.swf"
                tasks.append(loop.create_task(download_furniture(url,
                                                                 session)))
            await asyncio.wait(tasks)
    doc = etree.parse(f"{directory}/modules/acl.xml")
    root = doc.getroot()
    for el in root.findall(".//privilege[@minAuthority='5']"):
        el.attrib["minAuthority"] = "4"
    string = etree.tostring(root, pretty_print=True,
                            xml_declaration=True).decode()
    with open(f"{directory}/modules/acl.xml", "w") as f:
        f.write(string)
    shutil.copyfile("files/avacity_ru.xml",
                    "config_all_ru/translation/avacity_ru.xml")
    z = zipfile.ZipFile("files/data/config_all_ru.zip", mode="w")
    for root, dirs, files in os.walk(directory):
        for file in files:
            z.write(os.path.join(root, file),
                    arcname=os.path.join(root,
                                         file).split("config_all_ru/")[1])
    z.close()
    with open("files/data/config_all_ru.zip", mode="rb") as f:
        hash_ = hashlib.md5(f.read()).hexdigest()
    os.rename("files/data/config_all_ru.zip",
              f"files/data/config_all_ru_{hash_}.zip")
    versions["data/config_all_ru.zip"] = hash_
    with open("files/versions.json", "w") as f:
        f.write(json.dumps(versions))


def parse_clothes(directory):
    for filename in ["boyClothes", "girlClothes"]:
        doc = etree.parse(f"{directory}/inventory/{filename}.xml")
        new_doc = etree.parse(f"files/config/inventory/{filename}.xml")
        root = doc.getroot()
        new_root = new_doc.getroot()
        for el in root.xpath("//item[@canBuy='0']"):
            del el.attrib["canBuy"]
        for el in root.xpath("//item[@holiday]"):
            del el.attrib["holiday"]
        for el in root.xpath("//item[@clanOnly='1']"):
            del el.attrib["clanOnly"]
        for el in root.xpath("//item[@ruby]"):
            el.attrib["gold"] = el.attrib["ruby"]
            del el.attrib["ruby"]
        for i in ["clanSet2Clothes", "rock2020Clothes", "magic2020Clothes",
                  "police2020Clothes"]:
            for el in root.xpath(f"//item[@library='{i}']"):
                el.attrib["canBuy"] = "0"
        for category in new_root.xpath("//category"):
            tmp = category.attrib["logCategory2"]
            orig_category = root.xpath(f"//category[@logCategory2='{tmp}']")[0]
            for item in category:
                orig_category.append(item)
        string = etree.tostring(root, pretty_print=True,
                                xml_declaration=True).decode()
        with open(f"{directory}/inventory/{filename}.xml", "w") as f:
            f.write(string)


async def download_file(filename, version, session):
    if "music" in filename:
        final = filename
    else:
        final = filename.split(".")[0]+f"_{version}."+filename.split(".")[1]
    if os.path.exists("files/"+final):
        if "music" not in filename:
            versions[filename] = version
        return
    async with session.get(download_url+final) as resp:
        if resp.status != 200:
            print(f"Can't get {final}")
            return
        content = await resp.read()
    tmp = filename.split("/")
    tmp.pop()
    folder = "/".join(tmp)
    os.makedirs("files/"+folder, exist_ok=True)
    with open("files/"+final, "wb") as f:
        f.write(content)
    if "music" not in filename:
        versions[filename] = version
    print(f"Got {final}")


async def download_furniture(url, session):
    folder = url.split("/")[-2]
    final = f"swf/furniture/{folder}/{url.split('/')[-1]}"
    if os.path.exists("files/"+final):
        return
    async with session.get(url) as resp:
        if resp.status != 200:
            print(f"Can't get {folder}/{url.split('/')[-1]}")
            return
        content = await resp.read()
    os.makedirs(f"files/swf/furniture/{folder}", exist_ok=True)
    with open("files/"+final, "wb") as f:
        f.write(content)
    print(f"Got {folder}/{url.split('/')[-1]}")

asyncio.run(main())
