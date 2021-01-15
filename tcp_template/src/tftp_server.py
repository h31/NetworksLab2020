import socket
import os
import struct
from _thread import *
import time


def change_filename(filename):
    n = 1
    file = str(n) + '_' + filename
    while True:
        if os.path.isfile(file):
            n += 1
            file = str(n) + '_' + filename
        else:
            break
    return file


class Client:
    def __init__(self, client, server):
        self.client = client
        self.server = server
        self.size = 0
        self.block = 1
        self.create_file = None
        self.open_file = None
        self.is_end = False
        self.is_end_read = False
        self.packet = None
        self.repeat = -1

    def request(self, msg):
        req = msg[0:2]
        if req == b'\x00\x01':
            self.rrq(msg)
        if req == b'\x00\x02':
            self.wrq(msg)
        if req == b'\x00\x03':
            self.data(msg)
        if req == b'\x00\x04':
            self.ack(msg)

    def rrq(self, msg):
        #print("RRQ")
        self.is_end = False
        pack = msg[2:].split(b'\x00')
        print(pack)
        filename = bytes.decode(pack[0])
        file_path = os.path.abspath(filename)
        if os.path.isfile(file_path):
            self.open_file = open(file_path, 'rb')
            read_chunk = self.open_file.read(512)
            self.packet = b'\x00\x03' + struct.pack(b'!H', self.block) + read_chunk
            self.server.sendto(self.packet, self.client)
            if len(read_chunk) < 512:
                self.is_end = True
                self.block = 1
            start_new_thread(self.thread, ())
        else:
            print("file not exist")
            self.server.sendto(b'\x00\x05'+"file not exist".encode(), self.client)

    def wrq(self, msg):
        #print("WRQ")
        self.is_end = False
        pack = msg[2:].split(b'\x00')
        print(pack)
        filename = "client_"+bytes.decode(pack[0])
        file_path = os.path.abspath(filename)
        if os.path.isfile(file_path):
            file_path = os.path.abspath(change_filename(filename))
        self.create_file = open(file_path, 'wb')
        self.size = 0
        self.packet = b'\x00\x04' + struct.pack(b'!H', self.size)  # подтверждение пакета
        self.server.sendto(self.packet, self.client)
        start_new_thread(self.thread, ())

    def thread(self):
        self.repeat = -1
        print(self.is_end)
        while True:
            if self.is_end:
                print("Is end")
                break
            if self.repeat <= 10:
                self.server.sendto(self.packet, self.client)
                print("Resending")
            elif self.repeat > 10:
                print("Session timeout")
                break
            self.repeat += 1
            time.sleep(1)

    def data(self, msg):
        #print("DATA")
        curr_block = struct.unpack('!H', msg[2:4])[0]
        filling = msg[4:]
        #print(filling)
        self.size += len(filling)
        if curr_block == self.block:
            self.create_file.write(filling)
            self.block += 1
            if self.block == 65536:
                self.block = 0
            self.packet = b'\x00\x04' + struct.pack(b'!H', curr_block)
            self.server.sendto(self.packet, self.client)
            if len(filling) < 512:
                print("Done")
                self.create_file.close()
                self.is_end = True
                self.block = 1

    def ack(self, msg):
        #print("ACK")
        self.is_end_read = False
        curr_block = struct.unpack('!H', msg[2:4])[0]
        read_chunk = b''
        if curr_block == self.block and not self.is_end_read:
            read_chunk = self.open_file.read(512)
            chunk_size = len(read_chunk)
            self.block += 1
            if self.block == 65536:
                self.block = 0
            self.packet = b'\x00\x03' + struct.pack(b'!H', self.block) + read_chunk
            self.server.sendto(self.packet, self.client)
            if chunk_size < 512:
                print("Done")
                self.open_file.close()
                self.is_end = True
                self.is_end_read = True
                self.block = 1


def main():
    print("Server started")
    localhost = "127.0.0.1"
    port = 69
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((localhost, port))
    clients = {}
    while True:
        data, addr = server.recvfrom(65536)
        # print(data)
        # print(addr)
        if addr not in clients:
            clients[addr] = Client(addr, server)
        clients[addr].request(data)


if __name__ == '__main__':
    main()
