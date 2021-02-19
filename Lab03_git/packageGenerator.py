from util import makeBytes

OPCODE = {
    'RRQ': 1,
    'WRQ': 2,
    'DATA': 3,
    'ACK': 4,
    'ERROR': 5
}

MODE = {
    'NETASCII': 1,
    'OCTET': 2,
    'MAIL': 3
}

ERROR = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}


def generatePackage(type, fileData=b'', blockNumber=0, filename="", mode='octet', errorCode=0):
    data = bytearray()

    if (type == OPCODE['ACK']):
        data[0:0] = makeBytes(OPCODE['ACK'])
        data[2:2] = makeBytes(blockNumber)
    elif (type == OPCODE['DATA']):
        data[0:0] = makeBytes(OPCODE['DATA'])
        data[2:2] = makeBytes(blockNumber)
        data[4:4] = fileData
    elif (type == OPCODE['ERROR']):
        data[0:0] = makeBytes(OPCODE['ERROR'])
        data[2:2] = makeBytes(errorCode)
        data[4:4] = bytearray(ERROR[errorCode].encode('Windows-1251'))
        data.append(0)
    else:
        if (type == OPCODE['WRQ']):
            data[0:0] = makeBytes(OPCODE['WRQ'])
        elif (type == OPCODE['RRQ']):
            data[0:0] = makeBytes(OPCODE['RRQ'])
        data += bytearray(filename.encode('Windows-1251'))
        data.append(0)
        data += bytearray(bytes(mode, 'Windows-1251'))
        data.append(0)

    return data
