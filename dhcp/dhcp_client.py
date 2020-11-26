from generate_mac import generate_mac
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
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client_socket.bind(('', CLIENT_PORT))
        self.transaction_id = secrets.token_hex(4)
        self.mac = generate_mac.total_random()
        print(f'my mac is {self.mac}')

        self.dhcp_packet = DHCPPacket()
        self.dhcp_packet.x_id = int(self.transaction_id, 16)
        print('x_id ', self.dhcp_packet.x_id)
        self.dhcp_packet.cha_addr = self.mac

        self.connected = True

    def run(self):
        print('Client is running...')
        while self.connected:
            if self.ip_got == '0.0.0.0' and not self.discover_is_sent:  # we do not have an address yet. Discover for servers
                discover = self.create_discover()
                self.send_broadcast(discover.convert_to_bytes())
                print("Discover sent")
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
        msg_type = int(msg.options[53].data)
        print('Processing received message...')
        print(f'my char addr: {msg.cha_addr.lower() == self.mac.lower()}')
        print(msg_type)
        if msg_type == dhcp_messages_types['DHCPOFFER'] and msg.cha_addr.lower() == self.mac.lower():  # offer received
            print('Offer accepted')
            if self.msg_was_sent_to_me(msg):
                self.ip_offered = msg.yia_addr
                self.server_address = inet_ntoa(msg.sia_addr)
                self.dhcp_packet.sia_addr = self.server_address
                print(
                    f"Offer was addressed to this client. IP offered: {self.ip_offered}, server address:"
                    f" {self.server_address}")
                request = self.create_request()
                request.add_options({
                    50: self.ip_offered,
                    54: self.server_address,
                })
                self.send_broadcast(request.convert_to_bytes())
                print("Request sent")
            else:
                print("Caught offer addressed to another client")
        elif msg_type == dhcp_messages_types['DHCPACK'] and msg.cha_addr.lower() == self.mac.lower():  # acknowledge received
            print('Acknowledge accepted')
            if not self.msg_was_sent_to_me(msg):
                return
            if self.ip_got == '0.0.0.0':  # ack after 1st request (we are about to get an ip)
                self.ip_got = msg.yia_addr
                self.dhcp_packet.cia_addr = self.ip_got
                self.ip_lease_duration = msg.options[51].data
            self.create_waiting_for_renewal_thread()  # either 1st ack or ack after requesting for lease prolonging

    def create_waiting_for_renewal_thread(self):
        event = threading.Event()
        waiting_for_prolonging_thread = threading.Thread(target=self.prolong, args=(event,))
        waiting_for_prolonging_thread.daemon = True
        waiting_for_prolonging_thread.start()

    def prolong(self, event):
        event.wait(int(self.ip_lease_duration) / 2)  # request for renewal after half of lease time
        request = self.create_request()
        request.cia_addr = self.ip_got
        self.send_broadcast(request.convert_to_bytes())
        print("Request for prolonging sent")

    def msg_was_sent_to_me(self, msg):
        return True if msg.cha_addr.lower() == self.mac.lower() else False

    def send_broadcast(self, msg):
        self.client_socket.sendto(msg, (broadcast_mask, SERVER_PORT))

    def create_discover(self):
        dhcp_packet = self.dhcp_packet
        dhcp_packet.add_options({
            53: dhcp_messages_types['DHCPDISCOVER'],
            61: self.mac
            # add 55 for parameter request list later?
        })
        return dhcp_packet

    def create_request(self):
        dhcp_packet = self.dhcp_packet
        dhcp_packet.clear_options()
        dhcp_packet.flags = 0 if self.ip_got != '0.0.0.0' else 1
        dhcp_packet.add_options({
            53: dhcp_messages_types['DHCPREQUEST'],
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
            53: dhcp_messages_types['DHCPRELEASE'],
            61: self.mac,
            54: self.server_address
        })
        return dhcp_packet


if __name__ == "__main__":
    dhcp_server = Client()
    dhcp_server.run()
