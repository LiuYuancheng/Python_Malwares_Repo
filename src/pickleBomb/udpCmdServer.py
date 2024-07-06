
# A normal UDP server host on port 3000 accept different UDP client connection 
# execute cmd and send the result back to the related client.
# version: v0.0.3
# by Liu Yuancheng
import socket
import subprocess

BUFFER_SZ = 4096 
port = 3000
udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpServer.bind(('0.0.0.0', port))
while True:
    data, address = udpServer.recvfrom(BUFFER_SZ)
    cmdMsg = data.decode('utf-8')
    if cmdMsg == '': continue
    if cmdMsg == 'exit': 
        udpServer.sendto(str('exit').encode('utf-8'), address)
        exit()
    result = 'Command not found!'
    try:
        result = subprocess.check_output(cmdMsg, shell=True).decode()
    except Exception as err:
        result = str(err)
    udpServer.sendto(result.encode('utf-8'), address)