#pragma once

#ifdef WinSockApp
	#include "WindowsLib.h"
#endif
#ifdef UnixSockApp
	#include "UnixLib.h"
#endif

#include <unordered_map>

namespace PXE_Server {

#define BUFLEN 577 + 301	//Max length of DHCP packet is 576 bytes 

/*---------------BOOTP SECTION----------------*/

#define BOOTP_SERVER_PORT_NUM 67
#define BOOTP_CLIENT_PORT_NUM 68

//Bootp Message Type
#define BOOTPRequest 1
#define BOOTPReply   2

//Hardware Types
#define Hardware_Ethernet_Type 0x01

//Bootp Packet size
#define Bootp_Minimum_Size 236
#define Bootp_Maximum_Size 299

/*--------------------End---------------------*/

/*---------------DHCP SECTION----------------*/

//DHCP MESSAGE TYPES
	enum DHCPMessageType  
	{                     
		DHCPDiscover = 1, //Dynamic Host Configuration Protocol (DHCP) Discover message 
		DHCPOffer    = 2, //Dynamic Host Configuration Protocol (DHCP) Offer message 
		DHCPRequest  = 3, //Dynamic Host Configuration Protocol (DHCP) Request message
		DHCPDecline  = 4, //Dynamic Host Configuration Protocol (DHCP) Decline message
		DHCPAck      = 5, //Dynamic Host Configuration Protocol (DHCP) Acknowledgment message
		DHCPNak      = 6, //Dynamic Host Configuration Protocol (DHCP) Negative Acknowledgment message
		DHCPRelease  = 7, //Dynamic Host Configuration Protocol (DHCP) Release message
		DHCPInform   = 8  //Dynamic Host Configuration Protocol (DHCP) Informational message
	};

//options
#define Option_001 0x01 //Subnet Mask
#define Option_003 0x03 //Router
#define Option_006 0x06 //Domain Name Server
#define Option_007 0x07 //Log Server
#define Option_044 0x2c //
#define Option_051 0x33 //Ip Address Lease Time
#define Option_053 0x35 //Message Type
#define Option_054 0x36 //Server Identifier
#define Option_055 0x37 //Parametr Request List [Length(1 byte) - Option Numbers(1 byte each option num)]
#define Option_057 0x39 //Maximum DHCP Message Size
#define Option_058 0x3a //Renewal Time Value
#define Option_059 0x3b //Rebinding Time Value
#define Option_060 0x1c //Vendor Class Identifier
#define Option_066 0x42 //TFTP Name
#define Option_067 0x43 //Boot Filename
#define Option_093 0x5d //Client System Architecture
#define Option_094 0x5e //Client Network Device Interface
#define Option_097 0x61 //Vendor Class Interface
#define Option_255 0xff //End

/*-------------------End--------------------*/

	#pragma pack(push, 1) //push current value of pack to stack to prevent conflicts
	struct BOOTPPacket
	{
		char BootTypeMessage               = BOOTPReply;                       //0 byte
		char HardwareType                  = 6;                                //1 byte
		char HardwareAddrLength            = 0;                                //2 byte
		char HopCount                      = 0;                                //3 byte
		char TransactionID[4]              = { 0, 0, 0, 0 };                   //4 - 7 bytes
		char SecondElapsed[2]              = { 0, 0 };                         //8 - 9 bytes
		unsigned char BootpFlags[2]        = { 0x80, 0 };                      //10 - 11 bytes
		unsigned char ClientIpAddress[4]   = { 0, 0, 0, 0 };                   //12 - 15
		unsigned char YourIpAddr[4]        = { 192, 168, 56, 2 };                   //16 - 19
		unsigned char NextIpAddress[4]              = { 192, 168, 56, 1 };                   //20 - 23
		char RelayAgentIpAddress[4]        = { 0, 0, 0, 0 };                   //24 - 27
		char ClientMacAddress[6]           = { 0, 0, 0, 0, 0, 0 };             //28 - 33
		char ClientHardwareAddrPadding[10] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }; //34 - 43
		char ServerHostName[64];                                               // 44 - 107 bytes
		char BootFilename[128];                                                //108 - 235 bytes
		char VendorSpecificInfromation[64];                                    // 236 - 299 bytes
	};
	#pragma pack(pop) //pop current value of pack from stack to prevent conflicts

	struct DHCP_Config
	{
		std::string MyIp;
		std::string Filename;
		unsigned char StartIp[4]            = { 192, 168, 0, 201};
		unsigned char DHCPIp[4]             = { 0, 0, 0, 0 };           //Option 54
		unsigned char RouterIp[4]           = { 192, 168, 0, 1 };       //Option 3
		unsigned char SubnetMask[4]         = { 255, 255, 255, 0 };     //Option 1
		unsigned char TFTPIp[4]             = { 192, 168, 0, 200 };     //Option 66
		         char BootFilename[21]      = "pxeboot.n12\0";  //Option 67
		unsigned char LeaseTime[4]          = { 0,  0, 0x1c, 0x20 };    //Option 51
		unsigned char DNS[4]                = { 8, 8, 8, 8 };           //Option 6, 44 
		unsigned char RenewalTimeValue[4]   = { 0, 0x01, 0x51, 0x80 };  //Option 58
		unsigned char RebindingTimeValue[4] = { 0, 0x02, 0x1c, 0 };     //Option 59
		unsigned char LogServer[4]          = { 192, 168, 56, 1 };
	};

	class DHCP_Server
	{
	public:
		DHCP_Server();
		~DHCP_Server();

		void Run();

	private:
		bool Initialize();
		void ParseAddrToBytes(char* resultBuf, std::string& strAddr);
		void ParseConfig();

		uint8_t RecieveRequest(const char* buf, char* BootpRequestData);
		void SendReply(DHCPMessageType MessageType, BOOTPPacket& BootpRequestData);

	private:
		SOCKET SocketFd;
		uint16_t PortNumber;
		DHCP_Config Config;

		std::unordered_map <std::string, u_long> MacIpPairs;
	};
};