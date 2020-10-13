from enum import Enum
import time

HOST = 'localhost'
PORT = 5003
HEADER_SIZE = 10

while (HEADER_SIZE-1) % 3 != 0:
    HEADER_SIZE += 1

PART_SIZE = int((HEADER_SIZE-1)/3)
MAX_SIZE = int('9' * PART_SIZE)


class Type(Enum):
    CONNECTION = 0
    MESSAGE = 1
    EXIT = 2
    SERVER_EXIT = 3
    PING = 4


class Header:
    def __init__(self, data):
        part_size = PART_SIZE
        self.type = Type(int(data[0]))
        self.msg_len = int(data[1:part_size+1].strip())
        self.time_len = int(data[part_size+1:part_size*2+1].strip())
        self.name_len = int(data[part_size*2+1:part_size*3+1].strip())

    @property
    def type_to_len(self):
        yield 'msg', self.msg_len
        yield 'time', self.time_len
        yield 'name', self.name_len


def msg_content(t, name='', msg='', time=time.time()):
    #           protocol package
    # 0---1-2------4-5-------7-8--------10
    #  type len(msg) len(time) lan(name)
    #  msg body ........................
    #  ... time body ...................
    #  ... name body ...................
    part_size = int((HEADER_SIZE-1)/3)
    header = f'{t}' + \
        f'{len(msg.encode()):<{part_size}}' + \
        f'{len(str(time).encode()):<{part_size}}' + \
        f'{len(name.encode()):<{part_size}}'
    return (header + msg + str(time) + name).encode()


def _recv_msg(cs, size):
    data = b''
    while len(data) < size:
        data += cs.recv(size-len(data))
        if len(data) == 0:
            break  # err
    return data.decode()
