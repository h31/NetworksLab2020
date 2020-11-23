import socket
from socket import timeout
import common
import os
# from common import PACKET_SIZE, create_ack_packet, get_blocknum

HOST = "127.0.0.1"
POST = 3000
SERVER_ADDR = (HOST, POST)

block_num = 1
is_last_packet = False


def main():
    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        operation = input("Read or write? (r or w) ")
        filename = input("Input name of file: ")
        opcode = b''
        if operation == 'r':
            opcode = common.RRQ
            rq = create_RQ(opcode, filename)
            fd = open(filename, 'wb')
            print(rq)
            cli_sock.sendto(rq, SERVER_ADDR)
            while not is_last_packet:
                cli_sock.settimeout(3)
                try:
                    pack, addr = cli_sock.recvfrom(common.MAX_BLOCK_SIZE)
                    rd = recv_file(pack, addr, fd, cli_sock)
                    if rd == False:
                        os.remove(filename)
                    # print(is_last_packet)
                except timeout as e:
                    print(e)
                    os.remove(filename)
                    break
            reset()
        elif operation == 'w':
            opcode = common.WRQ
            rq = create_RQ(opcode, filename)
            sd = True
            try:
                fd = open(filename, 'rb') 
                cli_sock.sendto(rq, SERVER_ADDR)
                cli_sock.settimeout(3)
                while not is_last_packet:
                    pack, addr = cli_sock.recvfrom(common.MAX_BLOCK_SIZE)
                    sd = send_file(pack, cli_sock, fd)
            except timeout as e:
                print(e)
                sd = False
            except FileNotFoundError as e:
                print(e)
                sd = False
            reset()
            # print("Have reset after w error: ", block_num, is_last_packet)
            if not sd:
                continue
            pack, addr = cli_sock.recvfrom(4)
            blocks = common.get_blocknum(pack)
            print(f"Last Ack packet: {pack} + {blocks}")
            
        else:
            raise Exception("Nothing to do")
        
def create_RQ(opcode, filename, mode='octet'):
    rq = opcode + filename.encode('utf-8') + b'\x00' + mode.encode('utf-8') + b'\x00'
    return rq


def recv_file(packet, addr, fd, s):
    global is_last_packet
    global block_num
    host, port = addr
    if host != HOST:
        return False
    
    packet_len = len(packet)
    opcode = common.get_opcode(packet)
    if opcode == common.ERROR:
        err_code = common.get_errcode(packet)
        err_msg = common.get_err_msg(packet)
        is_last_packet = True
        fd.close()
        print(f"Error {err_code}: {err_msg}")
        return False
    
    elif opcode == common.DATA:
        blocks = common.get_blocknum(packet)
        if blocks != block_num:
            print(f"Unexpected block num {block_num}")
            return
        else:
            print(f"Packet number {blocks} has been received")
        data = common.get_data(packet)
        fd.write(data)
        ack_pack = common.create_ack_packet(blocks)
        s.sendto(ack_pack, SERVER_ADDR)
        block_num += 1
        if packet_len < common.PACKET_SIZE + 4:
            is_last_packet = True
            fd.close()
            print("Receiving has been done")
        return True
        
def reset():
    global block_num
    global is_last_packet
    block_num = 1
    is_last_packet = False

def send_file(packet, s, fd):
    global is_last_packet
    global block_num

    opcode = common.get_opcode(packet)

    if opcode == common.ERROR:
        # print(packet)
        # print(len(packet))
        err_code = common.get_errcode(packet)
        err_msg = common.get_err_msg(packet)
        is_last_packet = True
        fd.close()
        print(f"Error {err_code}: {err_msg}")
        return False

    elif opcode == common.ACK:
        blocks = common.get_blocknum(packet)
        print(f"Acknowledgment: {packet} + {blocks}")
        print("block_num", block_num)
        data = fd.read(512)
        data_pack = common.create_data_packet(block_num, data)
        s.sendto(data_pack, SERVER_ADDR)
        block_num += 1
        if len(data_pack) < common.PACKET_SIZE + 4:
            is_last_packet = True
            fd.close()
            print("Sending has been done")
        return True

if __name__ == '__main__':
    main()