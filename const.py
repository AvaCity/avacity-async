from datetime import datetime

XML = """<?xml version="1.0"?>
<cross-domain-policy>
<allow-access-from domain="*" to-ports="*" />
</cross-domain-policy>
""".encode()

MAX_NAME_LEN = 20
ROOM_LIMIT = 16
FREE_GOLD = True
DEBUG = ["1", "2"]
BLACKLIST_TROPHIES = ["kawaiiCat"]
PREMIUM_TROPHIES = []
PREMIUM_BUBBLES = []

room_items = [{"tpid": "wall15", "d": 3, "oid": 1, "x": 0.0, "y": 0.0,
               "z": 0.0},
              {"tpid": "wall15", "d": 5, "oid": 2, "x": 13.0, "y": 0.0,
               "z": 0.0},
              {"tpid": "floor4", "d": 5, "oid": 3, "x": 0.0, "y": 0.0,
               "z": 0.0},
              {"tpid": "door4", "d": 3, "oid": 4, "x": 3.0, "y": 0.0,
               "z": 0.0, "rid": "outside"}]
campaigns = []

clans = True
mobile = True
fortune2 = False
professions = True
reputation = True
school = True
competitions = False


# campaigns.append({"st": 1, "v": 1,
#                  "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 9999,
#                           "tid": "familyRelations", "cid": 999},
#                          {"sc": 0, "gl": 0, "si": 0, "id": 9998,
#                           "tid": "posePlayer", "cid": 999},
#                          {"sc": 0, "gl": 0, "si": 0, "id": 9997,
#                           "tid": "changeLevelModule", "cid": 999}],
#                  "id": 999, "iu": "", "tp": 9,
#                  "ed": datetime(2047, 5, 31, 11, 46)})
# campaigns.append({"st": 1, "v": 1,
#                  "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 8153,
#                           "tid": "kotex2015", "cid": 644}],
#                  "id": 644, "iu": "", "tp": 9,
#                  "ed": datetime(2047, 5, 31, 11, 46)})
campaigns.append({"st": 1, "v": 1,
                  "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 40950,
                           "tid": "nsPassport", "cid": 4490}],
                  "id": 4490, "iu": "", "tp": 9,
                  "ed": datetime(2018, 4, 2, 2, 0)})
campaigns.append({"st": 1, "v": 1,
                  "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 42200,
                           "tid": "nsPassportDecor", "cid": 4570}],
                  "id": 4570, "iu": "", "tp": 9,
                  "ed": datetime(2018, 6, 28, 2, 0)})
campaigns.append({"st": 1, "v": 1,
                  "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 4095,
                           "tid": "chatDecor", "cid": 449}],
                  "id": 449, "iu": "", "tp": 9,
                  "ed": datetime(2018, 4, 2, 2, 0)})
campaigns.append({"st": 1, "v": 1,
                  "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 4220,
                           "tid": "chatDecorShop", "cid": 457}],
                  "id": 457, "iu": "", "tp": 9,
                  "ed": datetime(2018, 6, 28, 2, 0)})
if clans:
    campaigns.append({"st": 1, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 8151,
                               "tid": "clans", "cid": 643},
                              {'sc': 0, 'gl': 0, 'si': 0, 'id': 8152,
                               'tid': 'clanActivityRating', 'cid': 643},
                              {'sc': 0, 'gl': 0, 'si': 0, 'id': 8668,
                               'tid': 'clanMemberRating', 'cid': 643},
                              {'sc': 0, 'gl': 0, 'si': 0, 'id': 9550,
                               'tid': 'clanLocationEdit', 'cid': 643},
                              {'sc': 0, 'gl': 0, 'si': 0, 'id': 10341,
                               'tid': 'clanContest', 'cid': 643}],
                      "id": 643, "iu": "", "tp": 9,
                      "ed": datetime(2027, 5, 31, 11, 46)})
if mobile:
    campaigns.append({"st": 1, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 2514,
                               "tid": "mobile", "cid": 316}],
                      "id": 316, "iu": "", "tp": 9,
                      "ed": datetime(2022, 7, 31, 2, 0)})
if fortune2:
    campaigns.append({"st": 2, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 2434,
                               "tid": "fortune2", "cid": 299}],
                      "id": 299, "iu": "", "tp": 9,
                      "ed": datetime(2030, 10, 31, 2, 0)})
if professions:
    campaigns.append({"st": 1, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 1110,
                               "tid": "professions", "cid": 114},
                              {"sc": 0, "gl": 0, "si": 0, "id": 1111,
                               "tid": "grdnr", "cid": 114},
                              {"sc": 0, "gl": 0, "si": 0, "id": 1112,
                               "tid": "jntr", "cid": 114},
                              {"sc": 0, "gl": 0, "si": 0, "id": 1577,
                               "tid": "vsgst", "cid": 114},
                              {"sc": 0, "gl": 0, "si": 0, "id": 1578,
                               "tid": "phtghr", "cid": 114}],
                      "id": 114, "iu": "", "tp": 9,
                      "ed": datetime(2015, 8, 27, 2, 0)})
if reputation:
    campaigns.append({"st": 1, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 1109,
                               "tid": "reputation", "cid": 113}],
                      "id": 113, "iu": "", "tp": 9,
                      "ed": datetime(2015, 8, 18, 2, 0)})
if school:
    campaigns.append({"st": 2, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 10589,
                               "tid": "schoolAvataria", "cid": 717}],
                      "id": 717, "iu": "", "tp": 9,
                      "ed": datetime(2021, 6, 1, 14, 0)})
if competitions:
    campaigns.append({"st": 2, "v": 1,
                      "cil": [{"sc": 0, "gl": 0, "si": 0, "id": 3239,
                               "tid": "competitions", "cid": 371}],
                      "id": 371, "iu": "", "tp": 9,
                      "ed": datetime(2030, 6, 28, 2, 0)})
