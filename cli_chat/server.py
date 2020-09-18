import socket
import select
import json
import time

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

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]
clients = {}

print(f"Listening for connections on {IP}:{PORT}")

def receive_message(client_socket):
	try:
		message_header = client_socket.recv(HEADER_LENGTH)

		if not len(message_header):
			return False

		message_length = int(message_header.decode(CODE).strip())
		return {"header": message_header, "data": client_socket.recv(message_length)}

	except:
		return False


while True:
	read_sockets, n_, exception_sockets = select.select(sockets_list, [], sockets_list)

	for notified_socket in read_sockets:
		if notified_socket == server_socket:
			client_socket, client_address = server_socket.accept()

			user = receive_message(client_socket)
			if user is False:
				continue

			sockets_list.append(client_socket)
			clients[client_socket] = user

			print(f"New connetion from {client_address[0]}:{client_address[1]} "
			 f"Username: {user['data'].decode(CODE)}")

		else:
			message = receive_message(notified_socket)

			if message is False:
				print(f"Connetion was closed by {clients[notified_socket]['data'].decode(CODE)}")
				sockets_list.remove(notified_socket)
				del clients[notified_socket]
				continue

			user = clients[notified_socket]
			username = user['data'].decode(CODE)

			print(f"Received message from {user['data'].decode(CODE)}: {message['data'].decode(CODE)}")

			message_time = time.strftime("%H:%M:%S", time.localtime()).encode(CODE)

			for client_socket in clients:
				if client_socket != notified_socket:
					client_socket.send(user['header'] + user['data'] + message['header'] + message['data'] + message_time)

	for notified_socket in exception_sockets:
		sockets_list.remove(notified_socket)
		del clients[notified_socket]

print("Server is started!")