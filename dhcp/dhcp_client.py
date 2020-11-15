from datetime import datetime
from generate_mac import generate_mac
from ipaddress import IPv4Network
import secrets
import socket
import threading

from dhcp.dhcp_packet import *
from dhcp.dhcp_collections import *

SERVER_PORT = 67
CLIENT_PORT = 68
BUFFER_SIZE = 4096


class Client:
    ip_got = '0.0.0.0'
    ip_offered = '0.0.0.0'
    server_address = '0.0.0.0'
    ip_lease_duration = None
    server_mac = None

    discover_is_sent = False

    def __init__(self):
        self.client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_address_port = (server_address, 67)
        self.transaction_id = secrets.token_hex(32)
        self.mac = generate_mac.total_random()

        self.dhcp_packet = DHCPPacket()
        self.dhcp_packet.x_id = self.transaction_id
        self.dhcp_packet.cha_addr = self.mac

        self.connected = True
        # client_socket.sendto(bytes_to_send server_address_port)
        # msgFromServer = UDPClientSocket.recvfrom(bufferSize)

    def run(self):
        print('Client is running...')
        while self.connected:
            if self.ip_got == '0.0.0.0' and not self.discover_is_sent:  # we do ot have an address yet. Discover for servers
                discover = self.create_discover()
                self.send_broadcast(discover.convert_to_bytes())
                self.discover_is_sent = True
            elif self.discover_is_sent:
                packet_received = self.client_socket.recvfrom(BUFFER_SIZE)
                try:
                    dhcp_message = DHCPPacket()
                    dhcp_message.convert_from_bytes(packet_received[0])  # get a proper format
                    if packet_received[0][0] == 2:  # message from the server
                        self.process_message(dhcp_message)
                except Exception as ex:
                    logging.error(ex)

    def process_message(self, msg):
        if msg.options[53] == dhcp_messages_types[2]:  # offer received
            print('Offer accepted')
            if self.msg_was_sent_to_me(msg):
                self.ip_offered = msg.yia_addr
                self.server_address = msg.sia_addr
                request = self.create_request()
                request.add_options({
                    50: self.ip_offered if self.ip_got == '0.0.0.0' else self.ip_got,
                    54: self.server_address,
                })
                self.send_broadcast(request.convert_to_bytes())
                print(
                    f"Offer was addressed to this client. IP offered: {self.ip_offered}, server address:"
                    f" {self.server_address}")
            else:
                print("Caught offer addressed to another client")
        elif msg.options[53] == dhcp_messages_types[5]:  # acknowledge received
            print('Acknowledge accepted')
            if not self.msg_was_sent_to_me(msg):
                return
            if self.ip_got == '0.0.0.0':  # ack after 1st request (we are about to get an ip)
                self.ip_got = msg.yia_addr
                self.ip_lease_duration = msg.options[51]
            self.create_waiting_for_renewal_thread()  # either 1st ack or ack after requesting for lease prolonging

    def create_waiting_for_renewal_thread(self):
        event = threading.Event()
        waiting_for_prolonging_thread = threading.Thread(target=self.prolong, args=(event,))
        waiting_for_prolonging_thread.daemon = True
        waiting_for_prolonging_thread.start()

    def prolong(self, event):
        event.wait(self.ip_lease_duration / 2)  # request for renewal after half of lease time
        request = self.create_request()
        request.cia_addr = self.ip_got
        self.send_unicast(request.convert_to_bytes())  # send request for ip prolonging

    def msg_was_sent_to_me(self, msg):
        return True if msg.cha_addr == self.mac else False

    def send_broadcast(self, msg):
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client_socket.sendto(msg, (broadcast_mask, 67))

    def send_unicast(self, msg):
        self.client_socket.sendto(msg, (self.server_address, SERVER_PORT))

    def create_discover(self):
        dhcp_packet = self.dhcp_packet
        dhcp_packet.add_options({
            53: 1,
            61: self.mac
            # add 55 for parameter request list later?
        })
        return dhcp_packet

    def create_request(self):
        dhcp_packet = self.dhcp_packet
        dhcp_packet.clear_options()
        dhcp_packet.flags = 0 if self.ip_got != '0.0.0.0' else 1
        dhcp_packet.add_options({
            53: 3,
            61: self.mac
            # add 55 for parameter request list later?
        })
        return dhcp_packet

    def create_release(self):
        dhcp_packet = self.dhcp_packet
        dhcp_packet.clear_options()
        dhcp_packet.flags = 0
        dhcp_packet.cia_addr = self.ip_got
        dhcp_packet.add_options({
            53: 7,
            61: self.mac,
            54: self.server_address
        })
        return dhcp_packet


if __name__ == "__main__":
    dhcp_server = Client()
    dhcp_server.run()
