import socket
import select
import json
import time
import threading
import sys

#Load config file
try:
	with open('server_config.json') as config:
		settings = json.load(config)
except:
	print('Config file does not exists. Default config file will be created.')

	with open('server_config.json', 'w') as default_config:
		settings =  {
			"ip": "127.0.0.1",
    		"port": 9999,
    		"code": "utf-8"
		}
		json.dump(settings, default_config)
		
IP = settings["ip"]
PORT = settings["port"]
CODE = settings["code"]
HEADER_LENGTH = 8

clients = {}
sockets_list = []
buffers = {}


def server():
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((IP, PORT))
	server_socket.setblocking(False)
	sockets_list.append(server_socket)

	server_socket.listen()
	print(f"Listening for connections on {IP}:{PORT}")

	while True:
		read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

		for notified_socket in read_sockets:
			if notified_socket == server_socket:
				new_connection(server_socket)
			else:
				message = receive_data(notified_socket)
				if message:
					receiver(notified_socket, message)
				else:
					continue

		for notified_socket in exception_sockets:
			close_connection(notified_socket)



def new_connection(server_socket):
	client_socket, client_address = server_socket.accept()
	client_socket.setblocking(False)
	sockets_list.append(client_socket)

	user = {'header': '', 'data': '', 'ip': client_address[0], 'port': client_address[1]}
	buffers[client_socket] = {'header': ''.encode(CODE), 'data': ''.encode(CODE), 'header_check': False, 'data_check': False}
	clients[client_socket] = user


def close_connection(client_socket):
	client_socket.shutdown(socket.SHUT_RDWR)
	client_socket.close()
	sockets_list.remove(client_socket)
	del clients[client_socket]
	del buffers[client_socket]
	return


def receive_data(client_socket):
	try:
		if not buffers[client_socket]['header_check']:
			header = buffers[client_socket]['header']
			message = completeness_check(client_socket, header, HEADER_LENGTH)

			buffers[client_socket]['header'] = message['data']
			buffers[client_socket]['header_check'] = message['data_check']

			if not buffers[client_socket]['header_check']:
				return None

		data_length = int(buffers[client_socket]['header'].decode(CODE).strip())

		if not buffers[client_socket]['data_check']:
			data = buffers[client_socket]['data']
			message = completeness_check(client_socket, data, data_length)

			buffers[client_socket]['data'] = message['data']
			buffers[client_socket]['data_check'] = message['data_check']

			if not buffers[client_socket]['data_check']:
				return None

		header = buffers[client_socket]['header']
		data = buffers[client_socket]['data']
		buffers[client_socket] = {'header': ''.encode(CODE), 'data': ''.encode(CODE), 'header_check': False, 'data_check': False}

		return {'header': header, 'data': data}

	except Exception as e:
		close_connection(client_socket)
		print(e)
		return None


def completeness_check(client_socket, data, length):
	if len(data) != length:
		data += (client_socket.recv(length - len(data)))
		if len(data) == length:
			return {'data': data, 'data_check': True}
		else:
			return {'data': data, 'data_check': False}


def recv_time():
	_time = str(int(time.time())).encode(CODE)
	_time_header = f"{len(_time):<{HEADER_LENGTH}}".encode(CODE)

	return {"header": _time_header, "data": _time}


def receiver(notified_socket, message):
	user = clients[notified_socket]
	send_time = recv_time()

	if user['data'] == '':
		user['header'] = message['header']
		user['data'] = message['data']
		print(f"New connetion from {user['ip']}:{user['port']}. Username: {user['data'].decode(CODE)}")
		return

	server_time = time.strftime("%H:%M:%S", time.gmtime())
	print(f"Received message from {user['data'].decode(CODE)} at {server_time}: {message['data'].decode(CODE)}")

	try:
		for client in clients:
			if client != notified_socket:
				client.send(user['header'] + user['data'] + message['header'] + message['data'] + send_time['header'] + send_time['data'])
	except BrokenPipeError as e:
		return

server()