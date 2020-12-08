"""TFTP (rev. 2) server realisation"""

import socket
import threading
import time

import exception as e
import tftp_formats as tf
import utilz as uz

users = dict()

def timeout_handler(sock):
    while True:
        for addr, user in list(users.items()):
            if time.time() - user.ts >= 5 and addr in users:
                if user.timeouted:
                    print(f'user with addr {addr} deleted due to timeouted twice')
                    del users[addr]
                elif user.last_package is not None:
                    print(f'user with addr {addr} timeouted')
                    user.ts = time.time()
                    user.timeouted = True
                    uz.send(sock, addr, user.last_package, user.mode)


def eloop(sock):
    timeout_thread = threading.Thread(target=timeout_handler, args=(sock, ))
    timeout_thread.start()
    while True:
        try:
            data, addr = uz.recv(sock)
        except e.IllegalOpCode:
            uz.send(sock, addr, tf.ERROR.create_from_code(tf.ErrorCode.ILLEGALOP), users[addr].mode)
            continue
        except:
            # on ctrl+c
            print('Server shutdown'.upper())
            break

        if addr not in users:
            users[addr] = uz.User()

        print(f'recieved {data} from {addr}')
        if data.opcode == tf.Operation.RRQ:
            users[addr].filename = data.filename
            users[addr].mode = data.mode
            if uz.read(data.filename) is None:
                error = tf.ERROR.create_from_code(tf.ErrorCode.NOTFOUND)
                uz.send(sock, addr, error, users[addr].mode)
                del users[addr]
                continue

            users[addr].data = data
            users[addr].block = 0
            package = tf.DATA.create(1, data[0:512])
            users[addr].last_package = package
            uz.send(sock, addr, package, users[addr].mode)

        elif data.opcode == tf.Operation.WRQ:
            users[addr].filename = data.filename
            users[addr].mode = data.mode
            if uz.read(data.filename) is not None:
                error = tf.ERROR.create_from_code(tf.ErrorCode.EXIST)
                uz.send(sock, addr, error, users[addr].mode)
                del users[addr]
                continue

            # check if disk full
            uz.send(sock, addr, tf.ACK.create(0), users[addr].mode)

        elif data.opcode == tf.Operation.ACK and users[addr].data:
            users[addr].block = data.block
            file = users[addr].data[users[addr].block * 512:users[addr].block * 512 + 512]
            if len(file) < 512:
                print(f'File {users[addr].filename} with {len(users[addr].data)} bytes send')
                del users[addr]
                continue

            package = tf.DATA.create(users[addr].block + 1, file)
            users[addr].last_package = package
            uz.send(sock, addr, package, users[addr].mode)

        elif data.opcode == tf.Operation.DATA:
            package = tf.ACK.create(data.block)
            users[addr].last_package = package
            uz.send(sock, addr, package, users[addr].mode)
            users[addr].data += data.data
            if data.last:
                uz.store(users[addr].filename, users[addr].data, users[addr].mode)
                print(f'File {users[addr].filename} with {len(users[addr].data)} bytes stored')
                del users[addr]
    timeout_thread.join()


def init():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(tuple(uz.SETTINGS['HOST'].values()))
    print('Server is ready'.upper())
    return sock


eloop(init())

