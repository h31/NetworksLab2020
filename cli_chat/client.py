import socket
import errno
import sys
import threading
import json
import time
import datetime
import signal

#Load config file
try:
	with open('client_config.json') as config:
		settings = json.load(config)
except:
	print('Config file does not exists. Default config file will be created.')

	with open('client_config.json', 'w') as default_config:
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


def client():
	input_username = input("Enter username: ")
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	client_socket.connect((IP, PORT))
	
	username = input_username.encode(CODE)
	username_header = f"{len(username):<{HEADER_LENGTH}}".encode(CODE)

	client_socket.send(username_header + username)

	receive_thread = threading.Thread(target=read, args=(client_socket, )).start()
	write_thread = threading.Thread(target=write, args=(client_socket, )).start()


def write(client_socket):
	while True:
		try:
			message = input()

			if message == '!q':
				message_header = None
				client_socket.send(message_header)

				close_connection(client_socket)
				return None

			if message:
				message = message.encode(CODE)
				message_header = f"{len(message):<{HEADER_LENGTH}}".encode(CODE)
				client_socket.send(message_header + message)

		except EOFError as e:
			print("EOF is not correct input.")
			return None

		except:
			close_connection(client_socket)
			sys.exit()
			print("Connection was closed. Unexcepted error.")
			continue


def close_connection(client_socket):
	client_socket.shutdown(socket.SHUT_RDWR)
	client_socket.close()
			

def receive(client_socket):

	header = client_socket.recv(HEADER_LENGTH)

	if not len(header):
		print("Connection closed by server")
		sys.exit()

	length = int(header.decode(CODE).strip())
	return client_socket.recv(length).decode(CODE)


def read(client_socket):
	while True:
		try:
			username = receive(client_socket)
			message = receive(client_socket)
			recv_time = receive(client_socket)

			client_time = time.strftime("%H:%M:%S", (time.localtime(int(recv_time))))
			print(f'<{client_time}> [{username}]: {message}')

		except Exception as e:
			print("Can not receive this message")
			print('Error', str(e))
			sys.exit()
			return None

client()