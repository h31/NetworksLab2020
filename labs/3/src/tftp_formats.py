"""TFTP (rev. 2) formats realisation"""

import os
from enum import Enum

from utilz import int_from_bytes, int_to_n_bytes


class Operation(Enum):
    RRQ = 1
    WRQ = 2
    DATA = 3
    ACK = 4
    ERROR = 5


class Mode(Enum):
    NETASCII = 'netascii'
    OCTET = 'octet'
    MAIL = 'mail'


class ErrorCode(Enum):
    NOTDEFINED = 0
    NOTFOUND = 1
    ACCESSVIOLATION = 2
    DISKFULL = 3
    ILLEGALOP = 4
    UNKNOWN = 5
    EXIST = 6
    NOUSER = 7


def get_error_msg(code):
    msg = ''
    if code == ErrorCode.NOTDEFINED:
        msg = 'Not defined, see error message (if any).'
    elif code == ErrorCode.NOTFOUND:
        msg = 'File not found.'
    elif code == ErrorCode.ACCESSVIOLATION:
        msg = 'Access violation.'
    elif code == ErrorCode.DISKFULL:
        msg = 'Disk full or allocation exceeded.'
    elif code == ErrorCode.ILLEGALOP:
        msg = 'Illegal TFTP operation.'
    elif code == ErrorCode.UNKNOWN:
        msg = 'Unknown transfer ID.'
    elif code == ErrorCode.EXIST:
        msg = 'File already exists.'
    elif code == ErrorCode.NOUSER:
        msg = 'No such user.'
    return msg


CR = b'\x0d'
LF = b'\x0a'
CRLF = CR + LF
NUL = b'\x00'
CRNUL = CR + NUL

if isinstance(os.linesep, bytes):
    NL = os.linesep
else:
    NL = os.linesep.encode("ascii")


def netascii(data, to):
    import re
    if to:
        adict = {NL: CRLF, CR: CRNUL}
    else:
        adict = {CRLF: NL, CRNUL: CR}
    rx = re.compile(b'|'.join(map(re.escape, adict)))
    return rx.sub(lambda match: adict[match.group(0)], data)


def mail(data):
    pass


class RRQ:
    def __init__(self, data):
        self.opcode = Operation(int_from_bytes(data[0:2]))
        self.filename = ''
        for byte in data[2::]:
            if byte == 0:
                break
            self.filename += chr(byte)
        mode_data = ''
        for byte in data[2 + len(self.filename) + 1::]:
            if byte == 0:
                break
            mode_data += chr(byte)
        self.mode = Mode(mode_data.lower())

    @staticmethod
    def create(filename, mode):
        return RRQ(
            int_to_n_bytes(Operation.RRQ.value)
            + filename.encode()
            + int_to_n_bytes(0, 1)
            + mode.encode()
            + int_to_n_bytes(0, 1)
        )

    @property
    def package(self):
        return (
            int_to_n_bytes(self.opcode.value)
            + self.filename.encode()
            + int_to_n_bytes(0, 1)
            + self.mode.value.encode()
            + int_to_n_bytes(0, 1)
        )

    def get_log(self):
        return f'\tfilename: {self.filename}\n\tmode: {self.mode}'


class WRQ(RRQ):
    @staticmethod
    def create(filename, mode):
        return WRQ(
            int_to_n_bytes(Operation.WRQ.value)
            + filename.encode()
            + int_to_n_bytes(0, 1)
            + mode.encode()
            + int_to_n_bytes(0, 1)
        )


class DATA:
    def __init__(self, data):
        self.opcode = Operation.DATA
        self.block = int_from_bytes(data[2:4])
        self.data = data[4::]
        self.last = True if len(self.data) < 512 else False

    @property
    def package(self):
        from utilz import int_to_n_bytes
        return int_to_n_bytes(self.opcode.value) + int_to_n_bytes(self.block) + self.data

    @staticmethod
    def create(block, data):
        return DATA(
            int_to_n_bytes(Operation.DATA.value)
            + int_to_n_bytes(block)
            + data
        )

    def get_log(self):
        return f'\tblock: {self.block}\n\tdata length: {len(self.data)}'


class ACK:
    def __init__(self, data):
        self.opcode = Operation.ACK
        self.block = int_from_bytes(data[2:4])

    @staticmethod
    def create(block):
        from utilz import int_to_n_bytes
        return ACK(int_to_n_bytes(Operation.ACK.value) + int_to_n_bytes(block))

    @property
    def package(self):
        from utilz import int_to_n_bytes
        return int_to_n_bytes(self.opcode.value) + int_to_n_bytes(self.block)

    def get_log(self):
        return f'\tblock: {self.block}'


class ERROR:
    def __init__(self, data):
        self.opcode = Operation.ERROR
        self.code = ErrorCode(int_from_bytes(data[2:4]))
        self.message = ''
        for byte in data[4:]:
            if byte == 0:
                break
            self.message += chr(byte)

    @staticmethod
    def create_from_code(code):
        opcode = Operation.ERROR
        message = get_error_msg(code)
        data = (
            int_to_n_bytes(opcode.value)
            + int_to_n_bytes(code.value)
            + message.encode()
            + int_to_n_bytes(0, 1)
        )
        return ERROR(data)

    @property
    def package(self):
        return (
            int_to_n_bytes(self.opcode.value)
            + int_to_n_bytes(self.code.value)
            + self.message.encode()
            + int_to_n_bytes(0, 1)
        )

    def get_log(self):
        return f'\terror code: {self.code}\n\terror message: {self.message}'


opcode_to_package = {
    Operation.RRQ: RRQ,
    Operation.WRQ: WRQ,
    Operation.DATA: DATA,
    Operation.ACK: ACK,
    Operation.ERROR: ERROR,
}

