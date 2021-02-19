import json
import socket
import sys

from encrypt import encrypt_password

HOST = '127.0.0.1'
PORT = 8080
BLOCK_SIZE = 1024

operations = ['1', '2', '3', '4']


def init_client():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
        print("Connected successfully")

        handle_operations(authenticate())

    except ConnectionRefusedError:
        print("The server is unreachable")


def authenticate():
    print("Enter admin password, otherwise press ENTER:")
    data = input()
    if data == '':
        auth_data = {"type": "auth", "password": -1}
        client_socket.send(bytes(json.dumps(auth_data), encoding="utf-8"))
        print("You are now entering USER mode")
        return False
    else:
        data = encrypt_password(data)
        auth_data = {"type": "auth", "password": data}  ##chtck
        client_socket.send(bytes(json.dumps(auth_data), encoding="utf-8"))

        # expecting {auth, 1} if success or {auth, -1} if deny
        data = client_socket.recv(BLOCK_SIZE).decode('utf-8')
        data = json.loads(data)
        flag = data.get("password", None)

        if flag == 1:
            print("You are now entering ADMIN mode")
            return True
        else:
            print("Wrong admin password. Entering user mode.")
            return False


def handle_operations(is_admin):
    print_menu(is_admin)

    while True:
        try:
            operation = input()

            if not operation:
                break

            if operation not in operations:
                print("Wrong input")
                continue

            if operation == '1':
                if is_admin:
                    operate_as_admin("history")
                else:
                    operate_as_user("park")
            elif operation == '2':
                if is_admin:
                    operate_as_admin("log")
                else:
                    operate_as_user("unpark")
            elif operation == '3':
                if is_admin:
                    operate_as_admin("total")
                else:
                    print_menu(is_admin)
            elif operation == '4':
                exit_message = {"type": "exit"}
                client_socket.send(bytes(json.dumps(exit_message), encoding="utf-8"))
                sys.exit(1)
        except ConnectionResetError:
            print("The server is not running. Try again later.")
            sys.exit(1)


def operate_as_user(operation_type):
    print("Enter car number:")
    number = input()
    data = {"type": operation_type, "number": number}
    client_socket.send(bytes(json.dumps(data), encoding="utf-8"))

    data = client_socket.recv(BLOCK_SIZE).decode('utf-8')
    data = json.loads(data)

    operation_type = data.get("type", None)

    if operation_type == 'error':
        print(f"Error: . Check car number you typed: {number}")
    elif operation_type == 'checkout':
        amount = data.get("amount", None)
        print(f"You finished your parking. Amount to pay: {amount}")
    else:
        print(f'Car {number} parked successfully.')


def operate_as_admin(operation_type):
    data = {"type": operation_type}
    client_socket.send(bytes(json.dumps(data), encoding="utf-8"))

    if operation_type == "total":
        data = client_socket.recv(BLOCK_SIZE).decode('utf-8')
        total = json.loads(data).get("total", None)
        print(f"Total amount: {total}")

    else:
        data = client_socket.recv(BLOCK_SIZE).decode('utf-8')
        data_size = json.loads(data).get("size", None)

        print(f'Size to transfer: {data_size}')

        actual_size = 0
        actual_data = b''
        while actual_size < data_size:
            actual_data += client_socket.recv(BLOCK_SIZE)
            actual_size = sys.getsizeof(actual_data)
            # print(f'Now received: {actual_size} of {data_size}')

        actual_data = json.loads(actual_data.decode("utf-8"))
        print(json.dumps(actual_data, indent=4, sort_keys=True))
        print(f'Now received: {actual_size} of {data_size} bytes. Received all data.')


def print_menu(is_admin):
    if is_admin:
        print("1 - get history\n"
              "2 - get log\n"
              "3 - view total payments amount\n"
              "4 - exit\n")
    else:
        print("1 - start parking\n"
              "2 - finish parking\n"
              "3 - print menu\n"
              "4 - exit\n")


if __name__ == '__main__':
    init_client()
