from datetime import datetime
from ipaddress import IPv4Network
import socket

from dhcp.dhcp_packet import *

SERVER_PORT = 67
CLIENT_PORT = 68

TIMEOUT = 1000
BUFFER_SIZE = 4096


class Server:
    def __init__(self):
        self.server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', SERVER_PORT))  # '' represents INADDR_ANY, which is used to bind to all interfaces
        self.connected = True
        self.leased_ips = {}

    def run(self):
        print("Server is running...")
        while self.connected:
            packet_received = self.server_socket.recvfrom(BUFFER_SIZE)
            try:  # trying to parse. With a correct message should do
                dhcp_message = DHCPPacket()
                dhcp_message.convert_from_bytes(packet_received[0])  # get a proper format
                if packet_received[0][0] == 1:  # message from the client
                    self.define_message_type(dhcp_message)
            except Exception as ex:
                logging.error(ex)
        ''' check if it is a dhcp message
        than message type case 
        '''

    def define_message_type(self, msg):
        if msg.options[53] == dhcp_messages_types[1]:  # discover received
            offer = self.create_offer(msg)
            self.send_broadcast(offer.convert_to_bytes())
        elif msg.options[53] == dhcp_messages_types[3]:  # request received
            ack = self.create_ack(msg)
            self.leased_ips[ack.cha_addr]['last_leased'] = datetime.now()
            self.send_ack(ack.convert_to_bytes())
        elif msg.options[53] == dhcp_messages_types[8]:  # inform received
            self.release_ip(msg.cha_addr)

    def send_broadcast(self, msg):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.server_socket.sendto(msg, (broadcast_mask, 68))

    def send_ack(self, msg):
        pass

    def lease_ip(self, client_mac):
        net = IPv4Network(f'{start_net_address}/{subnet_mask}')
        hosts_iterator = (host for host in net.hosts() if str(host) != default_gateway)
        for addr in hosts_iterator:
            if any([addr in self.leased_ips.keys() and self.leased_ips[addr]['last_leased'] is not None and (
                    datetime.now() - self.leased_ips[addr]['last_leased']).total_seconds() > lease_duration,
                    # if error encounters -> because assign None to last leased before the 1st ack, check this one
                    addr not in self.leased_ips.keys()]):  # reuse old ip that was not prolong or take a new one
                self.leased_ips[addr] = self.leased_ip_info(client_mac)
                return addr  # stop iterating after choosing an address
        pass

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
        dhcp_packet.gia_addr = msg_from_client.gia_addr
        dhcp_packet.cha_addr = msg_from_client.cha_addr
        dhcp_packet.add_options({
            53: 2,
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
        dhcp_packet.yia_addr = msg_from_client.options[50]
        dhcp_packet.gia_addr = msg_from_client.gia_addr
        dhcp_packet.cha_addr = msg_from_client.cha_addr
        dhcp_packet.flags = 0
        dhcp_packet.add_options({
            53: 5,
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
