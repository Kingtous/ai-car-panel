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

# starting driver..
sys.stdout.write("Loading Driver...")

# load pyserial
driver = Serial("/dev/ttyUSB0",38400,timeout=0.5)
if not driver.isOpen():
    print("Port Busy, please check other programs which is using ttyUSB0")

# load lib c library
so = cdll.LoadLibrary
lib = so("/home/root/workspace/deepcar/deeplearning_python/lib/libart_driver.so")
lib.art_racecar_init(38400, "/dev/ttyUSB0".encode("utf-8"))
print("Done.")



def send(data):
    cnt_init = 50
    result = []
    try:
        driver.read_all()
        for i in range(3,-1,-1):
            if i == 0:
                lib.send_cmd(i,data[i])
            else:
                lib.send_cmd(i,int(data[i]*1000))
        driver.read_all()
        cnt = cnt_init
        while cnt > 0:
            try:
                raw_num = driver.read()
                if raw_num == b'\t' or raw_num == b'\n' or raw_num == b'\r':
                    pass
                else:
                    #print(raw_num)
                    num = int.from_bytes(raw_num,byteorder="big",signed='true')
                    result.append(num)
                    cnt -= 1
            except UnicodeDecodeError as e:
                print("decode error",str(e))
                continue
        print("50 data ok.")
        lib.send_cmd(0,1500)
        print("speed reseted. collecting...")
        cnt = cnt_init
        while cnt > 0:
            try:
                raw_num = driver.read()
                if raw_num == b'\t' or raw_num == b'\n' or raw_num == b'\r':
                    pass
                else:
                    #print(raw_num)
                    num = int.from_bytes(raw_num,byteorder="big",signed='true')
                    result.append(num)
                    cnt -= 1
            except UnicodeDecodeError:
                print("decode error",str(e))
                continue
        print("done")
    except Exception as e:
        result = str(e)
    finally:
        return result
    
def revertDirection():
    lib.send_cmd(5,1500)

def send_mode2(x_args):
    # driver: 0：x坐标， 4：y坐标，1：P参数， 2：I参数 ，3：D参数
    # web: p0：x坐标， p1：y坐标，p2：P参数， p3：I参数 ，p4：D参数
    lib.send_cmd(0,x_args[0]) # x
    lib.send_cmd(4,x_args[1]) # y
    lib.send_cmd(1,int(x_args[2])*1000) # p
    lib.send_cmd(2,int(x_args[3])*1000) # i
    lib.send_cmd(3,int(x_args[4])*1000) # d
    # return 待用
    return []

# 只需要送PID
def send_pid_follow(x_args):
    # driver: 0：x坐标， 4：y坐标，1：P参数， 2：I参数 ，3：D参数
    # web: p0：x坐标， p1：y坐标，p2：P参数， p3：I参数 ，p4：D参数
    lib.send_cmd(1,int(x_args[0])*1000) # p
    lib.send_cmd(2,int(x_args[0])*1000) # i
    lib.send_cmd(3,int(x_args[1])*1000) # d
    # return 待用
    return []

if __name__ == "__main__":
    while True:
        try:
            print(driver.read_all())
            continue
            ps = input("Input 4 Params:")
            # 3 pid,
            data = ps.strip().split(" ")
            data = list(map(lambda x: int(float(x)),data))
            # driver.send_cmd(p1,p2)
            for i in range(4):
                driver.write()

            print(p1,p2,p3,p4,"sent.")

            print("start receiving data from UART...")


        except Exception as e:
            sys.stderr.write("Error:"+str(e)+"\n")
