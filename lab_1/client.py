import socket
import errno
import sys
import threading
import json

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
TIME_LENGTH = 8

input_username = input("Enter username: ")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

username = input_username.encode(CODE)
username_header = f"{len(username):<{HEADER_LENGTH}}".encode(CODE)

client_socket.connect((IP, PORT))
client_socket.send(username_header + username)


def write():
	while True:
		message = input()

		if message:
			message = message.encode(CODE)
			message_header = f"{len(message):<{HEADER_LENGTH}}".encode(CODE)
			client_socket.send(message_header + message)


def receive():
	while True:
		try:
			username_header = client_socket.recv(HEADER_LENGTH)

			if not len(username_header):
				print("Connection closed by server")
				sys.exit()

			username_length = int(username_header.decode(CODE).strip())
			username = client_socket.recv(username_length).decode(CODE)

			message_header = client_socket.recv(HEADER_LENGTH)
			message_length = int(message_header.decode(CODE).strip())

			message = client_socket.recv(message_length).decode(CODE)

			time = client_socket.recv(TIME_LENGTH).decode(CODE)

			print(f'<{time}> [{username}]: {message}')


		except Exception as e:
			print('Error', str(e))
			sys.exit()


receive_thread = threading.Thread(target=receive).start()
write_thread = threading.Thread(target=write).start()