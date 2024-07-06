# A normal pickle deserialized data file load program 
# version: v0.0.3
# Create: 06/07/2024
# by Liu Yuancheng 

import pickle
import base64

while True:
    choice = input("Input load serialized data file format([1] byte file, [2] txt file):")
    if choice == '1':
        orignalData = None
        try:
            with open('data.pkl', 'rb') as fh:
                orignalData = pickle.load(fh)
            print(orignalData)
        except Exception as err:
            print("Error to load the byte pickled file: %s" %str(err))
    elif choice == '2':
        dataStr = None
        try:
            with open('data.txt', 'r') as fh:
                dataStr = fh.read()
            orignalData = pickle.loads(base64.b64decode(dataStr))
            print(orignalData)
        except Exception as err:
            print("Error to load the txt pickled file: %s" %str(err))
    else:
        print("Exit....")
        exit()