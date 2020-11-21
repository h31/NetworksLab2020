#include "TFTP_Server.h"

#include <algorithm>

namespace PXE_Server {

	/*--------------------------------Init_Shut Funcs----------------------------------*/
	TFTP_Server::TFTP_Server()
		: SocketFd(socket(AF_INET, SOCK_STREAM, 0)),
		PortNumber(TFTP_PORT_SERVER),
		BootDir("E:/education/NetworksLab2020/lab3/tftpboot/Windows/"),
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

	size_t TFTP_Server::GetFileSize(std::string& Filename)
	{
		FILE* fp;
		fp = fopen((BootDir + Filename).c_str(), "rb");
		if (fp == NULL)
			return 0;
		fseek(fp, 0L, SEEK_END);
		size_t FileSize = ftell(fp);
		fclose(fp);
		return FileSize;
	}

	void TFTP_Server::SendNotFoundError(struct sockaddr_in& cli_addr)
	{
		char buf[OP_FILE_INFO_BUFF_LEN];
		bzero(buf, OP_FILE_INFO_BUFF_LEN);
		printf("File %s not found\n", ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].filename.c_str());
		buf[1] = OP_ERROR;
		buf[3] = 1; //FILE NOT FOUND ERROR CODE
		strcpy(&buf[4], "File not found");
		printf("sendto() ERROR packet to %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
		if (sendto(SocketFd, buf, 20, 0, (struct sockaddr*)&cli_addr, sizeof(cli_addr)) < 0)
		{
			printf("sendto() ERROR packet failed with error code : %d\n", WSAGetLastError());
			return;
		}
		return;
	}

	void TFTP_Server::SendFileInfo(sockaddr_in& cli_addr, bool IsTsizeNeed)
	{
		char buf[OP_FILE_INFO_BUFF_LEN];
		bzero(buf, OP_FILE_INFO_BUFF_LEN);
		ClientTransferInfo& TransferInfo = ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr];
		std::string& filename = TransferInfo.filename;

		TransferInfo.TSizeBytes = GetFileSize(filename);
		if (TransferInfo.TSizeBytes == FILE_NOT_FOUND)
		{
			SendNotFoundError(cli_addr);
			return;
		}

		if (TransferInfo.BlockSize == 0)
		{
			size_t SizeToTransfer = 8;
			buf[1] = OP_ACK_ANOTHER;
			strcpy(&buf[2], "tsize");
			SizeToTransfer += WriteUintAsStr(&buf[8], TransferInfo.TSizeBytes);
			printf("sendto() OP_RPQ_ACK packet to %s:%d with tsize: %d\n", inet_ntoa(TransferInfo.cli_addr.sin_addr), ntohs(TransferInfo.cli_addr.sin_port), TransferInfo.TSizeBytes);
			if (sendto(SocketFd, buf, SizeToTransfer, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
			{
				printf("sendto() failed with error code : %d\n", WSAGetLastError());
				return;
			}
		}
		else if (!IsTsizeNeed && TransferInfo.BlockSize != 0)
		{
			size_t SizeToTransfer = 10;
			buf[1] = OP_ACK_ANOTHER;
			strcpy(&buf[2], "blksize");
			SizeToTransfer += WriteUintAsStr(&buf[10], TransferInfo.BlockSize);
			printf("sendto() OP_RPQ_ACK packet to %s:%d with blcksize: %d\n", inet_ntoa(TransferInfo.cli_addr.sin_addr), ntohs(TransferInfo.cli_addr.sin_port), TransferInfo.BlockSize);
			if (sendto(SocketFd, buf, SizeToTransfer, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
			{
				printf("sendto() failed with error code : %d\n", WSAGetLastError());
				return;
			}
		}
		else
		{
			size_t SizeToTransfer = 8;
			buf[1] = OP_ACK_ANOTHER;
			strcpy(&buf[2], "tsize");
			SizeToTransfer += WriteUintAsStr(&buf[8], TransferInfo.TSizeBytes);
			strcpy(&buf[SizeToTransfer], "blksize");
			SizeToTransfer += 8;
			SizeToTransfer += WriteUintAsStr(&buf[SizeToTransfer], TransferInfo.BlockSize);
			printf("sendto() OP_RPQ_ACK packet to %s:%d with tsize: %d, blcksize: %d\n", inet_ntoa(TransferInfo.cli_addr.sin_addr),
				ntohs(TransferInfo.cli_addr.sin_port), TransferInfo.TSizeBytes, TransferInfo.BlockSize);
			if (sendto(SocketFd, buf, SizeToTransfer, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
			{
				printf("sendto() failed with error code : %d\n", WSAGetLastError());
				return;
			}
		}
	}

	void TFTP_Server::SendDataLooper(sockaddr_in& cli_addr)
	{
		char buf[OP_DATA_BUFF_LEN];
		bzero(buf, OP_DATA_BUFF_LEN);
		char PrevBuf[OP_DATA_BUFF_LEN];
		bzero(PrevBuf, OP_DATA_BUFF_LEN);
		//open file
		uint16_t BlockNum = 1;
		bool SendedAck = true;
		size_t CountOfReadedBytes = 1;
		size_t PrevCountOfReadedBytes = 1;
		ClientTransferInfo& TransferInfo = ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr];
		FILE* fp;
		fopen_s(&fp, (BootDir + TransferInfo.filename).c_str(), "rb");
		printf("start communicating with %s:%d with file: %s\n", inet_ntoa(TransferInfo.cli_addr.sin_addr), ntohs(TransferInfo.cli_addr.sin_port), TransferInfo.filename.c_str());
		do
		{
			bzero(buf, OP_DATA_BUFF_LEN);
			if (TransferInfo.Status == SEND_AGAIN)
			{
				std::unique_lock Locker(Mutex);
				if (sendto(SocketFd, PrevBuf, 2 + 2 + PrevCountOfReadedBytes, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
				{
					printf("sendto() failed with error code : %d\n", WSAGetLastError());
					fclose(fp);
					return;
				}
				TransferInfo.Status = WAIT;
			}
			else if (TransferInfo.Status == DATA)
			{
				std::unique_lock Locker(Mutex);
				buf[1] = OP_DATA;
				buf[2] = BlockNum >> 8;
				buf[3] = BlockNum & 0xff;
				//copy prev buffer context
				memcpy(PrevBuf, buf, OP_DATA_BUFF_LEN);
				PrevCountOfReadedBytes = CountOfReadedBytes;
				//read new block
				CountOfReadedBytes = fread((char*)&buf[4], sizeof(char), TransferInfo.BlockSize, fp);
				//printf("DATA packet to  %s:%d Block Number is %d, bytes %d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), BlockNum, CountOfReadedBytes);
				TransferInfo.BlockNumData = ++BlockNum;
				TransferInfo.Status = WAIT;
				if (sendto(SocketFd, buf, 2 + 2 + CountOfReadedBytes, 0, (struct sockaddr*)&TransferInfo.cli_addr, sizeof(TransferInfo.cli_addr)) < 0)
				{
					printf("sendto() failed with error code : %d\n", WSAGetLastError());
					fclose(fp);
					return;
				}
			}
		} while (!feof(fp));
		std::unique_lock Locker(Mutex);
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
		uint16_t BlockAckNum = 0;
		//prepare buffer for recv and sen, socket for accepting
		char buf[OP_RPQ_BUFF_LEN];
		int recv_len = 0;
		struct sockaddr_in cli_addr;
		int clilen = sizeof(cli_addr);
		ThreadPool.reserve(MAX_THREAD_POOL_SIZE);

		while (IsRunning)
		{
			bzero(buf, OP_RPQ_BUFF_LEN);
			recv_len = recvfrom(SocketFd, buf, OP_RPQ_BUFF_LEN, 0, (struct sockaddr*)&cli_addr, &clilen);
			if (recv_len == SOCKET_ERROR)
			{
				printf("Received packet from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
				printf("recvfrom() failed with error code : %d\n", WSAGetLastError());
				IsRunning = false;
				exit(EXIT_FAILURE);
			}
			
			switch (buf[1])
			{
			case OP_RPQ:
			{
				printf("RPQ packet from %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
				TFTP_RPQ_WRQ_PACKET RPQPacket;
				DesearilizeReadRequest(&buf[2], recv_len, cli_addr, RPQPacket);
				std::unique_lock Locker(Mutex);
				//if present change blcksize value and status
				if (ClientsAddrBytesMap.find(cli_addr.sin_addr.S_un.S_addr) != ClientsAddrBytesMap.end())
				{
					ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].cli_addr = cli_addr;
					ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].BlockSize = RPQPacket.Blcksize;
					ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].filename = RPQPacket.SourceFile;
					if (RPQPacket.NeedTsize) SendFileInfo(cli_addr, NEED_TSIZE);
					else                     SendFileInfo(cli_addr, NOT_NEED_TSIZE);
				}
				else
				{
					if (ThreadPool.size() < MAX_THREAD_POOL_SIZE)
					{
						//Add new
						ClientsAddrBytesMap.emplace(cli_addr.sin_addr.S_un.S_addr,
							ClientTransferInfo {cli_addr, 0, 0, -1, 1, RPQPacket.SourceFile, TransferingStatus::END});
						if (RPQPacket.NeedTsize == true) SendFileInfo(cli_addr, NEED_TSIZE);
						else SendFileInfo(cli_addr, NOT_NEED_TSIZE);
					}
					else
					{
						//try to free place in pool
						for (auto it : ClientsAddrBytesMap)
						{
							if (it.second.Status == TransferingStatus::END)
							{
								int16_t ThreadId = it.second.ThreadId;
								ClientsAddrBytesMap.erase(it.first);
								ClientsAddrBytesMap.emplace(cli_addr.sin_addr.S_un.S_addr, ClientTransferInfo
									{cli_addr, 0, 0, ThreadId, 1, RPQPacket.SourceFile, END});
								break;
							}
						}
					}
				}
			} break; //Client want some info about file
			case OP_ACK:
			{
				std::unique_lock Locker(Mutex);
				BlockAckNum = ((unsigned char)buf[2] << 8) | (unsigned char)buf[3];
				if (BlockAckNum == 0)
				{
					if (ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status != END)
					{
						printf("Looping %s:%d\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = DATA;
					}
					else
					{
						//Start Data Transfering Thread
						int16_t ThreadId = ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].ThreadId;
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].BlockNumData = 1;
						if (ThreadId == -1)
						{
							ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].ThreadId = ThreadPool.size();
							ThreadPool.emplace_back(std::thread(&PXE_Server::TFTP_Server::SendDataLooper, this, cli_addr));
							ThreadId = ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].ThreadId;
						}
						else
						{
							ThreadPool[ThreadId].detach();
							ThreadPool[ThreadId] = std::thread(&PXE_Server::TFTP_Server::SendDataLooper, this, cli_addr);
						}

						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = TransferingStatus::DATA;
					}
				}
				else
				{
					uint16_t BlockDataNum = ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].BlockNumData - 1;
					if (BlockDataNum < 0) BlockDataNum = 0;

					if (BlockAckNum - BlockDataNum > 0)
						printf("WRONG BlockAckNum: %d, BlockDataNum: %d, delta %d\n", BlockAckNum, BlockDataNum, BlockAckNum - BlockDataNum);
					if (BlockAckNum < BlockDataNum)
					{
						printf("Need to send data again to %s:%d with block number %u\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), BlockAckNum);
						ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = SEND_AGAIN;
					}
					else
					{
						//printf("ACK packet from %s:%d Block number is %u\n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), BlockAckNum);
						if (ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status == WAIT)
							ClientsAddrBytesMap[cli_addr.sin_addr.S_un.S_addr].Status = TransferingStatus::DATA;
					}
				}
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