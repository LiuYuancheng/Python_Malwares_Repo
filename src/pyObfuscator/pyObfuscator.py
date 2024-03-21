#-----------------------------------------------------------------------------
# Name:        pyObfuscator.py
#
# Purpose:     This module will provide a simplified python obfuscation encode and 
#              docode function to secure and protect Python code, this method use 
#              3 layers obfucation makes it difficult for hackers to gain access 
#              to your sensitive source code. 
#
# Author:      Yuancheng Liu
#
# Version:     v_0.0.1
# Created:     2024/03/21
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
""" Program design:
    This module follow the idea in the link:[ https://freecodingtools.org/py-obfuscator#:
    ~:text=A%20Python%20obfuscator%20is%20a,to%20your%20sensitive%20source%20code] and 
    alog in the pyarmor obfuscation lib[https://pyarmor.readthedocs.io/en/latest/] to 
    ofuscate a nomral python program (section) with the compress and base64 encode lib.
"""
import zlib
import uuid
import base64

CODE_HEADER = """def obfDecode(data): return __import__('zlib').decompress(__import__('base64').b64decode(data[::-1]))"""

#-----------------------------------------------------------------------------
def getRemoveCmtCode(codeStr):
    """ Remove the comments section in the code. """
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
    """ Obfuscate encode the input python code.
        Args:
            data (str): python code string
            removeCmt (bool, optional): flag to remove the code orignal comments and empty line. Defaults to True.
        Returns(bytes): obfuscated encoded byte data or None if input is invalid. 
    """
    if isinstance(data, str):
        codeConetent = getRemoveCmtCode(data) if removeCmt else data
        reversedData = base64.b64encode(zlib.compress(codeConetent.encode('utf-8'))).decode()[::-1]
        return reversedData.encode('utf-8')
    else:
        print("Error: the input data need to be a str type value.")
        return None 

#-----------------------------------------------------------------------------
def obfDecode(data, removeCmt=True):
    """ Decode the obfuscate bytes
        Args:
            data (bytes): obfuscate bytes data
            removeCmt (bool, optional): flag to remove the random comments and empty line 
                of the resutl. Defaults to True.
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
        print("Error: the input data need to be a bytes type value.")
        return None 

#-----------------------------------------------------------------------------
def executeObfuscateCode(obfBytes, debug=False):
    """ Execute the obfuscated code bytes.
        Args:
            codeStr (_type_): _description_
            debug (bool, optional): _description_. Defaults to False.
    """
    codeCode = obfDecode(obfBytes)
    if codeCode is None:
        return None
    try:
        if debug: print("start to execude the code %s " %str(codeCode))
        rst = exec(codeCode)
        return rst
    except Exception as err:
        print("Execution Error: %s" %str(err))
        return None

#-----------------------------------------------------------------------------
def getObfuscatedCode(codeStr, randomLen=0):
    """ Crete the executable obfuscated contents based on the random contents length."""
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
        print("Error: the input obfuscate need to be string type data.")

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def testCase(mode):
    testCodeStr = "print('hello world')#this is a comment\nprint(123)"
    if mode == 0:
        import os 
        print('Input the file name/path you want to obfuscate:')
        uInput = str(input())
        print('Input the random append contents length number:')
        randomLen = int(input())
        if os.path.isfile(uInput) and uInput.endswith('.py'):
            codeStr = ''
            with open(uInput,'r') as fh:
                codeStr = fh.read()
            data = getObfuscatedCode(codeStr, randomLen=randomLen)
            with open("obfuscateCode.py", "w") as f:
                f.write(data)
            print("- Done.")
    elif mode == 1:
        print("Test Case1: obfuscate encode and decode test")
        ecodeData = obfEecode(testCodeStr)
        print(ecodeData)
        decodeData = obfDecode(ecodeData)
        print(decodeData)
        exec(decodeData)
        if decodeData == "print('hello world')\nprint(123)\n":
            print("- Pass.")
        else:
            print("- Failed.")
    elif mode == 2:
        print("Test Case2: obfuscate encode and execute")
        ecodeData = obfEecode(testCodeStr)
        result = executeObfuscateCode(ecodeData)
        print(result)
    elif mode == 3:
        print("Test Case3: generate executable obfuscate code")
        data = getObfuscatedCode(testCodeStr, randomLen=10)
        with open("obfuscateCode.py", "w") as f:
            f.write(data)
        print("- Done.")
    elif mode == 4:
        print("Test Case4: create obfuscate code")
        data = getObfuscatedCode(testCodeStr, randomLen=10)
        print(data)
    else:
        print("Error: the input mode need to be 1, 2, 3 or 4.")
    
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    mode = 3
    testCase(mode)
