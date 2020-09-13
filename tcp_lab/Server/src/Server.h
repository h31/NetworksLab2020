#pragma once

#include "chat.h"

#include <thread>
#include <mutex>
#include <unordered_map>

namespace Tcp_lab {
	
	class Server
	{
	public: 
		Server();
		~Server();

		void Run();
	private:
		void ClientRun(SOCKET ClientSocket, struct sockaddr_in ClientAddr, int ClientLen);
		void CleanThread(SOCKET ClientSocket);

	private:
		SOCKET                   m_Sockfd;
		uint16_t                 m_PortNum;
		struct sockaddr_in       m_ServerAddr;

		std::unordered_map<SOCKET, std::thread> m_SocketToThreadMap;
		std::mutex m_Mutex;
	};
}