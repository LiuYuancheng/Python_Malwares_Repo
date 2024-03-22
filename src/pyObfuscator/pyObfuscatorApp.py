#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        pyObfuscatorApp.py [python3]
#
# Purpose:     This module is the main web interface to call the AI-llm MITRE 
#              ATT&CK-Mapper/ CWE-Matcher module to generate the related report.
#  
# Author:      Yuancheng Liu
#
# Created:     2024/03/02
# version:     v0.1.2
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------
import os
import threading

import pyObfuscator as obfscate

from flask import Flask, render_template, flash, redirect, url_for, request, session
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit # pip install Flask-SocketIO==5.3.5

#-----------------------------------------------------------------------------
# Init the flask web app program.
def createApp():
    """ Create the flask App."""
    app = Flask(__name__)
    #app.config['SECRET_KEY'] = gv.APP_SEC_KEY
    #app.config['UPLOAD_FOLDER'] = gv.gSceBank
    # init the data manager

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
   code = request.form['codeContents']
   randomLen = int(request.form['randomLen'])
   print(code)
   print("randomLen: %s" %str(randomLen))
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
    code = request.form['codeContents']
    checkboxVal = request.form.get('removeCmt')
    removCmtFlg = False if checkboxVal is None else True
    if str(code).startswith("b'"): code = str(code)[2:]
    if str(code).endswith("'"):code = str(code)[:-1]
    reusltCode = obfscate.obfDecode(code.encode('utf-8'), removeCmt=removCmtFlg)
    #print("removeCmt: [%s]" %str(checkbox_value))
    socketio.emit('decoderesult', {'data': reusltCode})
    return 'Python source code obfuscation decoded.'

#-----------------------------------------------------------------------------
# socketIO communication handling functions. 
@socketio.event
def connect():
    gWeblogCount = 0
    emit('serv_response', 
         {'data': 'LLM-LangChain Ready', 'count': gWeblogCount, 'logType':'ATK'})

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,  debug=False, threaded=True)
    #app.run(host=gv.gflaskHost,
    #    port=gv.gflaskPort,
    #    debug=gv.gflaskDebug,
    #    threaded=gv.gflaskMultiTH)
