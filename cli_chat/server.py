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

def server():
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((IP, PORT))
	server_socket.listen()
	print(f"Listening for connections on {IP}:{PORT}")

	sockets_list = [server_socket]

	new_connection(sockets_list, server_socket)
	

def new_connection(sockets_list, server_socket):
	while True:
		read_sockets, n_, exception_sockets = select.select(sockets_list, [], sockets_list)

		for notified_socket in read_sockets:
			if notified_socket == server_socket:
				client_socket, client_address = server_socket.accept()

				user = recv_message(client_socket)
				if user is False:
					continue

				sockets_list.append(client_socket)
				clients[client_socket] = user

				print(f"New connetion from {client_address[0]}:{client_address[1]} Username: {user['data'].decode(CODE)}")

			else:
				receiver(notified_socket)

		for notified_socket in exception_sockets:
			sockets_list.remove(notified_socket)
			del clients[notified_socket]


def recv_message(client_socket):
	message_header = client_socket.recv(HEADER_LENGTH)

	if not message_header:
		return False

	while len(message_header) < HEADER_LENGTH:
		recv_header = (client_socket.recv(HEADER_LENGTH - len(message_header)))

		message_header += recv_header

		if len(message_header) == HEADER_LENGTH:
			break

	if not len(message_header):
		return None

	try:
		int(message_header)
	except ValueError:
		print("Incorrect type of header. Must be 'int'.")
		return

	message_length = int(message_header.decode(CODE).strip())
	data = client_socket.recv(message_length)

	return {"header": message_header, "data": data}


def recv_time():
	_time = str(int(time.time())).encode(CODE)
	_time_header = f"{len(_time):<{HEADER_LENGTH}}".encode(CODE)

	return {"header": _time_header, "data": _time}


def receiver(notified_socket):

	user = clients[notified_socket]
	message = recv_message(notified_socket)
	send_time = recv_time()

	if not message:
		notified_socket.shutdown(socket.SHUT_WR)
		notified_socket.close()
		print(f"Connetion was closed by {clients[notified_socket]['data'].decode(CODE)}")
		del clients[notified_socket]
		return None

	while int(message['header']) > len(message['data']):
		message['data'] += (notified_socket.recv(int(message['header']) - len(message['data'])))
		if int(message['header']) == len(message['data']):
			break

	server_time = time.strftime("%H:%M:%S", time.gmtime())
	print(f"Received message from {user['data'].decode(CODE)} at {server_time}: {message['data'].decode(CODE)}")

	try:
		for client in clients:
			if client != notified_socket:
				client.send(user['header'] + user['data'] + message['header'] + message['data'] + send_time['header'] + send_time['data'])
	except BrokenPipeError as e:
		print("Error with not closed socket.")
		return

server()