import json
import logging
import shlex

from FirstTask.CustomSocket import CustomSocket

HEADER_LENGTH = 10

HOST = '127.0.0.1'
PORT = 8091

server_socket = CustomSocket()

is_customer = None

''' Customer dict; Seller dict '''
options = {True: {3: 'Get shops list: 3',
                  4: 'Get products in supermarket: 4 "Supermarket name"',
                  5: 'Make order: 5 "Supermarket name" "item1,item2,item3" zone',
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
    display_authentification()


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
    #print(f'\ntext: {data}\n')
    if msg_type == 1:
        msg_text = data['text']
        print(msg_text)
        if msg_text.split()[0].lower() == 'wrong':
            display_authentification()
    elif msg_type == 2:
        msg_text = data['text']
        print(msg_text)
        if msg_text == 'User with this name already exists ':
            display_authentification()
    elif is_customer:
        if msg_type == 3:
            display_shops(data['shops'])
        elif msg_type == 4:
            display_goods(data)
        elif msg_type == 5:
            print(f'Your order is successful!\nSum of purchase: {data["text"]}')
        elif msg_type == 6:
            print("Your purchase history:")
            display_history(data['history'])
    else:
        if msg_type == 3:
            display_shops(data['list'])
        elif msg_type == 4 or msg_type == 5:
            print(data['text'])
        elif msg_type == 6:
            print("Supermarket purchase history:")
            display_history(data['history'])


def display_authentification():
    send_msg(input('-------------------------\n'
                   '1 name password - sign in\n'
                   '2 name password - sign up\n'
                   '-------------------------\n'))


def display_goods(data):
    goods = data['goods']
    print("Available goods:")
    for good in goods:
        print(f'Item: {good[0]}; Price: {good[1]}')


def display_shops(data):
    shops = [shop[0] for shop in data]
    print('Shops: ', ','.join(shops))


def display_history(purchases):
    if not len(purchases):
        print("No history yet")
    else:
        for purchase in purchases:
            shop = purchase[-3]
            goods = purchase[-2].replace('{', '').replace('}', '').replace('"', '')
            price = purchase[-1]
            attribute_of_comparison = 'Shop' if is_customer else 'Customer'
            print(f'{attribute_of_comparison}: {shop}; Items: {goods}; Price: {price}')


def display_options_input():
    send_msg(input("--------------------------\n"
                   f"{options[is_customer][3]}\n"
                   f"{options[is_customer][4]}\n"
                   f"{options[is_customer][5]}\n"
                   f"{options[is_customer][6]}\n"
                   f"{options[is_customer][7]}\n"
                   "-------------------------\n"))


def send_msg(msg_text):
    while True:
        try:
            msg = build_msg(msg_text)
            if not msg:
                print("Enter valid command")
                display_options_input()
            server_socket.send_all(msg)
            if msg_text == '7':
                close_connection()
                exit()
        except Exception as ex:
            logging.error(ex)
            # print("Enter valid command")
            continue
        receive_msg()
        display_options_input()


def build_msg(msg_text):
    if not msg_text:
        return None
    try:
        msg_text_parts = shlex.split(msg_text)
    except:
        return None

    msg_type = int(msg_text_parts[0])
    msg = build_base_msg(msg_type)

    if msg_type == 1 or msg_type == 2:
        if len(msg_text_parts) != 3:
            return None
        set_name_pass(msg, msg_text_parts)
    elif is_customer:
        if msg_type == 4:
            if len(msg_text_parts) != 2:
                return None
            add_request_shop(msg, msg_text_parts)
        elif msg_type == 5:
            if len(msg_text_parts) < 4:  # "shop name" "product1,product 2,product3" zone
                return None
            add_order_requirements(msg, msg_text_parts)
    else:
        if msg_type == 4:
            if len(msg_text_parts) != 3:  # 'shop name' zone_m
                return None
            add_shop_adding_info(msg, msg_text_parts)
        elif msg_type == 5:
            if len(msg_text_parts) != 3:  # "product1:50,product 2:30" for product-price
                return None
            add_goods_adding_info(msg, msg_text_parts)
        elif msg_type == 6 and len(msg_text_parts) == 2:  # "shop name"
            add_request_shop(msg, msg_text_parts)

    msg = json.dumps(msg)
    return msg


def build_base_msg(msg_type):
    msg = {
        'type': msg_type,
        'is_customer': is_customer
    }
    return msg


def add_goods_adding_info(msg, msg_text_parts):
    add_request_shop(msg, msg_text_parts)
    products = []
    for product in msg_text_parts[2].replace('"', '').split(','):
        product_info = product.split(':')
        products.append({
            'product': product_info[0],
            'price': product_info[1]
        })
    msg['products'] = products


def add_shop_adding_info(msg, msg_text_parts):
    add_request_shop(msg, msg_text_parts)
    msg['zone'] = int(msg_text_parts[2])


def add_order_requirements(msg, msg_text_parts):
    add_request_shop(msg, msg_text_parts)
    msg['goods'] = msg_text_parts[2].replace('"', '').split(',')  # "'item1,it2,it2'" -> ["it1","it2","it3"]
    msg['zone'] = int(msg_text_parts[3])


def add_request_shop(msg, msg_text_parts):
    msg['shop'] = msg_text_parts[1].replace('"', '')


def set_name_pass(msg, msg_text_parts):
    msg['name'] = msg_text_parts[1]
    msg['pass'] = msg_text_parts[2]


if __name__ == "__main__":
    main()
