# Load Config
import time
from multiprocessing import Queue

from OldPython.BossRxThread import BossTxCommands
from Pedal.ProtocolSniffing.Helpers import getStateHex, BossSnifferRxProcess, loadConfig, setupDevice

templateMapping, commandLookup, originalConfig, commandConfig = loadConfig()

# Start RX Thread

device, endpointReadRef, endpointWriteRef = setupDevice()
rxQueue = Queue()
bossRxThread = BossSnifferRxProcess(device, endpointReadRef, rxQueue, templateMapping)

# Start running the threads!
bossRxThread.start()

# Send Startup Messages to initialise the device
endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_FIRST))
time.sleep(0.5)
endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_SECOND))
time.sleep(0.5)
endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_THIRD))
time.sleep(0.5)
endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_FOURTH))
time.sleep(0.5)
# endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_FIFTH))
time.sleep(0.5)

try:
    while True:
        rxQueue.get_nowait()
except:
    pass
getStateHex(rxQueue, endpointWriteRef)

i = 0