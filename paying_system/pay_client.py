import socket

from FirstTask.CustomSocket import CustomSocket

HEADER_LENGTH = 10


def receive(client_socket):
    received_header = client_socket.receive_bytes_num(HEADER_LENGTH)
    #msg_type = received_header[0]
    length_message = int(received_header[1:].decode('UTF-8'))
    #print(f'received header {received_header}, msg type: {msg_type}, msg_len: {length_message}')
    msg_accepted = client_socket.receive_bytes_num(length_message)
    #print(msg_accepted)
    return msg_accepted


def connection():
    HOST = '127.0.0.1'
    PORT = 8090
    client_socket = CustomSocket()
    print("Connecting to server...")
    client_socket.connect(HOST, PORT)
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
                msg, msg_len = build_msg(split_login)
                # print(f'sending msg: {msg} of length {len(msg)}')
                client_socket.send_bytes_num(msg, len(msg))
                # receive
                received_header = client_socket.receive_bytes_num(HEADER_LENGTH)
                length_message = int(received_header[1:].decode('UTF-8'))
                msg_accepted = client_socket.receive_bytes_num(length_message)
                # msg_accepted.insert(1, bytes(" Number of your wallet: ", 'UTF-8'))
                # msg_accepted = b' '.join(msg_accepted).decode('UTF-8')
                # print(msg_accepted)
                if 'You have been successfully register' in str(msg_accepted):
                    msg_accepted = msg_accepted.split(b'\0')
                    msg_accepted.insert(1, bytes("\nNumber of your wallet: ", 'UTF-8'))
                    msg_accepted = b' '.join(msg_accepted).decode('UTF-8')
                    print(msg_accepted)
                    user_command(client_socket)
                    break
                elif 'You have been successfully' in str(msg_accepted):
                    print(msg_accepted.decode("UTF-8"))
                    user_command(client_socket)
                    break
                else:
                    print(msg_accepted.decode("UTF-8"))
            else:
                print("Enter 1 to sign in or 2 to sign up")
        else:
            print("Enter 1 or 2 name password")
    while True:
        pass


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
            msg, msg_len = build_msg(split_command)
            client_socket.send_bytes_num(msg, len(msg))
            answer = receive(client_socket).decode('UTF-8')
            print(answer)
        elif len(split_command) == 1:
            if int(split_command[0]) == 3:
                msg, msg_len = build_msg(split_command)
                print(f'sending header: {msg} of length: {len(msg)}')
                client_socket.send_bytes_num(msg, len(msg))
                answer = [d.decode('UTF-8') for d in receive(client_socket).split(b'\0')]
                print(answer)
            elif int(split_command[0]) == 5:
                msg, msg_len = build_msg(split_command)
                client_socket.send_bytes_num(msg, len(msg))
                answer = receive(client_socket).decode('UTF-8')
                print(answer)
            elif int(split_command[0]) == 6:
                msg, msg_len = build_msg(split_command)
                client_socket.send_bytes_num(msg, len(msg))
                client_socket.shutdown()
                client_socket.close()
                exit()
            else:
                print("Wrong command")
        else:
            print("Wrong command")


def build_msg(input_msg):
    code = bytearray([int(input_msg[0])])
    if len(input_msg) > 1:
        first_piece = bytes(input_msg[1], "UTF-8")
    else:
        first_piece = b''

    if len(input_msg) > 2:
        second_piece = bytes(input_msg[2], "UTF-8")
    else:
        second_piece = b''

    if second_piece:
        msg_len = len(first_piece) + len(second_piece) + 1  # +1 - это пробел
        msg = code + bytes(f"{msg_len:<{HEADER_LENGTH}}", 'utf-8') + first_piece + b'\0' + second_piece
    else:
        msg_len = len(first_piece)
        msg = code + bytes(f"{msg_len:<{HEADER_LENGTH}}", 'utf-8') + first_piece
    #print(f'when building msg. msg is {msg}; len is {msg_len}')
    return msg, msg_len


def main():
    connection()


if __name__ == '__main__':
    main()
