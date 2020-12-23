import json
import logging
import shlex
import threading

from FirstTask.CustomSocket import CustomSocket

HEADER_LENGTH = 10

HOST = '127.0.0.1'
PORT = 8091

server_socket = CustomSocket()

is_customer = None

''' Customer dict; Seller dict '''
options = {True: {3: 'Get shops list: 3',
                  4: 'Get products in supermarket: 4 "Supermarket name"',
                  5: 'Make order: 5 "item1,item2,item3" zone',
                  6: 'Get history of your orders: 6',
                  7: 'Exit: 7'},
           False: {3: 'Get shops list: 3',
                   4: 'Add supermarket: 4 "Supermarket name" zone',
                   5: 'Add goods to supermarket: 5 "Supermarket name" "item1:price1,item2:price2,item3:price3"',
                   6: 'Get shopping history of supermarket: 6 "Supermarket name"',
                   7: 'Exit: 7'}}


def main():
    print('---FOOD DELIVERY---')
    define_if_customer()
    print('Connecting to server...')
    connect_to_server()


def connect_to_server():
    while True:
        try:
            server_socket.connect(HOST, PORT)
            print('Connected!')
            break
        except ConnectionRefusedError:
            pass
    send_msg(input('-------------------------\n'
                   '1 name password - sign in\n'
                   '2 name password - sign up\n'
                   '-------------------------'))


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


def close_connection():
    server_socket.shutdown()
    server_socket.close()


def receive_msg():
    while True:
        try:
            msg_accepted = json.loads(server_socket.receive().decode())
            msg_type = msg_accepted['type']
            print_received_msg(msg_type, msg_accepted)
        except ConnectionResetError:
            logging.error('The server has been disconnected')
            close_connection()
            return False
        except Exception as ex:
            logging.error(ex)
            close_connection()
            return False


def print_received_msg(msg_type, data):
    print(data['text'])
    if is_customer:
        if msg_type == 1:
            pass
        elif msg_type == 2:
            pass
        elif msg_type == 3:
            pass
        elif msg_type == 4:
            pass
        elif msg_type == 5:
            pass
        elif msg_type == 6:
            pass
    else:
        if msg_type == 1:
            pass
        elif msg_type == 2:
            pass
        elif msg_type == 3:
            pass
        elif msg_type == 4:
            pass
        elif msg_type == 5:
            pass
        elif msg_type == 6:
            pass


def send_msg(msg_text):
    while True:
        try:
            msg = build_msg(msg_text)
        except:
            print("Enter valid command")
            continue
        if threading.active_count() < 3 or not msg:
            return False
        server_socket.send_all(msg)
        receive_msg()
        send_msg(input("--------------------------\n"
                       f"{options[is_customer][3]}\n"
                       f"{options[is_customer][4]}\n"
                       f"{options[is_customer][5]}\n"
                       f"{options[is_customer][6]}\n"
                       f"{options[is_customer][7]}\n"
                       "-------------------------"))


def build_msg(msg_text):
    msg_text_parts = shlex.split(msg_text)
    msg_type = int(msg_text_parts[0])
    msg = {
        'type': msg_type,
        'is_customer': is_customer
    }

    if (msg_type == 1 or 2) and len(msg_text_parts) == 3:
        msg['name'] = msg_text_parts[1]
        msg['pass'] = msg_text_parts[2]
    elif msg_type == 7:
        close_connection()
        exit()
    elif is_customer:
        if msg_type == 4 and len(msg_text_parts) == 2:
            msg['shop'] = msg_text_parts[1].replace('"', '')
        elif msg_type == 5 and len(msg_text_parts) >= 4:  # "shop name" "product1,product 2,product3" zone
            msg['shop'] = msg_text_parts[1].replace('"', '')
            msg['goods'] = msg_text_parts[2:].replace('"', '').split(',')  # "'item1,it2,it2'" -> ["it1","it2","it3"]
            msg['zone'] = int(msg_text_parts[3])
    else:
        if msg_type == 4 and len(msg_text_parts) == 3:  # 'shop name' zone_m
            msg['shop'] = msg_text_parts[1].replace('"', '')
            msg['zone'] = int(msg_text_parts[3])
        elif msg_type == 5 and len(msg_text_parts) == 3:  # "product1:50,product 2:30" for product-price
            msg['shop'] = msg_text_parts[1].replace('"', '')
            products = []
            for product in msg_text_parts[2].replace('"', '').split(','):
                product_info = product.split(':')
                products.append({
                    'product': product_info[0],
                    'price': product_info[1]
                })
            msg['products'] = products
        elif msg_type == 6 and len(msg_text_parts) == 2:  # "shop name"
            msg['shop'] = msg_text_parts[1].replace('"', '')

    msg = json.dumps(msg)
    return msg


if __name__ == "__main__":
    main()
