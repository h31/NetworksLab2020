package main

import (
	"bytes"
	"database/sql"
	"dhcpLab/dhcpPackage"
	"encoding/binary"
	"fmt"
	_ "github.com/mattn/go-sqlite3"
	"net"
	"os"
	"strconv"
)

func contains(e string) bool {
	s, _ := net.Interfaces()
	for _, a := range s{
		if a.Name == e {
			return true
		}
	}
	return false
}

func main()  {
	if len(os.Args) == 1 {
		fmt.Println("No interface specified")
		os.Exit(1)
	}
	if !contains(os.Args[1]) {
		fmt.Println("Interface not founded")
		os.Exit(1)
	}
	ifi, _ := net.InterfaceByName(os.Args[1])
	con, err := net.ListenPacket("udp4", ":" + strconv.Itoa(dhcpPackage.ServerPort))
	if err != nil {
		fmt.Println("Cannot open listener")
		os.Exit(1)
	}
	defer con.Close()
	flash, err := sql.Open("sqlite3", "flash")
	if err != nil {
		fmt.Println("Error of reading flash memory")
		os.Exit(1)
	}
	buf := make([]byte, 600, 600)
	for {
		n, _, err := con.ReadFrom(buf)
		if err != nil {
			fmt.Println(fmt.Errorf("error of reading: %v", err))
			continue
		}
		if n > 588 {
			fmt.Println("Error of package size")
			continue
		}
		p := dhcpPackage.PacketFromBytes(buf)
		if p.Op == 2 || len(p.GetOption(dhcpPackage.OptionDHCPMessageType)) != 1 {
			fmt.Println("Error of package format")
			continue
		}
		if ci := p.GetOption(dhcpPackage.OptionClientIdentifier); len(ci) > 0 {
			if ci[0] != p.Htype || !bytes.Equal(ci[1:17], p.Chaddr[:]) {
				fmt.Println("Client Identifier option not equals to htype/chaddr")
				continue
			}
		}
		go handler(*flash, p, ifi)
	}
}

func handler(db sql.DB, p dhcpPackage.Packet, ifi *net.Interface) {
	buffer := &bytes.Buffer{}
	remote := net.UDPAddr{
		IP:   net.IPv4bcast,
		Port: dhcpPackage.ClientPort,
	}
	switch int(p.GetType()) {
		case 1:
			_, _ = db.Exec("delete from devices where Cast((JulianDay(date('now')) - JulianDay(ttl)) * 24 * 60 As Integer) > 120")
			exec, err := db.Exec("select xid, chaddr from session where xid = $1", dhcpPackage.ByteAsString(p.Xid[:]))
			if err != nil {
				fmt.Println("Error of reading from flash")
				return
			}
			offer, error := dhcpPackage.MakeOffer(p, *ifi)
			if error != "" {
				fmt.Println(error)
				return
			}
			db.Exec("Insert into session values ($1, $2)", dhcpPackage.ByteAsString(p.Xid[:]), dhcpPackage.ByteAsString(p.Chaddr[:]))
			sender, err := net.ListenUDP("udp4", &remote)
			if err != nil {
				fmt.Println("Cannot open dial to broadcast")
				return
			}
			row, err := db.Query("Select ip from devices order by ip desc limit 1")
			var ip []byte
			row.Next()
			row.Scan(&ip)
			ip[len(ip)] += 1
			copy(offer.Yiaddr[:], ip)
			binary.Write(buffer, binary.BigEndian, offer)
			sender.Write(buffer.Bytes())
			sender.Close()
		case 2:
			return
		case 3:
			exec, err := db.Exec("select xid, chaddr from session where xid = $1", dhcpPackage.ByteAsString(p.Xid[:]))
			if err != nil {
				fmt.Println("Error of reading from flash")
				return
			}
			if num, err := exec.RowsAffected(); err != nil || num != 1 {
				fmt.Println("Unknown xid")
				return
			}
			db.Exec("INSERT INTO devices (ip, mac, ttl) values ($1, $2, date('now'))",
				dhcpPackage.ByteAsString(p.GetOption(dhcpPackage.OptionRequestedIPAddress)),
				dhcpPackage.ByteAsString(p.Chaddr[:]))
			db.Exec("DELETE FROM session where xid = $1", dhcpPackage.ByteAsString(p.Xid[:]))
			ack, error := dhcpPackage.MakeAck(p, *ifi)
			if error != "" {
				fmt.Println(error)
				return
			}
			sender, err := net.ListenUDP("udp4", &remote)
			if err != nil {
				fmt.Println("Cannot open dial to broadcast")
				return
			}
			binary.Write(buffer, binary.BigEndian, ack)
			sender.Write(buffer.Bytes())
			sender.Close()
		case 4:
			return

	}
}
