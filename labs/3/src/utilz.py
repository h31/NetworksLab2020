"""Utils for TFTP"""

from functools import reduce

SETTINGS = {
    'HOST': {
        'ADDR': 'localhost',
        'PORT': 5001,
    },
    'BUFFERSIZE': 1024,
    'DISKSIZE': 1024 * 1024 * 1024  # 1 GB
}


class User:
    def __init__(self):
        self.mode = None
        self.filename = None
        self.block = None
        self.data = b''

    def clear(self):
        self.mode = None
        self.filename = None
        self.block = None
        self.data = b''


def read(filename, server=True):
    try:
        with open(('files/' if server else '') + filename, 'rb') as f:
            data = f.read()
        return data
    except:
        return None


def store(filename, data, mode, server=True):
    from tftp_formats import Mode, mail, netascii
    if mode == Mode.NETASCII:
        with open(('files/' if server else '') + filename, 'wb') as f:
            f.write(netascii(data, False))
    elif mode == Mode.OCTET:
        with open(('files/' if server else '') + filename, 'wb') as f:
            f.write(data)


def send(sock, addr, data, mode):
    print(f'sending {data} to {addr}')
    sock.sendto(data.package, addr)


def recv(sock):
    from tftp_formats import Operation, opcode_to_package
    data, addr = sock.recvfrom(SETTINGS['BUFFERSIZE'])
    try:
        opcode = int_from_bytes(data[0:2])
        frmt = opcode_to_package[Operation(opcode)](data)
    except:
        from exception import IllegalOpCode
        raise IllegalOpCode
    return frmt, addr


def int_to_n_bytes(val, n=2):
    return val.to_bytes(n, 'big')


def int_from_bytes(bytelist):
    return int.from_bytes(bytelist, 'big', signed=False)

