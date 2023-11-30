#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        selfprotectionExample1.py
#
# Purpose:     This program is a test case example to show how to use the 
#              <processWatchDog.py> to protect itself to be kill/stopped by user
#              or other program.
#              
# Author:      Yuancheng Liu
#
# Version:     v_0.1
# Created:     2023/11/30
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
""" Related program / file : 
    1. processWatchDog.py
    2. selfprotectionWatchdog.py
    3. selfprotectRcd.txt
    4. recoverZips/selfprotectionWatchdog.zip
"""

import os
import wx
import time
import processWatchDog

PERIODIC = 2000
print("Current working directory is : %s" % os.getcwd())
dirpath = os.path.dirname(__file__)
print("Current source code location : %s" % dirpath)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class MalwareEmuFrame(wx.Frame):
    """ Program UI frame"""

    def __init__(self, targetInfo, rcdFile,  idx=0, frameTitle='MalwareEmuUI', bgColorStr='BLUE'):
        """ Frame init function.
        Args:
            targetInfo (dict): refer to <processWatchdog> init doc.
            recordPath (str): refer to <processWatchdog> init doc.
            idx(ing): refer to <processWatchdog> init doc.
            frameTitle (str, optional): frame windows title. Defaults to 'MalwareEmuUI'.
            bgColor: backgound color string
        """
        super().__init__(parent=None, title=frameTitle)
        self.SetBackgroundColour(wx.Colour(bgColorStr))
        logoImg = os.path.join(dirpath, 'logo.png')
        # Init the process protector
        self.protector = processWatchDog.processWatchdog(targetInfo, rcdFile,
                                                         idx=idx, interval=3)
        # Init the UI sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.stTxt = wx.StaticText(self, -1, " Self ID : \n Targt ID : \n Target Running :")
        self.stTxt.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.NORMAL))
        sizer.Add(self.stTxt)
        if os.path.exists(logoImg):
            bmp = wx.Bitmap(logoImg, wx.BITMAP_TYPE_ANY)
            # create image button using BitMapButton constructor
            button = wx.BitmapButton(self, id = wx.ID_ANY, bitmap = bmp,
                            size =(bmp.GetWidth()+10, bmp.GetHeight()+10))
            sizer.Add(button)
        self.SetSizer(sizer)

        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('Protect Target File: %s' %str(targetInfo[processWatchDog.TGT_PATH_KEY]))
        self.timer = wx.Timer(self)
        self.updateLock = False
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.timer.Start(PERIODIC)  # every 3 second
        # start the process watch dog thread.
        self.protector.start()
        self.Show()
        
#-----------------------------------------------------------------------------
    def periodic(self, event):
        """ Call back every periodic time."""
        now = time.time()
        print("main frame update at %s" % str(now))
        dataDict = self.protector.getCrtInfo()
        self.stTxt.SetLabel(" Self ID : %s \n Targt ID : %s \n Target Running : %s " % (
            str(dataDict['ownPid']), str(dataDict['tgtPid']), str(dataDict['tgtRun'])))

#-----------------------------------------------------------------------------
    def onClose(self, event):
        self.timer.Stop()
        self.protector.stop()
        self.Destroy()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    # Init the paramters : 
    tgtFile = os.path.join(dirpath, 'selfprotectionWatchdog.py')
    rcdFile = os.path.join(dirpath, 'selfprotectRcd.txt')
    targetInfo = {
        'path': tgtFile,    # target file path.
        # target file exeuction cmd
        'execution': 'python C:\\Works\\NCL\\Project\\Malware_Repo\\src\\processWatchDog\\selfprotectionWatchdog.py',  
        'backup': 'C:\\Works\\NCL\\Project\\Malware_Repo\\src\\processWatchDog\\recoverZips\\selfprotectionWatchdog.zip', # target program zip file
        'rcdIdx': 1 # configured id in record file.
    }
    ownIdx = 0
    # Create the App
    app = wx.App()
    frame = MalwareEmuFrame(targetInfo, rcdFile, idx=ownIdx, frameTitle='Self-Protection-Example')
    app.MainLoop()
