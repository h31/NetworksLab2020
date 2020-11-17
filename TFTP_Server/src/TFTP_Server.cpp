#include "TFTP_Server.h"

#include <DhcpCSdk.h>

namespace PXE_Server {

	/*--------------------------------Init_Shut Funcs----------------------------------*/
	TFTP_Server::TFTP_Server()
		: SocketFd(socket(AF_INET, SOCK_STREAM, 0)), PortNumber(TFTP_PORT_SERVER), BootDir("E:/education/NetworksLab2020/lab3/tftpboot")
	{
		InitializeWinSock2();
	}

	bool TFTP_Server::Initialize()
	{
		SocketFd = socket(AF_INET, SOCK_DGRAM, 0);
		if (SocketFd < 0)
		{
			perror("ERROR opening socket");
			return false;
		}

		struct sockaddr_in ServerAddress;
		bzero((char*)&ServerAddress, sizeof(ServerAddress));
		ServerAddress.sin_family = AF_INET;
		ServerAddress.sin_addr.s_addr = inet_addr("192.168.56.1");
		ServerAddress.sin_port = htons(PortNumber); //port
		return bind(SocketFd, (struct sockaddr*)&ServerAddress, sizeof(ServerAddress)) < 0;
	}

	TFTP_Server::~TFTP_Server()
	{
		//close socket
		closesocket(SocketFd);
		//Cleanup winsock
		WSACleanup();
	}
	/*--------------------------------Init_Shut Funcs----------------------------------*/


	/*--------------------------------Send Funcs----------------------------------*/
	void TFTP_Server::SendRPQReply()
	{
		//send reply to request and start transfering
	}

	void TFTP_Server::SendData()
	{
		//while file not end
		//sendto
		//
	}
	/*--------------------------------Send Funcs----------------------------------*/


	/*--------------------------------Main----------------------------------*/
	void TFTP_Server::Run()
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

			uint16_t MessageType = 0;
			memcpy(&MessageType, &buf[0], 2);
			switch (MessageType)
			{
			case OP_RPQ   : SendRPQReply(); break; //send write request
			case OP_WRQ   : break; //Cant write to server
			case OP_DATA  : break; //Cant write to server
			case OP_ACK   : break; //Cant write to server
			case OP_ERROR : break; //TODO ERROR 
			}

			printf("Received packet from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
		}
	}
}

int main()
{
	PXE_Server::TFTP_Server Server;
	Server.Run();
	return 1;
}