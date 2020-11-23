# Description

Simple implementation of TFTP protocol(RFC 1350):

Command:

- r `file_Name` : RRQ. Get file from server. If file doesn't exist, it will be announced. If file in client has same name with `file_Name`, it will be overwritten

- w `file_Name` : WRQ. Send file to server. If file in server already exist, it will be announced, and file cannot be overwritten

- other options will throw `Syntax Problem`
