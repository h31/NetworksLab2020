package main

import (
	"log"
	"net"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	time "time"
)
import "fmt"
import "bufio"
import "os"

func main() {
	args := os.Args[1:]
	var ip, nik string
	if len(args) > 2 {
		ip = args[0] + ":" + args[1]
		nik = args[2]
	} else if len(args) == 2 {
		ip = args[0] + ":2156"
		nik = args[1]
	} else {
		reader := bufio.NewReader(os.Stdin)
		if len(args) == 1 {
			ip = args[0] + ":2156"
		} else {
			fmt.Print("IP with port for connect? Default port is 2156\n>")
			ip, _ = reader.ReadString('\n')
			ip = strings.Trim(ip, " \n\t\r")
			if strings.Index(ip, ":") == -1 {
				ip += ":2156"
			}
		}
		fmt.Print("Your nik?\n> ")
		nik, _ := reader.ReadString('\n')
		nik = strings.Trim(nik, " \n\t\r")
	}

	// connect to server
	var wg sync.WaitGroup
	work := true
	conn, err := net.Dial("tcp", ip)
	netreader := bufio.NewReader(conn)
	defer conn.Close()
	if err != nil {
		log.Fatal(err)
		return
	}
	wg.Add(1)
	reader := bufio.NewReader(os.Stdin)
	go func(conn net.Conn) {
		for work {
			fmt.Print(">")
			text, _ := reader.ReadString('\n')
			fmt.Fprintf(conn, "["+strconv.FormatInt(time.Now().Unix(), 10)+"]<"+nik+"> "+text)
		}
		wg.Done()
	}(conn)
	wg.Add(1)
	go func(conn net.Conn) {
		for work {
			var text string
			for {
				buf := make([]byte, 128)
				_, err := netreader.Read(buf)
				if err != nil {
					conn.Close()
					wg.Done()
					work = false
					fmt.Println("Server disconnected")
					os.Exit(0)
				}
				text += string(buf)
				if strings.Contains(text, "\n") {
					break
				}
			}
			text = strings.TrimSpace(text)
			timestamp, _ := strconv.ParseInt(text[1:strings.Index(text, "]")], 10, 64)

			text = ("[" + time.Unix(timestamp, 0).Format("2006-01-02 15:04:00") + "] " + text[strings.Index(text, "]")+1:])
			fmt.Print("\n->" + text)
			fmt.Print(">")
		}
		wg.Done()
	}(conn)
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	go func(c chan os.Signal) {
		<-c
		fmt.Println("Client shutting down")
		work = false
		netreader.Reset(netreader)
		reader.Reset(reader)
		conn.Close()
		os.Exit(0)
	}(c)
	wg.Wait()
	conn.Close()
}
