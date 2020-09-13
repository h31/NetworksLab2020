#pragma once

#include <WinSock2.h>
#include <chrono>
#include <ctime>
#include <memory.h> //memcpy
#include <stdint.h> //fixed size types
#include <string>
#include "WinTypes.h"

void InitializeWinSock2()
{
	//Initialize Winsock
	WSADATA WsaData;
	WORD DLLVersion = MAKEWORD(2, 2);
	//if Initializing is ok
	if (WSAStartup(DLLVersion, &WsaData) != 0)
	{
		//std::cout << "Initializing winsock ended with error" << std::endl;
		exit(1);
	}
}

struct MessageInfo
{
	uint8_t m_NameSize; //size of name string
	uint8_t m_MessageSize; // size of message string
	uint64_t m_Time; // time when message was sended
};

#define NameMaxSize 64
#define MessageMaxSize 255
#define MaxMessageSize NameMaxSize + MessageMaxSize + sizeof(MessageInfo)

namespace Tcp_lab {

	uint64_t GetExactCurrentTime()
	{
		auto time = std::chrono::system_clock::now();
		std::time_t CurrentTime = std::chrono::system_clock::to_time_t(time);
		return CurrentTime;
	}

	char* SerializeString(void* buffer, const char* data, const uint8_t length)
	{
		memcpy(buffer, data, length);
		char* ptr = static_cast<char*>(buffer);
		ptr += length;
		return ptr;
	}

	void Serialize(void* buffer, const char* Name, const char* Message, uint8_t NameSize, uint8_t MessageSize)
	{
		void* TempBuf = buffer;
		{
			MessageInfo* ptr = static_cast<MessageInfo*>(TempBuf);
			*ptr = MessageInfo{ NameSize, MessageSize, GetExactCurrentTime() };
			TempBuf = ++ptr;
		}

		//write two char array
		TempBuf = SerializeString(TempBuf, Name, NameSize);
		TempBuf = SerializeString(TempBuf, Message, MessageSize - 1);
	}

	char* DesearilizeString(char* data, void* buffer, const uint8_t length)
	{
		char* ptr = data;
		memcpy(buffer, data, length);
		ptr += length;
		return ptr;
	}

	void Desearilize(void* buffer, MessageInfo* Info, char* Name, char* Message)
	{
		
		MessageInfo* ptr = static_cast<MessageInfo*>(buffer);
		*Info = *ptr;
		buffer = ++ptr;

		buffer = DesearilizeString(static_cast<char*>(buffer), Name, Info->m_NameSize);
		buffer = DesearilizeString(static_cast<char*>(buffer), Message, Info->m_MessageSize);
	}
}

