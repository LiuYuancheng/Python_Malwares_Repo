#-----------------------------------------------------------------------------
# Name:        nmapUtils.py
#
# Purpose:     This module is a untility module of the lib <python-nmap> to provide
#              some extend function. The module need netowork scan software Nmap to 
#              be installed: https://nmap.org/download
#
# Author:      Yuancheng Liu
#
# Version:     v_0.1.1
# Created:     2023/03/10
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
""" Program Design:
    python-nmap is a python library which helps in using nmap port scanner. It allows 
    to easilly manipulate nmap scan results and will be a perfect tool for systems 
    administrators who want to automatize scanning task and reports. The nmapUtils module
    is a package moudle of python-nmap, it will parse the result of python-nmap and 
    only provide the result user need.

    <python-nmap> link: https://pypi.org/project/python-nmap/

"""
import re
import ipaddress
import nmap # pip install python-nmap, 

OPEN_TAG = 'open'       # Port opened 
CLOSE_TAG = 'closed'    # Port closed
FILTER_TAG = 'filtered' # Port touchable but no reponse or the response can not be recognised by nmap
UNKNOWN_TAG = 'unknown'
STATE_UP = 'up'
STATE_DOWN = 'down'

# Regular expression pattern string for IPv4 subnet format
SUBNET_PT_STR = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'  
# Regular expression pattern string for IPv4 address format
IP_PT_STR = r'^(\d{1,3}\.){3}\d{1,3}$'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class nmapScanner(object):
    """ A port scanner used to check the port, service state of a target IP. """

    def __init__(self) -> None:
        """ Init the scanner. Example: scanner = nmapScanner()"""
        self.scanner = nmap.PortScanner()
        self.resultDict = None

#-----------------------------------------------------------------------------
    def _parseNmapDict(self, nmapDict, protocalType='tcp', showFiltered=False):
        """ Convert the Nmap scan result dict to {'<portnum>':(<state>, <serviceType>), ...}
            format.
            Args:
                nmapDict (dict): nampScanDict[<ip>]
                protocalType (str, optional): protocalType. Defaults to 'tcp'.
                showFiltered (bool, optional): whether show 'filtered' port. Defaults to False.
            Returns:
                dict: refer to function introduction.
        """
        resultDict = {}
        if protocalType in nmapDict.keys():
            nmapInfo = nmapDict[protocalType]
            for port, state in nmapInfo.items():
                if state['state'] == FILTER_TAG and not showFiltered: continue
                serviceName = state['name'] if 'name' in state.keys() else UNKNOWN_TAG
                isopen = state['state'] if 'state' in state.keys() else CLOSE_TAG
                resultDict[str(port)] = (isopen, serviceName)
        return resultDict
#-----------------------------------------------------------------------------
    def getLastScanRawResult(self):
        return self.resultDict

#-----------------------------------------------------------------------------
    def scanPortDecorator(scanFunction):
        """ A decorator class to pre-check the target ip address, then call the detailed scan function 
            to do the port/service scan to update the reuslt.
            Args:
                scanFunction (_type_): a scan function same as below parameters config: 
                    scanFunction(self, target, portInfo, showFiltered=showFiltered)
        """
        def innerFunc(self, target, portInfo, showFiltered=False):
            self.resultDict = {}
            target = '127.0.0.1' if str(target).strip().lower() == 'localhost' else str(target).strip()
            self.resultDict = {'target': target, 'state': STATE_DOWN}
            # Call the detail scan function to update the <self.resultDict>
            # [*set(portInfo)] : remove the duplicate in the list [80, 80] => [80]
            scanFunction(self, target, [*set(portInfo)], showFiltered=showFiltered)
            if target in self.scanner.all_hosts():
                nmapInfo = self.scanner[str(target)]
                self.resultDict['state'] = nmapInfo.state()
                if self.resultDict['state'] == 'up':
                    self.resultDict.update(self._parseNmapDict(nmapInfo, protocalType='tcp',showFiltered=showFiltered))
            return self.resultDict.copy()
        return innerFunc
    
#-----------------------------------------------------------------------------
    @scanPortDecorator
    def scanTcpPorts(self, target, portList, showFiltered=False):
        """ Check a list TCP ports' state and service type.
            Args:
                target (_type_): target IP address/Url.
                portList (_type_): list of int ports.
                showFiltered (bool, optional): whether show the 'filtered' state port. 
                    Defaults to False.
            Returns:
                dict: example:  {   'target': '127.0.0.1', 
                                    'state': 'up', 
                                    '134': ('closed', 'ingres-net'), 
                                    '443': ('open', 'https'), 
                                    '3000': ('open', 'ppp')}
        """
        for i in portList:
            self.resultDict[str(i)] = (CLOSE_TAG, UNKNOWN_TAG) 
        argStr = '-p ' + ','.join([str(i) for i in portList])
        self.scanner.scan(hosts=target, arguments=argStr, timeout=10)

    #-----------------------------------------------------------------------------
    def scanTcpPortsOld(self, target, portList, showFiltered=False):
        """ Same as function function scanTcpPorts() without decorated, current this 
            function is not used.
        """
        if str(target).lower() == 'localhost': target = '127.0.0.1' 
        resultDict = {'target': target, 'state': 'down'}
        for i in portList:
            resultDict[str(i)] = (CLOSE_TAG, UNKNOWN_TAG) 
        argStr = '-p ' + ','.join([str(i) for i in portList])
        self.scanner.scan(hosts=target, arguments=argStr, timeout=10)
        if target in self.scanner.all_hosts():
            nmapInfo = self.scanner[str(target)]
            resultDict['state'] = nmapInfo.state()
            if resultDict['state'] == 'up':
                resultDict.update(self._parseNmapDict(nmapInfo, protocalType='tcp',showFiltered=showFiltered))
        return resultDict
    
#-----------------------------------------------------------------------------
    @scanPortDecorator
    def scanPortRange(self, target, portRange, showFiltered=False):
        """ Scan a port range and return the result.

            Args:
                target (str): target IP address/Url.
                portRange (tupple): (start port, end port)
                showFiltered (bool, optional): whether show the 'filtered' state port. 
                    Defaults to False.
            Returns:
                _type_: _description_
        """
        argStr = str(portRange[0])+'-'+str(portRange[1])
        self.scanner.scan(target, argStr, timeout=10)

    #-----------------------------------------------------------------------------
    def scanPortRangeOld(self, target, portRange, showFiltered=False):
        """ Same as function function scanPortRange()without decorated, current this 
            function is not used."""
        if str(target).lower() == 'localhost': target = '127.0.0.1' 
        resultDict = {'target': target, 'state': 'down'}
        argStr = str(portRange[0])+'-'+str(portRange[1])
        self.scanner.scan(target, argStr, timeout=10)
        if target in self.scanner.all_hosts():
            nmapInfo = self.scanner[str(target)]
            resultDict['state'] = nmapInfo.state()
            if resultDict['state'] == 'up':
                resultDict.update(self._parseNmapDict(nmapInfo, protocalType='tcp',showFiltered=showFiltered))
        return resultDict
    
#-----------------------------------------------------------------------------
    def fastScan(self, target):
        """ fast Scan a target, same as the cmd: nmap -F <ip> """
        return self._fastScanTarget(target, [])
    
    @scanPortDecorator
    def _fastScanTarget(self, target, portInfo, showFiltered=False):
        self.scanner.scan(hosts=target, arguments='-F', timeout=10)

#-----------------------------------------------------------------------------
    def scanServices(self, target, serviceList):
        """ Check a list of service type.
            Args:
                target (_type_): arget IP address/Url.
                serviceList (_type_): service list. 

            Returns:
                _type_: example:
                {   'target': '127.0.0.1', 
                    'state': 'up', 
                    'http': { '80': ('closed', 'http'),'8008': ('closed', 'http')}, 
                    'https': {'443': ('open', 'https')}
                }
            """
        resultDict = {'target': None, 'state': None}
        for se in serviceList:
            resultDict[str(se)] = {}
        self._scanServices(target, serviceList)
        resultDict['target'] = self.resultDict['target']
        resultDict['state'] = self.resultDict['state']
        for item in self.resultDict.items():
            key, val = item
            if isinstance(val, tuple):
                serviceType = val[-1]
                if serviceType in resultDict.keys():
                    resultDict[serviceType][key] = val
        return resultDict
         
    @scanPortDecorator
    def _scanServices(self, target, serviceList, showFiltered=False):
        #argStr = '-p ' + ','.join([str(i) for i in serviceList])
        #self.scanner.scan(hosts=target, arguments=argStr, timeout=10)
        self.scanTcpPorts(target, serviceList)

#-----------------------------------------------------------------------------
    def scanSubnetIps(self, subnetStr):
        """ Scan the subnet and find the reachable IP addresses. 
            Args:
                subnetStr (str): subnet string, such as 
        """
        # Check the input string valid
        pattern = re.compile(SUBNET_PT_STR)
        if bool(pattern.match(subnetStr)):
            self.scanner.scan(hosts=subnetStr, arguments='-sn')
            addresses = self.scanner.all_hosts()
            return addresses
        else:
            print("Error: scanSubnetIps() > Invalid subnet string: %s " %str(subnetStr))
            return None

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def testCase(mode):

    scanner = nmapScanner()
    if mode == 0:
        print("Test function: scanTcpPorts() ")
        print(' - 1.Scan reachable ip:')
        rst = scanner.scanTcpPorts('172.18.178.6', [22, 443,8008])
        print('\t', rst)
        print(' - 2.Scan reachable ip, show filtered port:')
        rst = scanner.scanTcpPorts('172.18.178.6', [80], showFiltered=True)
        print('\t', rst)
        print(' - 3.Scan un-reachable ip:')
        rst = scanner.scanTcpPorts('172.18.178.11', [80], showFiltered=True)
        print('\t', rst)
    elif mode == 4:
        print(' - 4.Scan localhhost:')
        rst = scanner.scanTcpPorts('localhost', [134, 443, 3000])
        print('\t', rst)
    elif mode == 5:
        print(' - 5.Scan port range 22 - 30')
        rst = scanner.scanPortRange('172.18.178.6', (22,30), showFiltered=True )
        print('\t', rst)
    elif mode == 6:
        print(' - 6.Fast scan')
        rst = scanner.fastScan('localhost')
        print('\t', rst)
    elif mode == 7:
        print(' - 7.Scan service test 1')
        rst = scanner.scanServices('localhost', ['http', 'http', 'ppp', 'https'])
        print('\t', rst)
    elif mode == 8:
        print(' - 8.Scan service test 2')
        rst = scanner.scanServices('sg.pool.ntp.org', ['ntp'])
        print('\t', rst)
    elif mode == 9:
        print(' - 9.Scan all IP address in Subnet')
        print('9.1 test invlid input')
        invalidSubnetStr = "172.18.178."
        rst = scanner.scanSubnetIps(invalidSubnetStr)
        print('\t', rst)
        subnetStr = "172.25.121.0/24"
        print('9.2 test scan subnet: %s' %str(subnetStr))
        rst = scanner.scanSubnetIps(subnetStr)
        print('\t', rst)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    testCase(9)
