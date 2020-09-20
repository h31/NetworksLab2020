#pragma once

//socket and serialization header
#include "chat.h"

namespace Tcp_lab {

	class Client
	{
	public:
		Client() : StdinHandle(GetStdHandle(STD_INPUT_HANDLE)), IsRunning(true), Name("Default"), SocketFd(0) {}
		~Client();

		//PCSTR - Pointer Const Not Wide String
		bool Initialize(PCSTR NodeName, PCSTR ServiceName);
		inline void SetNickname(PCSTR nickname);

		void SenderRun();
		void RecieverRun();

	public:
		std::thread Reciever;
		HANDLE StdinHandle;

	private:
		bool IsRunning = true;
		std::string Name;
		SOCKET SocketFd;
	};
}