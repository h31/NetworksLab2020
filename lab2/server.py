import socket
import select
import threading as th
import time
import sys

clients = {}
socket_list = []

HEADER = 10
ENCODE = 'utf-8'

AUTHORIZATION = '1'
DISCONNECT = '2'
SEND = '3'
CHANGE_NICK = '4'

def setup_server():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Choose where the server will be deployed:"
    f"\n1 - Enter manually"
    f"\n2 - localhost(127.0.0.1)"
    f"\n3 - Broadcast(0.0.0.0)"
    f"\n4 - {hostname}({ip_address})")
    while True:
        mode = input()
        if (mode != '1') & (mode != '2') & (mode != '3'): 
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
        elif mode == '4':
            ip_address = '0.0.0.0'
            break
        else: 
            break
    
    port = int(input("Enter port(1024 - 65535):"))
    if(1024 > port):
        print("Warning! Reserved port")
        port = 1024
    elif(port > 65535):
        print("Warning! Out of range")
        port = 65535

    server(ip_address, port) 

def server(IP, PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.setblocking(False)
    socket_list.append(server_socket)
    accept_thread(server_socket)

def accept_thread(server_socket):
    server_socket.listen()

    print(f"Waiting for new connections...")
    while True: 
        read_list, _,exception_list = select.select(socket_list, [],socket_list)
    
        for cs in read_list:
            if cs is server_socket:
                add_connection(server_socket)
            else:
                data = recv_package(cs)
                if data:
                    client_read(cs, data)
                else:
                    print('Error\n')

        for cs in exception_list:
                close_connection(cs)

def add_connection(server_socket):
    client_socket, client_addr = server_socket.accept()
    client_socket.setblocking(False)
    socket_list.append(client_socket)
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
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    return

def recv_package(client_socket):
    while True:
        msg_header = client_socket.recv(HEADER)
        if not msg_header:
            return False

        while(len(msg_header) != HEADER):
            msg_header_tmp = client_socket.recv(HEADER - len(msg_header))
            msg_header += msg_header_tmp
        
        msg_len = int(msg_header.decode(ENCODE).strip())

        msg = client_socket.recv(msg_len)
        if not msg_header:
            return False

        while(len(msg) != msg_len):
            msg_tmp = client_socket.recv(HEADER - len(msg))
            msg += msg_tmp
        
        return {'header':msg_header, 'data':msg}

def send_to_all(client_socket, package):
    for client in clients:
        if client == client_socket: continue
        client.send(package)

def client_read(client_socket, command_pack):
    try:    
        command = command_pack['data'].decode(ENCODE)
        print(f'command = {command}')
        if command == AUTHORIZATION:
            user = recv_package(client_socket)
            if user:
                clients[client_socket]['user'] = user
                print('{:=<30}'.format("="))
                print(f"Authorization on {clients[client_socket]['ip']}:{clients[client_socket]['port']} complete.")
                print(f"Username - {user['data'].decode(ENCODE)}.")
                print('{:=<30}'.format("="))
        elif command == DISCONNECT:
            raise OSError
        elif command == SEND:
            user = clients[client_socket]['user']
            print('{:-<30}'.format("-"))
            msg = recv_package(client_socket)
            _time = time.strftime("%H:%M:%S", time.gmtime()).encode(ENCODE)
            time_header = f"{len(_time):<{HEADER}}".encode(ENCODE)
            msg_time = {'header':time_header, 'data': _time}
            print(f"<{_time.decode(ENCODE)}> Received message from {user['data'].decode(ENCODE)}: \"{msg['data'].decode(ENCODE)}\"")
            print("Sending to other users.")
            send_to_all(client_socket, user['header'] + user['data'] + msg['header'] + msg['data'] + msg_time['header'] + msg_time['data'])
            print("Sending done.")
            print('{:-<30}'.format("-"))
        elif command == CHANGE_NICK:
            user = recv_package(client_socket)
            if user:
                print('{:/<30}'.format("/"))
                print(f"Nickname of {clients[client_socket]['ip']}:{clients[client_socket]['port']} changed.")
                print(f"Username - {user['data'].decode(ENCODE)}.")
                clients[client_socket]['user'] = user
                print('{:/<30}'.format("/"))
    except OSError:
        close_connection(client_socket)
        return
            
setup_server()