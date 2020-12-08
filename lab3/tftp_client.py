import socket
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

SERVER_ADDRESS = '192.168.31.135'
BLOCKSIZE = 512
TIMEOUT = 5

def client():
    while True:
        print('1 - Read file')
        print('2 - Write file')
        print('3 - Exit')
        while True:
            comm = input('Enter your wished operation: ')
            if comm != '1' and comm != '2' and comm != '3':
                print('Bad command')
                continue
            elif comm == '3':
                return
            else: break
            
        while True:
            filename = input('Enter filename: ')
            if comm == '1' and os.path.isfile(filename):
                print('File already exist')
                continue
            elif comm == '2' and not os.path.isfile(filename):
                print('No such file to send')
                continue
            else: break

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(TIMEOUT)
        server_address = (SERVER_ADDRESS, 69)
        req = make_request(int(comm), filename, 'octet')
        client_socket.sendto(req, server_address)

        if comm == '1':
            read_reqest_handler(client_socket, filename)
        elif comm == '2':
            write_request_handler(client_socket, filename)           

def read_reqest_handler(actual_socket, filename):
    received_text = b''
    exp_block_num = 1
    received_block_nums = {}
    
    while True:            
        actual_socket.settimeout(TIMEOUT)
        try:
            data, server = actual_socket.recvfrom(BLOCKSIZE + 4)
        except socket.timeout:
            if(exp_block_num == 1):
                print('Server did not recive request. Try again later.')
                return
            else:
                #Resent ack
                send_ack = make_ack_pack(exp_block_num)
                actual_socket.sendto(send_ack, client)
                continue
        if data is not None:
            opcode = data[1]

            if opcode == TFTP_OPCODES['data']:
                received_block_num = 256*data[2] + data[3]
                
                #Got already recived block
                if received_block_num in received_block_nums:
                    send_ack = make_ack_pack(received_block_num)
                    actual_socket.sendto(send_ack, server)
                    print(f'RESENT ACK to {server}: Block №{received_block_num}.')
                    continue
                #Got expected and first time
                elif exp_block_num == received_block_num and received_block_num not in received_block_nums:
                    received_block_nums[received_block_num] = 1
                    block_data = data[4:]
                    received_text += block_data
                    print(f'DATA from {server}: Block №{received_block_num} of size {len(block_data)}.')
                    send_ack = make_ack_pack(exp_block_num)
                    actual_socket.sendto(send_ack, server)
                    exp_block_num += 1
                    print(f'ACK to {server}: Block №{received_block_num} of size {len(block_data)}.')
                    if (len(block_data) < BLOCKSIZE):
                        print(f'DATA from {server}: Last block.')
                        with open(filename, 'wb') as file:
                            file.write(received_text)
                        actual_socket.close()
                        return
                    continue
            elif opcode == TFTP_OPCODES['error']:
                    error_code = data[3]
                    print(f'Error occured on server side:\n'
                        f'Code :{error_code}\n'
                        f'Message: {TFTP_SERVER_ERRORS[error_code]}')
                    actual_socket.close()
                    return

def write_request_handler(actual_socket, filename):

    exp_ack_block_num = 1
    block_num_to_send = 0
    text_to_send = []
    received_ack_block_nums = {}

    #https://stackoverflow.com/questions/1035340/reading-binary-file-and-looping-over-each-byte
    with open(filename, 'rb') as file:
        for byte in iter(lambda: file.read(BLOCKSIZE), b''):
            text_to_send.append(byte)
    blocks_num = len(text_to_send)
    
    while True:
        actual_socket.settimeout(TIMEOUT)
        try:
            #Waiting for ack
            data, server = actual_socket.recvfrom(BLOCKSIZE + 4)
        except socket.timeout:
            if(exp_ack_block_num == 1):
                print('Server did not recive request. Try again later.')
                return
            else:
                #Resent block
                print(f'DATA to {server}: Block №{block_num_to_send + 1} of size {len(text_to_send[block_num_to_send])}.')
                data_to_send = make_data_pack(text_to_send[block_num_to_send], exp_ack_block_num)
                actual_socket.sendto(data_to_send, server)

        if data is not None:
            opcode = data[1]
            if opcode == TFTP_OPCODES['ack']:
                received_ack_block_num = 256*data[2] + data[3]
                print(f'ACK from {server}: Block №{received_ack_block_num} of size {len(text_to_send[received_ack_block_num - 1])}.')
                if received_ack_block_num == 0:
                    print(f'ACK from {server}. Block №0.')
                elif received_ack_block_num == blocks_num:
                    print('All data has been sent.')
                    actual_socket.close()
                    return
                elif received_ack_block_num == exp_ack_block_num and received_ack_block_num not in received_ack_block_nums:
                    received_ack_block_nums[received_ack_block_num] = 1
                    exp_ack_block_num += 1
                    block_num_to_send += 1
                
            elif opcode == TFTP_OPCODES['error']:
                error_code = data[3]
                print(f'Error occured on server side:\n'
                    f'Code: {error_code}\n'
                    f'Message: {TFTP_SERVER_ERRORS[error_code]}')
                actual_socket.close()
                return

        #Sending block
        print(f'DATA to {server}: Block №{block_num_to_send + 1} of size {len(text_to_send[block_num_to_send])}.')
        data_to_send = make_data_pack(text_to_send[block_num_to_send], exp_ack_block_num)
        actual_socket.sendto(data_to_send, server)

def make_request(rq_type, filename, mode):
    request = bytearray()
    if rq_type == TFTP_OPCODES['read']:
        opcode_bytes = TFTP_OPCODES['read'].to_bytes(2, byteorder = 'big')
    elif rq_type == TFTP_OPCODES['write']:
        opcode_bytes = TFTP_OPCODES['write'].to_bytes(2, byteorder = 'big')
    request[0:0] = opcode_bytes
    filename = bytearray(filename.encode('Windows-1251'))
    #filename = bytearray(filename.encode('utf-8'))
    request += filename
    request.append(0)
    mode = bytearray(bytes(mode, 'utf-8'))
    request += mode
    request.append(0)
    return request

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

client()