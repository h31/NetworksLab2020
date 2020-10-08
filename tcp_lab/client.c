#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>

#define MAXDATASIZE 256

char msg[MAXDATASIZE];

void trimString(char str[32], int length)
{
	for (int i = 0; i < length; i++)
	{
		// trim \n
		if (str[i] == '\n')
		{
			str[i] = '\0';
			break;
		}
	}
}

void *recvmg(void *my_sock)
{
	int sock = *((int *)my_sock);
	int len;
	bzero(msg, MAXDATASIZE);
	// Client thread always ready to receive message
	while ((len = recv(sock, msg, MAXDATASIZE, 0)) > 0)
	{
		msg[len] = '\0';
		fputs(msg, stdout);
	}
}

int main(int argc, char *argv[])
{
	pthread_t recvt;
	int sockfd;
	char buf[MAXDATASIZE];
	struct sockaddr_in serverIP;
	char clientName[32];
	int port = atoi(argv[1]);
	char *ip = "127.0.0.1";
	time_t t = time(NULL);
	char h[2];
	char min[2];

	printf("Please enter your name: ");
	fgets(clientName, 32, stdin);
	trimString(clientName, strlen(clientName));

	sockfd = socket(AF_INET, SOCK_STREAM, 0);

	if (sockfd < 0)
	{
		printf("ERROR opening socket\n");
		exit(1);
	}

	memset(&serverIP, '0', sizeof(serverIP));
	serverIP.sin_port = htons(port);
	serverIP.sin_family = AF_INET;
	serverIP.sin_addr.s_addr = inet_addr(ip);

	if ((connect(sockfd, (struct sockaddr *)&serverIP, sizeof(serverIP))) == -1)
	{
		close(sockfd);
		printf("ERROR connection to socket failed\n");
		return 1;
	}

	// Creating a client thread which is always waiting for a message
	pthread_create(&recvt, NULL, (void *)recvmg, &sockfd);

	struct tm *tm = localtime(&t);

	// Ready to read a message from console
	while (fgets(msg, MAXDATASIZE, stdin) > 0)
	{
		bzero(buf, MAXDATASIZE);
		strftime(buf, MAXDATASIZE, "<%H:%M> ", tm);
		strcat(strcat(strcat(buf, clientName), " : "), msg);
		if (write(sockfd, buf, strlen(buf)) < 0)
		{
			printf("ERROR writing to socket\n");
			return 1;
		}
		bzero(msg, MAXDATASIZE);
	}

	// Thread is closed
	pthread_join(recvt, NULL);
	close(sockfd);
	return 0;
}