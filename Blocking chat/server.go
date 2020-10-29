package main

import (
	"fmt"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
)

func exit(sockets *[]int, listener int) {
	for _, val := range *sockets {
		_ = syscall.Close(val)
	}
	_ = syscall.Close(listener)
	os.Exit(2)
}

func handler(socket int, others *[]int) {
	var text string
	for {
		text = ""
		for {
			buffer := make([]byte, 1024)
			n, _, err := syscall.Recvfrom(socket, buffer, 0)
			if err != nil {
				if err != syscall.ENOTCONN {
					_, _ = os.Stderr.WriteString("Error of reading \n")
					_ = syscall.Close(socket)
				}
				return
			}
			if n > 0 {
				text += string(buffer[:])
				text = strings.Trim(text, "\u0000 ")
				if strings.HasSuffix(text, "\n") {
					break
				}
			}
		}
		fmt.Print(text)
		for _, sock := range *others {
			if sock != socket {
				err := syscall.Sendmsg(sock, []byte(text), []byte{}, nil, 0)
				if err != nil {
					_, _ = os.Stderr.WriteString("Error of resending to " + strconv.Itoa(sock) + " client\n")
				}
			}
		}
	}
}

func main() {
	var clients []int
	stackSize, args := 10, os.Args[1:]

	port, err := strconv.Atoi(args[0])
	sockOpt := syscall.SOCK_STREAM | syscall.SOCK_CLOEXEC
	if err != nil {
		_, _ = os.Stderr.WriteString("Port is not number\n")
		os.Exit(1)
	}
	listener, err := syscall.Socket(syscall.AF_INET, sockOpt, 0)
	if err != nil {
		_, _ = os.Stderr.WriteString("Input socket cannot created\n")
		os.Exit(1)
	}
	err = syscall.Bind(listener, &syscall.SockaddrInet4{
		Port: port,
		Addr: [4]byte{127, 0, 0, 1},
	})
	if err != nil {
		_, _ = os.Stderr.WriteString("Input socket arent bind to localhost\n")
		os.Exit(1)
	}
	if syscall.Listen(listener, stackSize) != nil {
		_, _ = os.Stderr.WriteString("Input socket arent open to listening\n")
		os.Exit(1)
	}
	fmt.Println("Server is online")
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	go func(c chan os.Signal) {
		<-c
		fmt.Println("\nClient shutting down")
		exit(&clients, listener)
		os.Exit(0)
	}(c)
	for {
		client, caddr, err := syscall.Accept(listener)
		if err == syscall.ENFILE {
			_, _ = os.Stderr.WriteString("Out of memory for new client\n")
		} else if err == syscall.EINTR {
			_, _ = os.Stderr.WriteString("Client knocked on the door and ran away\n")
		} else if err != nil {
			_, _ = os.Stderr.WriteString("Accept send strange error\n")
			exit(&clients, listener)
		} else {
			ip := ""
			for _, i := range caddr.(*syscall.SockaddrInet4).Addr {
				ip += strconv.Itoa(int(i)) + "."
			}
			ip = ip[:len(ip)-1]
			fmt.Println("New client on server. (" + strconv.Itoa(client) + ") " + ip + ":" + strconv.Itoa(caddr.(*syscall.SockaddrInet4).Port))
			clients = append(clients, client)
			go handler(client, &clients)
		}
	}
}
