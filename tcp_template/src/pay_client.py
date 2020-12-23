import json

from CustomSocket import CustomSocket

HEADER_LENGTH = 10


def receive(client_socket):
    msg_accepted = json.loads(client_socket.receive().decode('utf-8'))
    return msg_accepted


def connection():
    HOST = '127.0.0.1'
    PORT = 8090
    client_socket = CustomSocket()
    print("Connecting to server...")
    try:
        client_socket.connect(HOST, PORT)
    except ConnectionError:
        print('Failed to connect to the remote server')
        client_socket.close()
        exit()
    print("Connected!")
    print("-------------------------\n"
          "1 name password - sign in\n"
          "2 name password - sign up\n"
          "-------------------------")  # 1-войти 2-регистрация
    while True:
        login = input("Enter command: ")
        split_login = login.split()
        if len(split_login) == 3:
            if int(split_login[0]) == 1 or int(split_login[0]) == 2:
                try:
                    msg = build_msg(split_login)
                    client_socket.send_all(msg)
                    msg_accepted = receive(client_socket)
                    if 'You have been successfully register' in msg_accepted['text']:
                        print(msg_accepted['text'])
                        print(f"Number of your wallet: {msg_accepted['wallet']}")
                        user_command(client_socket)
                        break
                    elif 'You have been successfully' in msg_accepted['text']:
                        print(msg_accepted['text'])
                        user_command(client_socket)
                        break
                    else:
                        print(msg_accepted['text'])
                except ConnectionError:
                    print('The remote server has ended the session and the connection is broken')
                    client_socket.close()
                    exit()
            else:
                print("Enter 1 to sign in or 2 to sign up")
        else:
            print("Enter 1 or 2 name password")


def user_command(client_socket):
    while True:
        print("-------------------------\n"
              "3 - get wallets\n"
              "4 wallet sum - transaction\n"
              "5 - check balance\n"
              "6 - exit\n"
              "-------------------------")
        command = input("Enter command: ")
        split_command = command.split()
        if len(split_command) == 3 and int(split_command[0]) == 4:
            msg = build_msg(split_command)
            client_socket.send_all(msg)
            answer = receive(client_socket)
            print(answer['text'])
            if 'Transaction was successful' in answer['text']:
                print(answer['sum'])
        elif len(split_command) == 1:
            if int(split_command[0]) == 3:
                msg = build_msg(split_command)
                client_socket.send_all(msg)
                answer = receive(client_socket)
                print(answer['text'])
                for user in answer['users']:
                    print('name:', user['name'], 'wallet:', user['wallet'])
            elif int(split_command[0]) == 5:
                msg = build_msg(split_command)
                client_socket.send_all(msg)
                answer = receive(client_socket)
                print(answer['text'])
                print(answer['sum'])
            elif int(split_command[0]) == 6:
                msg = build_msg(split_command)
                client_socket.send_all(msg)
                client_socket.shutdown()
                client_socket.close()
                exit()
            else:
                print("Wrong command")
        else:
            print("Wrong command")


def build_msg(input_msg):
    code = int(input_msg[0])
    if code == 1 or code == 2:
        msg = {
            'type': code,
            'name': input_msg[1],
            'pass': input_msg[2]
        }
    elif code == 3 or code == 5 or code == 6:
        msg = {
            "type": code}
    elif code == 4:
        msg = {
            "type": code,
            "wallet": input_msg[1],
            "sum": input_msg[2]}
    msg = json.dumps(msg) #преобразование в строку json
    return msg


def main():
    connection()


if __name__ == '__main__':
    main()
