#-----------------------------------------------------------------------------
# Name:        networkServiceProber.py
#
# Purpose:     This module is prober function module used to check the target 
#              nodes service state through the network connection. The service
#              can be checked contents: NTP, http, https, FTP
#
# Author:      Yuancheng Liu
#
# Version:     v_0.1.2
# Created:     2023/03/11
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import socket
import requests
import urllib.request

import ntplib
import http.client
from ftplib import FTP

from pythonping import ping
DEF_TIMEOUT = 3 

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class Prober(object):
    """ A simple object with a private debugPrint function. the probe lib function 
        will be inheritance of it.
    """
    def __init__(self, debugLogger=None) -> None:
        self._debugLogger = debugLogger
        self._logInfo = 0
        self._logWarning = 1
        self._logError = 2
        self._logException =3 

    def _debugPrint(self, msg, prt=True, logType=None):
        if prt: print(msg)
        if not self._debugLogger: return 
        if logType == self._logWarning:
            self._debugLogger.warning(msg)
        elif logType == self._logError:
            self._debugLogger.error(msg)
        elif logType == self._logException:
            self._debugLogger.exception(msg)
        elif logType == self._logInfo:
            self._debugLogger.info(msg)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class networkServiceProber(Prober):
    """ 
    """
    def __init__(self, debugLogger=None) -> None:
        """ Init the obj, example: driver = networkServiceProber()"""
        super().__init__(debugLogger=debugLogger)
        self.tcpPortChecker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ntpClient = ntplib.NTPClient()
        
    def _parseTarget(self, target):
        """ Validate the input target IP-address/domain-name"""
        target = str(target).replace(' ', '')
        return '127.0.0.1' if target.lower() == 'localhost' else target

#-----------------------------------------------------------------------------
    def checkPing(self, target, timeout=0.5):
        """ Check whether the target is pingable (ICMP service avaliable).
            Args:
                target (str): IP-address/domain-name
                timeout (float, optional): ping timeout. Defaults to 0.5.
            Returns:
                dict(): {'target': '<target>', 'ping': [min(ms), avg(ms), max(ms)]} if pingable.
        """
        target = self._parseTarget(target)
        resultDict = {'target': target, 'ping': None}
        try:
            data = ping(target, timeout=timeout, verbose=False)
            if data.rtt_max_ms < timeout*1000:
                resultDict['ping'] = [data.rtt_min_ms, data.rtt_avg_ms, data.rtt_max_ms]
        except Exception as err:
            self._debugPrint("Error: checkPing(): target [%s] not pingable, " %target, logType=self._logWarning)
        return resultDict

#----------------------------------------------------------------------------- 
    def checkTcpConn(self, target, portList, timeout=1):
        """ Check a target's TCP service's ports are connectable.
            Args:
                target (str): IP-address/domain-name
                portList (list): [int, ...]
                timeout (float, optional): TCP connection timeout. Defaults to 1 sec.
            Returns:
                dict() : {'target': '<target>', '<port1>": True/Fase, ...}
        """
        resultDict = {'target': target}
        try:
            target = socket.gethostbyname(self._parseTarget(target)) # translate hostname to IPv4 if it is a doman
        except:
            self._debugPrint("Error: checkTcpConn() Invalid host: [%s]" %str(target), logType=self._logError)
            return resultDict
        
        socket.setdefaulttimeout(timeout)
        for port in portList:
            resultDict[str(port)] = False
            try:
                result = self.tcpPortChecker.connect_ex((str(target), int(port)))
                resultDict[str(port)] = result == 0
            except socket.gaierror as err:
                resultDict['target'] = None
                self._debugPrint("Hostname [%s] Could Not Be Resolved." %str(target), logType=self._logError)
                break
            except socket.error:
                resultDict['target'] = None
                self._debugPrint("Host ip [%s] is not reponsed." %str(target), logType=self._logError)
                break
            except Exception as err:
                self._debugPrint("Exception happens: %s" %str(err), logType=self._logException)
                continue
        return resultDict

#----------------------------------------------------------------------------- 
    def checkNtpConn(self, target, pingFlg=False, portFlg=False, ntpPort=123):
        """ Check whether a NTP(Network Time Protocol) service is avaliable. As if we use the nmap
            to scan the port, most of the public ntp server will ban the client who did the ports
            scan for their server, so the port state may show 'down' 

            Args:
                target (_type_): IP-address/domain-name
                pingFlg (bool, optional): whether ping the server. Defaults to False.
                portFlg (bool, optional): whether check ntp Port connectable. Defaults to False.
                ntpPort (int, optional): ntp port. Defaults to 123.

            Returns:
                dict() : {'target': '<target>', 'ping': [...], 'ntp': <time offset> }
        """
        target = self._parseTarget(target)
        resultDict = {'target': target, 'ping': None, 'ntp': None}
        # Check ping
        if pingFlg:resultDict.update(self.checkPing(target))
        # Check port Open
        if portFlg: resultDict.update(self.checkTcpConn(target, [ntpPort]))
        # Fetch time offset data
        try:
            data = self.ntpClient.request(target, version=3)
            resultDict['ntp'] = data.offset
        except Exception as err:
            self._debugPrint("Time server [%s] not response" % str(target), self._logException)
        return resultDict

#----------------------------------------------------------------------------- 
    def checkHttpConn(self, target, requestConfig, timeout=3):
        """ Check a http/https service is connectable.
            Args:
                target (str): IP-address/domain-name
                requestConfig (dict): { 'conn': <'http'/'https'>, 
                                        'port': <int>, 
                                        'req':  <Request type str ('GET. 'HEAD'')>, 
                                        'par' : <request parameter str('/')>}
                timeout (int, optional): connection timeout. Defaults to 3.

            Returns:
                dict: { target': target, 
                        'conn': 'http',
                        'port': 80 
                        '<req>:<par>' :(status, reason)}
        """
        target = self._parseTarget(target)
        #target = target.replace('http', 'https') if 'http://' in target else 'https://' + target
        resultDict = {  'target': target, 
                        'conn': 'http',
                        'port': 80 }
        if 'conn' in requestConfig.keys(): resultDict['conn'] = str(requestConfig['conn']).lower()
        if 'port' in requestConfig.keys(): resultDict['port'] = int(requestConfig['port'])
        conn = http.client.HTTPSConnection(target, resultDict['port'], timeout) if resultDict['conn'] == 'https' else http.client.HTTPConnection(
            target, resultDict['port'], timeout)
        req = requestConfig['req'] if 'req' in requestConfig.keys() else 'HEAD'
        par = requestConfig['par'] if 'par' in requestConfig.keys() else '/'
        resultDict[':'.join((req, par))] = None
        try:
            conn.request(req, par)
            rst = conn.getresponse()
            resultDict[':'.join((req, par))] = (rst.status, rst.reason)
        except Exception as error:
            self._debugPrint("Error when connect to the target: %s " %str(target), logType=self._logException)
        if conn: conn.close()
        return resultDict

#----------------------------------------------------------------------------- 
    def checkHttpRquest(self, requestType, url, param):
        """ Check the http request. 
        Args:
            requestType (str): the request type 'get'/'post'
            url (str): api/php url
            param (dict): get or post input dict

            GET request input example: 
            {
                "url" : "https://jsonplaceholder.typicode.com/posts/",
                "type" : "get",
                "parm": {
                    "id": [1, 2, 3], 
                    "userId":1
                }
            }
            
            POST request input example:
            {
                "url" : "https://jsonplaceholder.typicode.com/posts",
                "type" : "post",
                "parm": {
                    "userID": 1,
                    "id": 1,
                    "title": "Making a POST request",
                    "body": "This is the data we created."
                }
            }
        """
        showRst = False 
        if showRst: print("Send %s http request." %str(requestType))
        if str(requestType).lower() == 'get':
            try: 
                resp = requests.get(url = url, params = param)
                if showRst: print(resp)
            except Exception as err:
                print("Get request error for url: %s" %str(url))
        elif str(requestType).lower() == 'post':
            try: 
                resp = requests.get(url, json= param)
                if showRst: print(resp)
            except Exception as err:
                print("Post request error for url: %s" %str(url))
        else:
            print("Not supported requst type: %s" %str(requestType))

#----------------------------------------------------------------------------- 
    def checkFtpConn(self, target, loginConfig=None, timeout=3):
        """ Check a ftp service is connectable.
            Args:
                target (str): IP-address/domain-name
                loginConfig (dict, optional): {'user':<str>, 'password':<str>}. Defaults to None.
                timeout (int, optional): connection timeout.. Defaults to 3.

            Returns:
                _type_: { 'target': <target>, 'conn': False, 'login': <Login state> }
        """
        target = self._parseTarget(target)
        resultDict = { 'target': target, 'conn': False, 'login': False }
        try:
            ftpClient = FTP(target, timeout=timeout)
            resultDict['conn'] = True
            # try to login to confirm 
            logResp = ftpClient.login(user=loginConfig['user'], passwd=loginConfig['password']) if loginConfig else ftpClient.login()
            resultDict['login'] = logResp
        except Exception as err:
            self._debugPrint("Error to connect to the FTP server: %s" %str(err), self._logException)
        return resultDict

#----------------------------------------------------------------------------- 
    def checkUrlsConn(self, urlList):
        """ Check whether a list of url can be opened.
            Args:
                    urlList (list): urllist
            Returns:
                dict: {target: 'urlList', <url1>:<state>, ...}
        """
        resultDict = { 'target': 'urlList' }
        for url in urlList:
            resultDict[str(url)] = False
            try:
                _ = urllib.request.urlopen(url)
                resultDict[str(url)] = True
            except Exception as err:
                self._debugPrint("Url [%s] can not be opened" %url, self._logWarning)
        return resultDict

#----------------------------------------------------------------------------- 
#-----------------------------------------------------------------------------
def testCase(mode):
    # Init the logger;
    import os, sys
    import Log
    DIR_PATH = dirpath = os.path.dirname(__file__)
    TOPDIR = 'src'
    LIBDIR = 'lib'
    idx = dirpath.find(TOPDIR)
    gTopDir = dirpath[:idx + len(TOPDIR)] if idx != -1 else dirpath   # found it - truncate right after TOPDIR
    # Config the lib folder 
    gLibDir = os.path.join(gTopDir, LIBDIR)
    if os.path.exists(gLibDir):
        sys.path.insert(0, gLibDir)
    APP_NAME = ('TestCaseLog', 'networkServiceProber')
    import Log
    Log.initLogger(gTopDir, 'Logs', APP_NAME[0], APP_NAME[1], historyCnt=100, fPutLogsUnderDate=True)


    driver = networkServiceProber(debugLogger=Log)
    if mode == 0:
        result = driver.checkPing('172.18.178.6')
    if mode == 1:
        result = driver.checkTcpConn('172.18.178.6', [22, 23])

    elif mode ==2:
        result = driver.checkNtpConn('0.sg.pool.ntp.org', pingFlg=False, portFlg=False)
    
    elif mode ==3:
        testhttpCofig = {
            'target': '127.0.0.1',
            'port': 3000,
            'conn': 'http',
            'req': 'HEAD',
            'par': '/'
            }
        result = driver.checkHttpConn('127.0.0.1',testhttpCofig)
        print(result)
        testhttpCofig = {
            'target': '127.0.0.1',
            'port': 8080,
            'conn': 'http',
            'req': 'GET',
            'par': '/horizon'
            }
        result = driver.checkHttpConn('127.0.0.1',testhttpCofig)
    elif mode == 4:
        result = driver.checkFtpConn('ftp.pureftpd.org')
    elif mode == 5:
        testList = ['https://www.google.com/', '123123']
        result = driver.checkUrlsConn(testList)
    print(result)


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    testCase(5)
