from modules.base_module import Module


class_name = "Descriptor"
playAtHome2020 = [{'gg': {}, 'dg': []}]
playAtHome2020[0]["gg"]["beachRace"] = {'aw': {'win': {'slvr': 100, 'enrg': 0,
                                                       'gld': 0}},
                                        'gt': 'beachRace'}
playAtHome2020[0]["gg"]["snowboardRace"] = {'aw': {'win': {'slvr': 0,
                                                           'enrg': 0,
                                                           'gld': 1}},
                                            'gt': 'snowboardRace'}
playAtHome2020[0]["gg"]["meerkat"] = {'aw': {'ma1': {'slvr': 50, 'enrg': 0,
                                                     'gld': 0},
                                             'ma2': {'slvr': 100, 'enrg': 0,
                                                     'gld': 0},
                                             'ma3': {'slvr': 0, 'enrg': 0,
                                                     'gld': 1}},
                                      'gt': 'meerkat'}
playAtHome2020[0]["gg"]["schoolAvataria"] = {'aw': {}, 'gt': 'schoolAvataria'}
playAtHome2020[0]["gg"]["canyonRace"] = {'aw': {'win': {'slvr': 0, 'enrg': 0,
                                                        'gld': 1}},
                                         'gt': 'canyonRace'}
outsideLocations = []
outsideLocations.append({'zid': 'street', 'drid': 'y1',
                         'rms': [{'id': 'y1', 'vip': False, 'uc': 'yard_1_map',
                                  'bgs': 'outside1', 'dc': 'outside', 'ml': 0},
                                 {'id': 'y1e', 'vip': False,
                                  'uc': 'yard_1_map', 'bgs': 'outside1',
                                  'dc': 'outside', 'ml': 0}],
                         'ldc': 'yard,landscape', 'id': 'yard'})
outsideLocations.append({'zid': 'street', 'drid': 'cf1',
                         'rms': [{'id': 'cf1', 'vip': False,
                                  'uc': 'cafe_1_map', 'bgs': 'cafe1',
                                  'dc': 'outside', 'ml': 0},
                                 {'id': 'cf1e', 'vip': False,
                                  'uc': 'cafe_1_map', 'bgs': 'cafe1',
                                  'dc': 'outside', 'ml': 0}],
                         'ldc': 'cafe', 'id': 'cafe'})
outsideLocations.append({'zid': 'street', 'drid': 'cl1',
                         'rms': [{'id': 'cl1', 'vip': False,
                                  'uc': 'club_1_map', 'bgs': 'club1',
                                  'dc': 'outside', 'ml': 4},
                                 {'id': 'cl1e', 'vip': False,
                                  'uc': 'club_1_map', 'bgs': 'club1',
                                  'dc': 'outside', 'ml': 4},
                                 {'id': 'v1', 'vip': True, 'uc': 'vip_1_map',
                                  'bgs': 'vip1', 'dc': 'outside', 'ml': 0},
                                 {'id': 'v1e', 'vip': True, 'uc': 'vip_1_map',
                                  'bgs': 'vip1', 'dc': 'outside', 'ml': 0}],
                         'ldc': 'club,vip', 'id': 'club'})
outsideLocations.append({'zid': 'street', 'drid': 'p1',
                         'rms': [{'id': 'p1', 'vip': False, 'uc': 'park_1_map',
                                  'bgs': 'outside1', 'dc': 'outside', 'ml': 0},
                                 {'id': 'p1e', 'vip': False,
                                  'uc': 'park_1_map', 'bgs': 'outside1',
                                  'dc': 'outside', 'ml': 0}],
                         'ldc': 'park,landscape', 'id': 'park'})
outsideLocations.append({'zid': 'street', 'drid': 's1',
                         'rms': [{'id': 's1', 'vip': False,
                                  'uc': 'street_1_map', 'bgs': 'outside1',
                                  'dc': 'outside', 'ml': 0},
                                 {'id': 's1e', 'vip': False,
                                  'uc': 'street_1_map', 'bgs': 'outside1',
                                  'dc': 'outside', 'ml': 0}],
                         'ldc': 'street,landscape', 'id': 'street'})
outsideLocations.append({'zid': 'street', 'drid': 'pb1',
                         'rms': [{'id': 'pb1', 'vip': False,
                                  'uc': 'public_beach_1_map',
                                  'bgs': 'outside1', 'dc': 'beach', 'ml': 0},
                                 {'id': 'pb1e', 'vip': False,
                                  'uc': 'public_beach_1_map',
                                  'bgs': 'outside1', 'dc': 'beach', 'ml': 0}],
                         'ldc': 'publicBeach', 'id': 'publicBeach'})
outsideLocations.append({'zid': 'street', 'drid': 'br1',
                         'rms': [{'id': 'br1', 'vip': False,
                                  'uc': 'ballroom_1_map', 'bgs': 'outside1',
                                  'dc': 'ballroom', 'ml': 0},
                                 {'id': 'br1e', 'vip': False,
                                  'uc': 'ballroom_1_map', 'bgs': 'outside1',
                                  'dc': 'ballroom', 'ml': 0}],
                         'ldc': 'ballroom', 'id': 'ballroom'})
outsideLocations.append({'zid': 'street', 'drid': 'pc1',
                         'rms': [{'id': 'pc1', 'vip': False,
                                  'uc': 'canyon_1_map', 'bgs': 'outside1',
                                  'dc': 'outside', 'ml': 0}],
                         'ldc': 'canyon', 'id': 'canyon'})
outsideLocations.append({'zid': 'street', 'drid': 'sn1',
                         'rms': [{'id': 'sn1', 'vip': False,
                                  'uc': 'salon_1_map', 'bgs': 'cafe1',
                                  'dc': 'outside', 'ml': 6}],
                         'ldc': 'salon', 'id': 'salon'})
outsideLocations.append({'zid': 'street', 'drid': 'psn1',
                         'rms': [{'id': 'psn1', 'vip': False,
                                  'uc': 'photo_salon_1_map', 'bgs': 'cafe1',
                                  'dc': 'outside', 'ml': 0}],
                         'ldc': 'photoSalon', 'id': 'photoSalon'})
outsideLocations.append({'zid': 'street', 'drid': 'ctr1',
                         'rms': [{'id': 'ctr1', 'vip': False,
                                  'uc': 'couturier_1_map', 'bgs': 'outside1',
                                  'dc': 'outside', 'ml': 0}],
                         'ldc': 'couturier', 'id': 'couturier'})
outsideLocations.append({'zid': 'street', 'drid': 'sr1',
                         'rms': [{'id': 'sr1', 'vip': False,
                                  'uc': 'ski_resort_1_map', 'bgs': 'skiResort',
                                  'dc': 'outside', 'ml': 0},
                                 {'id': 'sr1e', 'vip': False,
                                  'uc': 'ski_resort_1_map', 'bgs': 'skiResort',
                                  'dc': 'outside', 'ml': 0}],
                         'ldc': 'skiResort', 'id': 'skiResort'})
outsideLocations.append({'zid': 'street', 'drid': 'wb1e',
                         'rms': [{'id': 'wb1e', 'vip': False,
                                  'uc': 'wedding_beach_1_map',
                                  'bgs': 'outside1', 'dc': 'outside',
                                  'ml': 0}],
                         'ldc': 'weddingBeach', 'id': 'weddingBeach'})
outsideLocations.append({'zid': 'street', 'drid': 'ir1',
                         'rms': [{'id': 'ir1', 'vip': False,
                                  'uc': 'iceRink_1_map', 'bgs': 'outside1',
                                  'dc': 'outside', 'ml': 15}],
                         'ldc': 'iceRink', 'id': 'iceRink'})
outsideLocations.append({'zid': 'street', 'drid': 'pdm',
                         'rms': [{'id': 'pdm', 'vip': False,
                                  'uc': 'podium_1_map', 'bgs': 'Podium1',
                                  'dc': 'beach', 'ml': 0},
                                 {'id': 'pdme', 'vip': False,
                                  'uc': 'podium_1_map', 'bgs': 'Podium1',
                                  'dc': 'beach', 'ml': 0}],
                         'ldc': 'podium,iceRink', 'id': 'podium'})


class Descriptor(Module):
    prefix = "dscr"

    def __init__(self, server):
        self.server = server
        self.commands = {"init": self.init, "load": self.load}

    async def init(self, msg, client):
        await client.send(['dscr.ldd', {'init': True,
                                        'outsideLocations': outsideLocations}])

    async def load(self, msg, client):
        msg = {"init": False}
        if msg[2]["key"] == "playAtHome2020":
            msg["playAtHome2020"] = playAtHome2020
        await client.send("dscr.ldd", msg)
