import binascii
import struct
from datetime import datetime


class BytesWithPosition():
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def __len__(self):
        return len(self.data)

    def hex(self):
        return self.data.hex()

    def read(self, amount):
        if self.pos+amount > len(self.data):
            print("пыталался читать то, чего нет, "
                  f"{self.pos} - {len(self.data)}")
            print(amount)
            raise Exception()
        old_pos = self.pos
        self.pos += amount
        return self.data[old_pos:self.pos]

    def read_i8(self):
        return struct.unpack(">b", self.read(1))[0]

    def read_u8(self):
        return struct.unpack(">B", self.read(1))[0]

    def read_i32(self):
        return struct.unpack(">i", self.read(4))[0]

    def read_u32(self):
        return struct.unpack(">I", self.read(4))[0]

    def read_i64(self):
        return struct.unpack(">q", self.read(8))[0]

    def read_f64(self):
        return struct.unpack(">d", self.read(8))[0]


def processFrame(data, client=False):
    data = BytesWithPosition(data)
    mask = data.read_u8()
    checksummed_mask = 1 << 3
    if 0 != (mask & checksummed_mask):
        checksummed = True
    else:
        checksummed = False
    if checksummed:
        checksum = data.read_u32()
        old_pos = data.pos
        message = data.read(len(data)-data.pos)
        data.pos = old_pos
        real_checksum = binascii.crc32(message)
        if checksum != real_checksum:
            print("чексуммы не совпадают")
            return
    if client:
        data.pos += 4  # message number
    type_ = data.read_i8()
    return {"type": type_, "msg": decodeArray(data)}


def decodeArray(data):
    result = []
    length = data.read_i32()
    i = 0
    while i < length:
        result.append(decodeValue(data))
        i += 1
    return result


def decodeValue(data):
    dataType = data.read_i8()
    if dataType == 0:  # null
        return None
    elif dataType == 1:  # bool
        if data.read_i8():
            return True
        else:
            return False
    elif dataType == 2:  # int
        return data.read_i32()
    elif dataType == 3:  # long
        return data.read_i64()
    elif dataType == 4:  # double
        return data.read_f64()
    elif dataType == 5:  # string
        return decodeString(data)
    elif dataType == 6:  # dictionary
        return decodeDictionary(data)
    elif dataType == 7:  # array
        return decodeArray(data)
    elif dataType == 8:  # date
        return datetime.fromtimestamp(data.read_i64()/1000)
    else:
        raise ValueError(f"Wrong datatype: {dataType}")


def decodeDictionary(data):
    fields = data.read_i32()
    obj = {}
    i = 0
    while i < fields:
        key = decodeString(data)
        obj[key] = decodeValue(data)
        i += 1
    return obj


def decodeString(data):
    i = 0
    b = data.read_u8()
    value = 0
    while b & 128 != 0:
        value += (b & 127) << i
        i += 7
        if i > 35:
            raise Exception("Variable length quantity is too long")
        b = data.read_u8()
    length = value | b << i
    return data.read(length).decode()


def encodeArray(data):
    final_data = struct.pack(">i", len(data))
    for item in data:
        final_data += encodeValue(item)
    return final_data


def encodeValue(data, forDict=False):
    final_data = b""
    if data is None:
        final_data += struct.pack(">b", 0)
    elif isinstance(data, bool):
        final_data += struct.pack(">b", 1)
        final_data += struct.pack(">b", int(data))
    elif isinstance(data, int):
        if data > 2147483647:
            final_data += struct.pack(">b", 3)
            final_data += struct.pack(">q", data)
        else:
            final_data += struct.pack(">b", 2)
            final_data += struct.pack(">i", data)
    elif isinstance(data, float):
        final_data += struct.pack(">b", 4)
        final_data += struct.pack(">d", data)
    elif isinstance(data, str):
        if not forDict:
            final_data += struct.pack(">b", 5)
        length = len(data.encode().hex())//2
        while (length & 4294967168) != 0:
            final_data += struct.pack(">B", length & 127 | 128)
            length = length >> 7
        final_data += struct.pack(">B", length & 127)
        final_data += data.encode()
    elif isinstance(data, dict):
        final_data += struct.pack(">b", 6)
        final_data += encodeObject(data)
    elif isinstance(data, list):
        final_data += struct.pack(">b", 7)
        final_data += encodeArray(data)
    elif isinstance(data, datetime):
        final_data += struct.pack(">b", 8)
        final_data += struct.pack(">q", int(data.timestamp() * 1000))
    else:
        raise ValueError("Не могу энкодить "+str(type(data)))
    return final_data


def encodeObject(data):
    final_data = struct.pack(">i", len(data))
    for item in data.keys():
        final_data += encodeValue(item, forDict=True)
        final_data += encodeValue(data[item])
    return final_data
