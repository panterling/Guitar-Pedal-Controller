import binascii
import time
from pathlib import Path
from multiprocessing import Process

import copy

import threading
import usb
import yaml
from usb.core import Endpoint

from OldPython.BossRxThread import BossTxCommands


def setupDevice():
    device = usb.core.find(idVendor=0x0582, idProduct=0x01d6)

    if device is None:
        raise Exception("Device not found")

    for i in range(4):
        if device.is_kernel_driver_active(i):
            device.detach_kernel_driver(i)

    # Has Endpoints
    interfaceIdx = 3

    # claim the device
    endpointWriteRef = None
    endpointReadRef = None
    try:
        usb.util.claim_interface(device, interfaceIdx)
        endpointWriteRef = device[0][(interfaceIdx, 0)][0]
        endpointReadRef = device[0][(interfaceIdx, 0)][1]
    except usb.USBError as e:
        raise e
    except Exception as e:
        raise e

    return device, endpointReadRef, endpointWriteRef #CP: Encode as Model


def getStateHex(rxQueue, endpointWriteRef):
    # Drain Queue
    try:
        while True:
            rxQueue.get_nowait()
    except:
        pass

    # Request State - PART 1
    print("Requesting STATE_1")
    endpointWriteRef.write(bytearray.fromhex(BossTxCommands.REQUEST_STATE))

    # Give some time for a response
    time.sleep(2)

    # Request State - PART 2
    print("Requesting STATE_2")
    endpointWriteRef.write(bytearray.fromhex(BossTxCommands.REQUEST_STATE2))

    # Give some time for a response
    time.sleep(2)

    # Request State - PART 3
    print("Requesting STATE_3")
    endpointWriteRef.write(bytearray.fromhex(BossTxCommands.REQUEST_STATE3))

    # Give some time for a response
    time.sleep(2)

    # State is the following  messages
    statePageResponses = [rxQueue.get_nowait() for x in range(11)]
    state = [x.item.value[2:-1] for x in statePageResponses]

    return state



def getTemplateForRx(rx, templateMapping):
    ret = None
    for templateName, templateInfo in templateMapping.items():
        if all([a == b for a, b in zip(templateInfo["pattern"], rx) if a != "*"]):
            ret = templateInfo
    return ret


def findCmdInConfig(rx, templateMapping):
    ret = None

    templateInfo = getTemplateForRx(rx, templateMapping)

    if templateInfo is not None:
        idHex = rx[templateInfo["idIdxs"][0]:templateInfo["idIdxs"][1]+1]
        for cmd in templateInfo["commands"]:
            if cmd["idHex"] == idHex:
                ret = cmd

    return ret


def loadConfig():
    configFilePath = Path.joinpath(Path(__file__).parent, "../../", "BossRxCommands/CommandDictionary.yaml")
    originalConfig = yaml.load(open(configFilePath))
    commandConfig = copy.deepcopy(originalConfig)

    templateMapping = {}
    commandLookup = {}
    for bt in commandConfig["boss"]["base_templates"]:
        templateInfo = commandConfig["boss"]["base_templates"][bt]

        pattern = templateInfo["template"].format(idHex="*" * (templateInfo["idIdxs"][1] - templateInfo["idIdxs"][0] + 1),
                                                  valueHex="*" * (templateInfo["valueHexIdxs"][1] - templateInfo["valueHexIdxs"][0] + 1),
                                                  trackerHex="*" * (templateInfo["trackerHexIdxs"][1] - templateInfo["trackerHexIdxs"][0] + 1))
        templateInfo["name"] = bt
        templateInfo["pattern"] = pattern
        templateInfo["commands"] = []
        templateMapping[bt] = templateInfo

    # Store commands for quick Rx/Tx Lookup
    for category in commandConfig["boss"]["commands"]:
        if commandConfig["boss"]["commands"][category] is not None:
            for name in commandConfig["boss"]["commands"][category]:
                cmd = commandConfig["boss"]["commands"][category][name]

                fullName = f"{category.upper()}.{name.upper()}"
                cmd["name"] = fullName

                templateMapping[cmd["base_template"]]["commands"].append(cmd)
                commandLookup[fullName] = cmd

    return templateMapping, commandLookup, originalConfig, commandConfig


class BossSnifferRxProcess(Process):
    def __init__(self, device, endpointReadRef, rxQueue, templateMapping=None):
        super().__init__()

        self.device = device
        self.endpointReadRef = endpointReadRef
        self.rxQueue = rxQueue
        self.templateMapping = templateMapping
        self.shutdownFlag = threading.Event()



    def run(self):
        while not self.shutdownFlag.is_set():
            try:
                data = self.device.read(self.endpointReadRef.bEndpointAddress, self.endpointReadRef.wMaxPacketSize)
                if sum(data) > 0:
                    payload = binascii.hexlify(bytearray(data))

                    rx = str(payload)[2:-1]

                    cmd = None
                    if self.templateMapping is not None:
                        cmd = findCmdInConfig(rx, self.templateMapping)

                    if cmd is not None:
                        valueHexIdxs = self.templateMapping[cmd["base_template"]]["valueHexIdxs"]
                        valueHex = rx[valueHexIdxs[0]: valueHexIdxs[1]+1]
                        value = int(valueHex, 16)
                        print(f"Rx:: {cmd['name']} = {value}")
                    else:
                        print(f"Rx:: {rx}")

                    self.rxQueue.put(payload)

            except usb.core.USBError as e:
                data = None
                if e.args == ('Operation timed out',):
                    print("Read timeout....")
                    print(e)
                    continue
            except Exception as e:
                print("Other exception")
                print(e)
                break

        print("BossRxThread:: DEAD")