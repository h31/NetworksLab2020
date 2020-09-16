import socket

print('Start client')
sock = socket.socket()
sock.connect(('localhost', 5001))
sock.send('test msg'.encode('utf-8'))
data = sock.recv(1024).decode('utf-8')
sock.shutdown(socket.SHUT_RD)
sock.close()
print(data)
print('Close client')
