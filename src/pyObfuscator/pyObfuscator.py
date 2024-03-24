#-----------------------------------------------------------------------------
# Name:        pyObfuscator.py
#
# Purpose:     This module will provide a simplified Python obfuscation encode and 
#              decode function to secure and protect the source code, the obfuscate 
#              encode method uses 3 layers obfuscation technque to makes it difficult 
#              for hackers to gain access to your sensitive source code. 
#
# Author:      Yuancheng Liu
#
# Version:     v_0.1.2
# Created:     2024/03/21
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
""" Program design:
    This module follow the idea in the link:[ https://freecodingtools.org/py-obfuscator#:
    ~:text=A%20Python%20obfuscator%20is%20a,to%20your%20sensitive%20source%20code] and 
    alog in the pyarmor obfuscation lib[https://pyarmor.readthedocs.io/en/latest/] to 
    obfuscate a normal python program (section) with the compress and base64 encode lib.

    Usage steps:
        1. Run the program with input test mode 0
        2. Type in the python source code program file name/path
        3. Set the random contents insertion paramter number
        4. The obfuscated code will be saved in the file <obfuscateCode.py>
"""
import zlib
import uuid
import base64

# the decode header works with the obfuscated code
CODE_HEADER = """def obfDecode(data): return __import__('zlib').decompress(__import__('base64').b64decode(data[::-1]))"""

#-----------------------------------------------------------------------------
def getRemoveCmtCode(codeStr):
    """ Remove the comments section in the input code. """
    codeConetent = ''
    for line in codeStr.split('\n'):
        # Removing the comments from the decoded data
        line = line.split("#")[0]
        # Removing the empty lines from the decoded data
        if line.strip() != "":
            # Adding the original encoded data to the output list
            codeConetent += line+'\n'
    return codeConetent

#-----------------------------------------------------------------------------
def obfEecode(data, removeCmt=True):
    """ Obfuscate encode the input python source code.
        Args:
            data (str): python source code string.
            removeCmt (bool, optional): flag to remove the code original comments and empty line. Defaults to True.
        Returns(bytes): obfuscated encoded bytes data or None if input is invalid. 
    """
    if isinstance(data, str):
        codeConetent = getRemoveCmtCode(data) if removeCmt else data
        reversedData = base64.b64encode(zlib.compress(codeConetent.encode('utf-8'))).decode()[::-1]
        return reversedData.encode('utf-8')
    else:
        print("Error: obfEecode() > The input data need to be str() type.")
        return None 

#-----------------------------------------------------------------------------
def obfDecode(data, removeCmt=True):
    """ Decode the obfuscate bytes back to source code.
        Args:
            data (bytes): obfuscated bytes data.
            removeCmt (bool, optional): flag to remove the random comments and empty line 
                of the result. Defaults to True.
        Returns:
            str: python code string
    """
    if isinstance(data, bytes):
        # Reversing the input string to get the original encoded data
        decompressedData = zlib.decompress(base64.b64decode(data[::-1]))
        codeData = decompressedData.decode('utf-8')
        codeConetent = getRemoveCmtCode(codeData) if removeCmt else codeData
        return codeConetent
    else:
        print("Error: obfDecode() > the input data need to be a bytes() type value.")
        return None 

#-----------------------------------------------------------------------------
def executeObfuscateCode(obfBytes, debug=False):
    """ Execute the input obfuscated code bytes.
        Args:
            obfBytes (bytes): obfusedated bytes data.
            debug (bool, optional): flag to identify whether show the execution result. 
                Defaults to False.
    """
    codeCode = obfDecode(obfBytes)
    if codeCode is None: return None
    try:
        if debug: print("Start to execude the code: %s " %str(codeCode))
        rst = exec(codeCode)
        return rst
    except Exception as err:
        print("Execution Error: executeObfuscateCode() > %s" %str(err))
        return None

#-----------------------------------------------------------------------------
def getObfuscatedCode(codeStr, randomLen=0):
    """ Crete the executable obfuscated contents based on the random contents length. 
        Args:
            codeStr (str): python source code string.
            randomLen (int): each line will add a randomLen*16 Bytes random sting before 
                do the Obfuscation encode.
    """
    if isinstance(codeStr, str):
        newCodeContents = ''
        if randomLen > 0:
            for line in codeStr.split('\n'):
                newCodeContents += '%s\n' % line
                newCodeContents += '''#'''
                for _ in range(randomLen):
                    newCodeContents += str(uuid.uuid4().hex)
                newCodeContents += '''\n'''
        else:
            newCodeContents = codeStr
        exeStr = str(obfEecode(newCodeContents, removeCmt=False))
        exeStr = """exec(obfDecode(%s))""" % exeStr if exeStr.startswith('b') else """exec(obfDecode(b'%s'))""" % exeStr
        return CODE_HEADER + '\n' + exeStr + '\n'
    else:
        print("Error: getObfuscatedCode()> the input obfuscate need to be string type data.")

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def testCase(mode):
    """ Program test cases """
    testCodeStr = "print('hello world')#this is a comment\nprint(123)"
    if mode == 0:
        import os 
        print('Input the file name/path you want to obfuscate encode:')
        uInput = str(input())
        print('Input the random append contents length number (0~100):')
        randomLen = int(input())
        if os.path.isfile(uInput) and uInput.endswith('.py'):
            codeStr = ''
            with open(uInput,'r') as fh:
                codeStr = fh.read()
            data = getObfuscatedCode(codeStr, randomLen=randomLen)
            with open("obfuscateCode.py", "w") as f:
                f.write(data)
            print("- Done.")
        else:
            print("Input file not exist or file type not match.")
    elif mode == 1:
        print("Test Case1: obfuscate encode and decode test")
        ecodeData = obfEecode(testCodeStr)
        print("Encoded data: %s" %str(ecodeData))
        decodeData = obfDecode(ecodeData)
        print("Decoded source: %s" %str(decodeData))
        exec(decodeData)
        if decodeData == getRemoveCmtCode(testCodeStr):
            print("- Pass.")
        else:
            print("- Failed.")
    elif mode == 2:
        print("Test Case2: obfuscate encode and execute")
        ecodeData = obfEecode(testCodeStr)
        print("Execute the encoded data: %s" %str(ecodeData))
        result = executeObfuscateCode(ecodeData)
        print(result)
    elif mode == 3:
        print("Test Case3: generate executable obfuscate code")
        data = getObfuscatedCode(testCodeStr, randomLen=10)
        with open("obfuscateCode.py", "w") as f:
            f.write(data)
        print("- Done.")
    else:
        print("Error: the input mode need to be 1, 2 or 3.")
    
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    mode = 0
    print('Input the test mode you want to run [0~3]:')
    mode = int(input())
    testCase(mode)
