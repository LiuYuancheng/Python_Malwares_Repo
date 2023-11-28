
#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        ddosAtkHubApp.py [python3]
#
# Purpose:     This module is the main website host program to host DDoS attacker
#              control hub to show the state of each ddos attacker.
#  
# Author:      Yuancheng Liu
#
# Created:     2023/11/26
# version:     v0.1.2
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
# CSS lib [bootstrap]: https://www.w3schools.com/bootstrap4/default.asp
# https://www.w3schools.com/howto/howto_css_form_on_image.asp
# https://medium.com/the-research-nest/how-to-log-data-in-real-time-on-a-web-page-using-flask-socketio-in-python-fb55f9dad100

import os
import json
import threading

from datetime import timedelta, datetime
from flask import Flask, render_template, jsonify, request 
from flask_socketio import SocketIO, emit # pip install Flask-SocketIO==5.3.5

import ddosAtkHubGlobal as gv
async_mode = None

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class dataMgr(object):
    """ Data management module to save the ddos-attacker's information."""
    def __init__(self, parent) -> None:
        self.attackers = {}

    #-----------------------------------------------------------------------------
    def updateAttackerInfo(self, attackerInfo):
        """ Update / add the attacker information.
            Args:
                attackerInfo (doct): example:
                {'id': "url-Attacker[192.168.50.33]",
                'type': 'url-post',
                'threads': 200,
                'count': 475520,
                'startT': '112000',
                'endT': '131010',
                'target': 'https://www.nus.edu.sg/canvas/login/',
                'state': 0}
        """
        attackerId = attackerInfo['id']
        if  attackerId in self.attackers.keys():
            self.attackers[attackerId].update(attackerInfo)
        else:
            attackerInfo = {
                'id': attackerInfo['id'],
                'type': attackerInfo['type'] if 'type' in attackerInfo.keys() else 'n.a',
                'threads': attackerInfo['threads'] if 'threads' in attackerInfo.keys() else 0,
                'count': attackerInfo['count'] if 'count' in attackerInfo.keys() else 0,
                'startT': attackerInfo['startT'] if 'startT' in attackerInfo.keys() else 'n.a',
                'endT': attackerInfo['endT'] if 'endT' in attackerInfo.keys() else 'n.a',
                'target': attackerInfo['target'] if 'target' in attackerInfo.keys() else 'n.a',
                'updateT': attackerInfo['updateT'] if 'updateT' in attackerInfo.keys() else str(datetime.now().strftime('%H:%M:%S')),
                'state': attackerInfo['state'] if 'state' in attackerInfo.keys() else 0
            }
            self.attackers[attackerId] = attackerInfo

    #-----------------------------------------------------------------------------
    def getAttackersInfo(self, attackerID=None):
        if attackerID and attackerID in self.attackers.keys(): 
            return self.attackers[attackerID]
        else:
            return self.attackers.values()

    #-----------------------------------------------------------------------------
    def loadTestData(self):
        """ load some data for testing"""
        if gv.iDataMgr:
            testAttackerInfo1 = {
                'id': "url-Attacker[192.168.50.33]",
                'type': 'url-post',
                'threads': 200,
                'count': 475520,
                'startT': '11:20:00',
                'endT': '13:10:10',
                'target': 'https://www.nus.edu.sg',
                'updateT': str(datetime.now().strftime('%H:%M:%S')),
                'state': 0
            }
            testAttackerInfo2 = {
                'id': "http-Attacker[192.168.50.33]",
                'updateT': str(datetime.now().strftime('%H:%M:%S'))
            }
            gv.iDataMgr.updateAttackerInfo(testAttackerInfo1)
            gv.iDataMgr.updateAttackerInfo(testAttackerInfo2)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Init the flask web app program.
def createApp():
    """ Create the flask App."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = gv.APP_SEC_KEY
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=gv.COOKIE_TIME)
    #app.config['UPLOAD_FOLDER'] = gv.UPLOAD_FOLDER
    # init the data manager
    gv.iDataMgr = dataMgr(app)
    if not gv.iDataMgr: exit()
    if gv.gTestMD: gv.iDataMgr.loadTestData()
    return app

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
app = createApp()
socketio = SocketIO(app, async_mode=async_mode)
gv.iSocketIO = socketio
thread = None
threadLock = threading.Lock()

#-----------------------------------------------------------------------------
@app.route('/')
def index():
    posts = gv.iDataMgr.getAttackersInfo()
    return render_template('index.html', 
                           async_mode=socketio.async_mode, 
                           posts=posts)

#-----------------------------------------------------------------------------
# Data post request handling 
@app.route('/dataPost/<string:uuid>', methods=('POST',))
def add_message(uuid):
    content = request.json
    gv.gDebugPrint("Get raw data from %s "%str(uuid), logType=gv.LOG_INFO)
    gv.gDebugPrint("Raw Data: %s" %str(content), prt=True, logType=gv.LOG_INFO)
    if gv.iDataMgr: gv.iDataMgr.updateAttackerInfo(content)
    return jsonify({"ok":True})

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,  debug=False, threaded=True)
