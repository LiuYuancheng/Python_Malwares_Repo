#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        keyEventActor.py
#
# Purpose:     This module will prvoide the computer keyboard actions handling 
#              function such as key record, play back, simulate user type in.
# Author:      Yuancheng Liu
#
# Version:     v_0.1.2
# Created:     2023/01/02
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
""" Program design: 
    We want to design one keyboard event actor program which can be used by our 
    Kypo tool to test user simulation login and record all the user's keybopard 
    input during the CS2107 mid-term exam in each lab machine.
"""

import time
import json
import threading 
import keyboard # keyboard event for windows.(Linux need sudo permission to execute this)
from pynput.keyboard import Key, Controller # keyboard event for Linux (no need sudo permit)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class keyEventActor(threading.Thread):
    """ Actor used to emulator user's key input.
        Args: winOS (bool): Windows OS Flag.
    """
    def __init__(self, winOS=True) -> None:
        threading.Thread.__init__(self)
        self.linuxKeyHd = None if winOS else Controller()
        self.recordFlg = False
        self.recordTime = 0
        self.keyEventList = None
        self.ternamted = False

    #-----------------------------------------------------------------------------
    def _linuxKeyMatch(self, char):
        """ convert key string to the pynput's key event parameter."""
        charL = str(char)
        if charL.lower() == 'tab':
            return Key.tab
        elif charL.lower() == 'shift':
            return Key.shift
        elif charL.lower() == 'enter':
            return Key.enter
        return char

    def clearRecord(self):
        """ Clear the current record."""
        self.keyEventList = None

    #-----------------------------------------------------------------------------
    def run(self):
        print("Keyboard event actor thread started.")
        while not self.ternamted:
            if self.recordFlg:
                #print("record flg: %s" %str(self.recordFlg))
                print("Start record user's keyboard event: %s" %str(self.recordTime))
                if self.recordTime > 0:
                    time.sleep(self.recordTime)
                    self.stopLogKeyInput()
                else:
                    while self.recordFlg:
                        time.sleep(1)
                print("Key record procedure finished.")
            time.sleep(0.1)

    #-----------------------------------------------------------------------------
    def playbackKeyEventList(self, keyEventList=None):
        if keyEventList is None: keyEventList = self.keyEventList
        k_thread = threading.Thread(target = lambda :keyboard.play(keyEventList))
        k_thread.start()

    #-----------------------------------------------------------------------------
    # Define all the get() functions here:           
    def getKeyEventList(self):
        return self.keyEventList

    def getKeyEventList(self):
        return self.keyEventList

    def getLinuxKeyHd(self):
        return self.linuxKeyHd 

    def getLastKeyEventRcd(self):
        return self.keyEventList

    def getKeyEventRcdStr(self):
        if self.keyEventList is None: return ''
        inputStr = ''
        for event in self.keyEventList:
            dataJson = json.loads(event.to_json())
            if dataJson['event_type'] == 'down':
                char = '\n' if dataJson['name'] == 'enter' else dataJson['name']
                inputStr+=char
        return inputStr

    #-----------------------------------------------------------------------------
    def pressAndrelease(self, keySet, interval=0.1):
        """ Simulate user press key and release the key
            Args:
                keySet (str): _description_
                interval (float, optional): time interval (sec) between 2 key press. 
                    Defaults to 0.1 sec.
            """
        if self.linuxKeyHd:
            if not (isinstance(keySet, list) or isinstance(keySet, tuple)): keySet = [keySet]
            for keyChar in keySet:
                self.linuxKeyHd.press(self._linuxKeyMatch(keyChar))
            if interval > 0.1 : time.sleep(interval)
            for keyChar in keySet:
                self.linuxKeyHd.release(self._linuxKeyMatch(keyChar))
        else:
            if isinstance(keySet, list) or isinstance(keySet, tuple):
                keySet = '+'.join(keySet)
            keyboard.press_and_release(keySet)

#-----------------------------------------------------------------------------
    def repeatPress(self, keySet, repeat=1, Interval=0.2):
        for _ in range(repeat):
            self.pressAndrelease(keySet)
            time.sleep(Interval)

#-----------------------------------------------------------------------------
    def startLogKeyInput(self, recordTime=0):
        if self.recordFlg: 
            print('The key report is in progress..')
            return False
        self.recordTime = int(recordTime)
        self.recordFlg = True
        keyboard.start_recording()
        return True

#-----------------------------------------------------------------------------
    def stopLogKeyInput(self):
        if self.recordFlg:
            self.keyEventList = keyboard.stop_recording()
            print(">>> %s" %str(self.getKeyEventRcdStr()))
            self.recordFlg = False
            self.recordTime = 0

#-----------------------------------------------------------------------------
    def simuUserType(self, typeinStr, interval=0.2):
        """ Simulate user type in a string. (under development)"""
        for char in typeinStr:
            # Handle the special char create via shift+key
            if char == '\n' :
                self.pressAndrelease('enter')
            elif char == ' ':
                self.pressAndrelease('space')
            elif char == '~':
                self.pressAndrelease(('shift', '`'))
            elif char == '!':
                self.pressAndrelease(('shift', '1'))
            elif char == '@':
                self.pressAndrelease(('shift', '2'))
            elif char == '#':
                self.pressAndrelease(('shift', '3'))
            elif char == '$':
                self.pressAndrelease(('shift', '4'))
            elif char == '%':
                self.pressAndrelease(('shift', '5'))
            elif char == '^':
                self.pressAndrelease(('shift', '6'))
            elif char == '&':
                self.pressAndrelease(('shift', '7'))
            elif char == '*':
                self.pressAndrelease(('shift', '8'))
            elif char == '(':
                self.pressAndrelease(('shift', '9'))
            elif char == ')':
                self.pressAndrelease(('shift', '0'))
            elif char == '_':
                self.pressAndrelease(('shift', '-'))
            elif char == '+':
                self.pressAndrelease(('shift', '='))
            else:
                self.pressAndrelease(char)
            time.sleep(interval)

    #-----------------------------------------------------------------------------
    def typeStr(self, inputStr):
        """ Simulate input string.
            Args:
                inputStr (_type_): _description_
        """
        if self.linuxKeyHd:
            self.linuxKeyHd.type(inputStr)
        else:
            keyboard.write(inputStr)

    #-----------------------------------------------------------------------------
    def stop(self):
        self.recordFlg = False 
        self.ternamted = True

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def testCase(mode):
    keyActor = keyEventActor()
    keyActor.start()
    time.sleep(1)
    if mode == 0: 
        print("TestCase 1: simulate user typein ")
        testStr = "hello world!\n"
        keyActor.typeStr(testStr)
        keyActor.simuUserType(testStr)
    elif mode == 1:
        print("TestCase 2: record user input and print.")
        keyActor.startLogKeyInput()
        print("Please type in a string:")
        inputStr = str(input())
        keyActor.stopLogKeyInput()
        print("Input Str: %s" % inputStr)
        print("KeyEventActor record: %s" %keyActor.getKeyEventRcdStr())
        print('\nKeyPress detail: ')
        keyevents = keyActor.getKeyEventList()
        for event in keyevents:
            print(event.to_json())
    elif mode == 2:
        print("TestCase 3: play back input")
        keyActor.startLogKeyInput()
        print("Please type in a string:")
        inputStr1 = str(input())
        keyActor.stopLogKeyInput()
        time.sleep(1)
        keyevents = keyActor.getKeyEventList()
        keyActor.playbackKeyEventList(keyevents)
        print("start to play back input:")
        inputStr2 = str(input())
        print("Keyboard input 1: %s" %inputStr1)
        print("Repaly input 2: %s" %inputStr2)
    elif mode == 3:
        keyActor.startLogKeyInput(recordTime=10)
        time.sleep(20)
        keyStr = keyActor.getKeyEventRcdStr()
        print("input:%s" %str(keyStr))

    keyActor.stop()

if __name__ == '__main__':
    testCase(2)