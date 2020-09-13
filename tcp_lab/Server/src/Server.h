#pragma once

#include "chat.h"

#include <WinSock2.h>
#include <stdint.h>
#include <vector>
#include <thread>
#include <list>
#include <string>

namespace Tcp_lab {
	
	class Server
	{
	public: 
		Server();
		~Server();

		void Run();
	private:
		void ClientRun(size_t IndexInSocketArray, struct sockaddr_in ClientAddr, int ClientLen);

	private:
		SOCKET                   m_Sockfd;
		uint16_t                 m_PortNum;
		struct sockaddr_in       m_ServerAddr;

		std::vector<SOCKET>      m_ClientSockets;
		std::vector<std::thread> m_ChatThreads;
	};
}