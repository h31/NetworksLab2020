import socket
import select
import time
import sys

clients = {}
socket_list = []
buffer = {}
command_buf = {}

HEADER = 10
ENCODE = 'utf-8'

AUTHORIZATION = '1'
DISCONNECT = '2'
SEND = '3'
CHANGE_NICK = '4'

def setup_server():
    # IP input
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Choose where the server will be deployed:"
    f"\n1 - Enter manually"
    f"\n2 - localhost(127.0.0.1)"
    f"\n3 - Broadcast(0.0.0.0)"
    f"\n4 - {hostname}({ip_address})")
    while True:
        mode = input()
        if (mode != '1') & (mode != '2') & (mode != '3') & (mode != '4'): 
            print("Bad input")
            continue
        elif mode == '1':
            while True:
                ip_address = input("Format - x.x.x.x: ")
                try:
                    socket.inet_aton(ip_address)
                    break
                except socket.error:
                    print("Bad input")
                    continue
            break
        elif mode == '2':
            ip_address = 'localhost'
            break
        elif mode == '3':
            ip_address = '0.0.0.0'
            break
        else: 
            break
    
    # Port input
    while True:
        try:
            port = int(input("Enter port(1024 - 65535):"))
            break
        except ValueError:
            print("Bad input")

    if(1024 > port):
        print("Warning! Reserved port. Port will be 1024.")
        port = 1024
    elif(port > 65535):
        print("Warning! Out of range. Port will be 65535.")
        port = 65535

    server(ip_address, port) 

def server(IP, PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.setblocking(False)
    socket_list.append(server_socket)
    server_socket.listen()

    print(f"Waiting for new connections...")
    while True: 
        read_list, _,exception_list = select.select(socket_list, [],socket_list)
    
        for cs in read_list:
            if cs == server_socket:
                add_connection(cs)
            else:
                client_read(cs)

        for cs in exception_list:
            close_connection(cs)

def add_connection(server_socket):
    client_socket, client_addr = server_socket.accept()
    client_socket.setblocking(False)
    socket_list.append(client_socket)
    buffer[client_socket] = {'header_recived': False, 'header': ''.encode(ENCODE),'data_recived': False, 'data':''.encode(ENCODE)} 
    command_buf[client_socket] = None
    print('{:*<30}'.format("*"))
    clients[client_socket] = {'ip': client_addr[0], 'port':client_addr[1], 'username':''}     
    print(f"Connection with {client_addr[0]}:{client_addr[1]} established.")
    print('{:*<30}'.format("*"))
    return

def close_connection(client_socket):
    user = clients[client_socket]['user']
    print(f"Connection was closed by user {user['data'].decode(ENCODE)}.")
    socket_list.remove(client_socket)
    del clients[client_socket]
    del buffer[client_socket]
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    return

def send_to_all(client_socket, package):
    for client in clients:
        if client == client_socket: continue
        client.send(package)

def length_control(client_socket, data, length):
    if (len(data) != length):
        data_tmp = client_socket.recv(length - len(data))
        data += data_tmp
    return {'data_recived': len(data) == length, 'data': data}

def recv_package(client_socket):
    try:
        # header recive
        if not buffer[client_socket]['header_recived']:
            msg_header = buffer[client_socket]['header']
            data = length_control(client_socket, msg_header, HEADER)

            buffer[client_socket]['header_recived'] = data['data_recived']
            buffer[client_socket]['header'] = data['data']
            if not data['data_recived']:
                return False

        # msg reciver
        msg = buffer[client_socket]['data']
        msg_len = int(buffer[client_socket]['header'].strip())
        data = length_control(client_socket, msg, msg_len)
        buffer[client_socket]['data_recived'] = data['data_recived']
        buffer[client_socket]['data'] = data['data']
        if not data['data_recived']:
            return False

        header = buffer[client_socket]['header']
        msg = buffer[client_socket]['data']
        buffer[client_socket] = {'header_recived':False, 'header': ''.encode(ENCODE),'data_recived':False, 'data':''.encode(ENCODE)}
        return {'header':header, 'data':msg}
    except:
        return False

def client_read(client_socket):
    try:  
        if command_buf[client_socket] == None:
            command_pack = recv_package(client_socket)
            if not command_pack:
                return
            else:
                command_buf[client_socket] = command_pack['data'].decode(ENCODE)

        command = command_buf[client_socket]
        if command != DISCONNECT:
            if not buffer[client_socket]['data_recived']:
                data_pack = recv_package(client_socket)
                if not data_pack:
                    return
                else:
                    if command == AUTHORIZATION:
                        clients[client_socket]['user'] = data_pack
                        print('{:=<30}'.format("="))
                        print(f"Authorization on {clients[client_socket]['ip']}:{clients[client_socket]['port']} complete.")
                        print(f"Username - {data_pack['data'].decode(ENCODE)}.")
                        print('{:=<30}'.format("="))
                    elif command == SEND:
                        user = clients[client_socket]['user']
                        print('{:-<30}'.format("-"))

                        # Server time
                        _time = str(time.time()).encode(ENCODE)
                        time_header = f"{len(_time.decode(ENCODE)):<{HEADER}}".encode(ENCODE)
                        msg_time = {'header': time_header, 'data': _time}

                        # Send msg to other clients
                        print("Sending to other users.")
                        send_to_all(client_socket, user['header'] + user['data'] + data_pack['header'] + data_pack['data'] + msg_time['header'] + msg_time['data'])
                        print("Sending done.")
                        print('{:-<30}'.format("-"))

                    elif command == CHANGE_NICK:
                        print('{:/<30}'.format("/"))
                        print(f"Nickname of {clients[client_socket]['ip']}:{clients[client_socket]['port']} changed.")
                        print(f"Username - {data_pack['data'].decode(ENCODE)}.")
                        clients[client_socket]['user'] = data_pack
                        print('{:/<30}'.format("/"))
                    command_buf[client_socket] = None
        elif command == DISCONNECT:
            command_buf[client_socket] = None
            raise OSError
    except OSError:
        close_connection(client_socket)
        return
            
setup_server()