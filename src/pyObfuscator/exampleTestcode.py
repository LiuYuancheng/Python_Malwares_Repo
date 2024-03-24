
import os
# Code comment 1
print("Current working directory is : %s" % os.getcwd())
dirpath = ''
# Code document 2
if os.path.dirname(__file__):
      dirpath = os.path.dirname(__file__)
else:
      dirpath = os.getcwd()
# Code comment 3
print("Current source code location : %s" % dirpath)
print("Hello world")