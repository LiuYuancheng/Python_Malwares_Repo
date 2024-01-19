#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SCPconnector.py
#
# Purpose:     This module will use SSHconnector and python-scp module to scp 
#              upload/download file from the program running host to the dest 
#              server (through a jump hosts chain).
#              
# Author:      Yuancheng Liu
#
# Created:     2022/08/01
# Version:     v_0.1
# Copyright:   National Cybersecurity R&D Laboratories
# License:     
#-----------------------------------------------------------------------------
""" Program Design:
    We want to create a scp connector which can scp transfer files (upload/download) 
    thought a ssh jumphosts chain: 
    
    scpConnectorHost ---> jumphost1 ---> jumphost2---> ... ---> destinationHost
    
    Dependency: 
    This module need to use: 
    - SSHconnector
    - python scp module: https://pypi.org/project/scp/

    Usage Example:
        destInfo = ('gateway.ncl.sg', '<userA>', '<userApassword>')
        scpClient = scpConnector(destInfo, showProgress=True)
        scpClient.uploadFile('scpTest.txt', '~/scpTest2.txt')
        scpClient.downFile('~/scpTest2.txt')
        scpClient.close()

        Detail usage example refer to testcase file <scpConnectorTest.py>
"""

import os
import sys
from scp import SCPClient
from SSHconnector import sshConnector

TNL_TEST_CMD = 'pwd' # a test cmd to confirm the ssh tunnel is ready. 

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

class scpConnector(object):

    def __init__(self, destInfo, jumpChain=None, showProgress=False) -> None:
        """ Init the connector.
        Args:
            destInfo (tuple): The destation host's ssh login information. 
                example: (sshHost(ip/domain), userName, password) 
            jumpChain (list, optional): The jump host chain ssh info:
                scpConnectorHost ---> jumphost1 ---> jumphost2---> ... ---> destinationHost
                [jumphost1Infor, jumphost2Info]. 
                example: 
                    [(JumpHost1_ip, userName, password),  (JumpHost2_ip, userName, password) ...]
                Defaults to None.
            showProgress (bool, optional): Flag to identify whether show the file transmation 
                progress. Defaults to False, better to set True when transfer big file.
        """
        self.destHost = None
        if len(destInfo) != 3:
            print("The destination information is invalid: %s" %str(destInfo))
            return None
        sshHost, userName, password = destInfo
        if jumpChain is None or len(jumpChain) == 0:
            self.destHost = sshConnector(None, sshHost, userName, password)
            self.destHost.addCmd(TNL_TEST_CMD, None)
            self.destHost.InitTunnel()
            self.destHost.runCmd(interval=0.1)
        else:
            jumpHostHead = jumpHostTail = None
            for jumpInfo in jumpChain:
                sshHostJP, userNameJP, passwordJP = jumpInfo
                if jumpHostHead is None:
                    jumpHostHead = jumpHostTail = sshConnector(None, sshHostJP, userNameJP, passwordJP)
                else:
                    jumpHost = sshConnector(jumpHostTail, sshHostJP, userNameJP, passwordJP)
                    jumpHostTail.addChild(jumpHost)
                    jumpHostTail = jumpHost
            self.destHost = sshConnector(jumpHostTail, sshHost, userName, password)
            self.destHost.addCmd(TNL_TEST_CMD, None)
            jumpHostTail.addChild(self.destHost)
            jumpHostHead.InitTunnel()
            jumpHostHead.runCmd(interval=0.1)
        if self.destHost is None:
            print('SSH tunnel fault')
            return None
        # File transfer progress display function. 
        def progress4(filename, size, sent, peername):
            sys.stdout.write(" => (%s:%s) %s's progress: %.2f%%   \r" % (peername[0], peername[1], filename, float(sent)/float(size)*100))
        self.scpClient = SCPClient(self.destHost.getTransport(), progress4=progress4) if showProgress else SCPClient(self.destHost.getTransport())
        print("scpConnector ready.")

#-----------------------------------------------------------------------------
    def uploadFile(self, srcPath, destPath):
        """ Upload srcPath file to the destination. 
        Args:
            srcPath (str): source file path.
            destPath (str): desination file path.
        """
        if self.scpClient:
            if os.path.exists(srcPath):
                try:
                    self.scpClient.put(srcPath, destPath)
                    print("File %s transfer finished" % str(srcPath))
                except Exception as err:
                    print("File translate failed: %s" % str(err))
            else:
                print("The srouce file is not exist")
        else:
            print("The scpConnector is not inited.")

#-----------------------------------------------------------------------------
    def downFile(self, srcPath, localPath=''):
        """ download file from destination.
        Args:
            srcPath (_type_): destination host file path.
            localPath (str, optional): local path. Defaults to '' same as the program
                folder.
        """
        if self.scpClient: 
            try:
                self.scpClient.get(srcPath, local_path=localPath)
                if localPath and os.path.exists(srcPath):
                    print("File %s transfer finished" % str(srcPath))
            except Exception as err:
                print("File translate failed: %s" %str(err))
        else:
            print("The scpConnector client is not inited")

#-----------------------------------------------------------------------------
    def close(self):
        """ close the scpClient and the sshTunnel."""
        self.scpClient.close()
        self.destHost.close()


