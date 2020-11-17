package dhcpPackage

import (
	"fmt"
	"math/rand"
	"net"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

var cookieEdge = [4]byte{99, 130, 83, 99}

type Packet struct {
	Op      byte
	Htype   byte
	Hlen    byte
	Hops    byte
	Xid     [4]byte
	Secs    [2]byte
	Flags   [2]byte
	Ciaddr  [4]byte
	Yiaddr  [4]byte
	Siaddr  [4]byte
	Giaddr  [4]byte
	Chaddr  [16]byte
	Sname   [64]byte
	File    [128]byte
	options [340]byte
}

func ByteAsString(arr []byte) string {
	res := ""
	for _, b := range arr {
		if b < 16 {
			res += fmt.Sprintf("0%x", b)
		} else {
			res += fmt.Sprintf("%x", b)
		}
	}
	return res
}

func (p Packet) AsString() string {
	res := ""
	if p.Op == 1 {
		res += "Request "
	} else {
		res += "Response "
	}
	res += fmt.Sprintf("XID: %v\n", p.Xid)
	res += fmt.Sprintf("Client's ip: %v\n", p.Ciaddr)
	res += fmt.Sprintf("Suggested ip: %v\n", p.Yiaddr)
	res += fmt.Sprintf("Server's ip: %s\n", p.Siaddr)
	res += fmt.Sprintf("Repeater's ip: %v\n", p.Giaddr)
	res += fmt.Sprintf("Hardware address: %v\n", p.Chaddr)
	res += fmt.Sprintf("Server name: %q\n", string(p.Sname[:]))
	res += "Options:\n"
	i := 4
	for p.options[i] != OptionEnd {
		res += OptionNames[p.options[i]] + " ("
		t := p.options[i] == OptionDHCPMessageType
		i += 1
		res += strconv.Itoa(int(p.options[i])) + ") "
		size := int(p.options[i])
		if t {
			res += MessageNames[p.options[i]] + "\n"
		} else {
			for j := 0; j < size; j++ {
				res += fmt.Sprintf("%#x ", p.options[i+j])
			}
			res += "\n"
		}
		i += size + 1
	}
	return res
}

func (p *Packet) addOption(code byte, offset int, value []byte) int {
	p.options[offset] = code
	offset += 1
	if len(value) != 0 {
		p.options[offset] = byte(len(value))
		offset += 1
		for j, b := range value {
			p.options[offset+j] = b
		}
	}
	return offset + len(value)
}

func (p Packet) GetOption(code byte) []byte {
	i := 4
	for ; p.options[i] != code && p.options[i] != 255; i += 1 {
		i += int(p.options[i+1]) + 1
	}
	i += 2
	res := make([]byte, int(p.options[i-1]))
	for j := 0; j < len(res); j++ {
		res[j] = p.options[i+j]
	}
	return res
}

func PacketFromBytes(q []byte) Packet {
	p := Packet{}
	p.Op = q[0]
	p.Htype = q[1]
	p.Hlen = q[2]
	p.Hops = q[3]
	copy(p.Xid[:], q[4:8])
	copy(p.Secs[:], q[8:10])
	copy(p.Flags[:], q[10:12])
	copy(p.Ciaddr[:], q[12:16])
	copy(p.Yiaddr[:], q[16:20])
	copy(p.Siaddr[:], q[20:24])
	copy(p.Giaddr[:], q[24:28])
	copy(p.Chaddr[:], q[28:44])
	copy(p.Sname[:], q[44:108])
	copy(p.File[:], q[108:236])
	copy(p.options[:], q[236:])
	return p
}

func getAddr(ifi net.Interface) []byte {
	ip := [4]byte{}
	addrs, err := ifi.Addrs()
	if err != nil {
		fmt.Println("Cannot get interface address")
		os.Exit(1)
	}
	for _, addr := range addrs {
		if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				copy(ip[:], ipnet.IP)
				return ip[:]
			}
		}
	}
	return ip[:]
}

func getMask(ifi net.Interface) []byte {
	ip := [4]byte{}
	addrs, err := ifi.Addrs()
	if err != nil {
		fmt.Println("Cannot get interface address")
		os.Exit(1)
	}
	for _, addr := range addrs {
		if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				copy(ip[:], ipnet.Mask)
				return ip[:]
			}
		}
	}
	return ip[:]
}

func genXID() []byte {
	res := make([]byte, 4)
	for i := 0; i < 4; i++ {
		res[i] = byte(rand.Int31n(256))
	}
	return res
}

func (p Packet) GetType() byte {
	return p.GetOption(OptionDHCPMessageType)[0]
}

func MakeDiscover(ifi net.Interface) Packet {
	p := typePackege(1, 1, 6, 0, ifi)
	offset := p.addOption(OptionDHCPMessageType, 4, []byte{MessageTypeDiscover})
	copy(p.Xid[:], genXID())
	buf := make([]byte, 17, 17)
	copy(buf[1:], p.Chaddr[:])
	buf[0] = 1
	offset = p.addOption(OptionClientIdentifier, offset, buf)
	offset = p.addOption(OptionEnd, offset, []byte{})
	return p
}

func MakeOffer(discover Packet, ifi net.Interface) (p Packet, error string) {
	discover.Op = 2
	copy(discover.Siaddr[:], getAddr(ifi)[0:4])
	copy(discover.Sname[:4], "hope")
	identifier := discover.GetOption(OptionClientIdentifier)
	discover.options = [340]byte{99, 130, 83, 99}
	offset := discover.addOption(OptionDHCPMessageType, 4, []byte{MessageTypeOffer})
	offset = discover.addOption(OptionServerIdentifier, offset, getAddr(ifi))
	offset = discover.addOption(OptionSubnetMask, offset, getMask(ifi))
	offset = discover.addOption(OptionIPAddressLeaseTime, offset, []byte{1, 0xc, 2, 0})
	out, err := exec.Command("ip", "route", "show", "default").Output()
	if err != nil {
		return Packet{}, "Cannot run `ip` for get gateway"
	}
	gateway := make([]byte, 4)
	for i, s := range strings.Split(strings.Split(string(out), " ")[2], ".") {
		tmp, _ := strconv.Atoi(s)
		gateway[i] = byte(tmp)
	}
	offset = discover.addOption(OptionRouter, offset, gateway)
	if len(identifier) > 0 {
		offset = discover.addOption(OptionClientIdentifier, offset, identifier)
	}
	discover.addOption(OptionEnd, offset, []byte{})
	return discover, ""
}

func MakeRequest(offer Packet, ifi net.Interface) (p *Packet, error string) {
	request := typePackege(1, 1, 6, 0, ifi)
	request.Xid = offer.Xid
	offset := request.addOption(OptionDHCPMessageType, 4, []byte{MessageTypeRequest})
	offset = request.addOption(OptionRequestedIPAddress, offset, offer.Yiaddr[:])
	offset = request.addOption(OptionServerIdentifier, offset, offer.Siaddr[:])
	request.addOption(OptionEnd, offset, []byte{})
	return &request, ""
}

func MakeURequest(ifi net.Interface, ciaddr []byte, siaddr []byte) (p Packet) {
	p = typePackege(1, 1, 6, 0, ifi)
	p.Flags = [2]byte{0, 0}
	copy(p.Ciaddr[:], ciaddr)
	copy(p.Siaddr[:], siaddr)
	offset := p.addOption(OptionDHCPMessageType, 4, []byte{MessageTypeRequest})
	offset = p.addOption(OptionServerIdentifier, offset, getAddr(ifi))
	p.addOption(OptionEnd, offset, []byte{})
	return p
}

func MakeUAck(req Packet) (p Packet) {
	req.Op = 2
	p.Flags = [2]byte{0, 0}
	id := req.GetOption(OptionServerIdentifier)
	req.options = [340]byte{99, 130, 83, 99}
	offset := req.addOption(OptionDHCPMessageType, 4, []byte{MessageTypeAck})
	offset = req.addOption(OptionServerIdentifier, offset, id)
	req.addOption(OptionEnd, offset, []byte{})
	return req
}

func MakeDecline(request Packet, ifi net.Interface) *Packet {
	request.Op = 2
	request.options = [340]byte{99, 130, 83, 99}
	offset := request.addOption(OptionDHCPMessageType, 4, []byte{MessageTypeDecline})
	offset = request.addOption(OptionServerIdentifier, offset, getAddr(ifi))
	request.addOption(OptionEnd, offset, []byte{})
	return &request
}

func MakeAck(request Packet, ifi net.Interface) (p Packet, error string) {
	request.Op = 2
	copy(request.Yiaddr[:], request.GetOption(50))
	request.options = [340]byte{99, 130, 83, 99}
	offset := request.addOption(OptionDHCPMessageType, 4, []byte{MessageTypeAck})
	offset = request.addOption(OptionServerIdentifier, offset, getAddr(ifi))
	offset = request.addOption(OptionSubnetMask, offset, getMask(ifi))
	offset = request.addOption(OptionIPAddressLeaseTime, offset, []byte{1, 0xc, 2, 0})
	out, err := exec.Command("ip", "route", "show", "default").Output()
	if err != nil {
		return Packet{}, "Cannot run `ip` for get gateway"
	}
	gateway := make([]byte, 4)
	for i, s := range strings.Split(strings.Split(string(out), " ")[2], ".") {
		tmp, _ := strconv.Atoi(s)
		gateway[i] = byte(tmp)
	}
	offset = request.addOption(OptionRouter, offset, gateway)
	request.addOption(OptionEnd, offset, []byte{})
	return request, ""
}

func typePackege(op byte, htype byte, hlen byte, hops byte, i net.Interface) Packet {
	p := Packet{Op: op, Htype: htype, Hlen: hlen, Hops: hops}
	p.Flags[0] = 0x80
	copy(p.options[:4], cookieEdge[:])
	for j, b := range i.HardwareAddr {
		if j >= 8 {
			break
		}
		p.Chaddr[10+j] = b
	}

	return p
}
