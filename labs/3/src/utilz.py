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
        self.data = None

    def clear(self):
        self.filename = None
        self.block = None


def read(filename):
    try:
        with open(filename, 'rb') as f:
            data = f.read()
        return data
    except:
        return None


def store(filename, data):
    with open(filename, 'ab') as f:
        f.write(data)


def send(sock, addr, data, mode):
    print(f'Sending {data.opcode} to {addr} with mode={mode.value}:\n\t' + data.get_log())
    from tftp_formats import DATA, ACK
    if isinstance(data, DATA):
        # use mode
        pass
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

