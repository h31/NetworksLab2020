from datetime import datetime
from ipaddress import IPv4Network
import socket

from dhcp.dhcp_packet import *

SERVER_PORT = 8067
CLIENT_PORT = 8068

TIMEOUT = 1000
BUFFER_SIZE = 4096


class Server:
    def __init__(self):
        self.server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.server_socket.bind(('', SERVER_PORT))  # '' represents INADDR_ANY, which is used to bind to all interfaces

        self.connected = True
        self.leased_ips = {}

    def run(self):
        print('Server is running...')
        while self.connected:
            packet_received = self.server_socket.recvfrom(BUFFER_SIZE)
            #try:  # trying to parse. With a correct message should do
            dhcp_message = DHCPPacket()
            dhcp_message.convert_from_bytes(packet_received[0])  # get a proper format
            if packet_received[0][0] == 1:  # message from the client
                print(f'Received message from the client with mac {dhcp_message.cha_addr}')
                print(f'from client {packet_received[1]}')
                self.process_message(dhcp_message)
            ''' except Exception as ex:
                logging.error(ex)'''

    def process_message(self, msg):
        msg_type = msg.options[53].data
        if msg_type == dhcp_messages_types['DHCPDISCOVER']:  # discover received
            print('Discover accepted')
            offer = self.create_offer(msg)
            self.send_broadcast(offer.convert_to_bytes())
            print('Offer sent')
        elif msg_type == dhcp_messages_types['DHCPREQUEST']:  # request
            print('Request accepted')
            ack = self.create_ack(msg)
            if msg.cia_addr != '0.0.0.0' and msg.options[54].data == server_address:
                ack.cia_addr = msg.cia_addr
                self.send_broadcast(ack.convert_to_bytes())
                print('Ack sent (ip prolonging requested)')
            else:
                self.send_broadcast(ack.convert_to_bytes())
                print('Ack sent (leasing new ip)')
            self.leased_ips[ack.yia_addr]['last_leased'] = datetime.now()
        elif msg_type == dhcp_messages_types['DHCPRELEASE'] and msg.options[54].data == server_address:  # release
            print('Release accepted')
            self.release_ip(msg.cia_addr)

    def send_broadcast(self, msg):
        self.server_socket.sendto(msg, (broadcast_mask, CLIENT_PORT))

    def lease_ip(self, client_mac):
        net = IPv4Network(f'{start_net_address}/{subnet_mask}')
        hosts_iterator = (host for host in net.hosts() if
                          (str(host) != default_gateway) and str(host) != server_address)
        for addr in hosts_iterator:
            str_addr = str(addr)
            if (str_addr in self.leased_ips.keys() and self.leased_ips[str_addr]['last_leased'] is not None and (
                    datetime.now() - self.leased_ips[str_addr]['last_leased']).total_seconds() > lease_duration) or (
                    str_addr not in self.leased_ips.keys()):  # reuse old ip that was not prolong or take a new one
                # if error encounters -> because assign None to last leased before the 1st ack, check this one
                self.leased_ips[str_addr] = self.leased_ip_info(client_mac)
                return str_addr  # stop iterating after choosing an address

    def leased_ip_info(self, mac):
        return {
            'mac': mac,
            'last_leased': None
        }

    def release_ip(self, addr):
        del self.leased_ips[addr]  # delete client's key

    def create_offer(self, msg_from_client):
        offer_ip = self.lease_ip(msg_from_client.cha_addr)
        dhcp_packet = DHCPPacket()
        dhcp_packet.op_code = 2
        dhcp_packet.x_id = msg_from_client.x_id
        dhcp_packet.yia_addr = offer_ip
        dhcp_packet.sia_addr = server_address
        dhcp_packet.gia_addr = msg_from_client.gia_addr
        dhcp_packet.cha_addr = msg_from_client.cha_addr
        dhcp_packet.add_options({
            53: dhcp_messages_types['DHCPOFFER'],
            1: subnet_mask,
            3: default_gateway,
            6: dns_server,
            51: lease_duration,
            54: server_address
        })
        return dhcp_packet

    def create_ack(self, msg_from_client):
        dhcp_packet = DHCPPacket()
        dhcp_packet.op_code = 2
        dhcp_packet.x_id = msg_from_client.x_id
        dhcp_packet.cia_addr = msg_from_client.cia_addr  # 0.0.0.0  if does not have any yet
        dhcp_packet.yia_addr = msg_from_client.options[
            50].data if msg_from_client.cia_addr == '0.0.0.0' else msg_from_client.cia_addr
        dhcp_packet.sia_addr = server_address
        dhcp_packet.gia_addr = msg_from_client.gia_addr
        dhcp_packet.cha_addr = msg_from_client.cha_addr
        dhcp_packet.flags = 0
        dhcp_packet.add_options({
            53: dhcp_messages_types['DHCPACK'],
            1: subnet_mask,
            3: default_gateway,
            6: dns_server,
            51: lease_duration,
            54: server_address
        })
        return dhcp_packet


if __name__ == "__main__":
    dhcp_server = Server()
    dhcp_server.run()
