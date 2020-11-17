#include "DHCP_Server.h"

#include <DhcpCSdk.h>
#include <fstream>
#include <sstream>
#include <vector>

namespace PXE_Server {

	/*
	SOCK_STREAM     1               stream socket 
	SOCK_DGRAM      2               datagram socket 
	SOCK_RAW        3               raw-protocol interface 
	SOCK_RDM        4               reliably-delivered message 
	SOCK_SEQPACKET  5               sequenced packet stream 
	*/
	DHCP_Server::DHCP_Server()
		: SocketFd(0), PortNumber(BOOTP_SERVER_PORT_NUM)
	{
		InitializeWinSock2();
	}

	void DHCP_Server::ParseAddrToBytes(char* resultBuf, std::string& strAddr)
	{
		std::vector<std::string> tokens;
		std::stringstream lineStream(strAddr);
		for (std::string each; std::getline(lineStream, each, '.'); tokens.push_back(each));
		for (size_t i = 0; i < 4; i++)
		{
			resultBuf[i] = std::stoi(tokens[i]);
		}
	}

	void DHCP_Server::ParseConfig()
	{
		const std::string config_path("E:/education/NetworksLab2020/lab3/DHCP_Server/cfg/dhcp.conf");
		std::ifstream ifs(config_path);
		if (!ifs.is_open())
			printf("Config could not be opened\n");

		std::vector<std::string> tokens;
		for (std::string line; std::getline(ifs, line, '\n');)
		{
			std::stringstream lineStream(line);
			for (std::string each; std::getline(lineStream, each, ':'); tokens.push_back(each));
		}

		for (size_t i = 0; i < tokens.size(); i += 2)
		{
			if (tokens[i] == "dhcp-ip")
			{
				Config.MyIp = tokens[i + 1];
				ParseAddrToBytes((char*)&Config.DHCPIp[0], tokens[i + 1]);
			}
			else if (tokens[i] == "subnet-ip")
				ParseAddrToBytes((char*)&Config.RouterIp[0], tokens[i + 1]);
			else if (tokens[i] == "subnet-mask")
				ParseAddrToBytes((char*)&Config.SubnetMask[0], tokens[i + 1]);
			else if (tokens[i] == "file-name")
				Config.Filename   = tokens[i + 1];
			else if (tokens[i] == "tftp-ip")
				ParseAddrToBytes((char*)&Config.TFTPIp[0], tokens[i + 1]);
			else if (tokens[i] == "router-ip")
				ParseAddrToBytes((char*)&Config.RouterIp[0], tokens[i + 1]);
		}
	}

	bool DHCP_Server::Initialize()
	{
		ParseConfig();
		SocketFd = socket(AF_INET, SOCK_DGRAM, 0);
		if (SocketFd < 0)
		{
			perror("ERROR opening socket");
			return false;
		}
		char broadcast = '1';
		if (setsockopt(SocketFd, SOL_SOCKET, SO_BROADCAST, &broadcast, sizeof(broadcast)) < 0)
		{
			closesocket(SocketFd);
			return false;
		}
		struct sockaddr_in ServerAddress;
		bzero((char*)&ServerAddress, sizeof(ServerAddress));
		ServerAddress.sin_family      = AF_INET; 
		ServerAddress.sin_addr.s_addr = inet_addr(Config.MyIp.c_str()); //IP addr
		ServerAddress.sin_port        = htons(PortNumber);                //port
		return bind(SocketFd, (struct sockaddr*)&ServerAddress, sizeof(ServerAddress)) < 0;
	}

	DHCP_Server::~DHCP_Server()
	{
		//close socket
		closesocket(SocketFd);
		//Cleanup winsock
		WSACleanup();
	}

	uint8_t DHCP_Server::RecieveRequest(const char* buf, char* BootpRequestData)
	{
		memcpy(&BootpRequestData[0], &buf[0], 236);

		const char CheckDHCPStart[4] = { 0x63, 0x82, 0x53, 0x63 };
		if (buf[236] == CheckDHCPStart[0] && buf[237] == CheckDHCPStart[1] && buf[238] == CheckDHCPStart[2] && buf[239] == CheckDHCPStart[3])
		{
			size_t i = 240;
			uint8_t DHCPMessageType = 0;
			//Start Reading DHCP Options 
			while (buf[i] != 255)
			{
				unsigned char option = buf[i++];
				int length = buf[i++];

				switch (option)
				{
				case Option_053: DHCPMessageType = buf[i]; break;// (*DHCPOfferData).DHCPMessageType = buf[i]; break;
				case Option_055: break;
				case Option_057: break;
				case Option_097: break;
				case Option_093: break;
				case Option_094: break;
				case Option_060: break;
				case Option_255: return DHCPMessageType;
				}
				i += length;
			}
			return DHCPMessageType;
		}

		//TODO CHECK FOR VENDOR INFO OR START DHCP OPTIONS
		//memcpy(&BootpRequestData[236], &buf[236], 64);
	}

	/*---------------------------------------------Send Function--------------------------------------------------*/
	void DHCP_Server::SendReply(DHCPMessageType MessageType, BOOTPPacket& BootpRequestData)
	{
		char BufReply[BUFLEN];
		bzero(BufReply, BUFLEN);
		BOOTPPacket BOOTPReplyData;
		bzero(&BOOTPReplyData.ServerHostName[0], 64);
		bzero(&BOOTPReplyData.BootFilename, 128);
		memcpy(&BOOTPReplyData.TransactionID[0], &BootpRequestData.TransactionID[0], 4);
		memcpy(&BOOTPReplyData.ClientMacAddress[0], &BootpRequestData.ClientMacAddress[0], 6);
		//copy data to buffer
		char* BootReplyPtr = (char*)&BOOTPReplyData;
		memcpy(&BufReply[0], &BootReplyPtr[0], 236);
		{
			const char CheckDHCPStart[4] = { 0x63, 0x82, 0x53, 0x63 };
			memcpy(&BufReply[236], &CheckDHCPStart[0], 4); //Write DHCP MAGIC COOKIE
		}
		size_t i = 240;
		//Option 53 - Message Type
		BufReply[i++] = Option_053;
		BufReply[i++] = 1;
		BufReply[i++] = MessageType;
		//Option 54 - Server Identifier
		BufReply[i++] = Option_054;
		BufReply[i++] = 4;
		memcpy((void*)&BufReply[i], (const void*)&Config.DHCPIp[0], 4);
		i += 4;
		//Option 51 - Lease Time
		BufReply[i++] = Option_051;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], &Config.LeaseTime[0], 4);
		i += 4;
		//Option 1 = Subnet Mask
		BufReply[i++] = Option_001;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], &Config.SubnetMask[0], 4);
		i += 4;
		//Option 3 - Router
		BufReply[i++] = Option_003;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], &Config.RouterIp[0], 4);
		i += 4;
		//Option 6 - DNS
		BufReply[i++] = Option_006;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], (const char*)&Config.DNS[0], 4);
		i += 4;
		//Option 66 - TFTP
		BufReply[i++] = Option_066;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], &Config.TFTPIp[0], 4); //Boot Filenam
		i += 4;
		//Option 67 - BOOTFILENAME
		BufReply[i++] = Option_067;
		BufReply[i++] = 21;
		strncpy(&BufReply[i], (const char*)&Config.BootFilename[0], 21); //Boot Filenam
		i += 21;
		//Option 44 - NetBios Over TcpIp Name Server
		BufReply[i++] = Option_044;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], (const char*)&Config.DNS[0], 4); //Boot Filenam
		i += 4;
		//Option 58 - Renewal Time Value
		BufReply[i++] = Option_058;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], &Config.RenewalTimeValue[0], 4);
		i += 4;
		//Option 59 - Rebinding Time Value
		BufReply[i++] = Option_059;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], &Config.RebindingTimeValue[0], 4);
		i += 4;
		//Option 7 - Log Server
		BufReply[i++] = Option_007;
		BufReply[i++] = 4;
		memcpy(&BufReply[i], &Config.LogServer[0], 4);
		i += 4;
		BufReply[i] = OPTION_END;

		struct sockaddr_in BroadcastResponseAddress;
		bzero((char*)&BroadcastResponseAddress, sizeof(BroadcastResponseAddress));
		BroadcastResponseAddress.sin_family      = AF_INET;
		BroadcastResponseAddress.sin_addr.s_addr = inet_addr("255.255.255.255");
		BroadcastResponseAddress.sin_port        = htons(BOOTP_CLIENT_PORT_NUM);

		if (sendto(SocketFd, BufReply, 547, 0, (sockaddr*)&BroadcastResponseAddress, sizeof(BroadcastResponseAddress)) < 0)
		{
			printf("sendto() failed with error code : %d\n", WSAGetLastError());
		}
	}

	/*---------------------------------------------Main Function--------------------------------------------------*/
	void DHCP_Server::Run()
	{
		bool WasErrorInInit = Initialize();
		if (WasErrorInInit)
		{
			printf("error in initializing\n");
			return;
		}
		//prepare buffer for recv and sen, socket for accepting
		char buf[BUFLEN];
		int recv_len = 0;
		struct sockaddr_in cli_addr;
		int clilen = sizeof(cli_addr);

		while (true)
		{
			memset((void*)buf, '\0', BUFLEN);
			recv_len = recvfrom(SocketFd, buf, BUFLEN, 0, (struct sockaddr*)&cli_addr, &clilen);
			if (recv_len == SOCKET_ERROR)
			{
				printf("Received packet from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
				printf("recvfrom() failed with error code : %d\n", WSAGetLastError());
				exit(EXIT_FAILURE);
			}

			if (buf[0] == BOOTPRequest)
			{
				//Parse Bootp Packet
				BOOTPPacket BootpRequestData;
				uint8_t DHCPMessageType = RecieveRequest(&buf[0], &(BootpRequestData.BootTypeMessage));
				switch (DHCPMessageType)
				{
				case DHCPDiscover: 
				{
					printf("DHCP Discover message from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
					SendReply(DHCPMessageType::DHCPOffer, BootpRequestData);
				} break;
				case DHCPRequest: 
				{
					printf("DHCP Request message from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
					SendReply(DHCPMessageType::DHCPAck, BootpRequestData);
				} break; 
				}
			}
		}
	}
}

int main()
{
	PXE_Server::DHCP_Server Server;
	Server.Run();
	return 1;
}