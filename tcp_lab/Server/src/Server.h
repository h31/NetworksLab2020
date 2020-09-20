#pragma once

//socket and serialization header
#include "chat.h"

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
		SOCKET             Sockfd;
		uint16_t           PortNum;
		struct sockaddr_in ServerAddr;

		std::unordered_map<SOCKET, std::thread> SocketToThreadMap;
		std::mutex Mutex;
	};
}