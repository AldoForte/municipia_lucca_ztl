#!/usr/bin/python3

import serial
import time
import sys

cmd = ""



def init_serial():
	ser = serial.Serial('/dev/ttyAMA0', baudrate=115200, bytesize=8, stopbits=1, parity='N', timeout=1)
	ser.close()
	ser.open()
	ser.flushOutput()
	return ser

error = 0



seriale = init_serial()

try:

    cmd = "$5b0a0100000000000004\r\n".encode()
    seriale.write(cmd)
    time.sleep(0.5)
    risposta = seriale.readline()
    print(risposta.decode())
except:
    error = 1

finally:

    seriale.close()

    if error > 0 :
        print("Si sono verificati degli errori!")
