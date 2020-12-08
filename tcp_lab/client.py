import socket
from socket import timeout
import common
import os
# from common import PACKET_SIZE, create_ack_packet, get_blocknum

HOST = "192.168.1.109"
#HOST = "127.0.0.1"
PORT = 69
#PORT = 6106
#PORT = 3000
SERVER_ADDR = (HOST, PORT)

block_num = 1
is_last_packet = False
count = 0
sv_addr = (HOST, PORT)
data_len = 0
tmp_pack = b""

def main():
    global count, sv_addr, tmp_pack
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
                cli_sock.settimeout(5)
                try:
                    pack, addr = cli_sock.recvfrom(common.MAX_BLOCK_SIZE)
                    sv_addr = addr
                    # print("packet nek:", pack)
                    rd = recv_file(pack, addr, fd, cli_sock)
                    if rd == False:
                        os.remove(filename)
                    # print(is_last_packet)
                    count = 0
                except timeout as e:
                    if count < 10 and block_num == 1:
                        print("count = " + str(count))
                        print("resend request: ", rq)
                        cli_sock.sendto(rq, SERVER_ADDR)
                        count += 1
                        continue
                    if count < 10 and block_num != 1:
                        re_ack = tmp_pack
                        print("count = " + str(count))
                        print("resend ack", re_ack)
                        cli_sock.sendto(re_ack, sv_addr)
                        count += 1
                        continue
                    elif count == 10:
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
            
                if sd:
                    cli_sock.sendto(rq, SERVER_ADDR)
                    cli_sock.settimeout(5)
                    while True:
                        try:
                            pack, addr = cli_sock.recvfrom(common.MAX_BLOCK_SIZE)
                            sv_addr = addr
                            count = 0
                            print("ACK nek:", pack)
                            if not is_last_packet:
                                sd = send_file(pack, cli_sock, fd, addr)
                            elif is_last_packet:
                                reset()
                                blocks = common.get_blocknum(pack)
                                print(f"Last Ack packet: {pack} + {blocks}")
                                print("Sending has been done")
                                fd.close()
                                break
                        except timeout as e:
                            if count < 10 and block_num == 1:
                                print("count = " + str(count))
                                print("resend request: ", rq)
                                cli_sock.sendto(rq, SERVER_ADDR)
                                count += 1
                                continue
                            elif count < 10 and block_num != 1:
                                # fd.seek(fd.tell() - data_len, 0)
                                # data = fd.read(512)
                                data_pack = tmp_pack
                                cli_sock.sendto(data_pack, sv_addr)
                                count += 1
                                continue
                            elif count == 10:
                                print(e)
                                sd = False
                                reset()
                                break
            except FileNotFoundError as e:
                    print(e)
                    sd = False
            reset()
            # print("Have reset after w error: ", block_num, is_last_packet)
            # if not sd:
            #     continue
            # pack, addr = cli_sock.recvfrom(4)
            # blocks = common.get_blocknum(pack)
            # print(f"Last Ack packet: {pack} + {blocks}")
            
        else:
            raise Exception("Nothing to do")
        
def create_RQ(opcode, filename, mode='octet'):
    rq = opcode + filename.encode('utf-8') + b'\x00' + mode.encode('utf-8') + b'\x00'
    return rq


def recv_file(packet, addr, fd, s):
    global is_last_packet, block_num, tmp_pack

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
        # if blocks == block_num - 1:
        #     print(f"Unexpected block num {blocks}")
        #     ack_pack = tmp_pack
        #     print("resend ack", ack_pack)
        #     s.sendto(tmp_pack, addr)
        #     return True
        if blocks == block_num:
            print(f"Packet number {blocks} has been received")
            data = common.get_data(packet)
            fd.write(data)
            ack_pack = common.create_ack_packet(blocks)
            tmp_pack = ack_pack
            # print("ack gui di nek:", ack_pack)
            s.sendto(ack_pack, addr)
            block_num += 1
            if packet_len < common.PACKET_SIZE + 4:
                is_last_packet = True
                fd.close()
                print("Receiving has been done")
            return True
        
def reset():
    global block_num, is_last_packet
    global count, data_len, tmp_pack
    block_num = 1
    is_last_packet = False
    count = 0
    data_len = 0
    tmp_pack = b""

def send_file(packet, s, fd, addr):
    global is_last_packet
    global block_num, data_len, tmp_pack

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
        if blocks == block_num - 1:
            print(f"Acknowledgment: {packet} + {blocks}")
            print("block_num: ", block_num)
            data = fd.read(512)
            data_len = len(data)
            data_pack = common.create_data_packet(block_num, data)
            tmp_pack = data_pack
            s.sendto(data_pack, addr)
            block_num += 1
            # if len(data_pack) < common.PACKET_SIZE + 4:
            #     is_last_packet = True
                # fd.close()
                # print("Sending has been done")
            # return True
        # elif blocks == block_num - 2:
        #     print("number of blocks not compare")
        #     # fd.seek(fd.tell() - data_len, 0)
        #     # data = fd.read(512)
        #     # data_len = len(data)
        #     data_pack = tmp_pack
        #     # data_len = len(data_pack) - 4
        #     s.sendto(data_pack, addr)
        #     # if len(data_pack) < common.PACKET_SIZE + 4:
        #     #     is_last_packet = True
        #         # fd.close()
        #         # print("Sending has been done")
        #     # return True

        if data_len < 512:
            is_last_packet = True

if __name__ == '__main__':
    main()