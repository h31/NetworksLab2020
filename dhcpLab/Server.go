package main

import (
	"bytes"
	"database/sql"
	"dhcpLab/dhcpPackage"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	_ "github.com/mattn/go-sqlite3"
	"net"
	"os"
	"strconv"
)

func contains(e string) bool {
	s, _ := net.Interfaces()
	for _, a := range s {
		if a.Name == e {
			return true
		}
	}
	return false
}

func start() (*net.Interface, *net.UDPConn) {
	if len(os.Args) == 1 {
		fmt.Println("No interface specified")
		os.Exit(1)
	}
	if !contains(os.Args[1]) {
		fmt.Println("Interface not founded")
		os.Exit(1)
	}
	addr := &net.UDPAddr{
		IP:   net.IPv4zero,
		Port: dhcpPackage.ServerPort,
	}
	ifi, _ := net.InterfaceByName(os.Args[1])
	con, err := net.ListenUDP("udp", addr)
	if err != nil {
		fmt.Println("Cannot open listener")
		os.Exit(1)
	}
	return ifi, con
}

func main() {
	ifi, con := start()
	defer con.Close()
	flash, err := sql.Open("sqlite3", "flash")
	if err != nil {
		fmt.Println("Error of reading flash memory")
		os.Exit(1)
	}
	println("Server online")
	buf := make([]byte, 600, 600)
	for {
		n, addr, err := con.ReadFromUDP(buf)
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
		fmt.Printf("Got request: type %d from %s\n", p.GetType(), addr.String())
		go handler(flash, p, ifi, con, *addr)
	}
}

func cleanUp(db *sql.DB) {
	_, _ = db.Exec("delete from devices where id > 1 and Cast((JulianDay(datetime('now')) - JulianDay(ttl)) * 24 * 60 As Integer) > 120")
	_, _ = db.Exec("delete from session where Cast((JulianDay(datetime('now')) - JulianDay(dstart)) * 24 * 60 As Integer) > 300")
}

func handler(db *sql.DB, p dhcpPackage.Packet, ifi *net.Interface, sock *net.UDPConn, rem net.UDPAddr) {
	cleanUp(db)
	buffer := &bytes.Buffer{}
	remote := &net.UDPAddr{
		IP:   net.IPv4bcast,
		Port: dhcpPackage.ClientPort,
	}
	switch int(p.GetType()) {
	case 1:
		ip := make([]byte, 4)
		exec, err := db.Query("SELECT ip from devices d INNER join session s on hex(d.mac) = hex(s.chaddr) where d.mac = X'" + hex.EncodeToString(p.Xid[:]) + "'")
		if err != nil {
			fmt.Println("Error of reading from flash")
			return
		}
		for exec.Next() {
			_ = exec.Scan(&ip)
		}
		_ = exec.Close()
		if ip[0] == 0 && ip[1] == 0 {
			_, _ = db.Exec("INSERT into session VALUES (x'" + hex.EncodeToString(p.Xid[:]) + "', x'" + hex.EncodeToString(p.Chaddr[:]) + "', datetime('now')) on CONFLICT(chaddr) do update set xid = excluded.xid, dstart = datetime('now')")
			row, _ := db.Query("Select ip from devices order by ip desc limit 1")
			row.Next()
			_ = row.Scan(&ip)
			row.Close()
			ip[3] += 1
		}
		offer, ecode := dhcpPackage.MakeOffer(p, *ifi, ip)
		if ecode != "" {
			fmt.Println(ecode)
			return
		}

		binary.Write(buffer, binary.BigEndian, offer)
		_, err = sock.WriteToUDP(buffer.Bytes(), remote)
		if err != nil {
			println(err)
		}
	case 2:
		return
	case 3:
		xid := make([]byte, 4)
		if p.Ciaddr[0] != 0 {
			buffer := &bytes.Buffer{}
			id := 0
			row, err := db.Query("SELECT id from devices d where d.mac = X'" + hex.EncodeToString(p.Chaddr[:]) + "' and d.ip = x'" + hex.EncodeToString(p.Ciaddr[:]) + "'")
			if err == nil {
				for row.Next() {
					row.Scan(&id)
				}
			}
			row.Close()
			_, _ = db.Exec("Update devices set ttl = datetime('now') where id = " + strconv.Itoa(id))
			ac := dhcpPackage.MakeUAck(p)
			binary.Write(buffer, binary.BigEndian, ac)
			sock.WriteToUDP(buffer.Bytes(), &rem)
			fmt.Printf("Ip %v for %v client ttl refreshed\n", p.Ciaddr, p.Chaddr)
			return
		}
		exec, err := db.Query("select xid from session where xid = X'" + hex.EncodeToString(p.Xid[:]) + "'")
		if err != nil {
			fmt.Println("Error of reading from flash")
			return
		}
		for exec.Next() {
			exec.Scan(&xid)
		}
		exec.Close()
		ip := make([]byte, 4)
		if xid[0] != 0 || xid[1] != 0 || xid[2] != 0 || xid[3] != 0 {
			exec, err := db.Query("SELECT ip from devices d INNER join session s on hex(d.mac) = hex(s.chaddr) where s.xid = X'" + hex.EncodeToString(p.Xid[:]) + "'")
			if err != nil {
				fmt.Println("Error of reading from flash")
				return
			}
			for exec.Next() {
				_ = exec.Scan(&ip)
			}
			db.Exec("DELETE FROM session where xid = x'" + hex.EncodeToString(xid) + "'")
			if ip[0] == 0 {
				copy(ip, p.GetOption(dhcpPackage.OptionRequestedIPAddress))
				_, err = db.Exec("INSERT INTO devices(ip,mac,ttl) values (x'" + hex.EncodeToString(ip) + "',x'" + hex.EncodeToString(p.Chaddr[:]) + "',datetime('now'))")
			}
			accept, ecode := dhcpPackage.MakeAck(p, *ifi)
			if ecode != "" {
				println(ecode)
				return
			}
			binary.Write(buffer, binary.BigEndian, accept)
			sock.WriteToUDP(buffer.Bytes(), remote)
		}
	case 4:
		return

	}
}
