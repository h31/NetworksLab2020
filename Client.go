package main

import (
	"bytes"
	"dhcpLab/dhcpPackage"
	"encoding/binary"
	"fmt"
	"net"
	"os"
	"time"
)

func getBroadcastPair() (listener *net.UDPConn, sender *net.UDPConn) {
	local := &net.UDPAddr{
		IP: net.IPv4(127,0,0,1),
		Port: dhcpPackage.ClientPort,
	}
	addr := &net.UDPAddr{
		IP:   net.IPv4bcast,
		Port: dhcpPackage.ServerPort,
	}
	listener, err := net.ListenUDP("udp4", local)
	if err != nil {
		fmt.Println("Error of opening listener")
		os.Exit(1)
	}
	sender, err = net.ListenUDP("udp4", addr)
	if err != nil {
		fmt.Println("Error of dial creation")
		os.Exit(1)
	}
	return listener, sender
}

func getUnicastPair(pzu []byte) (lsnr *net.UDPConn, snd *net.UDPConn) {
	addr, _ := net.ResolveUDPAddr("udp4", ":68")
	addr.Port = dhcpPackage.ClientPort
	lsnr, err := net.ListenUDP("udp4", addr)
	if err != nil {
		fmt.Println("Error of opening listener")
		os.Exit(1)
	}
	copy(addr.IP, pzu[4:8])
	chaddr := addr
	copy(chaddr.IP, pzu[0:4])
	chaddr.Port = dhcpPackage.ServerPort
	snd, err = net.ListenUDP("udp4", addr)
	if err != nil {
		fmt.Println("Error of opening sender dial")
		os.Exit(1)
	}
	return lsnr, snd
}

func retrySend(lsnr *net.UDPConn, snd *net.UDPConn, buffer *bytes.Buffer) (p dhcpPackage.Packet, i int) {
	addr := &net.UDPAddr{
		IP:   net.IPv4bcast,
		Port: dhcpPackage.ServerPort,
	}
	for ; i < 5; i++ {
		_, err := snd.WriteTo(buffer.Bytes(), addr)
		if err != nil {
			fmt.Println("Cannot send broadcast packet")
			continue
		}
		buf := make([]byte, 590)
		ch := make(chan dhcpPackage.Packet)
		go func() {
			n, addr, err := lsnr.ReadFromUDP(buf)
			if n > 576 {
				fmt.Println("Strange size of packet")
			}
			if err != nil {
				fmt.Println("Error of reading")
				ch <- dhcpPackage.Packet{}
				return
			}
			of := dhcpPackage.PacketFromBytes(buf)
			if of.GetType() == 2 && !bytes.Equal(of.Siaddr[:], addr.IP) {
				fmt.Println("Error of packet composition")
				ch <- dhcpPackage.Packet{}
				return
			}
			ch <- of
		}()
		select {
		case <-time.After(time.Second * time.Duration(5+5*i)):
			fmt.Printf("Timeout of reading operation. Retry send request (%d s)\n", 5+5*i)
			continue
		case p = <-ch:
			if p.Op != 0 {
				fmt.Println(p.AsString())
				return p, i
			} else {
				fmt.Println("Error of incoming offer. Retrying")
			}
		}
	}
	return dhcpPackage.Packet{}, i
}

func main() {
	if len(os.Args) == 1 {
		fmt.Println("Interface for configuration is not specified")
		os.Exit(1)
	}
	ifi, err := net.InterfaceByName(os.Args[1])
	if err != nil {
		fmt.Println("No interface with specified name founded")
		return
	}
	fmt.Println("Hello. Demo client of DHCP-protocol started")
	fmt.Printf("You specified %s(%v) interface\n", ifi.Name, ifi.HardwareAddr)
	fmt.Println("Please, choose working mode")
	fmt.Println("1. Get new ip from server")
	fmt.Println("2. Extend ip lease time")
	var mode int
	fmt.Print(">")
	fmt.Fscan(os.Stdin, &mode)
	switch mode {
		case 1:
			pzu, err := os.Create("client.pzu")
			if err != nil {
				fmt.Println("Cannot create pzu file")
				return
			}
			p := dhcpPackage.Packet{}
			lsnr, snd := getBroadcastPair()
			for expr := true; expr; expr = p.Op == 3 || p.GetType() == 4 {
				buffer := &bytes.Buffer{}
				println("Send discover request")
				p = dhcpPackage.MakeDiscover(*ifi)
				println(p.AsString())
				binary.Write(buffer, binary.BigEndian, p)
				p, i := retrySend(lsnr, snd, buffer)
				if (i == 5 && p.Op == 0) || p.GetType() != 2 {
					fmt.Println("Offer not received")
					p.Op = 3
					continue
				}
				pzu.Write(p.Siaddr[:])
				r, e := dhcpPackage.MakeRequest(p, *ifi)
				fmt.Println("Send Request request")
				fmt.Println(r.AsString())
				if e != "" {
					fmt.Println("Error in gotten packet")
					fmt.Println(e)
					p.Op = 3
					continue
				}
				binary.Write(buffer, binary.BigEndian, r)
				p, i = retrySend(lsnr, snd, buffer)
				if i == 5 && p.Op == 0 ||p.GetType() != 5 {
					fmt.Println("Ack not received")
					p.Op = 3
					continue
				}
				fmt.Println("Ack gotten")
				fmt.Println(p.AsString())
				pzu.Write(p.Yiaddr[:])
				break
			}
			fmt.Printf("Your new ip: %v", p.Yiaddr)
			lsnr.Close()
			snd.Close()
		case 2:
			pzu, err := os.Open("client.pzu")
			if err != nil {
				fmt.Println("Cannot open pzu file. Please get your ip")
				return
			}
			buf := make([]byte, 8)
			pzu.Read(buf)
			lsnr, snd := getUnicastPair(buf)
			p := dhcpPackage.MakeURequest(*ifi, buf[4:], buf[:4])
			binary.Write(buffer, binary.BigEndian, p)
			p, i := retrySend(lsnr, snd, buffer)
			if i == 5 && p.Op != 2 {
				fmt.Println("Ack not received. Maybe DHCP server is offline")
				lsnr.Close()
				snd.Close()
				return
			}
			lsnr.Close()
			snd.Close()
		default:
			fmt.Println("Something strange in input. Rerun client, please")
			return
	}

}
