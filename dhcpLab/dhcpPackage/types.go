package dhcpPackage

const (
	ServerPort = 67 //67
	ClientPort = 68 //68
)

const (
	MessageTypeDiscover byte = 1
	MessageTypeOffer    byte = 2
	MessageTypeRequest  byte = 3
	MessageTypeDecline  byte = 4
	MessageTypeAck      byte = 5
	MessageTypeNak      byte = 6
	MessageTypeRelease  byte = 7
	MessageTypeInform   byte = 8
)

const (
	OptionSubnetMask           byte = 1
	OptionRouter               byte = 3
	OptionHostName             byte = 12
	OptionRequestedIPAddress   byte = 50
	OptionIPAddressLeaseTime   byte = 51
	OptionOptionOverload       byte = 52
	OptionDHCPMessageType      byte = 53
	OptionServerIdentifier     byte = 54
	OptionParameterRequestList byte = 55
	OptionMessage              byte = 56
	OptionClientIdentifier     byte = 61
	OptionEnd                  byte = 255
)

var MessageNames = map[byte]string{
	MessageTypeDiscover: "Discover",
	MessageTypeOffer:    "Offer",
	MessageTypeRequest:  "Request",
	MessageTypeDecline:  "Decline",
	MessageTypeAck:      "Ack",
	MessageTypeNak:      "Nak",
	MessageTypeRelease:  "Release",
	MessageTypeInform:   "Inform",
}

var OptionNames = map[byte]string{
	OptionSubnetMask:           "Subnet Mask",
	OptionRouter:               "Router",
	OptionHostName:             "HostName",
	OptionRequestedIPAddress:   "Requested address",
	OptionIPAddressLeaseTime:   "IP lease time",
	OptionOptionOverload:       "Option extended",
	OptionDHCPMessageType:      "Message type",
	OptionServerIdentifier:     "Server id",
	OptionParameterRequestList: "Requested parameters",
	OptionMessage:              "Message",
	OptionClientIdentifier:     "Client id",
}
