#include "TFTP_Server.h"

#include <algorithm>

namespace PXE_Server {

	/*--------------------------------Init_Shut Funcs----------------------------------*/
	TFTP_Server::TFTP_Server()
		: SocketFd(socket(AF_INET, SOCK_STREAM, 0)),
		PortNumber(TFTP_PORT_SERVER),
		BootDir("E:/education/NetworksLab2020/lab3/tftpboot/CentOS/"),
		IsRunning(true)
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
	
	/*--------------------------------Receive Funcs----------------------------------*/
	void TFTP_Server::ReceiveRPQPacket()
	{

	}

	/*--------------------------------Send Funcs----------------------------------*/
	size_t TFTP_Server::WriteUintAsStr(char* Dst, size_t Value)
	{
		size_t tmp = Value;
		size_t i = 0;
		std::string TempString;
		
		while (tmp != 0)
		{
			TempString.push_back((tmp % 10) + 48);
			i++;
			tmp /= 10;
		}
		std::reverse(TempString.begin(), TempString.end());
		for (size_t j = 0; j < TempString.size(); j++)
		{
			Dst[j] = TempString[j];
		}
		return i + 1;
	}

	void TFTP_Server::SendDataLooper(sockaddr_in& cli_addr, std::string& filename)
	{
		
		char buf[OP_DATA_BUFF_LEN];
		bzero(buf, OP_DATA_BUFF_LEN);
		//open file
		
		uint16_t BlockNum = 1;
		bool SendedAck = true;
		size_t CountOfReadedBytes = 1;
		ClientTransferInfo& TransferInfo = ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr];
		
		{
			FILE* fp = fopen((BootDir + filename).c_str(), "rb");
			if (fp == NULL)
			{
				printf("File not found\n");
				buf[1] = OP_ERROR;
				buf[3] = 1; //FILE NOT FOUND ERROR CODE
				strcpy(&buf[4], "File not found");
				TransferInfo.Status = END;
				printf("sendto() ERROR packet to %s:%d\n", inet_ntoa(TransferInfo.cli_addr.sin_addr), ntohs(TransferInfo.cli_addr.sin_port));
				if (sendto(SocketFd, buf, 20, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
				{
					printf("sendto() failed with error code : %d\n", WSAGetLastError());
					return;
				}
				return;
			}
			fseek(fp, 0L, SEEK_END);
			size_t FileSize = ftell(fp);
			TransferInfo.TSizeBytes = FileSize;
			fclose(fp);
		}
		FILE* fp;
		fopen_s(&fp, (BootDir + filename).c_str(), "rb");
		printf("start communicating with %s:%d\n", inet_ntoa(TransferInfo.cli_addr.sin_addr), ntohs(TransferInfo.cli_addr.sin_port));
		while (!feof(fp))
		{
			bzero(buf, OP_DATA_BUFF_LEN);
			if (TransferInfo.Status == FILE_INFO)
			{
				if (TransferInfo.BlockSize == 0)
				{
					size_t SizeToTransfer = 8;
					buf[1] = OP_ACK_ANOTHER;
					strcpy(&buf[2], "tsize");
					SizeToTransfer += WriteUintAsStr(&buf[8], TransferInfo.TSizeBytes);
					TransferInfo.Status = TransferingStatus::WAIT;
					printf("sendto() OP_6 packet to %s:%d with tsize: %d\n", inet_ntoa(TransferInfo.cli_addr.sin_addr), ntohs(TransferInfo.cli_addr.sin_port), TransferInfo.TSizeBytes);
					if (sendto(SocketFd, buf, SizeToTransfer, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
					{
						printf("sendto() failed with error code : %d\n", WSAGetLastError());
						fclose(fp);
						return;
					}
				}
				else if (TransferInfo.BlockSize != 0 && TransferInfo.TSizeBytes == 0)
				{
					size_t SizeToTransfer = 10;
					buf[1] = OP_ACK_ANOTHER;
					strcpy(&buf[2], "blksize");
					SizeToTransfer += WriteUintAsStr(&buf[10], TransferInfo.BlockSize);
					TransferInfo.Status = TransferingStatus::WAIT;
					printf("sendto() OP_6 packet to %s:%d with blcksize: %d\n", inet_ntoa(TransferInfo.cli_addr.sin_addr), ntohs(TransferInfo.cli_addr.sin_port), TransferInfo.BlockSize);
					if (sendto(SocketFd, buf, SizeToTransfer, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
					{
						printf("sendto() failed with error code : %d\n", WSAGetLastError());
						fclose(fp);
						return;
					}
				}
				else if (TransferInfo.BlockSize != 0 && TransferInfo.TSizeBytes != 0)
				{
					size_t SizeToTransfer = 8;
					buf[1] = OP_ACK_ANOTHER;
					strcpy(&buf[2], "tsize");
					SizeToTransfer += WriteUintAsStr(&buf[8], TransferInfo.TSizeBytes);
					strcpy(&buf[SizeToTransfer], "blksize");
					SizeToTransfer += 8;
					SizeToTransfer += WriteUintAsStr(&buf[SizeToTransfer], TransferInfo.BlockSize);
					TransferInfo.Status = TransferingStatus::WAIT;
					printf("sendto() OP_6 packet to %s:%d with tsize: %d, blcksize: %d\n", inet_ntoa(TransferInfo.cli_addr.sin_addr),
						ntohs(TransferInfo.cli_addr.sin_port), TransferInfo.TSizeBytes, TransferInfo.BlockSize);
					if (sendto(SocketFd, buf, SizeToTransfer, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
					{
						printf("sendto() failed with error code : %d\n", WSAGetLastError());
						fclose(fp);
						return;
					}
				}
			}

			if (TransferInfo.Status == DATA)
			{
				buf[1] = OP_DATA;
				//WriteUintAsStr(&buf[2], BlockNum++);
				buf[3] = BlockNum++;
				CountOfReadedBytes = fread((char*)&buf[4], sizeof(char), TransferInfo.BlockSize, fp);
				printf("byte readed: %d with Block Size: %d\n", CountOfReadedBytes, TransferInfo.BlockSize);
				//printf("sendto() OP_DATA packet to %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
				TransferInfo.Status = WAIT;
				if (sendto(SocketFd, buf, 2 + 2 + CountOfReadedBytes, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
				{
					printf("sendto() failed with error code : %d\n", WSAGetLastError());
					fclose(fp);
					return;
				}
			}
		}
		fclose(fp);
		TransferInfo.Status = END;
	}
	
	char* TFTP_Server::DesearilizeString(std::string& Dst, const char* Src)
	{
		size_t StrSize = strlen(Src) + 1;
		Dst.resize(StrSize);
		strcpy((char*)Dst.c_str(), Src);
		return (char*)Src + StrSize;
	}

	size_t TFTP_Server::ReadStrAsUint(char* Src)
	{
		size_t StrSize = strlen(Src);
		size_t Offset = StrSize - 1;
		size_t Value = 0;
		uint8_t DefaultASCIINumberValue = 48u;
		for (size_t i = 0; i < StrSize; i++)
			Value += ((size_t)(Src[i] - DefaultASCIINumberValue)) * pow(10, (Offset - i));
		return Value;
	}

	void TFTP_Server::DesearilizeReadRequest(char* buf, int size, struct sockaddr_in& cli_addr, TFTP_RPQ_WRQ_PACKET& RPQPacket)
	{
		char* Addr = buf;
		char* FinalAddr = buf + size - 1;
		Addr = DesearilizeString(RPQPacket.SourceFile, Addr);
		Addr = DesearilizeString(RPQPacket.Type, Addr);
		
		while (Addr < FinalAddr)
		{
			std::string Option;
			std::string Value;
			Addr = DesearilizeString(Option, Addr);
			Addr = DesearilizeString(Value, Addr);
			if (Option[0] == 't')
			{
				RPQPacket.NeedTsize = true;
			}
			else if (Option[0] == 'b')
			{
				RPQPacket.Blcksize = ReadStrAsUint((char*)Value.c_str());
			}
		}
	}

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

		while (IsRunning)
		{
			memset((void*)buf, '\0', BUFLEN);
			recv_len = recvfrom(SocketFd, buf, BUFLEN, 0, (struct sockaddr*)&cli_addr, &clilen);
			if (recv_len == SOCKET_ERROR)
			{
				printf("Received packet from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
				printf("recvfrom() failed with error code : %d\n", WSAGetLastError());
				IsRunning = false;
				exit(EXIT_FAILURE);
			}
			printf("Received packet from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
			
			switch (buf[1])
			{
			case OP_RPQ:
			{
				TFTP_RPQ_WRQ_PACKET RPQPacket;
				DesearilizeReadRequest(&buf[2], recv_len, cli_addr, RPQPacket);
				//if present change blcksize value and status
				if (ClientsAddrBytesMap.find(cli_addr.sin_addr.S_un.S_addr) != ClientsAddrBytesMap.end())
				{
					if (ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status != END)
					{
						if (RPQPacket.Blcksize != 0)
							ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].BlockSize = RPQPacket.Blcksize;
						if (RPQPacket.NeedTsize == true)
							ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].NeedTsize = true;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].cli_addr = cli_addr;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = TransferingStatus::FILE_INFO;
					}
					else
					{
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].BlockSize = RPQPacket.Blcksize;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].cli_addr = cli_addr;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].NeedTsize = RPQPacket.NeedTsize;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = TransferingStatus::FILE_INFO;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].TSizeBytes = 0;
						size_t ThreadId = ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].ThreadId;
						ThreadPool[ThreadId].detach();
						ThreadPool[ThreadId] = std::thread(&PXE_Server::TFTP_Server::SendDataLooper, this, cli_addr, RPQPacket.SourceFile);
					}
					
				}
				else
				{
					if (ThreadPool.size() < 3)
					{
						//Add new
						ClientsAddrBytesMap.emplace(cli_addr.sin_addr.S_un.S_addr, ClientTransferInfo{});
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].cli_addr = cli_addr;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = TransferingStatus::FILE_INFO;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].ThreadId = ThreadPool.size();
						ThreadPool.push_back(std::thread(&PXE_Server::TFTP_Server::SendDataLooper, this, cli_addr, RPQPacket.SourceFile));
					}
					else
					{
						//try to free place in pool
						for (auto it : ClientsAddrBytesMap)
						{
							if (it.second.Status == TransferingStatus::END)
							{
								size_t ThreadId = ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].ThreadId;
								ClientsAddrBytesMap.erase(it.first);
								ClientsAddrBytesMap.emplace(cli_addr.sin_addr.S_un.S_addr, ClientTransferInfo{});
								ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].cli_addr = cli_addr;
								ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = TransferingStatus::FILE_INFO;
								ThreadPool[ThreadId] = std::thread(&PXE_Server::TFTP_Server::SendDataLooper, this, cli_addr, RPQPacket.SourceFile);
								break;
							}
						}
					}
				}
			} break; //Client want some info about file
			case OP_ACK:
			{
				printf("ACK packet from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
				if (ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status == WAIT)
					ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = TransferingStatus::DATA;
			} break;  //Client want to start transfering
			case OP_ERROR:
			{
				
			} break;                   //Client has an error in transfering
			}
		}
	}
}

int main()
{
	PXE_Server::TFTP_Server Server;
	Server.Run();
	return 1;
}