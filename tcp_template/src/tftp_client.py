import socket
import os
import struct


def put(client, filename, addr):
    #file_path = os.path.abspath(filename)
    try:
        open_file = open(filename, 'rb')
    except FileNotFoundError:
        print(filename + " can not open. Maybe file not exist")
        return
    title = b'\x00\x02' + filename.encode()+b'\x00'+"octet".encode()+b'\x00'
    client.sendto(title, addr)
    block = 0
    while True:
        data, sock = client.recvfrom(65536)
        req = data[0:2]
        if req == b'\x00\x04':
            curr_block = struct.unpack('!H', data[2:4])[0]
            if curr_block != block:
                continue
            curr_block += 1
            if curr_block == 65536:
                curr_block = 0
            read_data = open_file.read(512)
            curr_pack = b'\x00\x03'+struct.pack(b'!H', curr_block)+read_data
            client.sendto(curr_pack, addr)
            block += 1
            if block == 65536:
                block = 0
            if len(read_data) < 512:
                open_file.close()
                print("Done")
                break
        elif req == b'\x00\x05':
            print(data)
            break


def get(client, filename, addr):
    file_path = os.path.abspath("server_"+filename)
    if os.path.isfile(file_path):
        file_path = os.path.abspath(change_filename(filename))
    curr_pack = b'\x00\x01'+filename.encode()+b'\x00'+'octet'.encode()+b'\x00'
    client.sendto(curr_pack, addr)
    create_file = open(file_path, 'wb')
    block = 1
    while True:
        try:
            data, sock = client.recvfrom(65536)
            req = data[0:2]
        except socket.timeout:
            client.sendto(curr_pack, addr)
            print("Timeout")
            create_file.close()
            os.remove(create_file.name)
            break
        if req == b'\x00\x03':
            curr_block = struct.unpack('!H', data[2:4])[0]
            read_data = data[4:]
            if curr_block != block:
                continue
            block += 1
            if block == 65536:
                block = 1
            create_file.write(read_data)
            curr_pack = b'\x00\x04'+struct.pack(b'!H', curr_block)
            client.sendto(curr_pack, addr)
            if len(read_data) < 512:
                print("Done")
                create_file.close()
                break
        elif req == b'\x00\x05':
            print(data)
            create_file.close()
            os.remove(file_path)
            break


def change_filename(filename):
    n = 1
    file = str(n) + '_server_' + filename
    while True:
        if os.path.isfile(file):
            n += 1
            file = str(n) + '_server_' + filename
        else:
            break
    return file


def main():
    SERVER = "127.0.0.1"
    PORT = 69
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        inp_req = input("Enter command: ")
        req = str(inp_req).lower().split()
        if len(req) == 1:
            if req[0] == "--help":
                print("Enter get filename to download or put filename to upload")
            else:
                print("Wrong command. Try again")
        elif len(req) == 2:
            if req[0] == "get":
                get(client, req[1], (SERVER, PORT))
            elif req[0] == "put":
                put(client, req[1], (SERVER, PORT))
            else:
                print("Wrong command. Try again")
        else:
            print("Wrong command. Try again")


if __name__ == '__main__':
    main()