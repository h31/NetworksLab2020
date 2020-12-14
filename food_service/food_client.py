from FirstTask.CustomSocket import CustomSocket

HEADER_LENGTH = 10

HOST = '127.0.0.1'
PORT = 8091

server_socket = CustomSocket()

is_customer = None


def main():
    print('---FOOD DELIVERY---')
    define_if_customer()
    print('Connecting to server...')
    connect_to_server()


def connect_to_server():
    while True:
        try:
            server_socket.connect(HOST, PORT)
            print('Connected!\n'
                  '-------------------------\n'
                  '1 name password - sign in\n'
                  '2 name password - sign up\n'
                  '-------------------------')
            break
        except ConnectionRefusedError:
            pass


def define_if_customer():
    global is_customer
    while is_customer is None:
        if_customer_reply = input('Are you a customer? [Y/n]')
        if if_customer_reply == 'Y':
            is_customer = True
            print('Using customers interface')
        elif if_customer_reply == 'n':
            is_customer = False
            print('Using sellers interface')
        else:
            pass


if __name__ == "__main__":
    main()
