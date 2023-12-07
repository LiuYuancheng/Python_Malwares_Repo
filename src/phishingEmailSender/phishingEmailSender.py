#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        phishingEmailSender.py
#
# Purpose:     This module is used to simulate a hacker to send a phishing 
#              email to the railway company enginners. This email sender can 
#              also tiggered by a MS-Word document's macro. 
#
# Author:      Yuancheng Liu
#
# Version:     v_0.1
# Created:     2023/09/21
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import os, sys
import json

# import the module from lib folder
print("Current working directory is : %s" % os.getcwd())
dirpath = os.path.dirname(__file__)
print("Current source code location : %s" % dirpath)

TOPDIR = 'src'
LIBDIR = 'lib'

idx = dirpath.find(TOPDIR)
gTopDir = dirpath[:idx + len(TOPDIR)] if idx != -1 else dirpath   # found it - truncate right after TOPDIR
# Config the lib folder 
gLibDir = os.path.join(gTopDir, LIBDIR)
if os.path.exists(gLibDir):
    sys.path.insert(0, gLibDir)

# import the email Actor module
import emailActor

htmlContent ="""\
    <html>
        <body>
            <p> Dear Maintenance Department Engineers: <br><br>
            This is software support team from rail IT department, we are working on updating the 
            software for all the Linux-OS computer in the company.
            <br> 
            <p> Please make sure your computer is connect to the internet and follow below steps 
            to update your computer: </p>
            <p> ------ </p>
            <p> 1. Download the auto-update installer *.zip in the attahcment. 
            <p> 2. Unzip the file and run the update_installer.sh with sudo permission.</b> </p>
            <p> 3. Wait the update installer finish and then delete the zip file. </b> </p>
            <p> ------ </p>
            <p> If you meet any problem, please send an email to us lT_SUPP0RT@rail.co
            </p>
            <p> Thanks</p>
            <p> Rail IT support Team </p>
        </body>
    </html>
"""

configDict = {
    'fakeSenderEmailAcc': 'support@ncl.sg',
    'fakeSenderEmailPwd': '123456',
    'smtpServer': 'smtp.gmail.com',
    'smtpPort': 587,
    'targetEmails': ['liu_yuan_cheng@hotmail.com'],
    'emailSubject': 'Software update [maintenance department]',
    'emailContent': htmlContent,
    'attachment': 'update_installer.zip',
}

# if set the config json file, use the config json file.
configFile = 'config.json'
# configFile = None  # if set to None, use the program default setting

# update the config
if configFile:
    configFilePath = os.path.join(dirpath, configFile)
    print("Load config file file: %s" % str(configFilePath))
    if os.path.exists(configFilePath):
        with open(configFilePath) as fh:
            data = json.load(fh)
            for key, val in data.items():
                configDict[key] = val

print('Init the email sender.')
sender = emailActor.emailActor(configDict['fakeSenderEmailAcc'],
                               configDict['fakeSenderEmailPwd'])
sender.initEmailSender(configDict['smtpServer'],
                       smtpPort=configDict['smtpPort'], sslConn=False)

attachPath = os.path.join(dirpath, configDict['attachment'])
if not os.path.exists(attachPath):
    attachPath = None

print("Start to send the phishing email to targets:")

for targetEmail in configDict['targetEmails']:
    print("- send email to : %s" % str(targetEmail))
    sender.sendEmailHtml(targetEmail, configDict['emailSubject'],
                         configDict['emailContent'], attachmentPath=attachPath)

print('Email send Finished.')
