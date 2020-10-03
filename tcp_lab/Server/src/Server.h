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

		//for run from main
		void Run();
	private:
		//Accept new connections if present
		const bool AcceptIncomingConnections();
		//Broadcast getted messages if present
		const int32_t BroadcastMessages(char* buffer, const int32_t index);

	private:
		//Socket Info
		SOCKET             Sockfd;
		uint16_t           PortNum;
		struct sockaddr_in ServerAddr;

		//Application properties
		bool IsRunning = true;
		std::vector<WSAPOLLFD> ClientsPollInfo;
	};
}