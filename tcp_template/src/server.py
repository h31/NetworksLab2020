import socket

print('Start server')
sock = socket.socket()
sock.bind(('', 5001))
sock.listen()
conn, addr = sock.accept()

print('connected')

while True:
    data = (conn.recv(1024))
    if data == b'':
        break
    data_decoded = data.decode('utf-8')
    print('Пришло:', data)
    conn.send('Сообщение доставлено'.encode('utf-8'))

conn.shutdown(socket.SHUT_RD)
conn.close()
sock.shutdown(socket.SHUT_RD)
sock.close()
print('Close server')
