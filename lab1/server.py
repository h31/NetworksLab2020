import socket
import time  # импортируем 2 модуля

host = socket.gethostbyname(socket.gethostname())  # принимает в себе ip 192.168.56.1
print(socket.gethostbyname(socket.gethostname()))
port = 9090  # порт

clients = []  # адреса (!) подключенных клиентов

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # объявляем переменную s содержащую сокеты (2 - udp, 1 - ip)
s.bind((host, port))  # объявляем технологию на создание

quit = False
print("---Server Started---")

while not quit:
    try:
        data, addr = s.recvfrom(1024)  # дата - сообщение, отправленное пользователем, аддр - адрес пользователя, 1024 - кол-во байт максимум

        if addr not in clients:
            clients.append(addr)

        currentTime = time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())

        print(addr)
        print("[" + addr[0] + "]=[" + str(addr[1]) + "]=[" + currentTime + "]/", end="")
        print(data.decode("utf-8"))  # Для корректного отображения сообщений на сервере

        # Отправка сообщения клиентам
        for client in clients:
            if addr != client:
                s.sendto(data, client)

    except:
        print("---Server Stopped---")
        quit = True

s.close()
