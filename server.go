package main

import (
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"time"
)
import "bufio"

type Server struct {
	Addr string

	listener   *net.Listener
	conns      []*net.Conn
	inShutdown bool
}

func handle(conn net.Conn, pull *[]*net.Conn) error {
	defer func() {
		log.Printf("closing connection from %v", conn.RemoteAddr())
		conn.Close()
	}()
	r := bufio.NewReader(conn)
	for {
		var text string
		for {
			buf := make([]byte, 128)
			_, err := r.Read(buf)
			if err == io.EOF {
				conn.Close()
				return err
			}
			if err != nil {
				conn.Close()
				return err
			}
			text += string(buf)
			if strings.Contains(text, "\n") {
				break
			}
		}
		text = strings.TrimSpace(text)
		timestamp, _ := strconv.ParseInt(text[1:strings.Index(text, "]")], 10, 64)

		fmt.Print("[" + time.Unix(timestamp, 0).Format("2006-01-02 15:04:00") + "] " + text[strings.Index(text, "]")+1:])
		for _, c := range *pull {
			if *c != conn {
				w := bufio.NewWriter(*c)
				w.WriteString(text)
				w.Flush()
			}
		}
	}
	return nil
}

func (srv Server) ListenAndServe() error {
	log.Printf("starting server on %v\n", srv.Addr)
	listener, err := net.Listen("tcp", srv.Addr)
	if err != nil {
		log.Fatal(err)
		return err
	}
	srv.listener = &listener
	defer listener.Close()
	for {
		con, err := listener.Accept()
		if err != nil {
			log.Printf("error accepting connection %v", err)
			continue
		}
		srv.conns = append(srv.conns, &con)
		log.Printf("accepted connection from %v", con.RemoteAddr())
		go handle(con, &srv.conns)
	}
}

func main() {
	args := os.Args[1:]
	var ip string
	if len(args) >= 2 {
		ip = args[0] + ":" + args[1]
	} else if len(args) == 1 {
		ip = args[0] + ":2156"
	} else {
		reader := bufio.NewReader(os.Stdin)
		fmt.Print("IP with port for connect? Default port is 2156\n")
		ip, _ = reader.ReadString('\n')
		ip = strings.Trim(ip, " \n\r")
		if strings.Index(ip, ":") == -1 {
			ip += ":2156"
		}
	}
	srv := Server{
		Addr: ip,
	}

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	go func(c chan os.Signal, srv Server) {
		<-c
		fmt.Println("Server shutting down")
		for _, c := range srv.conns {
			(*c).Close()
		}
		os.Exit(0)
	}(c, srv)

	fmt.Println("Server started")
	srv.ListenAndServe()

}
