# Operation code
RRQ = b'\x00\x01'
WRQ = b'\x00\x02'
DATA = b'\x00\x03'
ACK = b'\x00\x04'
ERROR = b'\x00\x05'

# Type of ERROR
UNKNOWN = b'\x00\x00'
FILE_NOT_FOUND = b'\x00\x01'
ACCESS_VIOLATION = b'\x00\x02'
DISK_FULL = b'\x00\x03'
ILLEGAL_OPERATION = b'\x00\x04'
UNKNOWN_TRANFER_ID = b'\x00\x05'
FILE_EXIST = b'\x00\x06'
NO_SUCH_USER = b'\x00\x07'

ERR_MESSAGE = {
    UNKNOWN: "Error not defined",
    FILE_NOT_FOUND: "File not found",
    ACCESS_VIOLATION: "Access violation",
    DISK_FULL: "Disk full or allocation exceeded",
    ILLEGAL_OPERATION: "Illegal TFTP operation",
    FILE_EXIST: "File already exists",
    NO_SUCH_USER: "No such user"
}

PACKET_SIZE = 512
MAX_BLOCK_SIZE = 1428

def create_data_packet(block_num, data):
    num_bytes = block_num.to_bytes(2, 'big')
    data_bytes = DATA + num_bytes + data
    return data_bytes

def create_ack_packet(block_num):
    num_bytes = block_num.to_bytes(2, 'big')
    ack_bytes = ACK + num_bytes
    return ack_bytes

def create_err_packet(type):
    return ERROR + type + ERR_MESSAGE[type].encode('utf-8') + b'\x00'

def get_opcode(packet):
    return packet[0:2]

def get_blocknum(packet):
    number = int.from_bytes(packet[2:4], 'big')
    return number

def get_data(packet):
    return packet[4:]

def get_errcode(packet):
    return int.from_bytes(packet[2:4], 'big')

def get_err_msg(packet):
    return packet[4:-1].decode('utf-8')

def get_filename(packet):
    return packet[2:-1].split(b'\x00')[0].decode('utf-8')