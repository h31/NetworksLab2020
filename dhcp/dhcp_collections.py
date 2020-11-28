MAGIC_COOKIE = '99.130.83.99'

default_gateway = '192.168.1.1'
server_address = '192.168.1.1'
start_net_address = '192.168.1.0'
subnet_mask = '255.255.255.0'
broadcast_mask = '255.255.255.255'
dns_server = '192.168.1.1'

lease_duration = 5 * 2  # seconds. set to  3600 * 2 for 2 hours


def mac_to_bytes(mac_string):
    mac_parts = mac_string.split(':')
    mac_byte_list = [bytes.fromhex(part) for part in mac_parts]
    return b''.join(mac_byte_list)


def mac_from_bytes(mac_bytes):
    mac_string = ''
    for mac_byte in mac_bytes:
        mac_string += bytes([mac_byte]).hex()
        if mac_bytes.index(mac_byte) != len(mac_bytes) - 1:
            mac_string += ':'
    return mac_string


dhcp_messages_types = {'DHCPDISCOVER': 1,
                       'DHCPOFFER': 2,
                       'DHCPREQUEST': 3,
                       'DHCPDECLINE': 4,
                       'DHCPACK': 5,
                       'DHCPNAK': 6,
                       'DHCPRELEASE': 7,
                       'DHCPINFORM': 8}

options_dict = {0: 'pad', 1: 'subnet_mask', 2: 'time_offset', 3: 'router', 4: 'time_server', 5: 'name_server',
                6: 'domain_server', 7: 'log_server', 8: 'quotes_server', 9: 'lpr_server', 10: 'impress_server',
                11: 'rlp_server', 12: 'hostname', 13: 'boot_file_size', 14: 'merit_dump_file', 15: 'domain_name',
                16: 'swap_server', 17: 'root_path', 18: 'extension_file', 19: 'forwarding',
                20: 'non_local_source_routing', 21: 'policy_filter', 22: 'max_dg_assembly', 23: 'default_ip_ttl',
                24: 'mtu_timeout', 25: 'mtu_plateau', 26: 'mtu_interface', 27: 'mtu_subnet', 28: 'broadcast_address',
                29: 'mask_discovery', 30: 'mask_supplier', 31: 'router_discovery', 32: 'router_request',
                33: 'static_route', 34: 'trailers', 35: 'arp_timeout', 36: 'ethernet', 37: 'default_tcp_ttl',
                38: 'keepalive_time', 39: 'keepalive_data', 40: 'nis_domain', 41: 'nis_servers', 42: 'ntp_servers',
                43: 'vendor_specific', 44: 'netbios_name_srv', 45: 'netbios_dist_srv', 46: 'netbios_node_type',
                47: 'netbios_scope', 48: 'x_window_font', 49: 'x_window_manager', 50: 'address_request',
                51: 'address_time', 52: 'overload', 53: 'dhcp_msg_type', 54: 'dhcp_server_id', 55: 'parameter_list',
                56: 'dhcp_message', 57: 'dhcp_max_msg_size', 58: 'renewal_time', 59: 'rebinding_time', 60: 'class_id',
                61: 'client_id', 62: 'netware_ip_domain', 63: 'netware_ip_option', 64: 'nis_domain_name',
                65: 'nis_server_addr', 66: 'server_name', 67: 'bootfile_name', 68: 'home_agent_addrs',
                69: 'smtp_server', 70: 'pop3_server', 71: 'nntp_server', 72: 'www_server', 73: 'finger_server',
                74: 'irc_server', 75: 'streettalk_server', 76: 'stda_server', 77: 'user_class', 78: 'directory_agent',
                79: 'service_scope', 80: 'rapid_commit', 81: 'client_fqdn', 82: 'relay_agent_information', 83: 'isns',
                84: 'removed_unassigned', 85: 'nds_servers', 86: 'nds_tree_name', 87: 'nds_context',
                88: 'bcmcs_controller_domain_name_list', 89: 'bcmcs_controller_ipv4_address_option',
                90: 'authentication', 91: 'client_last_transaction_time_option', 92: 'associated_ip_option',
                93: 'client_system', 94: 'client_ndi', 95: 'ldap', 96: 'removed_unassigned', 97: 'uuid_guid',
                98: 'user_auth', 99: 'geoconf_civic', 100: 'pcode', 101: 'tcode', 102: 'removed_unassigned',
                103: 'removed_unassigned', 104: 'removed_unassigned', 105: 'removed_unassigned',
                106: 'removed_unassigned', 107: 'removed_unassigned', 108: 'ipv6_only_preferred',
                109: 'option_dhcp4o6_s46_saddr', 110: 'removed_unassigned', 111: 'unassigned', 112: 'netinfo_address',
                113: 'netinfo_tag', 114: 'dhcp_captive_portal', 115: 'removed_unassigned', 116: 'auto_config',
                117: 'name_service_search', 118: 'subnet_selection_option', 119: 'domain_search',
                120: 'sip_servers_dhcp_option', 121: 'classless_static_route_option', 122: 'ccc', 123: 'geoconf_option',
                124: 'v_i_vendor_class', 125: 'v_i_vendor_specific_information', 126: 'removed_unassigned',
                127: 'removed_unassigned', 128: 'tftp_server_ip_address', 129: 'call_server_ip_address',
                130: 'discrimination_string', 131: 'remote_statistics_server_ip_address', 132: 'ieee_802_1q_vlan_id',
                133: 'ieee_802_1d_p_layer_2_priority',
                134: 'diffserv_code_point__for_voip_signalling_and_media_streams',
                135: 'http_proxy_for_phone_specific_applications', 136: 'option_pana_agent', 137: 'option_v4_lost',
                138: 'option_capwap_ac_v4', 139: 'option_ipv4_address_mos', 140: 'option_ipv4_fqdn_mos',
                141: 'sip_ua_configuration_service_domains', 142: 'option_ipv4_address_andsf',
                143: 'option_v4_sztp_redirect', 144: 'geoloc', 145: 'forcerenew_nonce_capable', 146: 'rdnss_selection',
                147: 'unassigned', 148: 'unassigned', 149: 'unassigned', 150: 'grub_configuration_path_name',
                151: 'status_code', 152: 'base_time', 153: 'start_time_of_state', 154: 'query_start_time',
                155: 'query_end_time', 156: 'dhcp_state', 157: 'data_source', 158: 'option_v4_pcp_server',
                159: 'option_v4_portparams', 160: 'unassigned', 161: 'option_mud_url_v4', 162: 'unassigned',
                163: 'unassigned', 164: 'unassigned', 165: 'unassigned', 166: 'unassigned', 167: 'unassigned',
                168: 'unassigned', 169: 'unassigned', 170: 'unassigned', 171: 'unassigned', 172: 'unassigned',
                173: 'unassigned', 174: 'unassigned', 175: 'etherboot', 176: 'ip_telephone',
                177: 'packetcable_and_cablehome', 178: 'unassigned', 179: 'unassigned', 180: 'unassigned',
                181: 'unassigned', 182: 'unassigned', 183: 'unassigned', 184: 'unassigned', 185: 'unassigned',
                186: 'unassigned', 187: 'unassigned', 188: 'unassigned', 189: 'unassigned', 190: 'unassigned',
                191: 'unassigned', 192: 'unassigned', 193: 'unassigned', 194: 'unassigned', 195: 'unassigned',
                196: 'unassigned', 197: 'unassigned', 198: 'unassigned', 199: 'unassigned', 200: 'unassigned',
                201: 'unassigned', 202: 'unassigned', 203: 'unassigned', 204: 'unassigned', 205: 'unassigned',
                206: 'unassigned', 207: 'unassigned', 208: 'pxelinux_magic', 209: 'configuration_file',
                210: 'path_prefix', 211: 'reboot_time', 212: 'option_6rd', 213: 'option_v4_access_domain',
                214: 'unassigned', 215: 'unassigned', 216: 'unassigned', 217: 'unassigned', 218: 'unassigned',
                219: 'unassigned', 220: 'subnet_allocation_option', 221: 'virtual_subnet_selection_option',
                222: 'unassigned', 223: 'unassigned', 224: 'reserved', 225: 'reserved', 226: 'reserved',
                227: 'reserved', 228: 'reserved', 229: 'reserved', 230: 'reserved', 231: 'reserved', 232: 'reserved',
                233: 'reserved', 234: 'reserved', 235: 'reserved', 236: 'reserved', 237: 'reserved', 238: 'reserved',
                239: 'reserved', 240: 'reserved', 241: 'reserved', 242: 'reserved', 243: 'reserved', 244: 'reserved',
                245: 'reserved', 246: 'reserved', 247: 'reserved', 248: 'reserved', 249: 'reserved', 250: 'reserved',
                251: 'reserved', 252: 'reserved', 253: 'reserved', 254: 'reserved', 255: 'end'}
