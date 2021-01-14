import json
import logging
import random
import socket
import string
import threading

import psycopg2

from FirstTask.CustomSocket import CustomSocket

HOST = '127.0.0.1'
PORT = 8090
USERS_EXPECTED_NUMBER = 20

server_socket = CustomSocket()
connections = {}  # [addr][connection]

users_online = {}  # [addr][num of wallet]

sql_get_wallet_num_by_name = "SELECT user_wallet_num FROM users WHERE user_name=%s" \
                             " AND user_password=crypt(%s, user_password);"
sql_insert_new_user_data = "INSERT INTO users (user_name, user_password, user_wallet_num, user_sum) VALUES " \
                           "(%s, crypt(%s, gen_salt('bf')), %s, 100) ON CONFLICT DO NOTHING RETURNING 'OK';"
sql_get_all_other_wallets = "SELECT user_name, user_wallet_num FROM users WHERE NOT user_wallet_num=%s;"
sql_subtract_sum = "UPDATE users SET user_sum = user_sum - %s WHERE user_wallet_num = %s RETURNING 'OK';"
sql_add_sum = "UPDATE users SET user_sum = user_sum + %s WHERE user_wallet_num = %s RETURNING 'OK';"
sql_get_sum = "SELECT user_sum FROM users WHERE user_wallet_num=%s;"


def get_cursor_connection():
    connection = psycopg2.connect(dbname='payments_system', user='postgres', password='supersecurepassword',
                                  host='127.0.0.1')
    return connection.cursor(), connection


def connect_users():
    for user in range(USERS_EXPECTED_NUMBER):
        conn, addr = server_socket.accept()

        if conn not in connections:
            connections[addr] = conn
            threading.Thread(target=process_message, args=(addr,)).start()
        print(f'Connection with user at address {addr} has been established')
        threading.Thread(target=connect_users).start()


def build_msg(msg_type, msg_text, params=None):
    msg = {
        'type': msg_type,
        'text': msg_text
    }
    if msg_type in [4, 5] and params and params[0]:
        msg['sum'] = params[0]
    if msg_type == 2 and params and params[0]:
        msg['wallet'] = params[0]
    elif msg_type == 3:
        list_of_users = []
        for user_data in params[0]:
            list_of_users.append({
                'name': user_data[0],
                'wallet': user_data[1]
            })
        msg['users'] = list_of_users
    print(f'Reply for command {msg_type} has been created. msg: {msg}')
    msg = json.dumps(msg)
    msg = bytes(msg, encoding='utf-8')
    return msg


def process_message(user):
    while True:
        try:
            message_type, data = receive_data(user)
            if not message_type:
                return False
            # close the user connection if smth is wrong with the data received
            # different actions on different message type
            if message_type == 1:  # sign in
                print(f'User with address {user} wants to sign in')
                wallet_num = sign_in(user, data['name'], data['pass'])
                sign_in_response = 'You have been successfully logged in' if wallet_num else 'Wrong user credentials'
                connections[user].sendall(build_msg(message_type, sign_in_response, (wallet_num,)))
            elif message_type == 2:
                print(f'User with address {user} wants to sign up')
                registered_wallet_num = register(user, data['name'], data['pass'])
                register_response = 'You have been successfully registered' if registered_wallet_num else \
                    'User with this name already exists'
                connections[user].sendall(build_msg(message_type, register_response, (registered_wallet_num,)))
            elif message_type == 3:
                print(f'User {users_online[user]} wants to see info about other users')
                existing_wallets = get_existing_wallets(user)
                connections[user].sendall(build_msg(message_type, 'Existing users:', (existing_wallets,)))
            elif message_type == 4:
                print(f'User {users_online[user]} wants to send {data["sum"]}€ to user {data["wallet"]}')
                user_new_sum = transfer_sum(users_online[user], data['wallet'],
                                            data['sum'])  # from what wallet, to what wallet, sum to transfer
                msg = build_msg(message_type, 'Transaction was successful. Your balance...',
                                (str(user_new_sum),)) if user_new_sum else build_msg(message_type,
                                                                                     'Error occurred! Check your'
                                                                                     ' balance and receiver wallet'
                                                                                     ' number.')
                connections[user].sendall(msg)
            elif message_type == 5:
                print(f'User {users_online[user]} want to know how much money he has on the account')
                sum_on_account = get_sum_on_account(users_online[user])
                connections[user].sendall(build_msg(message_type, 'Your balance:', (str(sum_on_account),)))
            elif message_type == 6:  # user wants to quit. send goodbye
                close_user_connection(user)
            else:
                pass
        except ConnectionResetError as ex:
            if user in users_online.keys():
                print(f'User {users_online[user]} has disconnected unexpectedly:')
            logging.error(ex)
            close_user_connection(user)
            return False


def sign_in(user, name, password):
    cursor, connection = get_cursor_connection()
    cursor.execute(sql_get_wallet_num_by_name, (name, password))
    try:
        wallet_num = cursor.fetchall()[0][0]
    except IndexError:
        wallet_num = False
    connection.commit()

    if not wallet_num:
        return False
    else:
        users_online[user] = wallet_num
        return wallet_num


def register(user, name, password):
    cursor, connection = get_cursor_connection()
    wallet_num = ''.join(random.choices(string.digits, k=16))
    cursor.execute(sql_insert_new_user_data, (name, password, wallet_num))
    try:
        was_successful = cursor.fetchall()[0][0]
    except IndexError:
        was_successful = False
    connection.commit()

    if was_successful:
        users_online[user] = wallet_num
    return wallet_num if was_successful else None


def get_existing_wallets(user):
    cursor, connection = get_cursor_connection()
    cursor.execute(sql_get_all_other_wallets, (users_online[user],))
    wallets = cursor.fetchall()
    connection.commit()
    return wallets


def transfer_sum(sender_wallet_num, receiver_wallet_num, sum_to_transfer):
    user_new_sum = None
    if int(sum_to_transfer) <= 0:
        return user_new_sum
    cursor, connection = get_cursor_connection()
    cursor.execute(sql_subtract_sum, (sum_to_transfer, sender_wallet_num))
    sum_subtracted = cursor.fetchall()[0][0]
    if sum_subtracted:
        cursor.execute(sql_add_sum, (sum_to_transfer, receiver_wallet_num))
        try:
            sum_added = cursor.fetchall()[0][0]
        except IndexError:
            sum_added = False
        if sum_added:
            cursor.execute(sql_get_sum, (sender_wallet_num,))
            user_new_sum = cursor.fetchall()[0][0]
            if user_new_sum < 0:
                return None
    connection.commit()
    return user_new_sum


def get_sum_on_account(wallet_num):
    cursor, connection = get_cursor_connection()
    cursor.execute(sql_get_sum, (wallet_num,))
    sum_on_account = cursor.fetchall()[0][0]
    connection.commit()
    return sum_on_account


def receive_data(user):
    try:
        data = json.loads(server_socket.receive(connections[user]).decode())
    except KeyError:
        return [False] * 2
    if not data:
        return [False] * 2
    message_type = data['type']
    return message_type, data


def close_user_connection(user):
    connections[user].shutdown(socket.SHUT_WR)
    connections[user].close()
    print(f'Disconnecting addr {user}')
    del connections[user]
    if user in users_online.keys():
        print(f'Client {users_online[user]} has been disconnected')
        del users_online[user]


def run_server():
    server_socket.setsockopt()
    server_socket.bind(HOST, PORT)
    server_socket.listen(USERS_EXPECTED_NUMBER)
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