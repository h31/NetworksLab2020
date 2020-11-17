"""TFTP (rev. 2) server realisation"""

import socket

import exception as e
import tftp_formats as tf
import utilz as uz

users = dict()


def eloop(sock):
    new = True
    while True:
        try:
            data, addr = uz.recv(sock)
        except e.IllegalOpCode:
            uz.send(sock, addr, tf.ERROR.create_from_code(
                tf.ErrorCode.ILLEGALOP), users[addr].mode)
            continue

        if addr not in users:
            users[addr] = uz.User()
            new = True
        else:
            new = False
        print(f'Recieved {data.opcode} from {"new" if new else "already known"} {addr} with:\n' + data.get_log())
        if data.opcode == tf.Operation.RRQ:
            users[addr].clear()
            users[addr].filename = data.filename
            users[addr].mode = data.mode
            if ((data := uz.read(data.filename)) == None):
                error = tf.ERROR.create_from_code(tf.ErrorCode.NOTFOUND)
                uz.send(sock, addr, error, users[addr].mode)
                users[addr].filename = None
                users[addr].mode = None
                continue
            else:
                users[addr].data = data
                users[addr].block = 0
                uz.send(sock, addr, tf.DATA.create(1, data[0:512]), users[addr].mode)

        elif data.opcode == tf.Operation.WRQ:
            users[addr].clear()
            users[addr].filename = data.filename
            users[addr].mode = data.mode
            if (uz.read(data.filename) != None):
                error = tf.ERROR.create_from_code(tf.ErrorCode.EXIST)
                uz.send(sock, addr, error, users[addr].mode)
                users[addr].filename = None
                users[addr].mode = None
                continue

            # check if disk full
            uz.send(sock, addr, tf.ACK.create(0), users[addr].mode)

        elif data.opcode == tf.Operation.ACK and users[addr].data:
            users[addr].block = data.block
            file = users[addr].data[users[addr].block * 512:users[addr].block*512 + 512]
            uz.send(sock, addr, tf.DATA.create(users[addr].block+1, file), users[addr].mode)
            if len(file) < 512:
                print(f'File {users[addr].filename} with {len(users[addr].data)} bytes send')
                users[addr].clear()

        elif data.opcode == tf.Operation.DATA:
            uz.send(sock, addr, tf.ACK.create(data.block), users[addr].mode)
            users[addr].data += data.data
            if data.last:
                uz.store(users[addr].filename, users[addr].data, users[addr].mode)
                print(f'File {users[addr].filename} with {len(users[addr].data)} bytes stored')
                users[addr].clear()


def init():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(tuple(uz.SETTINGS['HOST'].values()))
    print('Server is ready'.upper())
    return sock


eloop(init())

