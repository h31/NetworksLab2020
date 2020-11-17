#pragma once

#ifdef WinSockApp
#include "WindowsLib.h"
#endif
#ifdef UnixSockApp
#include "UnixLib.h"
#endif

namespace PXE_Server {

//
#define TFTP_PORT_SERVER 69

//TFTP Message Type 
#define OP_RPQ   0x01 //Read Request
#define OP_WRQ   0x02 //Write Request
#define OP_DATA  0x03 //Data Request
#define OP_ACK   0x04 //Acknowledgment 
#define OP_ERROR 0x05 //Error

//Buffer Size
#define BUFLEN 2048

/*------------------------------TFTP Packet Structures---------------------------------*/
//for rpq and wrq packets
#pragma pack(push, 1) //push current value of pack to stack to prevent conflicts
	struct TFTP_RPQ_WRQ_PACKET
	{
		uint16_t Opcode; //Type of packet
		std::string Data;
		char Oktet[6] = { 'o', 'k', 't', 'e', 't', '\0' };
		std::string Name;
		char Value[5];
		//Option Name
		//Option Value
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

		void ReceiveRPQPacket();
		void ReceuveACKPacket();

		void SendRPQReply();
		void SendData();

	private:
		SOCKET SocketFd;
		uint16_t PortNumber;
		std::string BootDir;
	};
};