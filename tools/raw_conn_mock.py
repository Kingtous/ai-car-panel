'''
Filename: /home/kingtous/py-files/NEUQcar-SourceCode/raw_conn_2.py
Path: /home/kingtous/py-files/NEUQcar-SourceCode
Created Date: Auguest 7th 2020, 10:43:47 am
Author: kingtous

Copyright (c) 2020 Kingtous
'''

from ctypes import cdll
import sys
from serial import Serial

def send(data):
    return [0,200,150,80]
    
def revertDirection():
    print("direct")
    pass