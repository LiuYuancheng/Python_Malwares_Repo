#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        emailActor.py
#
# Purpose:     This module is used to login different kinds of email server to 
#              send (with attachment) email or receive email (download attachment).
# Author:      Yuancheng Liu
#
# Version:     v_0.1.2
# Created:     2022/12/28
# Copyright:   Copyright (c) LiuYuancheng
# License:     MIT License 
#-----------------------------------------------------------------------------
""" Program design : 
    we want to build a email module provide the email implementation API for user to:
    1. Read multiple email (in sequential order or randomly). 
    2. Batch download the attachment from email list.
    3. Batch deploy emails to multiple targets as an email bot.

    Program config : 
    Gmail account configure :
    - Turn on the "Less secure app access" setting at: Google Account > Security > Less secure app access 
    - Enable the IMAP Access at: Gmail Settings > Forwarding and POP / IMAP > IMAP Acess
    Hotmail account configure : 
    - N.A 

    Program Usage: refer to the testCase program <emailActorTest.py>
"""

# Import basic build-in lib
import os
import time
import random

# Import build-in function lib
import re
import ssl
import smtplib
import imaplib

# Import the email module
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define standard SMTP email server port config:
SMTP_PORT_READ = 993
SMTP_PORT_SEND = 587
SMTP_PORT_SEND_SSL = 465

# default email read config. 
DEFAULT_CFG = {
    'mailBox'   : 'inbox',  # Inbox mail folder name (different email vendor may use other name).
    'sender'    : None,     # Search email based on sender. None: read all email.
    'number'    : 10,       # Numher of email will be fetched. 
    'randomNum' : 0,        # if set > 0, download the random number for email from the fetched email. if set=0 read all
    'interval'  : 0,        # Time interval between download(read) 2 emails.
    'returnFlg' : False     # the flag indentify whether return all the email contents.
}

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class emailActor(object):
    """ The main email actor module, for differnt email vendors, use the below 
        server port and connection type config: 
        - GMail:        smtpPort[993], sslConn[True]
        - HotMail:      smtpPort[587], sslConn[True]
        - Mailu/:       smtpPort[143], sslConn[True]
        - Hmailserver:  smtpPort[143], sslConn[True]
    """
    def __init__(self, account, password) -> None:
        """ Each email actor will bind to one valid email account. Init example:
            actor = emailActor.emailActor('xxx@gmail.com', '******')
            Args:
                account (str): full email address.For example: liu_yuan_cheng@hotmail.com
                password (str): password.
        """
        if not self._isEmailFmtValid(account): 
            print("Email actor init failed.")
            return None
        self.account = account
        self.password = password
        self.emailReader = None
        self.emailSender = None
        
#-----------------------------------------------------------------------------
    def _isEmailFmtValid(self, emailStr):
        """ Verify the email address format."""
        if re.match("^[a-zA-Z0-9-_.]+@[a-zA-Z0-9]+\.[a-z]{1,3}$", emailStr):
            return True
        print("Error: the input email account format is not valid: %s" %str(emailStr))
        return False

#-----------------------------------------------------------------------------
    def initEmailReader(self, smtpServer, smtpPort=SMTP_PORT_READ, sslConn=True):
        """ Connect(login) to the email read IMAP server and init the reader object. 
            Args:
                smtpServer (str): email IMAP server url.
                smtpPort (int, optional): email IMAP server port. Defaults to SMTP_PORT_READ.
                sslConn (bool, optional): email account's connection ssl encryption 
                    config. Defaults to True.
            Returns:
                _type_: true if connect to the server successful, else false.
        """
        try:
            self.emailReader = imaplib.IMAP4_SSL(
                host=smtpServer, port=smtpPort) if sslConn else imaplib.IMAP4(host=smtpServer, port=smtpPort)
            self.emailReader.login(self.account, self.password)
            return True
        except Exception as err:
            print("Login the email server failed.")
            print("- Error: %s" % str(err))
            return False

#-----------------------------------------------------------------------------
    def initEmailSender(self, smtpServer, smtpPort=SMTP_PORT_SEND, sslConn=True):
        """ Connect(login) to the email read IMAP server and init the sender object.
            You can send email from local without login but your email will be treated 
            as spam/fake.
            Args:
                smtpServer (_type_): email IMAP server url.
                smtpPort (_type_, optional): email IMAP server port. Defaults to SMTP_PORT_SEND.
                sslConn (bool, optional): email account's connection ssl encryption 
                    config. Defaults to True.
            Returns:
                _type_: true if connect to the server successful, else false.
        """
        try:
            if sslConn:
                ssl_context = ssl.create_default_context()
                service = smtplib.SMTP_SSL(smtpServer, smtpPort, context=ssl_context)
                service.login(self.account, self.password)
            else:
                self.emailSender = smtplib.SMTP(smtpServer, smtpPort)
                self.emailSender.starttls()
                self.emailSender.login(self.account, self.password)
            return True
        except Exception as err:
            print("Login the email server failed.")
            print("- Error: %s" % str(err))
            return False

#-----------------------------------------------------------------------------
    def getMailboxList(self):
        """ Get the email box list.
            Returns:
                list(): ['inbox', 'sent', 'spam'...] None if reader is not init.
        """
        if self.emailReader:
            return self.emailReader.list()
        return None

#-----------------------------------------------------------------------------
    def getEmailIdList(self, emailBox='inbox', emailNum=10, sender=None):
        """ Get the email unique ID list.
            Args:
                emailBox (str, optional): mailbox name. Defaults to 'inbox'.
                emailNum (int, optional): number of email. Defaults to 10.
                sender (_type_, optional): if set not None, only return the ID list 
                    of the email from the sender. Defaults to None.
            Returns:
                list(): list of the email ID.
        """
        if self.emailReader:
            try:
                self.emailReader.select(emailBox)
                emailInfo = self.emailReader.search(None, 'ALL') if sender is None else self.emailReader.search(None, 'FROM', f'"{sender}"')
                IdList = emailInfo[1][0].split() 
                mailIds = IdList if len(IdList) < emailNum else IdList[-emailNum:]
                return mailIds
            except Exception as err:
                print("Get the mail ids error: %s" %str(err))
        print("Email reader is not init.")
        return None

#-----------------------------------------------------------------------------
    def getEmailDetail(self, emailId):
        """ Get the email info.
            Args:
                emailIdx (_type_): _description_
        """
        if self.emailReader:
            mailId = int(emailId)
            data = self.emailReader.fetch(str(mailId), '(RFC822)')
            for responsePart in data:
                arr = responsePart[0]
                if isinstance(arr, tuple):
                    try:
                        return email.message_from_string(str(arr[1],'utf-8'))
                    except:
                        return None
        else:
            print("Email reader is not init.")
            return None

#-----------------------------------------------------------------------------
    def readLastMail(self, configDict=DEFAULT_CFG, downloadDir=None):
        """ Read the email based on the config setting.
            Args:
                configDict (dict(), optional): refer to the <DEFAULT_CFG>.
                  Defaults to DEFAULT_CFG.
                  example: 
                    readConfig2 = {
                        'mailBox': 'inbox',
                        'sender': None,
                        'number': 1,
                        'randomNum': 1,
                        'interval': 0.5,
                        'returnFlg': False
                    }
                downloadDir (str, optional): The folder to save the attachment
                    - None: Don't download the attachment. 
                    - str(<folder path>): download the attachment to the folder.
            Returns:
                str/None: The successed read emails detail, None if read error.
        """
        if not isinstance(configDict, dict):
            print("The input config setting is invalid: %s" %str(configDict))
            return None
        configKeys = configDict.keys()
        result = [] if 'returnFlg' in configKeys and configDict['returnFlg'] else None
        if self.emailReader:
            mailIds = self.getEmailIdList(emailBox=configDict['mailBox'], emailNum=configDict['number'], sender=configDict['sender'])
            if mailIds is None :
                print("Can not file email-ID based on the config.")
                return None
            randMailIds = random.sample(mailIds, configDict['randomNum']) if 'randomNum' in configKeys and configDict['randomNum'] > 0 else mailIds
            # Fetch email detail information basedon the email ID.
            for mailId in randMailIds:
                msg = self.getEmailDetail(mailId)
                if msg:
                    print("Get email: %s " %str(msg['subject']))
                    # print the email detail if no need return the data, else archive the data in 
                    # result list:
                    if result is None:
                        print("Email idx=%s info:" %str(mailId))
                        print('From : ' + msg['from'] + '\n')
                        print('To : ' + msg['to'] + '\n')
                        print('Subject : ' + msg['subject'] + '\n')
                    else:
                        result.append(msg)
                    # Download the email attachment if specified the foler.
                    if downloadDir:
                        print("Start to download attachment if contents")
                        self.downloadAttachment(msg, downloadDir)
                else:
                    print("The email id = %s is not readable" %str(mailId))
                if 'interval' in configKeys and configDict['interval'] > 0:
                    time.sleep(configDict['interval'])
            print("Read all email contents finish.")
            if result: return result
        else:
            print("Email send is not init.")
            return None

#-----------------------------------------------------------------------------
    def downloadAttachment(self, emailMsg, downloadDir):
        """ Download the attachment from the mail.
            Args:
                emailMsg : refer to <email.message_from_string()> return value.
                downloadDir: download folder (absolute path).
        """
        for part in emailMsg.walk():
            if part.get_content_maintype() == 'multipart':
                print(part.as_string())
                continue
            if part.get('Content-Disposition') is None:
                print(part.as_string())
                continue
            fileName = part.get_filename()
            print('Get attachment file name [%s] to process.' %str(fileName))
            if bool(fileName):
                if not (os.path.exists(downloadDir) and os.path.isdir(downloadDir)):
                    print("Attachment download folder not exist, create the dir...")
                    os.mkdir(downloadDir)
                filePath = os.path.join(downloadDir, fileName)
                with open(filePath, 'wb') as fh:
                    fh.write(part.get_payload(decode=True))
                print("Finished download the attachment.")

#-----------------------------------------------------------------------------
    def forwardEml(self, dests, emlFilePath):
        """ Forward an exported email file *.eml as email to destinations.
            Args:
                dests (str): destination email address.
                emlFilePath (_type_): *.eml file path.
        """
        if not ('eml' in emlFilePath):
            print('The file format must be and *eml')
            return False
        if os.path.exists(emlFilePath):
            with open(emlFilePath, "rb") as file:
                message = file.read()
                self.sendMsg(self.account, dests, message)
            return True
        else:
            print("The input eml file is not found, file path: %s" %str(emlFilePath))
            return False

#-----------------------------------------------------------------------------
    def sendEmailHtml(self, dests, subjectStr, htmlContent, attachmentPath=None):
        """ Send a html formate email.
            Args:
                dests (str) : receiver's email address.
                subjectStr (str) : email subject title.
                htmlContent (str) : refer to the example below.
                attachmentPath: attachment file absolute path.
        """
        # An Example of the html content:
        # html = """\
        #         <html>
        #         <body>
        #             <p>Hi,<br>
        #             How are you?<br>
        #             <a href="http://www.realpython.com">Real Python</a> 
        #             has many great tutorials.
        #             </p>
        #         </body>
        #     </html>
        #     """
        message = MIMEMultipart("alternative")
        message["Subject"] = str(subjectStr)
        message["From"] = self.account
        message["To"] = str(dests)
        message.attach(MIMEText(htmlContent, "html"))
        # attach the attachment file to the email.
        if not attachmentPath is None:
            if os.path.exists(attachmentPath):
                part = None
                with open(attachmentPath, "rb") as attachment:
                    # Add file as application/octet-stream
                    # Email client can usually download this automatically as attachment
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                attachName = os.path.basename(attachmentPath)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachName}",
                )
                message.attach(part)
        else:
            print("The input attachment file is not found.")
        self.sendEmailMsg(dests, message.as_string())

#-----------------------------------------------------------------------------
    def sendEmailMsg(self, dests, message):
        """ Send a simple message to email destination(s)"""
        if self.emailSender:
            if isinstance(dests, str): dests = (dests,) 
            if isinstance(dests, list) or isinstance(dests, tuple):
                for dest in dests:
                    self.sendMsg(self.account, dest, message)

#-----------------------------------------------------------------------------
    def sendMsg(self, sender, receiver, message):
        """ Send a email to the receiver."""
        if self._isEmailFmtValid(sender) and self._isEmailFmtValid(sender):
            self.emailSender.sendmail(sender, receiver, message)
        
#-----------------------------------------------------------------------------
    def close(self):
        if self.emailReader:
            self.emailReader.close()
            self.emailReader.logout()
            self.emailReader = None
    
        if self.emailSender:
            self.emailSender.quit()
            self.emailSender.close()
            self.emailSender = None

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def testCase(mode):
    account = 'alice@gt.org'
    account = 'bob@gt.org'
    account = 'charles@gt.org'
    password = '123'
    smtpServer = 'email.gt.org'
    smtpPort = 143
    actor = emailActor(account, password, smtpServer, smtpPort=smtpPort, sslConn=False)
    actor.readLastMail(emailNum=2)

if __name__ == '__main__':
    testCase(1)
