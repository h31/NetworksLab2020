"""TFTP (rev. 2) client realisation"""

import socket

import tftp_formats as tf
import utilz as uz

SETTINGS = {
    'MODE': tf.Mode.OCTET,
    'TRACE': True,
    'CONNECT': ('127.0.0.1', 5001),
}


def trace_log(msg):
    if SETTINGS['TRACE']:
        print(f'{msg}')


def eloop(sock):
    while True:
        try:
            inp = input('> ').lower().split(' ')
        except:
            break
        if inp[0] == 'connect':
            if len(inp) < 2:
                print('Not enough arguments')
                continue
            connect(*inp[1:3])

        elif inp[0] == 'binary':
            change_mode('octet')

        elif inp[0] == 'ascii':
            change_mode('netascii')

        elif inp[0] == 'mode':
            if inp[1] not in tf.Mode.values():
                print('Unsopported mode')
            else:
                change_mode(inp[1])

        elif inp[0] == 'trace':
            toggle_trace()

        elif inp[0] == 'get':
            if check_connect():
                get(sock, inp[1:])

        elif inp[0] == 'put':
            if check_connect():
                put(sock, inp[1:])

        elif inp[0] == 'quit':
            break

        elif inp[0] in ['help', 'h', '?']:
            help()

        else:
            print('?Invalid command')


def check_connect():
    if SETTINGS['CONNECT'] is None:
        print('Use connect first')
        return False
    return True


def toggle_trace():
    SETTINGS['TRACE'] = not SETTINGS['TRACE']
    res = 'enabled' if SETTINGS['TRACE'] else 'disabled'
    print(f'Trace {res}')


def change_mode(mode):
    SETTINGS['MODE'] = tf.Mode(mode)
    print(f'Mode changed to {mode}')


def help():
    print(
        '''Avaliable commands:
connect     connect to remote tftp
mode        set file transfer mode
trace       toggle packet tracing
put         send file
get         receive file
quit        exit tftp
binary      set mode to octet
ascii       set mode to netascii
?           print help information
help        print help information'''
    )


def put(sock, filenames):
    for filename in filenames:
        file = uz.read(filename, False)
        if SETTINGS['MODE'] == tf.Mode.NETASCII:
            file = tf.netascii(file, True)
        if file is None:
            print(f'File {filename} does not exists')
            continue

        wrq = tf.WRQ.create(filename, SETTINGS['MODE'].value)
        trace_log(f'sending {wrq}')
        sock.sendto(wrq.package, SETTINGS['CONNECT'])
        block = 0
        while True:
            data, _ = uz.recv(sock)
            trace_log(f'recieved {data}')
            if data.opcode == tf.Operation.ERROR:
                break

            elif data.opcode == tf.Operation.ACK:
                block = data.block
                file_block = file[block * 512:block * 512 + 512]
                data_pack = tf.DATA.create(block + 1, file_block)
                if len(data_pack.data) == 0:
                    break
                trace_log(f'sending {data_pack}')
                sock.sendto(data_pack.package, SETTINGS['CONNECT'])


def get(sock, filenames):
    for filename in filenames:
        if uz.read(filename) is not None:
            print(f'File {filename} already exist')
            continue
        rrq = tf.RRQ.create(filename, SETTINGS['MODE'].value)
        trace_log(f'sending {rrq}')
        sock.sendto(rrq.package, SETTINGS['CONNECT'])
        file = b''
        last = False

        while not last:
            data, _ = uz.recv(sock)
            trace_log(f'recieved {data}')
            if data.opcode == tf.Operation.ERROR:
                last = False
                break

            if data.opcode == tf.Operation.DATA:
                last = data.last
                ack = tf.ACK.create(data.block)
                file += data.data
                trace_log(f'sending {ack}')
                sock.sendto(ack.package, SETTINGS['CONNECT'])

        if last:
            uz.store(filename, file, SETTINGS['MODE'], False)


def connect(addr, port='5001'):
    try:
        if addr.count('.') != 3 or not all(0 <= int(val) <= 255 for val in addr.split('.')):
            print('Wrong address passed')
            return

        if port and not(1 <= int(port) <= 65535):
            print('Wrong port passed')
            return
    except:
        print('Unexpected values passed')
        return

    SETTINGS['CONNECT'] = (addr, int(port))


def init():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock


eloop(init())

