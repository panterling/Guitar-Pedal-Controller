import queue
import queue
import time

from OldPython.BossRxThread import BossTxCommands
from Pedal.CommandCatalogue import CommandCatalogue
from Pedal.DataModels import PedalFSMActionSendStaticCommand, PedalRequest
from Pedal.Device import Device, DeviceRxThread, DeviceTxThread
from Pedal.FSM import PedalFSM
from Pedal.ProtocolSniffing.Helpers import setupDevice, getStateHex, BossSnifferRxProcess, loadConfig, findCmdInConfig, \
    getTemplateForRx

# Load Config
templateMapping, commandLookup, originalConfig, commandConfig = loadConfig()

# # Start RX Thread
# print("Setting up Device")
# device, endpointReadRef, endpointWriteRef = setupDevice()
# rxQueue = queue.Queue()
# print("Starting BossSnifferRxProcess")
# bossRxThread = BossSnifferRxProcess(device, endpointReadRef, rxQueue, templateMapping)
#
# # Start running the threads!
# print("Starting bossRxThread")
# bossRxThread.start()
##############################################

def putRxQueue(obj):
    priority = 0
    rxQueue.put(PedalFSM.PrioritizedItem(priority, item=obj))


device = Device()
print("Connected. Initialising...")


rxQueue = queue.PriorityQueue()
deviceTxQueue = queue.Queue()

# Setup Rx/Tx threads
rxThread = DeviceRxThread(txCallback=putRxQueue, device=device)
rxThread.start()

# Setup Rx/Tx threads
deviceTxThread = DeviceTxThread(txQueue=deviceTxQueue, txCallback=putRxQueue, device=device)
deviceTxThread.start()

# Send Startup Messages to initialise the device
print("Sending Startup Messages")

cmd = CommandCatalogue.getStaticCommand("STARTUP.FIRST")
pedalRequest = PedalRequest(name="STARTUP.FIRST", hexPayload=cmd["request"])
deviceTxQueue.put(pedalRequest)
time.sleep(0.2)

cmd = CommandCatalogue.getStaticCommand("STARTUP.SECOND")
pedalRequest = PedalRequest(name="STARTUP.FIRST", hexPayload=cmd["request"])
deviceTxQueue.put(pedalRequest)
time.sleep(0.2)

cmd = CommandCatalogue.getStaticCommand("STARTUP.THIRD")
pedalRequest = PedalRequest(name="STARTUP.FIRST", hexPayload=cmd["request"])
deviceTxQueue.put(pedalRequest)
time.sleep(0.2)

cmd = CommandCatalogue.getStaticCommand("STARTUP.FOURTH")
pedalRequest = PedalRequest(name="STARTUP.FIRST", hexPayload=cmd["request"])
deviceTxQueue.put(pedalRequest)
time.sleep(0.2)

# Wait for confirmation (async)

time.sleep(1)

# CP: TODO: Confirm all 4 STARTUP responses to declare initialisation successful and w're ready to proceed to CONNECTED state.
##############################################



# CONFIG
BASIC_CASE_IDX_SET = [34, 35, 36, 37]
EXTENDED_CASE_IDX_SET = [35, 36, 37, 38, 39]
#def valueIs(m):
#    return (int(str(m)[2:-1][34:36], 16) * 128) + int(str(m)[2:-1][36:38], 16)




def checkExistsInConfig(rx):
    return findCmdInConfig(rx, templateMapping) is not None

print("Entering main Loop")
while True:
    def drainQueue():
        try:
            while True:
                rxQueue.get_nowait()
        except:
            pass

    def getLastRxMsg():
        LastMsg = None
        try:
            while True:
                lastMsg = rxQueue.get_nowait()
        except:
            pass

        return lastMsg


    def getStateConfig(lowestValueStateHex, highestValueStateHex):
        ret = None
        for i, statePage in enumerate(lowestValueStateHex):
            changeIdxsRaw = [i for i, x in enumerate(zip(lowestValueStateHex[i], highestValueStateHex[i])) if x[0] != x[1]]

            changeIdxs = []
            for j in changeIdxsRaw:
                if len(changeIdxs) == 0 or j == changeIdxs[-1] + 1:
                    changeIdxs.append(j)

            if len(changeIdxs) > 0:
                print(changeIdxs)
                if len(changeIdxs) > 3:
                    raise Exception("getStateConfig: More than two values changed - unexpected - perhaps you accidentally touched more than one control?")

                if len(changeIdxs) not in [1, 2, 3]:
                    raise Exception("getStateConfig: Unknown number of change fields")

                if ret is not None:
                    raise Exception("getStateConfig: State in more than one page - unexpected!")

                # If only a single value has changed (least significant digit) - assume it includes the idx before
                if len(changeIdxs) in [1, 3] and changeIdxs[0] % 2 == 1:
                    idx = [changeIdxs[0]-1] + changeIdxs
                else:
                    idx = changeIdxs

                ret = {
                    "pageId": i,
                    "idx": idx,
                }

        return ret


    drainQueue()
    getStateHex(rxQueue, device.endpointWriteRef)
    commandName = input("Enter value name")

    ok = input("Move to lowest Value")
    lowestValueHex = str(getLastRxMsg())[2:-1]

    if checkExistsInConfig(lowestValueHex):
        print("Already known this command - Breaking ")
        continue

    lowestValueStateHex = getStateHex(rxQueue, device.endpointWriteRef)

    ok = input("Move to highest Value")
    highestValueHex = str(getLastRxMsg())[2:-1]
    highestValueStateHex = getStateHex(rxQueue, device.endpointWriteRef)


    changingIdxs = [i for i, x in enumerate(zip(lowestValueHex, highestValueHex)) if x[0] != x[1]]

    # Most significant value didn't change, intervene and append to idx lis
    if len(changingIdxs) == 3:
        changingIdxs = BASIC_CASE_IDX_SET

    if changingIdxs == [35, 37]:
        changingIdxs = BASIC_CASE_IDX_SET

    # CP: TODO: Use set tests?
    if min(changingIdxs) in BASIC_CASE_IDX_SET[0:2] and max(changingIdxs) == BASIC_CASE_IDX_SET[-1]:
        lowValueHex = lowestValueHex[changingIdxs[0]: changingIdxs[1] + 1]
        highValueHex = highestValueHex[changingIdxs[0]: changingIdxs[1] + 1]

        lowValueInt = int(lowValueHex, 16)
        highValueInt = int(highValueHex, 16)

        stateConfig = getStateConfig(lowestValueStateHex, highestValueStateHex)

        cmdTemplate = getTemplateForRx(highestValueHex, templateMapping)
        idHex = highestValueHex[cmdTemplate["idIdxs"][0]: cmdTemplate["idIdxs"][1]+1]

        trackerHex = lowestValueHex[cmdTemplate["trackerHexIdxs"][0]:cmdTemplate["trackerHexIdxs"][1]+1]

        cmdConfig = {
            'idHex': idHex,
            'trackerHex': trackerHex,
            'base_template': cmdTemplate["name"],
            'minValue': lowValueInt,
            'maxValue': highValueInt,
            'stateConfig': stateConfig,
        }

        ## Verify Config
        print("Verifying Command Config....")

        # Set to Mid Value using config
        midValue = int(highValueInt / 2)
        trackerMinInt = int(trackerHex, 16)

        valueHex = hex(midValue)[2:].rjust(2, "0")
        trackerHex = hex(128 - (midValue - trackerMinInt) if midValue > trackerMinInt else trackerMinInt - midValue)[2:].rjust(2, "0")
        hexPayloadStr = cmdTemplate["template"].format(idHex=idHex, valueHex=valueHex, trackerHex=trackerHex)
        payload = bytearray.fromhex(hexPayloadStr)
        device.endpointWriteRef.write(payload)

        # Pause then Request State
        time.sleep(1)
        state = getStateHex(rxQueue, device.endpointWriteRef)

        # Check state is correct
        setValue = int(str(state[cmdConfig["stateConfig"]["pageId"]])[2:-1][cmdConfig["stateConfig"]["idx"][0]:cmdConfig["stateConfig"]["idx"][1]+1], 16)

        if setValue != midValue:
            print("FAILED")
        else:
            print("PASSED")
            categoryName = input("Enter Category: ")
            if categoryName not in originalConfig["boss"]["commands"]:
                print("Unknown category - bailing out!")
            else:
                if originalConfig["boss"]["commands"][categoryName] is None:
                    originalConfig["boss"]["commands"][categoryName] = {}

                if commandName in originalConfig["boss"]["commands"][categoryName]:
                    print("Command already exists - bailing out")
                else:
                    originalConfig["boss"]["commands"][categoryName][commandName] = cmdConfig
        print("Done....")



        i = 0

    elif min(changingIdxs) in EXTENDED_CASE_IDX_SET[0:2] and max(changingIdxs) == EXTENDED_CASE_IDX_SET[-1]:
        # CP: TODO: Magic Strings

        lowValueHex = lowestValueHex[34:38]
        highValueHex = highestValueHex[34:38]

        lowValueInt = (int(lowValueHex[0:2], 16) * 128) + int(lowValueHex[2:], 16)
        highValueInt = (int(highValueHex[0:2], 16) * 128) + int(highValueHex[2:], 16)


        stateConfig = getStateConfig(lowestValueStateHex, highestValueStateHex)

        cmdTemplate = getTemplateForRx(highestValueHex, templateMapping)
        idHex = highestValueHex[cmdTemplate["idIdxs"][0]: cmdTemplate["idIdxs"][1]+1]

        trackerHex = lowestValueHex[cmdTemplate["trackerHexIdxs"][0]:cmdTemplate["trackerHexIdxs"][1]+1]

        cmdConfig = {
            'idHex': idHex,
            'trackerHex': trackerHex,
            'base_template': cmdTemplate["name"],
            'minValue': lowValueInt,
            'maxValue': highValueInt,
            'stateConfig': stateConfig,
        }

        ## Verify Config
        print("Verifying Command Config....")

        # Set to Mid Value using config
        midValue = int(highValueInt / 2)
        trackerMinInt = int(trackerHex, 16)

        valueHex = hex(int(midValue / 128))[2:].rjust(2, "0") + hex(midValue % 128)[2:].rjust(2, "0")
        trackerHex = hex((128 - (((midValue) % 128) - trackerMinInt) if ((midValue) % 128) > trackerMinInt else trackerMinInt - ((midValue) % 128)) - (int(midValue / 128) - 1)) [2:].rjust(2, "0")
        templateStr = cmdTemplate["template"]
        hexPayloadStr = templateStr.format(idHex=idHex, valueHex=valueHex, trackerHex=trackerHex)
        payload = bytearray.fromhex(hexPayloadStr)
        device.endpointWriteRef.write(payload)

        # Pause then Request State
        time.sleep(1)
        state = getStateHex(rxQueue, device.endpointWriteRef)

        # Check state is correct
        # Original - Might not be correct - needs testing against REVERB.DTIME
        #setValue = int(str(state[cmdConfig["stateConfig"]["pageId"]])[2:-1][cmdConfig["stateConfig"]["idx"][0]:cmdConfig["stateConfig"]["idx"][-1]+1], 16)
        stateValueHex = str(state[cmdConfig["stateConfig"]["pageId"]])[2:-1][cmdConfig["stateConfig"]["idx"][0]:cmdConfig["stateConfig"]["idx"][-1] + 1]
        setValue = (int(stateValueHex[0:2], 16) * 128) + int(stateValueHex[2:], 16)

        if setValue != midValue:
            print("FAILED")
        else:
            print("PASSED")
            categoryName = input("Enter Category: ")
            if categoryName not in originalConfig["boss"]["commands"]:
                print("Unknown category - bailing out!")
            else:
                if originalConfig["boss"]["commands"][categoryName] is None:
                    originalConfig["boss"]["commands"][categoryName] = {}

                if commandName in originalConfig["boss"]["commands"][categoryName]:
                    print("Command already exists - bailing out")
                else:
                    originalConfig["boss"]["commands"][categoryName][commandName] = cmdConfig
        print("Done....")

        i = 0
    else:
        print(f"Unrecognised set of value changes: {changingIdxs}")

    #if len(changingIdxs)




    i = 0

bossRxThread.join()

i = 0
