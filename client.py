import socket
import errno
import sys
import threading
import time

HEADER_LENGTH = 10

IP = '127.0.0.1'
PORT = 9999
CODE = 'utf-8'

input_username = input("Enter username: ")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
client_socket.setblocking(False)

username = input_username.encode(CODE)
username_header = f"{len(username):<{HEADER_LENGTH}}".encode(CODE)

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

			message_time = time.strftime("%H:%M:%S", time.localtime())

			print(f'<{message_time}> [{username}]: {message}')


		except IOError as e:
			if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
				print('IO Error', str(e))
				sys.exit()
			continue

		except Exception as e:
			print('Error', str(e))
			sys.exit()

receive_thread = threading.Thread(target=receive)
receive_thread.start()		

write_thread = threading.Thread(target=write)
write_thread.start()	