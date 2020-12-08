import socket
from socket import timeout
import common
import os
# from common import MAX_BLOCK_SIZE, WRQ, get_blocknum, get_opcode

HOST = "0.0.0.0"
PORT69 = 69
PORT = 5000
SERVER_ADDR69 = (HOST, PORT69)
SERVER_ADDR = (HOST, PORT)
block_num_RRQ = 0
block_num_WRQ = 0
is_last_packet = False
client = []
file_do = [None] * 2
count = 0


def main():

    server69 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server69.bind(SERVER_ADDR69)
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(SERVER_ADDR)
    while True:
        handle_client(server69, server)


def handle_client(s69, s):
    global block_num_RRQ, block_num_WRQ
    global is_last_packet, count

    while True:
        pack, addr = s69.recvfrom(1024)
        # print("receive_pack: ", pack)
        # client.append(addr)
        opcode = common.get_opcode(pack)
        # print("opcode: ", opcode)
        s_packet = b""
        if opcode == common.RRQ:
            file_n = common.get_filename(pack)
            file_do[0] = file_n
            print(f"Server will send file to {addr}")
            try:
                fd = open(file_n, 'rb')
                file_do[1] = fd
                rd = fd.read(512)
                # print("doc file ", rd)
                block_num_RRQ += 1
                data_pack = common.create_data_packet(block_num_RRQ, rd)
                # print("data_pack: ", data_pack)
                s_packet = data_pack
                s.sendto(data_pack, addr)
                if(len(data_pack) < common.PACKET_SIZE):
                    is_last_packet == True
            except FileNotFoundError:
                error_pack = common.create_err_packet(common.FILE_NOT_FOUND)
                # print(error_pack)
                s.sendto(error_pack, addr)
                continue

        elif opcode == common.WRQ:
            file_n = common.get_filename(pack)
            if os.path.exists(file_n):
                error_pack = common.create_err_packet(common.FILE_EXIST)
                # print(error_pack)
                s.sendto(error_pack, addr)
                continue
            else:
                file_do[0] = file_n
                print(f"Server will receive file from {addr}")
                fd = open(file_n, 'wb')
                file_do[1] = fd
                # send ACK
                ack_pack = common.create_ack_packet(block_num_WRQ)
                s_packet = ack_pack
                s.sendto(ack_pack, addr)
                block_num_WRQ += 1

        else:
            error_pack = common.create_err_packet(common.ILLEGAL_OPERATION)
            s.sendto(error_pack, addr)
            continue

        tmp_pack = s_packet
        s.settimeout(5)

        while True:
            try:
                pack, addr = s.recvfrom(1024)
                opcode = common.get_opcode(pack)
                if opcode == common.ACK:
                    # receive ACK and send file
                    # print("da tung o day")
                    if len(tmp_pack) < common.PACKET_SIZE + 4:
                        is_last_packet = True
                    num = common.get_blocknum(pack)
                    # if num == block_num_RRQ:
                    #     print(f'Data packet number {num} has been sent')
                    # else:
                    #     print("Packet lost")
                    #     # continue
                    if num == block_num_RRQ:
                        print(f'Data packet number {num} has been sent')
                        block_num_RRQ += 1
                        data = file_do[1].read(512)
                        data_pack = common.create_data_packet(
                            block_num_RRQ, data)
                        tmp_pack = data_pack
                        if not is_last_packet:
                            s.sendto(data_pack, addr)
                        else:
                            print("All of file has been sent")
                            reset()
                            break
                        # if(len(data_pack) < common.PACKET_SIZE):
                        #     is_last_packet = True
                    # elif num == block_num_RRQ - 1:
                    #     s.sendto(tmp_pack, addr)
                    # if is_last_packet:
                    #     print("All of file has been sent")
                    #     reset()
                    #     break

                elif opcode == common.DATA:
                    # receive DATA and write to file then send ACK
                    num = common.get_blocknum(pack)
                    if num == block_num_WRQ:
                        data = common.get_data(pack)
                        file_do[1].write(data)
                        ack_pack = common.create_ack_packet(num)
                        tmp_pack = ack_pack
                        s.sendto(ack_pack, addr)
                        block_num_WRQ += 1
                        print(f'Data packet number {num} has been receive')
                        # else:
                        #     print(f"Unexpected block num {num}")
                        # continue

                        if len(data) < common.PACKET_SIZE:
                            is_last_packet = True
                            print("File has been receive fully")
                            file_do[1].close()
                            reset()
                            print("After reset: ", block_num_WRQ, block_num_RRQ)
                            break
                    # elif num == block_num_WRQ - 1:
                    #     s.sendto(tmp_pack, addr)
                    # if block_num_WRQ == num:

                elif opcode == common.RRQ or opcode == common.WRQ:
                    s.sendto(s_packet, addr)

            except timeout as e:
                if count < 10 and (block_num_RRQ == 0 or block_num_WRQ == 0):
                    print("resend start packet", s_packet)
                    print("count = " + str(count))
                    s.sendto(s_packet, addr)
                elif count < 10 and (block_num_RRQ != 0 or block_num_WRQ != 0):
                    print("resend packet:", tmp_pack)
                    print("count = " + str(count))
                    s.sendto(tmp_pack, addr)
                elif count == 10:
                    print(e)
                    reset()
                    break


def reset():
    global block_num_RRQ, block_num_WRQ
    global is_last_packet
    is_last_packet = False
    block_num_RRQ = 0
    block_num_WRQ = 0
    file_do[0] = None
    file_do[1] = None


if __name__ == '__main__':
    main()
