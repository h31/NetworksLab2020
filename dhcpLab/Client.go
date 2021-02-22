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

func compareXID(a [4]byte, b [4]byte) bool {
	return a[0] == b[0] && a[1] == b[1] && a[2] == b[2] && a[3] == b[3]
}

func getBroadcastPair() (listener *net.UDPConn) {
	local := &net.UDPAddr{
		IP:   net.IPv4zero,
		Port: dhcpPackage.ClientPort,
	}
	listener, err := net.ListenUDP("udp4", local)
	if err != nil {
		fmt.Println("Error of opening listener")
		os.Exit(1)
	}
	return
}

func retrySend(lsnr *net.UDPConn, p dhcpPackage.Packet) (resp dhcpPackage.Packet, i int) {
	buffer := &bytes.Buffer{}
	binary.Write(buffer, binary.BigEndian, p)
	var addr net.UDPAddr
	if p.Flags[0] == 0x80 {
		addr = net.UDPAddr{
			IP:   net.IPv4bcast,
			Port: dhcpPackage.ServerPort,
		}
	} else {
		addr = net.UDPAddr{
			IP:   net.IPv4(p.Siaddr[0], p.Siaddr[1], p.Siaddr[2], p.Siaddr[3]),
			Port: dhcpPackage.ServerPort,
		}
	}
	for ; i < 5; i++ {
		_, err := lsnr.WriteToUDP(buffer.Bytes(), &addr)
		if err != nil {
			fmt.Println("Cannot send broadcast packet")
			continue
		}
		buf := make([]byte, 590)
		ch := make(chan dhcpPackage.Packet)
		go func() {
			n, _, err := lsnr.ReadFromUDP(buf)
			if n > 576 {
				fmt.Println("Strange size of packet")
			}
			if err != nil {
				fmt.Println("Error of reading")
				ch <- dhcpPackage.Packet{}
				return
			}
			of := dhcpPackage.PacketFromBytes(buf)
			if of.Op != 2 || !compareXID(p.Xid, of.Xid) {
				fmt.Println("Error of packet composition")
				fmt.Println(of.AsString())
				ch <- dhcpPackage.Packet{}
				return
			}
			ch <- of
		}()
		select {
		case <-time.After(time.Second * time.Duration(5+5*i)):
			fmt.Printf("Timeout of reading operation. Retry send request (%d s)\n", 5+5*i)
			continue
		case resp = <-ch:
			if resp.Op != 0 {
				return resp, i
			} else {
				fmt.Println("Error in server answer. Retrying")
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
	fmt.Print("> ")
	fmt.Fscan(os.Stdin, &mode)
	switch mode {
	case 1:
		pzu, err := os.Create("client.pzu")
		if err != nil {
			fmt.Println("Cannot create pzu file")
			return
		}
		p := dhcpPackage.Packet{}
		lsnr := getBroadcastPair()
		for expr := true; expr; expr = p.GetType() == 4 || p.Op == 3 {
			println("Send discover request")
			p = dhcpPackage.MakeDiscover(*ifi)
			println(p.AsString())
			offer, i := retrySend(lsnr, p)
			if (i == 5 && offer.Op == 0) || offer.GetType() != 2 {
				fmt.Println("Offer not received")
				p.Op = 3
				continue
			}
			println(offer.AsString())
			pzu.Write(p.Siaddr[:])
			r, e := dhcpPackage.MakeRequest(offer, *ifi)
			fmt.Println("Send Request request")
			fmt.Println(r.AsString())
			if e != "" {
				fmt.Println("Error in gotten packet")
				fmt.Println(e)
				p.Op = 3
				continue
			}
			ack, i := retrySend(lsnr, *r)
			if (i == 5 && ack.Op == 0) || ack.GetType() != 5 {
				fmt.Println("Ack not received")
				p.Op = 3
				continue
			}
			fmt.Println("Ack gotten")
			fmt.Println(ack.AsString())
			p = ack
			pzu.Write(ack.Yiaddr[:])
			break
		}
		fmt.Printf("Your new ip: %v", p.Yiaddr)
		lsnr.Close()
	case 2:
		pzu, err := os.Open("client.pzu")
		if err != nil {
			fmt.Println("Cannot open pzu file. Please get your ip")
			return
		}
		buf := make([]byte, 8)
		pzu.Read(buf)
		lsnr := getBroadcastPair()
		p := dhcpPackage.MakeURequest(*ifi, buf[4:], buf[:4])
		p, i := retrySend(lsnr, p)
		if i == 5 && p.Op != 2 {
			fmt.Println("Ack not received. Maybe DHCP server is offline")
			lsnr.Close()
			return
		}
		fmt.Println("IP lease time successfully extend")
		lsnr.Close()
	default:
		fmt.Println("Something strange in input. Rerun client, please")
		return
	}

}
