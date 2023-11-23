#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SSHconnector.py
#
# Purpose:     This module is used to create a ssh connector to provide nested 
#              ssh tunnel connection through jumphosts with an editable tcp port.
#              (host with NAT port forwarding setup such as: ssh -p port ...@host).
#              
# Author:      Yuancheng Liu
#
# Created:     2022/08/01
# Version:     v_0.1
# Copyright:   National Cybersecurity R&D Laboratories
# License:     
#-----------------------------------------------------------------------------
""" Program Design:
    We want to create a ssh connector program to provide single/multiple ssh access
    tunnel function through jumphosts and execute command as normal user or admin on
    different host. The commands will be added in a queue and execution sequence will
    be FIFO.
    
    SSH tunnel function:

    1.Single connection 
        A ---> jumphost1 ---> jumphost2---> ... ---> targethost (run cmd)

    2.Multiple connection (root)
        A ---> jumphost1 ---> jumphost2 ---> ... ---> targethost1 (run cmd)
                    |
                    + ---> jumphost3 ---> ... ---> targethost2
                                |
                                + ---> jumphost4 ---> ... ---> targethost3

    3.Multiple connection (tree)
        A ---> jump host1 ---> target host
               |
        B ---> +
               |
        C ---> +

    Dependency:
    This module need to use the python paramiko ssh lib: https://www.paramiko.org/
    
    Usage steps:
    1. Init all the connectos.
    2. Create the ssh tunnel chain by addChlid() function.
    3. Add the cmd you want to execute and the reply handler function in each host's 
       related connector by addCmd() function.
    4. Init the ssh tunnel chain by all the root connector's InitTunnel().
    5. Run all the cmds in every connecot by call the root connectors' runCmd() function.
    6. After finished call root connector's close() to close all the ssh session.

    Detail usage example refer to testcase file <sshConnectorTest.py>

"""

import time
import paramiko
CH_KIND = 'direct-tcpip' # open channel type/kind for jump hosts, we use direct TCP.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class sshConnector(object):

    def __init__(self, parent, host, username, password, port=22) -> None:
        """ Init the ssh connector obj.
        Args:
            parent (sshConnector or paramiko.SSHClient: parent ssh client.
            host (str): host ip address or host domain name.
            username (str): username.
            password (str): user password.
            port (int, optional): ssh port. Defaults to 22.
        """
        # init public parameters.
        self.parent = parent        # object parent. 
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        
        self.childConnectors = []   # children connectors.
        self.cmdlines = []          # commands need to run under the current host.
        self.replyHandler = None    # own reply handler.
        self.lock = False           # lock the new added in

#-----------------------------------------------------------------------------
    def addChild(self, childConnector):
        """ Add a ssh connector/paramiko.SSHClient as a child. 
        Args:
            childConnector (sshConnector): ssh connector/paramiko.SSHClient object.
        Returns:
            bool: True if the chlid is added. 
        """
        if self.lock: 
            print("Error: can not add new child host: children host adding locked!")
            return False
        self.childConnectors.append(childConnector)
        return True

#-----------------------------------------------------------------------------
    def addCmd(self, cmdline, handleFun=None):
        """ Add the a cmd need to be executed in the current connector. (remove
            all the cmds in the command list if the input is 'None')
        Args:
            cmdline (string): command line string.
            handleFun: a function use to handle the command response. default use 
                       None. Below reply dict will be passed in the handle function.
                       reply = { 'host': self.host,
                                 'cmd':  cmdline,
                                 'reply':stdout.read().decode()}
        """
        if cmdline is None: 
            self.cmdlines = []
        else:
            self.cmdlines.append((cmdline, handleFun))

#-----------------------------------------------------------------------------
    def clearChildren(self):
        """ Remove all the children connectors."""
        self.close()
        self.lock = False
        self.childConnectors = []

#-----------------------------------------------------------------------------
    def updateParent(self, parent):
        """ Update the current connector's parent if it doesn't have one."""
        if not self.parent:
            self.parent = parent
            return True
        return False 

#-----------------------------------------------------------------------------
    def InitTunnel(self):
        """ Lock the setting and init the ssh chain tunnel."""
        self.lock = True    # lock the connector's edit after tunnel init.
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.parent and self.parent.client:  # the parent's client need to be init.
            # create a transport socket channel if the connector is mid jumphost.
            transport = self.parent.client.get_transport()
            srcAddr = (self.parent.host, self.parent.port)
            destAddr = (self.host, self.port)
            # create the channle from parent to current host.
            channel = transport.open_channel(CH_KIND, destAddr, srcAddr)
            self.client.connect(self.host, username=self.username,
                                password=self.password, port=self.port, sock=channel)
        else:
            self.client.connect(self.host, username=self.username,
                                password=self.password, port=self.port)
        # Init all the children.
        for childconnector in self.childConnectors:
            childconnector.InitTunnel()

#-----------------------------------------------------------------------------
    def runCmd(self, interval=0.1):
        """ Run the cmd in the command queue one by one, sleep time interval 
            after finihsed executed one command.
        Args:
            interval (_type_, optional): Sleep time after time interval (unit second). 
                                        Defaults to None.
        """
        if not self.lock:
            print("Error: can not run cmd, please init the tunnel first!")
            return
        for cmdset in self.cmdlines:
            cmdline, handleFun = cmdset
            print("Run cmd in host: %s" % str(self.host))
            # Request a pseudo-terminal for the sudo to input the admin password.
            pty = 'sudo' in cmdline
            stdin, stdout, stderr = self.client.exec_command(cmdline, get_pty=pty)  # edited#
            # Input the sudo password, TODO: will add the function updateSudoPasswd() later.
            if pty:
                stdin.write('%s\n' % self.password)
                stdin.flush()
            if interval:
                time.sleep(interval)
            # Handle the cmd reply.    
            rplDict = {'host': self.host, 'cmd':  cmdline, 'reply':stdout.read().decode()} if self.replyHandler or handleFun else None
            if handleFun: handleFun(rplDict)
            if self.replyHandler: self.replyHandler(rplDict)

        for childconnector in self.childConnectors:
            childconnector.runCmd(interval=interval)

#-----------------------------------------------------------------------------
    def getTransport(self):
        if not self.lock:
            print("The tunnel is not init, please call the initTunnel first!")
            return None
        else:
            return self.client.get_transport()

#-----------------------------------------------------------------------------
    def setAllreplyHandler(self, func):
        """ set the replay handler for all the cmd's reply.
        Args:
            func (reference): function.
        """
        self.replyHandler = func

#-----------------------------------------------------------------------------
    def close(self):
        """ Close all session."""
        for  childConnector in self.childConnectors:
            childConnector.close()
        if self.client: self.client.close()


