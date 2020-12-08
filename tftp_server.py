import socket
import random
import os.path

TFTP_OPCODES = {
    'unknown': 0,
    'read': 1,  # RRQ
    'write': 2, # WRQ
    'data': 3,  # DATA
    'ack': 4,   # ACKNOWLEDGMENT
    'error': 5  # ERROR
    }
TFTP_MODES = {
    'unknown': 0,
    'netascii': 1,
    'octet': 2,
    'mail': 3
    }
TFTP_SERVER_ERRORS = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
    }

SERVER_ADDRESS = 'localhost'
BLOCKSIZE = 512
TIMEOUT = 5

def read_reqest_handler(data, client):
    actual_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    actual_socket.bind((SERVER_ADDRESS, random.randint(1024, 65535)))

    exp_ack_block_num = 1
    block_num_to_send = 0
    opcode = data[1]
    text_to_send = []

    filename, flag = file_check(data)

    if not flag:
        print(f'ERROR to {client}: Error 1: {TFTP_SERVER_ERRORS[1]}.')
        error_to_send = make_err_pack(1)
        actual_socket.sendto(error_to_send, client)
        return
    
    #https://stackoverflow.com/questions/1035340/reading-binary-file-and-looping-over-each-byte
    with open(filename, 'rb') as file:
        for byte in iter(lambda: file.read(BLOCKSIZE), b''):
            text_to_send.append(byte)
    blocks_num = len(text_to_send)
    received_ack_block_nums = {}

    while True:
        #Sending block
        print(f'DATA to {client}: Block №{block_num_to_send + 1} of size {len(text_to_send[block_num_to_send])}.')
        data_to_send = make_data_pack(text_to_send[block_num_to_send], exp_ack_block_num)
        actual_socket.sendto(data_to_send, client)

        #Waiting for ack
        actual_socket.settimeout(TIMEOUT)
        try:
            data, client = actual_socket.recvfrom(BLOCKSIZE + 4)
        except:
            #We need to resent DATA block
            continue
        if data is not None:
            opcode = data[1]

            if opcode == TFTP_OPCODES['ack']:
                received_ack_block_num = 256*data[2] + data[3]
                print(f'ACK from {client}: Block №{received_ack_block_num} of size {len(text_to_send[received_ack_block_num - 1])}.')
                if received_ack_block_num == blocks_num:
                    print('All data has been sent.')
                    actual_socket.close()
                    return
                elif received_ack_block_num not in received_ack_block_nums:
                    received_ack_block_nums[received_ack_block_num] = 1
                    if received_ack_block_num == exp_ack_block_num:
                        exp_ack_block_num += 1
                        block_num_to_send += 1
                        continue
                elif received_ack_block_num in received_ack_block_nums:
                    #We need to resent DATA block
                    continue    
            elif opcode == TFTP_OPCODES['error']:
                error_code = data[3]
                print(f'Error occured on client side:\n'
                    f'Code :{error_code}\n'
                    f'Message: {TFTP_SERVER_ERRORS[error_code]}')
                actual_socket.close()
                return

def write_request_handler(data, client):
    actual_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    actual_socket.bind((SERVER_ADDRESS, random.randint(1024, 65535)))
    
    filename, flag = file_check(data)

    if flag:
        print(f'ERROR to {client}: Error 6: {TFTP_SERVER_ERRORS[6]}.')
        error_to_send = make_err_pack(6)
        actual_socket.sendto(error_to_send, client)
        return

    received_text = b''
    exp_block_num = 0
    received_block_nums = {}
    block_data = b''    
    
    while True:
        #Sending ack
        send_ack = make_ack_pack(exp_block_num)
        actual_socket.sendto(send_ack, client)
        if exp_block_num != 0:
            print(f'ACK to {client}: Block №{exp_block_num - 1} of size {len(block_data)}.')
        else : print(f'ACK to {client}: Block №0')
        exp_block_num += 1
        
        actual_socket.settimeout(TIMEOUT)
        try:
            data, client = actual_socket.recvfrom(BLOCKSIZE + 4)
        except:
            #We need to resent ACK
            continue
        if data is not None:
            opcode = data[1]

            if opcode == TFTP_OPCODES['data']:
                received_block_num = 256*data[2] + data[3]
                
                #Got already recived block
                if received_block_num in received_block_nums:
                    #We need to resent ACK
                    continue
                #Got expected and first time
                elif exp_block_num == received_block_num and received_block_num not in received_block_nums:
                    received_block_nums[received_block_num] = 1
                    block_data = data[4:]
                    received_text += block_data
                    print(f'DATA from {client}: Block №{received_block_num} of size {len(block_data)}.')
                    if (len(block_data) < BLOCKSIZE):
                        print(f'DATA from {client}: Last block.')
                        with open(filename, 'wb') as file:
                            file.write(received_text)
                        actual_socket.close()
                        return
                    continue
            elif opcode == TFTP_OPCODES['error']:
                    error_code = data[3]
                    print(f'Error occured on client side:\n'
                        f'Code :{error_code}\n'
                        f'Message: {TFTP_SERVER_ERRORS[error_code]}')
                    actual_socket.close()
                    return

def file_check(data):
    split_data = str(data).split('\\x')
    filename = split_data[2][2:]
    file_path = f'{filename}'
    return filename, os.path.isfile(file_path)

def make_err_pack(error_code):
    """
    Format of error packege:
    2 bytes     2 bytes      string    1 byte
    -------------------------------------------
    | Opcode |  ErrorCode |   ErrMsg   |   0  |
    -------------------------------------------
    """
    pack = bytearray()
    opcode_bytes = TFTP_OPCODES['error'].to_bytes(2, byteorder = 'big')
    pack[0:0] = opcode_bytes
    error_code_bytes = error_code.to_bytes(2, byteorder = 'big')
    pack[2:2] = error_code_bytes
    error_msg_bytes = bytearray(TFTP_SERVER_ERRORS[error_code].encode('utf-8'))
    pack[4:4] = error_msg_bytes
    pack.append(0)
    return pack

def make_data_pack(data, block):
    """
    2 bytes     2 bytes      n bytes
    ------------------------------------
    | Opcode |   Block #  |   Data     |
    ------------------------------------
    """
    pack = bytearray()
    opcode_bytes = TFTP_OPCODES['data'].to_bytes(2, byteorder = 'big')
    pack[0:0] = opcode_bytes
    block_bytes = block.to_bytes(2, byteorder = 'big')
    pack[2:2] = block_bytes
    pack[4:4] = data
    return pack

def make_ack_pack(block):
    """
    2 bytes     2 bytes
    -----------------------
    | Opcode |   Block #  |
    -----------------------
    """
    pack = bytearray()
    opcode_bytes = TFTP_OPCODES['ack'].to_bytes(2, byteorder = 'big')
    pack[0:0] = opcode_bytes
    block_bytes = block.to_bytes(2, byteorder = 'big')
    pack[2:2] = block_bytes
    return pack

def server():
    print('Starting...')
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((SERVER_ADDRESS, 69))
    print('Listening for requests on port 69...')
    while True:
        data, client = listen_socket.recvfrom(BLOCKSIZE + 4)
        opcode = data[1]
        if opcode == TFTP_OPCODES['read']:
            print(f'Received RRQ from {client}.')
            read_reqest_handler(data, client)
            print(f'RRQ from {client} processed.')
        elif opcode == TFTP_OPCODES['write']:
            print(f'Received WRQ from {client}.')
            write_request_handler(data, client)
            print(f'WRQ from {client} processed.')
    listen_socket.close()
    return

server()