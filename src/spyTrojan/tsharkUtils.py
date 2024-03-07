#-----------------------------------------------------------------------------
# Name:        tsharkUtils.py
#
# Purpose:     This module is a untility module of the lib <python-pyshark> to 
#              provide some extend traffic load and capturefunctions. The program 
#              needs to work with the below lib / software installed:
#              - pyshark: https://pypi.org/project/pyshark/
#              - tshark module of wireshark: https://www.wireshark.org/
#
# Author:      Yuancheng Liu
#
# Version:     v_0.1.1
# Created:     2024/03/07
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
""" Program design: We want to create a OOP WireShark wrapper program which can 
    be used as lib for other program to capture the host traffic. (Such as used 
    by the spytrojan) to eavesdroping / mirroring the victim's network communication.
    Additional Info: 
    - To get the device interface info, For Windows platform run: 
        'D:\Tools\Wireshark>tshark -D' to list all the network interfaces
    - Display filter doc: https://wiki.wireshark.org/DisplayFilters
"""

import os
import psutil
import pyshark  # https://github.com/KimiNewt/pyshark

MAX_TIMEOUT = 1800  # maximum packet capture time 1800 sec in one round.
MAX_PACKET_COUNT = 10000    # maximum number of packets capture in one round

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class trafficSniffer(object):
    """ Main traffic sniffer program."""
    def __init__(self, debugFlg=False) -> None:
        self.packetList = None
        self.captureFilePath = None
        self.maxTimeout = MAX_TIMEOUT
        self.maxPctnum = MAX_PACKET_COUNT
        self.crtNicInfo = {
            "name": None,
            "interface": None # in linux system the interface is same as the name
        }
        self.debugMD = debugFlg

    #-----------------------------------------------------------------------------
    def getLastCaptureFilePath(self):
        return self.captureFilePath

    #-----------------------------------------------------------------------------
    def getlastCaptureData(self, index=None):
        if self.packetList is None or len(self.packetList)==0: return None 
        if index is None:
            return self.packetList
        elif int(index) < len(self.packetList):
            return self.packetList[index]
        else:
            print("Idx out of range")
            return None
        
    #-----------------------------------------------------------------------------
    def loadCapFile(self, filePath, decryptionkKey=None):
        """ Load the network packet capture file (*.cap, *.pcap, *.pcapng)
            Args:
                filePath ([str]): pcap file path.
        """
        if os.path.exists(filePath):
            capture = pyshark.FileCapture(filePath, decryption_key=str(decryptionkKey))
            self.packetInfoLines = [str(cap).split('\n') for cap in capture]
            if self.debugMD: print(str(self.packetInfoLines))
            return True
        print(">> Error: loadCapFile() file %s not found." % str(filePath))
        return False
    
    #-----------------------------------------------------------------------------
    def resetSniffer(self):
        self.packetList = []
        self.captureFilePath = None
        self.crtNicInfo = {
            "name": None,
            "interface": None 
        } # in linux system the interface is same as the name

    def setMaxTimeout(self, maxTimeout):
        self.maxTimeout = int(maxTimeout)

    def setMaxPecketNum(self, maxPacketNum):
        self.maxPctnum = int(maxPacketNum)

    #-----------------------------------------------------------------------------
    def setNicInfo(self, nicName, deviceAddr):
        """ Set the current sniff network interface information.
            Args:
                nicName (str): NIC name 
                deviceAddr (str): interface ID.
        """
        nicList = psutil.net_if_addrs()
        if nicName in nicList.keys():
            self.crtNicInfo['name'] = nicName
            self.crtNicInfo['interface'] = deviceAddr
            self.packetList = []
            return True
        print(">> Error: the NIC name is not found on the target")
        return False

    #-----------------------------------------------------------------------------
    def capture2File(self, filePath, displayFilter=None, timeoutInt=30):
        """ Capture the packet to file. If applied the filter, only capture the 
            packet which match the filter.

            Args:
                filePath (str): pcap file path
                displayFilter (str, optional): display filter https://wiki.wireshark.org/DisplayFilters
                    Defaults to None.
                timeoutInt (int, optional): Capture time. Defaults to 30.
            Returns:
                bool: True if capture successful. False if the interface not config.
        """
        if self.crtNicInfo['interface'] is None: return False
        timeoutInt = int(min(timeoutInt, self.maxTimeout))
        if not str(filePath).lower().endswith('.pcap'): filePath+='.pcap'
        self.captureFilePath = filePath
        # Pre create the pcap file:
        if not os.path.exists(self.captureFilePath):
            try:
                with open(self.captureFilePath, 'w') as fp:
                    print("Created the pcap file %s" %str(self.captureFilePath))
            except Exception as err:
                print(">> Error: capture2File() unable to create pcap file: %s" % str(err))
                return False
        capture = pyshark.LiveCapture(interface=self.crtNicInfo['interface'], 
                            output_file=filePath, 
                            display_filter=displayFilter)
        print("Start to capture interface [%s] to file, timeout=%s." % (self.crtNicInfo['name'], str(timeoutInt)))
        capture.sniff(timeout=timeoutInt)
        print("Capture finished.")
        return True

    #-----------------------------------------------------------------------------
    def capture2Mem(self, displayFilter=None, packetCount=20):
        """ Capture the packet in the memory <self.packetList>
            Args:
                displayFilter (str, optional): display filter. Defaults to None.
                packetCount (int, optional): number of packet which can match to 
                    the filter. Defaults to 20.
            Returns:
                bool: True if capture successful. False if the interface not config.
        """
        if self.crtNicInfo['interface'] is None: return False
        packetCount = int(min(packetCount, self.maxPctnum))
        capture = pyshark.LiveCapture(interface=self.crtNicInfo['interface'], 
                                      display_filter=displayFilter)
        print("Start to capture interface [%s] to file, packetNum=%s." % (self.crtNicInfo['name'], str(packetCount)))
        for captureArr in capture.sniff_continuously(packet_count=packetCount):
            self.packetList.append(captureArr)
        return True
    
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def testCase(mode=0):
    sniffer = trafficSniffer(debugFlg=True)
    dirpath = os.path.dirname(__file__)
    sniffer.setNicInfo('Wi-Fi', '\\Device\\NPF_{172B21B5-878D-41B5-9C51-FE1DD27C469B}')
    if mode == 0:
        print("Test case 0: sniff traffic to pcap file.")
        snifFileName = os.path.join(dirpath, "test.pcap")
        sniffer.capture2File(snifFileName, timeoutInt=10)
        print("file path: %s" %str(sniffer.getLastCaptureFilePath()))
    elif mode == 1:
        print("Test case 1: sniff to memory")
        sniffer.capture2Mem(packetCount=10)
        data = sniffer.getlastCaptureData()
        for packet in data:
            print(packet)
    elif mode == 2:
        # This test need to run ping google.com cmd during the exection.
        print("Test case 2: sniff to memory with filter")
        filterStr = 'icmp'
        sniffer.capture2Mem(displayFilter=filterStr, packetCount=2)
        data = sniffer.getlastCaptureData()
        for packet in data:
            print(packet)
    else:
        # add the new test case
        pass

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    mode = 0
    print("Please type in the test case number you want to run: ")
    uInput = str(input())
    mode = int(uInput)
    testCase(mode)
