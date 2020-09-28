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

	#Waiting for connections
	while True:
		client_socket, client_address = server_socket.accept()
		user = recv_message(client_socket)

		if user:
			clients[client_socket] = user
			print(f"New connetion from {client_address[0]}:{client_address[1]} "
		 	f"Username: {user['data'].decode(CODE)}")
		 	#Thread for every users
			threading.Thread(target=receiver, args=(client_socket, user, )).start()


def recv_message(client_socket):
	while True:
		try:
			message_header = client_socket.recv(HEADER_LENGTH)

			if not len(message_header):
				return False

			message_length = int(message_header.decode(CODE).strip())
			return {"header": message_header, "data": client_socket.recv(message_length)}

		except:
			return False


def recv_time():
	_time = str(int(time.time())).encode(CODE)
	_time_header = f"{len(_time):<{HEADER_LENGTH}}".encode(CODE)

	return {"header": _time_header, "data": _time}


def receiver(client_socket, user):
	while True:
		
		message = recv_message(client_socket)
		send_time = recv_time()

		if not message:
			try:
				print(f"Connetion was closed by {clients[client_socket]['data'].decode(CODE)}")
				del clients[client_socket]
				client_socket.shutdown(socket.SHUT_RDWR)
				client_socket.close()
				continue
			except:
				continue

		server_time = time.strftime("%H:%M:%S", time.gmtime())
		print(f"Received message from {user['data'].decode(CODE)} at {server_time}: {message['data'].decode(CODE)}")

		for client in clients:
			if client != client_socket:
				client.send(user['header'] + user['data'] + message['header'] + message['data'] + send_time['header'] + send_time['data'])

server()