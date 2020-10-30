import socket, time, threading

key = 8194

shutdown = False
join = False

# Позволяет принимать данные другого пользователя
def receving(name, sock):
    while not shutdown:
        try:
            while True:
                data, addr = sock.recvfrom(1024)
                #print(data.decode("utf-8"))

                dataSplit = data.decode("utf-8").split(': ', maxsplit=1)
                decrypt = dataSplit[0]
                if len(dataSplit) == 2:
                    decrypt += ": "
                    for i in dataSplit[1]:
                        decrypt += chr(ord(i) ^ key)
                print(decrypt)

                time.sleep(0.2)
        except:
            pass

host = socket.gethostbyname(socket.gethostname())  # принимает в себе ip
port = 0  # порт. 0 так как только подключаемся

server = ("192.168.56.1", 9090)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # объявляем переменную s содержащую сокеты (2 - udp, 1 - ip)
s.bind((host, port))  # объявляем технологию на создание
s.setblocking(0)

alias = input("Name: ")

rT = threading.Thread(target = receving, args = ("RecvThread", s))
rT.start()

while shutdown == False:
    if join == False:
        # Если только подключились, отправить сообщение об этом на сервер
        s.sendto(("[" + alias + "] => join chat").encode("utf-8"), server)
        join = True
    else:
        try:
            message = input()

            crypt = ""
            for i in message:
                crypt += chr(ord(i) ^ key)
            message = crypt

            # Если отправили не пустоту
            if message != "":
                s.sendto(("[" + alias + "]: " + message).encode("utf-8"), server)

            time.sleep(0.2)
        except:
            s.sendto(("[" + alias + "] <= left chat").encode("utf-8"), server)
            shutdown = True

rT.join()
s.close()















