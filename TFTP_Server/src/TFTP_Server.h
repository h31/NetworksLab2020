#pragma once

#ifdef WinSockApp
#include "WindowsLib.h"
#endif
#ifdef UnixSockApp
#include "UnixLib.h"
#endif

#include <unordered_map>
#include <thread>
#include <mutex>

namespace PXE_Server {

//
#define TFTP_PORT_SERVER 69

//TFTP Message Type 
#define OP_RPQ   0x01 //Read Request
#define OP_WRQ   0x02 //Write Request
#define OP_DATA  0x03 //Data Request
#define OP_ACK   0x04 //Acknowledgment 
#define OP_ERROR 0x05 //Error
#define OP_ACK_ANOTHER 0x06

//Buffer Size
#define BUFLEN 2048
#define OP_DATA_BUFF_LEN 2 + 2 + 2048 //Opcode + Block Number + Data Part

#define MAX_THREAD_POOL_SIZE 2

	enum TransferingStatus
	{
		WAIT      =  0,
		DATA      =  1,
		FILE_INFO =  2,
		END       =  3
	};

	struct ClientTransferInfo
	{
		struct sockaddr_in cli_addr;
		size_t ThreadId          = 0;
		size_t BlockSize         = 0;
		size_t TSizeBytes        = 0;
		bool NeedTsize           = false;
		TransferingStatus Status = TransferingStatus::WAIT;
	};

/*------------------------------TFTP Packet Structures---------------------------------*/
//for rpq and wrq packets
#pragma pack(push, 1) //push current value of pack to stack to prevent conflicts
	struct TFTP_RPQ_WRQ_PACKET
	{
		uint16_t Opcode; //Type of packet
		std::string SourceFile;
		std::string Type;
		bool NeedTsize = false;
		size_t Blcksize = 0;
	};
#pragma pack(pop) //pop current value of pack from stack to prevent conflicts

//For data packets
#pragma pack(push, 1) //push current value of pack to stack to prevent conflicts
	struct TFTP_DATA_PACKET
	{
		uint16_t Opcode = 3; //Type of packet
		uint16_t Block;
		std::string Data;
	};
#pragma pack(pop) //pop current value of pack from stack to prevent conflicts

//for acknoweledgment packets
#pragma pack(push, 1) //push current value of pack to stack to prevent conflicts
	struct TFTP_ACK_PACKET
	{
		uint16_t Opcode; //Type of packet
		uint16_t Block;
	};
#pragma pack(pop) //pop current value of pack from stack to prevent conflicts

//for error packets
#pragma pack(push, 1) //push current value of pack to stack to prevent conflicts
	struct TFTP_ERROR_PACKET
	{
		uint16_t Opcode; //Type of packet
		uint16_t Block;
		std::string ErrorMessage;
	};
#pragma pack(pop) //pop current value of pack from stack to prevent conflicts
/*------------------------------TFTP Packet Structures---------------------------------*/

	class TFTP_Server
	{
	public:
		TFTP_Server();
		~TFTP_Server();

		void Run();

	private:
		bool Initialize();

		char* DesearilizeString(std::string& Dst, const char* Src);
		void DesearilizeReadRequest(char* buf, int size, struct sockaddr_in& cli_addr, TFTP_RPQ_WRQ_PACKET& RPQPacket);
		
		size_t ReadStrAsUint(char* Src);
		size_t WriteUintAsStr(char* Dst, size_t Value);

		void SendDataLooper(struct sockaddr_in& cli_addr, std::string& filename);

		void ReceiveRPQPacket();

	private:
		SOCKET SocketFd;
		uint16_t PortNumber;
		std::string BootDir;
		bool IsRunning;
		//Client Ip Addr and Least bytes to transfer
		std::unordered_map<u_long, ClientTransferInfo> ClientsAddrBytesMap;
		std::mutex Mutex;
		std::vector<std::thread> ThreadPool;
	};
};