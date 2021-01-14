import json
import logging
import random
import socket
import string
import threading
import psycopg2
from FirstTask.CustomSocket import CustomSocket


HOST = '127.0.0.1'
PORT = 8091
server_socket = CustomSocket()
connections = {}  # [addr][connection]
DELIVERY_PRICE = 1000
name = ""

sql_insert_new_user_data = "INSERT INTO users (user_name, user_password, user_mode) VALUES " \
                           "(%s, crypt(%s, gen_salt('bf')), %s) ON CONFLICT DO NOTHING RETURNING 'OK';"
sql_check_sign_in = "SELECT * FROM users WHERE user_name=%s" \
                    " AND user_password=crypt(%s, user_password) AND user_mode=%s;"
sql_insert_new_shop_data = "INSERT INTO shops (shop_name,  shop_zone) VALUES " \
                           "(%s, %s) ON CONFLICT DO NOTHING RETURNING 'OK';"
sql_insert_new_good_data = "INSERT INTO goods (shop_name,  good_name, good_price) VALUES " \
                           "(%s, %s, %s) ON CONFLICT DO NOTHING RETURNING 'OK';"
sql_get_shop_id = "SELECT id FROM shops WHERE shop_name=%s;"
sql_get_shop_name = "SELECT shop_name FROM shops WHERE id=%s;"
sql_get_user_name = "SELECT user_name FROM users WHERE id=%s;"
sql_get_shops = "SELECT shop_name FROM shops"
sql_get_goods = "SELECT good_name, good_price FROM goods WHERE shop_name=%s;"
sql_get_price = "SELECT good_price FROM goods WHERE good_name=%s AND shop_name = %s"
sql_get_zone = "SELECT shop_zone FROM shops WHERE shop_name=%s"
sql_insert_new_history_data = "INSERT INTO history (user_name, shop_name, order_goods, sum) VALUES " \
                           "(%s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING 'OK';"
sql_get_user_id = "SELECT id FROM users WHERE user_name=%s;"
sql_get_history_shop = "SELECT user_name, order_goods, sum FROM history WHERE shop_name=%s;"
sql_get_history_user = "SELECT shop_name, order_goods, sum FROM history WHERE user_name=%s;"


def get_cursor_connection():
    connection = psycopg2.connect(dbname='food_service', user='postgres', password='supersecurepassword', host='127.0.0.1')
    return connection.cursor(), connection


def build_msg(msg_type, msg_text, is_customer):
    if msg_type == 3 and is_customer:
        msg = {
            'type': msg_type,
            'shops': msg_text
        }
    elif msg_type == 3 and not is_customer:
        msg = {
            'type': msg_type,
            'list': msg_text
        }
    elif msg_type == 4 and is_customer:
        msg = {
            'type': msg_type,
            'goods': msg_text
        }
    elif msg_type == 6:
        msg = {
            'type': msg_type,
            'history': msg_text
        }
    else:
        msg = {
            'type': msg_type,
            'text': msg_text
        }
    print(f'Reply for command {msg_type} has been created. msg: ')
    print(msg)
    msg = json.dumps(msg)
    msg = bytes(msg, encoding='utf-8')
    return msg


def request(sql_request, params=None):
    cursor, connection = get_cursor_connection()
    if len(params) == 3:
        cursor.execute(sql_request, (params[0], params[1], params[2]))
    elif len(params) == 2:
        cursor.execute(sql_request, (params[0], params[1]))
    else:
        cursor.execute(sql_request, (params[0]))
    try:
        was_successful = cursor.fetchall()[0][0]
    except IndexError:
        was_successful = False
    connection.commit()
    return was_successful


def register_good(shop_name, good_name, good_price):
    shop_id = request(sql_get_shop_id, [(shop_name,)])
    if shop_id:
        was_successful = request(sql_insert_new_good_data, [shop_id, good_name, good_price])
    else:
        was_successful = False
    return was_successful


def make_order(shop_name, good_name):
    shop_id = request(sql_get_shop_id, [(shop_name,)])
    if shop_id:
        was_successful = request(sql_get_price, [good_name, shop_id])
    else:
        was_successful = None
    return was_successful


def get_for_customers(sql_request, params=None):
    cursor, connection = get_cursor_connection()
    if params:
        cursor.execute(sql_request, params[0])
    else:
        cursor.execute(sql_request)
    try:
        was_successful = cursor.fetchall()
    except IndexError:
        was_successful = False
    connection.commit()
    return was_successful


def get_goods(shop_name):
    shop_id = request(sql_get_shop_id, [(shop_name,)])
    if shop_id:
        was_successful = get_for_customers(sql_get_goods, [(shop_id,)])
    else:
        was_successful = False
    return was_successful


def delivery_price(shop_name, customer_zone):
    shop_zone = request(sql_get_zone, [(shop_name,)])
    delivery = (abs(shop_zone-customer_zone)+1)*DELIVERY_PRICE
    return delivery


def create_history(user_name, shop_name, goods, total_sum):
    cursor, connection = get_cursor_connection()
    shop_id = request(sql_get_shop_id, [(shop_name,)])
    user_id = request(sql_get_user_id, [(user_name,)])
    cursor.execute(sql_insert_new_history_data, (user_id, shop_id, goods, total_sum))
    try:
        was_successful = cursor.fetchall()[0][0]
    except IndexError:
        was_successful = False
    connection.commit()
    return was_successful


def get_history(name, sql_request, sql_id):
    cursor, connection = get_cursor_connection()
    is_id = request(sql_id, [(name,)])
    if is_id:
        cursor.execute(sql_request, (is_id,))
        try:
            was_successful = cursor.fetchall()
        except IndexError:
            was_successful = False
        connection.commit()
    else:
        was_successful = False
    return was_successful


def receive_data(user):
    try:
        msg = server_socket.receive(connections[user]).decode()
        data = json.loads(msg)
    except KeyError:
        return [False] * 2
    if not data:
        return [False] * 2
    message_type = data['type']
    #print(message_type)
    #print(data)
    return message_type, data


def process_message(user):
    while True:
        try:
            message_type, data = receive_data(user)
            if not message_type:
                return False
            if message_type == 1:  # sign in
                print(f'User with address {user} wants to sign in')
                successful = request(sql_check_sign_in, [data['name'], data['pass'], data['is_customer']])
                sign_in_response = 'You have been successfully logged in' if successful else 'Wrong user credentials'
                connections[user].sendall(build_msg(message_type, sign_in_response, data['is_customer']))
                if sign_in_response in "Wrong user credentials":
                    process_message(user)
                global name
                if not data['is_customer']:
                    process_message_seller(user)
                else:
                    name = data['name']
                    process_message_customer(user)
            elif message_type == 2:
                print(f'User with address {user} wants to sign up')
                successful = request(sql_insert_new_user_data, [data['name'], data['pass'], data['is_customer']])
                sign_in_response = 'You have been successfully registered' if successful else 'User with this name already ' \
                                                                                              'exists '
                connections[user].sendall(build_msg(message_type, sign_in_response, data['is_customer']))
                if sign_in_response in "User with this name already exists ":
                    process_message(user)
                if not data['is_customer']:
                    process_message_seller(user)
                else:
                    name = data['name']
                    process_message_customer(user)
        except ConnectionResetError as ex:
            logging.error(ex)
            close_user_connection(user)
            return False


def process_message_seller(user):
    while True:
        try:
            message_type, data = receive_data(user)
            if not message_type:
                return False
            if message_type == 3:
                shops_list = get_for_customers(sql_get_shops)
                connections[user].sendall(build_msg(message_type, shops_list, False))
            if message_type == 4:
                successful = request(sql_insert_new_shop_data, [data['shop'], data['zone']])
                response = 'You have been successfully registered your shop' if successful else 'Shop with this name already ' \
                                                                                                'exists '
                connections[user].sendall(build_msg(message_type, response, False))
            if message_type == 5:
                for i in range(0, len(data['products'])):
                    successful = register_good(data['shop'], data['products'][i]['product'], data['products'][i]['price'])
                response = 'You added goods' if successful else 'Shop with this name does not exist'
                connections[user].sendall(build_msg(message_type, response, False))
            if message_type == 6:
                history_shop = get_history(data['shop'], sql_get_history_shop, sql_get_shop_id)
                for i in range(0, len(history_shop)):
                    title = request(sql_get_user_name, [(history_shop[i][0],)])
                    history_shop[i] = (title, history_shop[i][1], history_shop[i][2])
                connections[user].sendall(build_msg(message_type, history_shop, False))
            if message_type == 7:
                close_user_connection(user)
        except ConnectionResetError as ex:
            logging.error(ex)
            close_user_connection(user)
            return False


def process_message_customer(user):
    while True:
        try:
            message_type, data = receive_data(user)
            global name
            if not message_type:
                return False
            if message_type == 3:
                shops_list = get_for_customers(sql_get_shops)
                connections[user].sendall(build_msg(message_type, shops_list, True))
            if message_type == 4:
                goods_list = get_goods(data['shop'])
                connections[user].sendall(build_msg(message_type, goods_list, True))
            if message_type == 5:
                good_price = 0
                for i in range(0, len(data['goods'])):
                    order = make_order(data['shop'], data['goods'][i])
                    if order:
                        good_price += order
                    else:
                        good_price = 0
                delivery = delivery_price(data['shop'], data['zone'])
                if good_price:
                    response = good_price+delivery
                    create_history(name, data['shop'], data['goods'], response)
                else:
                    response = "Wrong goods or name of shop"
                #print(response)
                connections[user].sendall(build_msg(message_type, response, True))
            if message_type == 6:
                history_shop = get_history(name, sql_get_history_user, sql_get_user_id)
                for i in range(0, len(history_shop)):
                    title = request(sql_get_shop_name, [(history_shop[i][0],)])
                    history_shop[i] = (title, history_shop[i][1], history_shop[i][2])
                connections[user].sendall(build_msg(message_type, history_shop, True))
            if message_type == 7:
                close_user_connection(user)
        except ConnectionResetError as ex:
            logging.error(ex)
            close_user_connection(user)
            return False


def connect_users():
    conn, addr = server_socket.accept()
    if conn not in connections:
        connections[addr] = conn
        threading.Thread(target=process_message, args=(addr,)).start()
    print(f'Connection with user at address {addr} has been established')
    threading.Thread(target=connect_users).start()


def close_user_connection(user):
    connections[user].shutdown(socket.SHUT_WR)
    connections[user].close()
    print(f'Disconnecting addr {user}')
    del connections[user]


def run_server():
    server_socket.setsockopt()
    server_socket.bind(HOST, PORT)
    server_socket.listen(20)
    print('Waiting for clients to connect...')
    connect_users()

    while True:
        pass


def main():
    global HOST
    global PORT

    '''while True:
        HOST = input('Enter host name: ')

        def _validate_ip(assumed_ip):
            assumed_ip_parts = assumed_ip.split('.')
            if len(assumed_ip_parts) != 4:
                return False
            for x in assumed_ip_parts:
                if not x.isdigit():
                    return False
                i = int(x)
                if i < 0 or i > 255:
                    return False
            return True

        if _validate_ip(HOST):
            break

    while True:
        try:
            PORT = int(input('Enter port to run on: '))
            if 1 <= PORT <= 65535:
                break
        except ValueError:
            continue'''

    run_server()


if __name__ == '__main__':
    main()
