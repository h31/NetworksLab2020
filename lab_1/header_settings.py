H_LEN_CHAR = 8  # how much char are in header for length of message
H_NAME_CHAR = 8  # nickname max len
H_TIME_CHAR = 16  # char count for time in header
CLIENT_HEADER_LENGTH = H_LEN_CHAR + H_NAME_CHAR
SERVER_HEADER_LENGTH = H_LEN_CHAR + H_NAME_CHAR + H_TIME_CHAR
