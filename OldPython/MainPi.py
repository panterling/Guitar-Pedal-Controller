import json
import queue
import time
from threading import Thread

import RPi.GPIO as GPIO

import atexit

from bluetooth import *
import binascii

import usb.core
import usb.util

from BluetoothManager import BluetoothManager
from Config import GPIO_PINS
from GPIOManager import GPIOManager
from Helpers import DeFramer
from BossUSBManager import BossUSBManager






##################
## PI SETUP
GPIOManager.setupWithDefaults()

atexit.register(GPIOManager.turnOffPins)

##################


bossNotificationQueue = queue.Queue()

bossManager = BossUSBManager(bossNotificationQueues = [bossNotificationQueue])

bossManager.start()

#########

bluetoothManager = BluetoothManager(bossManager)

#########

print("=================")
print("=================")
print("=================")
print("=================")

SOF_TOKEN = (127).to_bytes(1, byteorder='big')
EOF_TOKEN = (126).to_bytes(1, byteorder='big')

def buildResponse(jsonPayload):
    ff = SOF_TOKEN
    fd = EOF_TOKEN
    bytesSOF = bytearray( ff + ff + ff + ff ).decode()
    bytesEOF = bytearray( fd + fd + fd + fd ).decode()

    jsonBytes = json.dumps( jsonPayload )

    return bytesSOF + jsonBytes + bytesEOF



class COMMANDS:
    USER_PATCH = 1



gt1RxThread = None

def gt1RxThreadFunc(bossNotificationQueue, bluetoothTxQueue):
    while True:
        if not bossNotificationQueue.empty():
            try:
                msgJSon = bossNotificationQueue.get(block=False)
                ret = buildResponse(msgJSon)
                bluetoothTxQueue.put(ret)
                print("gt1RxThreadFunc:: Passed from GT1 to Bluetooth Queue .... ")

            except Exception as e:
                print("gt1RxThreadFunc:: Cannot get from bossNotificationQueue?!")
                print(e)

gt1RxThread = Thread(target = gt1RxThreadFunc, args=[bossNotificationQueue, bluetoothManager.getTxQueue()])
gt1RxThread.setName("GT1 Rx Thread")
gt1RxThread.start()

