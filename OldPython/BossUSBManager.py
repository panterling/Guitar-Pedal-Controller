from threading import Thread
import queue

from GPIOManager import GPIOManager

import usb.core
import usb.util
import binascii

from BossRxThread import BossRxThread, BossTxCommands
from Config import GPIO_PINS


class BossUSBManager():
    TUNER_ON = 1
    TUNER_OFF = 2
    SET_OUTPUT_LEVEL = 3
    SET_PATCH_LEVEL = 4
    SELECT_USER_PATCH = 5
    SELECT_PRESET_PATCH = 6

    # TOGGLES
    FX1_ON = 7
    FX1_OFF = 8
    ODDS_ON = 9
    ODDS_OFF = 10
    PREAMP_ON = 11
    PREAMP_OFF = 12
    FX2_ON = 13
    FX2_OFF = 14
    DELAY_ON = 15
    DELAY_OFF = 16
    REVERB_ON = 17
    REVERB_OFF = 18
    PDL_ON = 19
    PDL_OFF = 20

    # MISC
    GET_USER_PATCH_NAME = 21

    REQUEST_STATE = 22

    # PREAMP SPECIFIC
    SET_PREAMP_LEVEL = 23
    


    def __init__(self, bossNotificationQueues):

        self.bossConnected = False

        self.bossRxThread = None

        self.bossNotificationQueues = bossNotificationQueues

        self.rxQueue = queue.Queue()
        self.commandMap = {
            self.TUNER_ON: self.tunerOn,
            self.TUNER_OFF: self.tunerOff,
            self.FX1_ON: self.fx1On,
            self.FX1_OFF: self.fx1Off,
            self.ODDS_ON: self.oddsOn,
            self.ODDS_OFF: self.oddsOff,

            self.PREAMP_ON: self.preampOn,
            self.PREAMP_OFF: self.preampOff,

            self.SET_PREAMP_LEVEL: self.preampSetLevel,
            #self.SET_PREAMP_GAIN: self.preampSetGain,
            #self.SET_PREAMP_BASS: self.preampSetBass,
            #self.SET_PREAMP_MIDDLE: self.preampSetMiddle,
            #self.SET_PREAMP_TREBLE: self.preampSetTreble,
            #self.SET_PREAMP_PRESENCE: self.preampSetPresence,
            #self.SET_PREAMP_TYPE: self.preampSetType,
            #self.SET_PREAMP_SPTYPE: self.preampSetSPType,
            #self.SET_PREAMP_BRIGHT: self.preampSetBright,


            self.FX2_ON: self.fx2On,
            self.FX2_OFF: self.fx2Off,
            self.DELAY_ON: self.delayOn,
            self.DELAY_OFF: self.delayOff,
            self.REVERB_ON: self.reverbOn,
            self.REVERB_OFF: self.reverbOff,
            self.PDL_ON: self.pedalOn,
            self.PDL_OFF: self.pedalOff,

            self.SET_OUTPUT_LEVEL: self.setOutputLevel,
            self.SET_PATCH_LEVEL: self.setPatchLevel,
            self.SELECT_USER_PATCH: self.selectUserPatch,
            self.SELECT_PRESET_PATCH: self.selectPresetPatch,

            self.GET_USER_PATCH_NAME: self.getUserPatchName,

            self.REQUEST_STATE: self.requestState,

        }

    def selectUserPatch(self, id):
        self.selectUserPatchById(id)

    def selectPresetPatch(self, id):
        self.selectPermenantPatchById(id)

    def fx1On(self):
        self.sendHexString(BossTxCommands.FX1_ON)

    def fx1Off(self):
        self.sendHexString(BossTxCommands.FX1_OFF)

    def oddsOn(self):
        self.sendHexString(BossTxCommands.ODDS_ON)

    def oddsOff(self):
        self.sendHexString(BossTxCommands.ODDS_OFF)


    def preampOn(self):
        self.sendHexString(BossTxCommands.PREAMP_ON)

    def preampOff(self):
        self.sendHexString(BossTxCommands.PREAMP_OFF)

    def preampSetLevel(self, level):
        level = int(level)

        if level < 0:
            level = 0
        elif level > 100:
            level = 100

        hexValue = hex(level)
        if level <= 72:
            tailValue = hex(0x48 - level)
        else:
            tailValue = hex(0x7f - (level - 73))
        self.sendHexString("04f0410004000000043012600400005807{}{}f7".format(str(hexValue)[2:].rjust(2, "0"),
                                                                             str(tailValue)[2:].rjust(2, "0")))


    def fx2On(self):
        self.sendHexString(BossTxCommands.FX2_ON)

    def fx2Off(self):
        self.sendHexString(BossTxCommands.FX2_OFF)

    def delayOn(self):
        self.sendHexString(BossTxCommands.DELAY_ON)

    def delayOff(self):
        self.sendHexString(BossTxCommands.DELAY_OFF)

    def reverbOn(self):
        self.sendHexString(BossTxCommands.REVERB_ON)

    def reverbOff(self):
        self.sendHexString(BossTxCommands.REVERB_OFF)

    def pedalOn(self):
        self.sendHexString(BossTxCommands.PDL_ON)

    def pedalOff(self):
        self.sendHexString(BossTxCommands.PDL_OFF)

    def requestState(self):
        self.sendHexString(BossTxCommands.REQUEST_STATE)


    def getUserPatchName(self, i):
        i = int(i)

        hexValue = hex(i)
        tailValue = hex(96 - i) if i < 97 else hex(127 - (i - 97))

        hexValue = str(hexValue[2:]).rjust(2, "0")
        tailValue = str(tailValue[2:]).rjust(2, "0")

        self.sendHexString("04f04100040000000430111004{}0000040000000710{}f7".format(hexValue, tailValue))


    def start(self):
        print("Preparing Boss GT1")
        self.dev = usb.core.find(idVendor=0x0582, idProduct=0x01d6)

        if self.dev is None:
            print(ValueError('Device not found/connected - Aborting startup'))
            return

        for i in range(4):
            if self.dev.is_kernel_driver_active(i):
                self.dev.detach_kernel_driver(i)

        # dev.set_configuration()
        cfg = self.dev.get_active_configuration()

        # Has Endpoints
        interfaceIdx = 3

        # claim the device
        usb.util.claim_interface(self.dev, interfaceIdx)
        self.endpointWriteRef = self.dev[0][(interfaceIdx, 0)][0]
        self.endpointReadRef = self.dev[0][(interfaceIdx, 0)][1]

        # Start Rx Thread

        if self.bossRxThread is not None:
            if self.bossRxThread.is_alive():
                self.bossRxThreadPoisonPillQueue.put("DIE")

        self.bossRxThreadPoisonPillQueue = queue.Queue()

        self.bossRxThread = BossRxThread(self.rxQueue, self.bossRxThreadPoisonPillQueue, self.bossNotificationQueues, self.dev, self.endpointReadRef)

        # Start running the threads!
        self.bossRxThread.start()

        self.bossConnected = True

        # First
        self.sendHexString(BossTxCommands.STARTUP_FIRST)
        self.rxQueue.get(block = True, timeout = 2)

        # Second
        self.sendHexString(BossTxCommands.STARTUP_SECOND)
        self.rxQueue.get(block = True, timeout = 2)

        # Third
        self.sendHexString(BossTxCommands.STARTUP_THIRD)
        self.rxQueue.get(block = True, timeout = 2)


        # Fourth
        self.sendHexString(BossTxCommands.STARTUP_FOURTH)

        # Fifth
        self.sendHexString(BossTxCommands.STARTUP_FIFTH)
        self.rxQueue.get(block = True, timeout = 2)

        GPIOManager.outputHigh(GPIO_PINS.GT1_STATUS_PIN)
        print(" == Boss Manager Ready == ")


    def runCommand(self, commandIndex, value = None):
        commandIndex = int(commandIndex)
        if commandIndex in self.commandMap:
            if value is not None:
                self.commandMap[commandIndex](value)
            else:
                self.commandMap[commandIndex]()
        pass

    def sendHexString(self, s):
        if self.bossConnected:
            payload = bytearray.fromhex(s)
            print("Tx:: " + str(binascii.hexlify(bytearray(payload))))
            try:
                self.endpointWriteRef.write(payload)
            except Exception as e:
                self.bossConnected = False

        else:
            print("Tx - ERROR: GT1 Not connected - Attempting to re-connect")

            # Inform App
            for q in self.bossNotificationQueues:
                q.put({
                    "source": "SERVER",
                    "type": "GT1_DISCONNECTED",
                    "values": []
                })

            ## Pi Indicator
            GPIOManager.outputLow(GPIO_PINS.GT1_STATUS_PIN)

            ## Attempt to reconnect
            self.start()





    def selectUserPatchById(self, id):
        id = int(id)

        if id < 1 or id > 99:
            raise Exception("Invalid Patch Id: 1 - 99 only")

        hexValue = hex(id - 1)
        tailValue = hex(0x7f - (id - 1))

        hexValue = str(hexValue[2:]).rjust(2, "0")
        tailValue = str(tailValue[2:]).rjust(2, "0")

        self.sendHexString("04f041000400000004301200040100000400{}{}05f70000".format(hexValue, tailValue))

    def selectPermenantPatchById(self, id):
        id = int(id)

        if id < 1 or id > 99:
            raise Exception("Invalid Patch Id: 1 - 99 only")

        if id < 30:
            leadHex = hex(0)
            hexValue = hex(id + 99 - 1)
            tailValue = hex(0x7f - (id + 99 - 1))
        else:
            leadHex = hex(1)
            hexValue = hex((id - 29) + - 1)
            tailValue = hex(0x7e - (id - 30))

        leadHex = str(leadHex[2:]).rjust(2, "0")
        hexValue = str(hexValue[2:]).rjust(2, "0")
        tailValue = str(tailValue[2:]).rjust(2, "0")

        self.sendHexString("04f0410004000000043012000401000004{}{}{}05f70000".format(leadHex, hexValue, tailValue))

    def requestState(self):
        self.sendHexString("04f0410004000000043011600400000004000008070018f7")

    def tunerOn(self):
        self.sendHexString("04f04100040000000430127f0400000207017ef7")

    def tunerOff(self):
        self.sendHexString("04f04100040000000430127f0400000207007ff7")



    def setOutputLevel(self, level):
        level = int(level)

        if level < 0:
            level = 0
        elif level > 200:
            level = 200
        elif level % 2 == 1:
            level += 1

        halfLevel = int(level / 2)# if int(level / 2) % 2 == 0 else int(level / 2) - 1

        hexValue = hex(halfLevel)
        if halfLevel <= 70:
            tailValue = hex(0x46 - halfLevel)
        else:
            tailValue = hex(0x7f - (halfLevel - 71))

        self.sendHexString("04f0410004000000043012000400033707{}{}f7".format(str(hexValue)[2:].rjust(2, "0"), str(tailValue)[2:].rjust(2, "0")))

    def setPatchLevel(self, level):
        level = int(level)

        if level < 0:
            level = 0
        elif level > 200:
            level = 200
        elif level % 2 == 1:
            level += 1

        halfLevel = int(level / 2)# if int(level / 2) % 2 == 0 else int(level / 2) - 1

        hexValue = hex(halfLevel)
        if halfLevel <= 9:
            tailValue = hex(0x46 - halfLevel)
        else:
            tailValue = hex(0x7f - (halfLevel - 10))
        self.sendHexString("04f0410004000000043012600400071007{}{}f7".format(str(hexValue)[2:].rjust(2, "0"), str(tailValue)[2:].rjust(2, "0")))

    def getPatchNames(self):

        # User-Defined
        for i in range(99):
            self.getUserPatchName(i)

        # Permenant
        for i in range(99):
            hexValue = hex(i)
            tailValue = hex(80 - i) if i < 81 else hex(127 - (i - 81))

            hexValue = str(hexValue[2:]).rjust(2, "0")
            tailValue = str(tailValue[2:]).rjust(2, "0")

            self.sendHexString("04f04100040000000430112004{}0000040000000710{}f7".format(hexValue, tailValue))