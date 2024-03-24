#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        pyObfuscatorApp.py [python3]
#
# Purpose:     This module is the main web interface to call the obfuscator 
#              API to encode/decode the python program and use the socketIO
#              to update result. 
#
# Author:      Yuancheng Liu
#
# Created:     2024/03/21
# version:     v0.1.2
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------
import os
import threading

import pyObfuscator as obfscate

from flask import Flask, render_template, flash, redirect, url_for, request
from flask_socketio import SocketIO, emit # pip install Flask-SocketIO==5.3.5

DEBUG_MD = False 

gflaskHost = "0.0.0.0"
gflaskPort = 5000
gflaskDebug = False
gflaskMultiTH = True

#-----------------------------------------------------------------------------
# Init the flask web app program.
def createApp():
    """ Create the flask App."""
    app = Flask(__name__)
    return app
app = createApp()

# SocketIO asynchronous mode
async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
#gv.iSocketIO = socketio
thread = None
threadLock = threading.Lock()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# web request handling functions. 
@app.route('/')
def index():
    """ route to introduction index page."""
    posts = {'page': 0} # page index is used to highlight the left page slide bar.
    return render_template('index.html', posts=posts)

#-----------------------------------------------------------------------------
@app.route('/encoder')
def encoder():
    """ route to introduction index page."""
    posts = {'page': 1} # page index is used to highlight the left page slide bar.
    return render_template('obfencoder.html', posts=posts)

@app.route('/encodesubmit', methods=['POST'])
def encodesubmit():
    """ Call the encoder API to encode the program and emit the result."""
    code = request.form['codeContents']
    randomLen = int(request.form['randomLen'])
    if DEBUG_MD:
        print("code: %s" % str(code))
        print("randomLen: %s" % str(randomLen))
    ofsCode = obfscate.getObfuscatedCode(code, randomLen=randomLen)
    socketio.emit('encoderesult', {'data': ofsCode})
    return 'Python source code obfuscation encoded.'

#-----------------------------------------------------------------------------
@app.route('/decoder')
def decoder():
    """ route to introduction index page."""
    posts = {'page': 2} # page index is used to highlight the left page slide bar.
    return render_template('obfdecoder.html', posts=posts)

@app.route('/decodesubmit', methods=['POST'])
def decodesubmit():
    """ Call the decoder API to encode the program and emit the result."""
    code = request.form['codeContents']
    checkboxVal = request.form.get('removeCmt')
    removCmtFlg = False if checkboxVal is None else True
    if str(code).startswith("b'"): code = str(code)[2:]
    if str(code).endswith("'"):code = str(code)[:-1]
    reusltCode = obfscate.obfDecode(code.encode('utf-8'), removeCmt=removCmtFlg)
    #print("removeCmt: [%s]" %str(checkbox_value))
    socketio.emit('decoderesult', {'data': reusltCode})
    return 'Python source code obfuscation decoded.'

@app.route('/usagemanual')
def usagemanual():
    """ route to introduction index page."""
    posts = {'page': 3} # page index is used to highlight the left page slide bar.
    return render_template('usagemanual.html', posts=posts)

#-----------------------------------------------------------------------------
# socketIO communication handling functions. 
@socketio.event
def connect():
    gWeblogCount = 0
    emit('serv_response', 
         {'data': 'server ready', 'count': gWeblogCount,})

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=5000,  debug=False, threaded=True)
    app.run(host=gflaskHost,
        port=gflaskPort,
        debug=gflaskDebug,
        threaded=gflaskMultiTH)
