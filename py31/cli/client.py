import socket
import os

HOST = "192.168.0.109"
PORT = 69
sv_addr = (HOST, PORT)

DATA_LENGTH = 512

opcode_rq = {
    "RRQ": 1,
    "WRQ": 2,
    "DATA": 3,
    "ACK": 4,
    "ERR": 5,
}

error_msg = {
    0: "Not defined",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user.",
}

cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def main():
    while 1:
        inp = input().split(" ")
        if len(inp) != 2:
            print("Syntax problem")
        else:
            type_RQ = inp[0]
            fileName = inp[1]
            if type_RQ == "r":
                recv_File(opcode_rq["RRQ"], fileName)
            elif type_RQ == "w":
                send_File(opcode_rq["WRQ"], fileName)
            else:
                print("Syntax problem")


# create and send READ WRITE request
def create_RQ(mode, fileName):
    rq = bytearray()
    rq += mode.to_bytes(2, "big")
    rq += fileName.encode("utf_8")
    rq.append(0)
    rq += "octet".encode("utf_8")
    rq.append(0)
    cli.sendto(rq, sv_addr)
    print(len(rq))
    print(rq)


# Packing data
def packing_data(block, data):
    pkg = bytearray()
    pkg += opcode_rq["DATA"].to_bytes(2, "big")
    pkg += block.to_bytes(2, "big")
    pkg += data
    return pkg


# get ack, throw error if have
def recv_Ack():
    rq, server = cli.recvfrom(516)
    opcode = int.from_bytes(rq[0:2], "big")
    if opcode != opcode_rq["ACK"]:
        if opcode != opcode_rq["ERR"]:
            return opcode_rq["ERR"], 4, server
        else:
            return opcode_rq["ERR"], int.from_bytes(rq[2:4], "big"), server
    block = int.from_bytes(rq[2:], "big")
    return opcode, block, server


# send file to server
def send_File(mode, fileName):
    try:
        cli.settimeout(2)
        fileOpen = open(fileName, "rb")
        create_RQ(mode, fileName)
        # check ack0. throw error if have
        op, ack0, server = recv_Ack()
        if op == opcode_rq["ERR"]:
            print(error_msg[ack0])
            return 0
        block = 1
        while 1:
            data = fileOpen.read(512)
            pkg = packing_data(block, data)
            cli.sendto(pkg, server)
            print(server)
            # print error if have and send to client
            opcode, block_ACK, server = recv_Ack()
            print(opcode)
            if opcode == opcode_rq["ERR"]:
                error_code = block_ACK
                print(error_msg[error_code])
                return 0
            print(block_ACK)
            # illegal error
            if block_ACK != block:
                cli.sendto(error_RQ(4), server)
                return 0
            if len(data) < DATA_LENGTH:
                print(block_ACK)
                break
            block += 1
    except FileNotFoundError:
        print(error_msg[1])
        return 0
    except socket.timeout:
        print("Time OUT")
        return 0


# send ack to client
def send_ACK(data, sv):
    ack = bytearray(data)
    ack[0] = 0
    ack[1] = opcode_rq["ACK"]
    cli.sendto(ack, sv)


# receive file from server
def recv_File(mode, fileName):
    create_RQ(mode, fileName)
    fileOpen = open(fileName, "wb")
    cli.settimeout(2)
    while 1:
        try:
            rq, server = cli.recvfrom(516)
            print(server)

            print(len(rq))
            # handle error if have
            if int.from_bytes(rq[0:2], "big") == opcode_rq["ERR"]:
                error_code = int.from_bytes(rq[2:4], "big")
                print(error_code)
                print(error_msg[error_code])
                os.remove(fileName)
                break
            send_ACK(rq[0:4], server)
            data = rq[4:]
            fileOpen.write(data)
            # end of data
            if len(data) < DATA_LENGTH:
                print(int.from_bytes(rq[2:4], "big"))
                break
        except socket.timeout:
            print("Time OUT")
            os.remove(fileName)
            return 0


# build error package
def error_RQ(error_code):
    pkg = bytearray()
    pkg += opcode_rq["ERR"].to_bytes(2, "big")
    pkg += error_code.to_bytes(2, "big")
    pkg += error_msg[error_code].encode("utf_8")
    pkg.append(0)
    return pkg


if __name__ == "__main__":
    main()