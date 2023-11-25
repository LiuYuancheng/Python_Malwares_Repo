#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        tcpCom.py
#
# Purpose:     This module will provide TCP client and server communication API. 
#
# Author:      Yuancheng Liu
#
# Created:     2019/01/13
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License  
#-----------------------------------------------------------------------------

import socket

BUFFER_SZ = 4096    # TCP buffer size.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class tcpClient(object):
    """ TCP client module."""
    def __init__(self, ipAddr):
        """ Create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
            init example: client = tcpClient(('127.0.0.1', 502))
        """
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ipAddr = ipAddr
        self.connected = False  # connection state flag.
        self.connect()          # connect to the server.

#--tcpClient-------------------------------------------------------------------
    def connect(self, ipAddr=None):
        """ Connect/Reconnect to the TCP server and return connected state.(T/F) """
        if self.connected:
            self.client.close() # disconnect the existed connection.
            self.client = None  # re-init the socket for the new connection.
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not ipAddr is None: self.ipAddr = ipAddr
        try:
            self.client.connect(self.ipAddr)
            self.connected = True
        except:
            print("Connect to server %s failed" % str(self.ipAddr))
            self.connected = False
        return self.connected

#--tcpClient-------------------------------------------------------------------
    def sendMsg(self, msg=None, resp=False):
        """ Convert the msg to bytes and send it to TCP server. 
            - resp: server response flag, method will wait server's response and 
                return the bytes format response if it is set to True. 
        """
        if self.connected:
            if not isinstance(msg, bytes): msg = str(msg).encode('utf-8')
            self.client.send(msg)
            response = self.client.recv(BUFFER_SZ) if resp else True
            return response
        return False

#--tcpClient-------------------------------------------------------------------
    def disconnect(self):
        """ Send an empty message to inform the server (avoid make server block at 
            the recv() functiuon) and close the socket.
        """
        self.sendMsg(msg='')
        self.client.close()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class tcpServer(object):
    """ TCP server module. The way to insert this module into another program 
        by packaged it with a new thread is shown in the test case <tcpComTest.py>.
    """
    def __init__(self, parent, port, connectNum=1):
        """ Create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
            init example: server = tcpServer(None, 5005, connectNum=1)
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('0.0.0.0', port)) # 0.0.0.0 can host tcp from other server.
        self.server.listen(connectNum)
        self.terminate = False  # Server terminate flag.

#--tcpServer-------------------------------------------------------------------
    def serverStart(self, handler=None):
        """ Start the TCP server to handle the incoming messages."""
        print("TCP server started.")
        while not self.terminate:
            clientSocket, address = self.server.accept()
            print("Accepted new connection from %s" % str(address))
            while not self.terminate:
                request = clientSocket.recv(BUFFER_SZ)
                if request == b'': break  # client disconnected
                msg = handler(request) if not handler is None else request
                if not msg is None: # don't response client if the handler feed back is None
                    if not isinstance(msg, bytes): msg = str(msg).encode('utf-8')
                    clientSocket.send(msg)
        self.server.close()

#--tcpServer-------------------------------------------------------------------
    def serverStop(self):
        self.terminate = True

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Test case program: tcpComTest.py

def msgHandler(msg):
    """ The test handler method passed into the UDP server to handle the 
        incoming messages.
    """
    print("Incomming message: %s" % str(msg))
    return msg

def main():
    """ Main function used for demo the module."""
    print('Run the module as a TCP (1) TCP echo server (2)TCP client')
    uInput = str(input())
    if uInput == '1':
        print(" - Please input the TCP port: ")
        udpPort = int(str(input()))
        server = tcpServer(None, udpPort)
        print("Start the TCP echo server licening port [%s]" % udpPort)
        server.serverStart(handler=msgHandler)
    elif uInput == '2':
        print(" - Please input the IP address: ")
        ipAddr = str(input())
        print(" - Please input the TCP port: ")
        udpPort = int(str(input()))
        client = tcpClient((ipAddr, udpPort))
        while True:
            print(" - Please input the message: ")
            msg = str(input())
            resp = client.sendMsg(msg, resp=True)
            print(" - Server resp: %s" % str(resp))
    else:
        print("Input %s is not valid, program terminate." % str(uInput))

if __name__ == '__main__':
    main()

        
