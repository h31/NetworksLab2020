import socket
import os

HOST = "127.0.0.1"
PORT = 5000
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


def main():
    sv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sv.bind((HOST, PORT))
    while 1:
        rq, cli = sv.recvfrom(516)
        print(rq)
        RQ_Packet(sv, rq, cli)


# HANDLE READ AND WRITE REQUEST
def RQ_Packet(sv, rq, cli):
    opcode = int.from_bytes(rq[0:2], "big")
    param = rq[2:].split(b"\x00")
    fileName = param[0].decode("utf_8")
    mode = param[1].decode("utf_8")
    if opcode == opcode_rq["RRQ"]:
        send_File(sv, fileName, cli)
    elif opcode == opcode_rq["WRQ"]:
        recv_File(sv, fileName, cli)
    else:
        sv.sendto(error_RQ(4), cli)


# Packing data
def packing_data(block, data):
    pkg = bytearray()
    pkg += opcode_rq["DATA"].to_bytes(2, "big")
    pkg += block.to_bytes(2, "big")
    pkg += data
    return pkg


# get ack, throw error if have
def recv_Ack(sv):
    rq, _ = sv.recvfrom(516)
    opcode = int.from_bytes(rq[0:2], "big")
    if opcode != opcode_rq["ACK"]:
        if opcode != opcode_rq["ERR"]:
            return opcode_rq["ERR"], 4
        else:
            return opcode_rq["ERR"], int.from_bytes(rq[2:4], "big")
    block = int.from_bytes(rq[2:], "big")
    return opcode, block


# Send file, if file doesnt exist on server, send error
def send_File(sv, fileName, cli):
    block = 1
    try:
        fileOpen = open(fileName, "rb")
        while 1:
            data = fileOpen.read(512)
            pkg = packing_data(block, data)
            sv.sendto(pkg, cli)
            # print error if have and send to client
            opcode, block_ACK = recv_Ack(sv)
            if opcode == opcode_rq["ERR"]:
                error_code = block_ACK
                sv.sendto(error_RQ(4), cli)
                print(error_msg[error_code])
                return 0
            # illegal error
            if block_ACK != block:
                sv.sendto(error_RQ(4), cli)
                return 0
            if len(data) < DATA_LENGTH:
                break
            block += 1
    except FileNotFoundError:
        sv.sendto(error_RQ(1), cli)
        print(error_msg[1])
        return 0


# send ack to client
def send_ACK(sv, data, cli):
    ack = bytearray(data)
    ack[1] = opcode_rq["ACK"]
    sv.sendto(ack, cli)


# receive file from client if file exist throw error
def recv_File(sv, fileName, cli):
    if os.path.exists(fileName):
        sv.sendto(error_RQ(6), cli)
        return 0
    # send first ack=0 one time only.
    ack0 = bytearray()
    ack0.append(0)
    ack0.append(opcode_rq["ACK"])
    ack0.append(0)
    ack0.append(0)
    send_ACK(sv, ack0, cli)

    fileOpen = open(fileName, "wb")
    while 1:
        rq, _ = sv.recvfrom(516)
        # handle error if have
        if int.from_bytes(rq[0:2], "big") == opcode_rq["ERR"]:
            error_code = int.from_bytes(rq[2:4], "big")
            print(error_msg[error_code])
            os.remove(fileName)
            break
        # send ack
        send_ACK(sv, rq[0:4], cli)
        data = rq[4:]
        fileOpen.write(data)
        # end of data
        if len(data) < DATA_LENGTH:
            break


# build error package
def error_RQ(error_code):
    pack = bytearray()
    pack += opcode_rq["ERR"].to_bytes(2, "big")
    pack += error_code.to_bytes(2, "big")
    pack += error_msg[error_code].encode("utf_8")
    pack.append(0)
    return pack


if __name__ == "__main__":
    main()