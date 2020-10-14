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
		void Deinitialize();
		inline void SetNickname(LPCWCH nickname, unsigned long readedBytes);

		void SenderRun();
		void RecieverRun();

		void PrintDebug();

	public:
		std::thread Reciever;
		HANDLE StdinHandle;

	private:
		bool IsRunning = true;
		char Name[NameMaxSize * sizeof(wchar_t)];
		SOCKET SocketFd;
	};
}