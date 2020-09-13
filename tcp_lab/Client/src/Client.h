#pragma once

#include "chat.h"

#include <WinSock2.h>
#include <ws2ipdef.h>

#include <thread>

namespace Tcp_lab {

	class Client
	{
	public:
		Client() { m_Name = "Default"; };
		~Client();

		void Initialize(PCSTR NodeName, PCSTR ServiceName);
		inline void SetNickname(char* nickname);

		void SenderRun();
		void RecieverRun();

	public:
		std::thread Sender;
		std::thread Reciever;

	private:
		std::string m_Name;
		//char m_Name[NameMaxSize];

		SOCKET m_SocketFd;
		struct addrinfo m_Hints, * m_ServInfo;
		char s[INET_ADDRSTRLEN];
	};
}