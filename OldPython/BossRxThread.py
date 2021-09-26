from threading import Thread
import queue

import binascii

import usb.core

from BossRxCommands.DynamicCommandBase import DynamicCommandBase
from BossRxCommands.Preamp import DynamicCommandPreampType, DynamicCommandPreampSpeakerType, DynamicCommandPreampGain, \
    DynamicCommandPreampLevel, DynamicCommandPreampBass, DynamicCommandPreampMiddle, DynamicCommandPreampTreble, \
    DynamicCommandPreampPresence, DynamicCommandPreampBright


def valDict(name, value):
    return {"name": str(name), "value": str(value)}



class DynamicCommandStateUpdate():
    name = "STATE_UPDATE_PAGE_"
    base = ""
    maskIndices = []

    bases = [
        "04f0410004000000043012600400000004",
        "04f0410004000000043012600400017104",
        "04f0410004000000043012600400036204",
        "04f0410004000000043012600400055304",
        "04f0410004000000043012600400074404",
    ]

    def getValuesPage0(self, source):
        ret = []

        ## FX1 Button
        ret.append(valDict("FX1", "OFF" if str(source[547]) == str(0) else "ON"))
        ret.append(valDict("FX1_TYPE", int("".join(source[548:549 +1]), 16)))

        ## ODDS Button
        if str(source[163]) == str(0):
            ret.append(valDict("ODDS", "OFF"))

        if str(source[163]) == str(1):
            ret.append(valDict("ODDS", "ON"))

        ## PREAMP Button
        try:
            ret.append(valDict("PREAMP_ON", "OFF" if str(source[247]) == str(0) else "ON"))
            ret.append(valDict("PREAMP_TYPE", int("".join(source[250:251 +1]), 16)))
            ret.append(valDict("PREAMP_GAIN", int("".join(source[252:253 +1]), 16)))
            ret.append(valDict("PREAMP_LEVEL", int("".join(source[268:269 +1]), 16)))
            ret.append(valDict("PREAMP_BASS", int("".join(source[258:259 +1]), 16)))
            ret.append(valDict("PREAMP_MIDDLE", int("".join(source[260:261 +1]), 16)))
            ret.append(valDict("PREAMP_TREBLE", int("".join(source[262:263 +1]), 16)))
            ret.append(valDict("PREAMP_PRESENCE", int("".join(source[266:267 +1]), 16)))
            ret.append(valDict("PREAMP_SP_TYPE", int(str(source[283]), 16)))
            ret.append(valDict("PREAMP_BRIGHT", "OFF" if str(source[271]) == str(0) else "ON"))
        except Exception as e:
            print(e)


        return ret
    def getValuesPage1(self, source):
        ret = []

        ## FX2 Button
        if str(source[619]) == str(0):
            ret.append(valDict("FX2", "OFF"))

        if str(source[619]) == str(1):
            ret.append(valDict("FX2", "ON"))

        return ret

    def getValuesPage2(self, source):
        ret = []
        return ret

    def getValuesPage3(self, source):
        ret = []
        ## DELAY Button
        if str(source[69]) == str(0):
            ret.append(valDict("DELAY", "OFF"))

        if str(source[69]) == str(1):
            ret.append(valDict("DELAY", "ON"))

        ## REVERB Button
        if str(source[197]) == str(0):
            ret.append(valDict("REVERB", "OFF"))

        if str(source[197]) == str(1):
            ret.append(valDict("REVERB", "ON"))

        ## PATCH LEVEL
        ret.append(valDict("PATCH_LEVEL", int("".join(source[538:540]), 16) * 2))

        return ret
    def getValuesPage4(self, source):
        ret = []
        return ret

    def getValues(self, listifiedInput, page):
        ret = []

        try:
            if page == 0:
                ret = self.getValuesPage0(listifiedInput)
            elif page == 1:
                ret = self.getValuesPage1(listifiedInput)
            elif page == 2:
                ret = self.getValuesPage2(listifiedInput)
            elif page == 3:
                ret = self.getValuesPage3(listifiedInput)
            elif page == 4:
                ret = self.getValuesPage4(listifiedInput)
        except:
            pass

        return ret

    def matches(self, source):
        ret = None
        values = []
        for i in range(len(self.bases)):
            if len(source) >= len(self.bases[i]):
                sourceAsString = "".join(source)
                if sourceAsString[0:len(self.bases[i])] == self.bases[i]:
                    ret = self.name + str(i)
                    values = self.getValues(source, i)
                    break

        return ret, values

class DynamicCommandPatchName(DynamicCommandBase):
    name = "USER_PATCH_NAME"
    base = "04f04100040000000430121004"

    maskIndices = [26, 27, 44, 45]
    def getValues(self, listifiedInput):
        ret = []

        try:
            id = int("".join(listifiedInput[26:28]), 16)
            r = bytes.fromhex("".join(listifiedInput))
            patchName = "".join([chr(x) for x in r[16:len(r) - 2] if x == 32 or 43 <= x <= 126])
            ret.append(valDict("id", id + 1))
            ret.append(valDict("name", patchName))
        except:
            pass

        return ret

    def matches(self, source):
        ret = None
        values = []
        if len(source) >= 26:
            if "".join(source[0:26]) == self.base:
                ret = self.name
                values = self.getValues(source)

        return ret, values

class DynamicCommandPedal(DynamicCommandBase):
    name = "PDL_POSITION"
    base = "04f041000400000004301260040006**07****f7"
    maskIndices = [30, 31, 34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict("POS", int("".join(listifiedInput[34:36]), 16)))
        except:
            pass

        return ret

class DynamicCommandPatchLevel(DynamicCommandBase):
    name = "PATCH_LEVEL"
    base = "04f0410004000000043012600400071007****f7"
    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict("LEVEL", int("".join(listifiedInput[34:36]), 16) * 2))
        except:
            pass

        return ret

class DynamicCommandOutputLevel(DynamicCommandBase):
    name = "OUTPUT_LEVEL"
    base = "04f0410004000000043012000400033707****f7"
    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict("LEVEL", int("".join(listifiedInput[34:36]), 16) * 2))
        except:
            pass

        return ret

class DynamicCommandPatchSelect(DynamicCommandBase):
    name = "PATCH_SELECT"
    base = "04f0410004000000043012000401000004******05f70000"

    maskIndices = [34, 35, 36, 37, 38, 39]

    def getValues(self, listifiedInput):
        ret = []

        try:
            leadHexValue = int("".join(listifiedInput[34:36]), 16)
            hexValue = int("".join(listifiedInput[36:38]), 16)
            if leadHexValue == 0 and 0 <= hexValue <= 98:
                ret.append(valDict("type", "USER"))
                ret.append(valDict("id", str(hexValue + 1)))
            else:
                ret.append(valDict("type", "PRESET"))
                if leadHexValue == 1:
                    #ret.append("P" + str(hexValue + 30))
                    ret.append(valDict("id", str(hexValue + 30)))
                    pass
                else:
                    #ret.append("P" + str(hexValue - 99 + 1))
                    ret.append(valDict("id", str(hexValue - 99 + 1)))
                    pass
        except:
            pass

        return ret

"04f041000400000004301200040100000400****05f70000"

class BossTxCommands:
    STARTUP_FIRST      = "04f07e7f070601f7"
    STARTUP_SECOND     = "04f07e00070601f7"
    STARTUP_THIRD      = "04f04100040000000430117f0400000004000000070100f7"
    STARTUP_FOURTH     = "04f04100040000000430127f0400000107017ff7"
    STARTUP_FIFTH      = "04f0410004000000043011100400000004000000071060f7"

    FX1_ON             = "04f0410004000000043012600400014007015ef7"
    FX1_OFF            = "04f0410004000000043012600400014007005ff7"

    ODDS_ON            = "04f0410004000000043012600400003007016ff7"
    ODDS_OFF           = "04f04100040000000430126004000030070070f7"

    PREAMP_ON          = "04f0410004000000043012600400005007014ff7"
    PREAMP_OFF         = "04f04100040000000430126004000050070050f7"

    FX2_ON             = "04f0410004000000043012600400034c070150f7"
    FX2_OFF            = "04f0410004000000043012600400034c070051f7"

    DELAY_ON           = "04f0410004000000043012600400056007013af7"
    DELAY_OFF          = "04f0410004000000043012600400056007003bf7"

    REVERB_ON          = "04f04100040000000430126004000610070109f7"
    REVERB_OFF         = "04f0410004000000043012600400061007000af7"

    #CTL1_ON            = ""
    #CTL1_OFF           = ""

    PDL_ON             = "04f04100040000000430126004000620070179f7"
    PDL_OFF            = "04f0410004000000043012600400062007007af7"

    REQUEST_STATE      = "04f0410004000000043011600400000004000008070018f7"
    REQUEST_STATE2      = "04f0410004000000043011600400080004000008070010f7"
    REQUEST_STATE3      = "04f0410004000000043011600400100004000008070008f7"

class BossRxCommands:
    STATICS = {
        b"04f04100040000000430127f0400000207017ef7":               "TUNER_ON_CONFIRMATION",
        b"04f04100040000000430127f0400000207007ff7":               "TUNER_OFF_CONFIRMATION",

        b"04f0410004000000043012600400014007015ef7":               "FX1_ON_CONFIRMATION",
        b"04f0410004000000043012600400014007005ff7":               "FX1_OFF_CONFIRMATION",

        b"04f0410004000000043012600400003007016ff7":               "ODDS_ON_CONFIRMATION",
        b"04f04100040000000430126004000030070070f7":               "ODDS_OFF_CONFIRMATION",

        b"04f0410004000000043012600400005007014ff7":               "PREAMP_ON_CONFIRMATION",
        b"04f04100040000000430126004000050070050f7":               "PREAMP_OFF_CONFIRMATION",

        b"04f0410004000000043012600400034c070150f7":               "FX2_ON_CONFIRMATION",
        b"04f0410004000000043012600400034c070051f7":               "FX2_OFF_CONFIRMATION",

        b"04f0410004000000043012600400056007013af7":               "DELAY_ON_CONFIRMATION",
        b"04f0410004000000043012600400056007003bf7":               "DELAY_OFF_CONFIRMATION",

        b"04f04100040000000430126004000610070109f7":               "REVERB_ON_CONFIRMATION",
        b"04f0410004000000043012600400061007000af7":               "REVERB_OFF_CONFIRMATION",

        #b"":               "CTL1_ON_CONFIRMATION",
        #b"":               "CTL1_OFF_CONFIRMATION",

        b"04f04100040000000430126004000620070179f7":               "PDL_ON_CONFIRMATION",
        b"04f0410004000000043012600400062007007af7":               "PDL_OFF_CONFIRMATION",
    }

    DYNAMICS = [
        DynamicCommandPedal(),
        DynamicCommandPatchLevel(),
        DynamicCommandOutputLevel(),
        DynamicCommandPatchSelect(),
        DynamicCommandPatchName(),
        DynamicCommandStateUpdate(),

        DynamicCommandPreampType(),
        DynamicCommandPreampGain(),
        DynamicCommandPreampLevel(),
        DynamicCommandPreampBass(),
        DynamicCommandPreampMiddle(),
        DynamicCommandPreampTreble(),
        DynamicCommandPreampPresence(),
        DynamicCommandPreampBright(),
        DynamicCommandPreampSpeakerType(),
    ]

    @staticmethod
    def checkForStaticMatch(payload):
        if payload in BossRxCommands.STATICS:
            return {
                "source": "GT1",
                "type": BossRxCommands.STATICS[payload],
                "values": []
            }

    @staticmethod
    def checkForDynamicMatch(listifiedInput):
        ret = None
        for candidate in BossRxCommands.DYNAMICS:
            type, values = candidate.matches(listifiedInput)
            if type is not None:
                return {
                    "source": "GT1",
                    "type": type,
                    "values": values
                }

        return None



class BossRxThread(Thread):
    def __init__(self, queue, bossRxThreadPoisonPillQueue, bossNotificationQueues, device, endpoint):
        Thread.__init__(self)
        self.queue = queue
        self.bossNotificationQueues = bossNotificationQueues
        self.bossRxThreadPoisonPillQueue = bossRxThreadPoisonPillQueue
        self.endpoint = endpoint
        self.device = device

    def run(self):
        while True:
            if not self.bossRxThreadPoisonPillQueue.empty():
                print("BossRxThread:: GOT POISON PILL...")
                break
            try:
                data = self.device.read(self.endpoint.bEndpointAddress, self.endpoint.wMaxPacketSize)
                if sum(data) > 0:
                    payload = binascii.hexlify(bytearray(data))



                    # Do we recognise this message?
                    match = None
                    staticMatch = BossRxCommands.checkForStaticMatch(payload)
                    if staticMatch is not None:
                        match = staticMatch
                    else:
                        listifiedHexStream = list(str(payload)[2:-1])
                        dynMatch = BossRxCommands.checkForDynamicMatch(listifiedHexStream)
                        if dynMatch is not None:
                            match = dynMatch


                    if match is not None:
                        for q in self.bossNotificationQueues:
                            q.put(match)


                    print("\t\t BossRxThread - Rx:: [{match}] :: {raw}".format(match = match, raw = str(payload)))

                    self.queue.put(payload)

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

