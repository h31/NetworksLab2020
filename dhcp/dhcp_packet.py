from binascii import unhexlify, hexlify
import logging
from socket import inet_aton, inet_ntoa
import struct

from dhcp.dhcp_collections import *


class DHCPPacket:
    op_code = 1  # 1 for DHCPREQUEST (from client), 2 for DHCPACK or DHCPNAK (to client)
    h_type = 1  # ethernet (10Mb) hardware type
    h_length = 6  # constant for this hardware type
    hops = 0  # set to 0 by client; used by relay agents to control the forwarding of message; == num of agents
    x_id = 0  # 32-bit identification generated by client; to match up the request with replies from server
    secs = 0  # number of seconds elapsed since a client began an attempt to acquire or renew a lease
    flags = 1  # 1 if client does not know his IP and server should broadcast; else set to 0 (unicast)
    cia_addr = '0.0.0.0'  # client ip; 0 if a client does not know his ip; else set tot current client ip address
    yia_addr = '0.0.0.0'  # 'your' ip; The IP address that the server is assigning to the client.
    sia_addr = '0.0.0.0'  # this address the client should use in the next step (may or may not be server who is
    # sending this reply.The sending server always includes its own IP address in the Server Identifier option.
    gia_addr = '0.0.0.0'  # gateway ip; to route messages when relay agents are involved to facilitate the communication
    cha_addr = 'FF:FF:FF:FF:FF:FF'  # client hardware address;
    s_name = None  # server can OPTIONALLY include its name (sample text/DNS domain name); or for option overload
    boot_file = None  # OPTIONALLY used by client to request particular type of boot file; by server to specify its path
    options = {}  # DHCP options; option_num : option_val

    def add_options(self, options):
        for option_tag, option_data in options.items():  # add options to dict
            if type(option_data) != str:
                option_data = str(option_data)
            self.options[option_tag] = Option(option_tag, option_data)
        self.options[255] = Option(255)

    def convert_to_bytes(self):
        byte_packet = bytearray([self.op_code, self.h_type, self.h_length, self.hops])
        byte_packet += struct.pack('!I', self.x_id)  # 32 bit number -> 4 byte; unsigned int
        byte_packet += struct.pack('!H', self.secs)  # 2 bytes; unsigned short
        byte_packet += struct.pack('!H', self.flags)
        byte_packet += inet_aton(self.cia_addr)  # ip addr to bytes
        byte_packet += inet_aton(self.yia_addr)
        byte_packet += inet_aton(self.sia_addr)
        byte_packet += inet_aton(self.gia_addr)
        byte_packet += unhexlify(self.cha_addr.replace(':', '').replace('-', ''))  # mac addr to bytes
        if self.s_name is not None:
            try:
                byte_packet += bytes(self.s_name + '\0' * (64 - len(self.s_name)), 'utf-8')
            except RuntimeError:
                logging.error("Server name is way too long. Cannot be longer than 64 bytes")
        if self.boot_file is not None:
            try:
                byte_packet += bytes(self.boot_file + '\0' * (128 - len(self.boot_file)), 'utf-8')
            except RuntimeError:
                logging.error("File path is way too long. Cannot be longer than 128 bytes")
        byte_packet += inet_aton(MAGIC_COOKIE)
        for option in self.options.values():
            current_option = option.get_option()
            byte_packet += bytes([current_option[0], current_option[1]]) + bytes(current_option[2], 'utf-8') if type(
                current_option) == tuple else bytes(current_option)
        return byte_packet

    def convert_from_bytes(self, byte_packet):
        index = 28 + self.h_length

        self.op_code = byte_packet[0]
        self.h_type = byte_packet[1]
        self.h_length = byte_packet[2]
        self.hops = byte_packet[3]
        self.x_id = struct.unpack('!I', byte_packet[4:8])[0]
        self.secs = struct.unpack('!H', byte_packet[8:10])[0]
        self.flags = struct.unpack('!H', byte_packet[10:12])[0]
        self.cia_addr = inet_ntoa(byte_packet[12:16])
        self.yia_addr = inet_ntoa(byte_packet[16:20])
        self.sia_addr = inet_ntoa(byte_packet[20:24])
        self.gia_addr = inet_ntoa(byte_packet[24:28])

        cha_addr = hexlify(byte_packet[28:index]).decode('utf-8')
        cha_addr_iter = iter(cha_addr)
        self.cha_addr = ':'.join(a + b for a, b in zip(cha_addr_iter, cha_addr_iter))

        next_is_cookie = inet_ntoa(byte_packet[index:index + 4]) == MAGIC_COOKIE
        if not next_is_cookie:
            s_name = byte_packet[index:byte_packet[index:index + 64].find('\x00')]
            self.s_name = s_name.decode('utf-8')
            index += 64
            if not next_is_cookie:
                boot_file = byte_packet[index:byte_packet[index:index + 128].find('\x00')]
                self.boot_file = boot_file.decode('utf-8')
                index += 128
        index += 4  # magic cookie

        self.options.clear()
        while index < len(byte_packet):
            tag = byte_packet[index]
            if tag != 255 and tag != 0:
                data_len = byte_packet[index + 1]
                data = byte_packet[index + 2:index + 2 + data_len].decode('utf-8')
                index += 2 + data_len
            else:
                data = None
                index += 1
            self.options[tag] = Option(tag, data)


class Option:
    tag = None
    len = None
    data = None

    def __init__(self, tag, data=None):
        self.tag = int(tag)
        if data is not None:
            self.len = len(data) if type(data) is str else len(bytearray(data))
            self.data = data

    '''If we have 0 or 255 in the tag field, there is no value
     If 0: such option will simply be skipped
     If 255: the sign that that was the last option in the options list'''

    def get_option(self):
        return (self.tag, self.len, self.data) if self.data is not None else [self.tag]
