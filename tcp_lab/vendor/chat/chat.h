#pragma once

#include <stdio.h>
#include <stdlib.h>
#include <chrono>
#include <ctime>
#include <memory.h> //memcpy
#include <string>
#include <thread>
#include <tchar.h>

//to be defined in premake or project
//need to be recompiled
#ifdef WinSockApp

    #include <stdint.h> //fixed size types
    #include <WinSock2.h>
    #include <ws2ipdef.h>

    #define bzero(buffer, len) (memset((buffer), '\0', (len)), (void) 0)  

    #include <WS2tcpip.h>
    #include <AF_Irda.h>
    #include <in6addr.h>
    #include <mstcpip.h>
    #include <MSWSock.h>
    #include <nsemail.h>
    #include <NspAPI.h>
    #include <socketapi.h>
    //#include <SpOrder.h>
    #include <transportsettingcommon.h>
    #include <winsock.h>
    #include <WS2atm.h>
    #include <WS2spi.h>
    #include <wsipv6ok.h>
    #include <WSNwLink.h>
    #include <wsrm.h>
    
    void InitializeWinSock2()
    {
    	//Initialize Winsock
    	WSADATA WsaData;
    	WORD DLLVersion = MAKEWORD(2, 2);
    	//if Initializing is ok
    	if (WSAStartup(DLLVersion, &WsaData) != 0)
    	{
			printf("WinSock process initialized with error\n");
    		exit(1);
    	}
    }
#endif

//to be defined in premake or project
//need to be recompiled
#ifdef UnixSockApp
	
    #include <netdb.h>
    #include <netinet/in.h>
    #include <unistd.h>
    
    #define send(socket, buffer, length, flag) write(socket, buffer, length) 
    #define recv(socket, buffer, length, flag) read(socket, buffer, length);
	#define WSACleanup()
	#define InitializeWinSock2() 

#endif

/*
* Структура заголовка данных
* uint8_t  
*
*
*
*/

//without padding
#pragma pack(1)
struct MessageInfo
{
	//uint32_t EndiassNumber = 1u; // check endiass if 1 in the most left bit it's 
	uint16_t NameSize; //size of name string
	uint32_t MessageSize; // size of message string
	uint64_t Time; // time when message was sended
};

#define NameMaxSize 64
#define WideMessageMaxSize 255
#define MessageMaxSize WideMessageMaxSize * sizeof(wchar_t)
#define MaxBufferSize NameMaxSize + MessageMaxSize + sizeof(MessageInfo)

namespace Tcp_lab {

	uint64_t GetExactCurrentTime()
	{
		auto time = std::chrono::system_clock::now();
		std::time_t CurrentTime = std::chrono::system_clock::to_time_t(time);
		return CurrentTime;
	}

	char* SerializeString(void* buffer, const char* data, const uint32_t length)
	{
		memcpy(buffer, data, length);
		char* ptr = static_cast<char*>(buffer);
		ptr += length;
		return ptr;
	}

	void Serialize(void* buffer, const char* Name, const char* Message, uint8_t NameSize, uint32_t MessageSize)
	{
		void* TempBuf = buffer;
		{
			uint16_t* ptr = static_cast<uint16_t*>(TempBuf);
			*ptr = 1;
			TempBuf = ++ptr;
		}
		{
			MessageInfo* ptr = static_cast<MessageInfo*>(TempBuf);
			*ptr = MessageInfo{ NameSize, MessageSize, GetExactCurrentTime() };
			TempBuf = ++ptr;
		}

		//write two char array
		TempBuf = SerializeString(TempBuf, Name, NameSize);
		TempBuf = SerializeString(TempBuf, Message, MessageSize);
	}

	char* DesearilizeString(char* data, void* buffer, const uint32_t length)
	{
		char* ptr = data;
		memcpy(buffer, data, length);
		ptr += length;
		return ptr;
	}

	void Desearilize(void* buffer, MessageInfo* Info, char* Name, char* Message)
	{
		uint16_t* ptrEnd = static_cast<uint16_t*>(buffer);
		uint16_t SendedEndiassNum = *ptrEnd;
		buffer = ++ptrEnd;

		MessageInfo* ptr = static_cast<MessageInfo*>(buffer);
		*Info = *ptr;
		buffer = ++ptr;

		uint32_t CheckNumber = 1u;
		if (!(CheckNumber & SendedEndiassNum))
		{
			printf("Machine End: %i - Sended End: %i\n", CheckNumber, SendedEndiassNum);
			//Endiass decoding x0001 - little endian, x1000 - big endian
			if (CheckNumber) //little endiand
			{
				ptr->MessageSize = ntohs(static_cast<u_short>(ptr->MessageSize));
				ptr->NameSize = ntohs(static_cast<u_short>(ptr->NameSize));
				ptr->Time = ntohll(static_cast<unsigned long long>(ptr->Time));
			}
			else //big endian
			{
				ptr->MessageSize = htons(static_cast<u_short>(ptr->MessageSize));
				ptr->NameSize = htons(static_cast<u_short>(ptr->NameSize));
				ptr->Time = htonll(static_cast<unsigned long long>(ptr->Time));
			}
		}

		buffer = DesearilizeString(static_cast<char*>(buffer), Name,    Info->NameSize);
		buffer = DesearilizeString(static_cast<char*>(buffer), Message, Info->MessageSize);
	}
}

