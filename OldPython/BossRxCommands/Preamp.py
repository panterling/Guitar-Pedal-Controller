from BossRxCommands.DynamicCommandBase import DynamicCommandBase

# CP: Non-DRY
def valDict(name, value):
    return {"name": str(name), "value": str(value)}

class DynamicCommandPreampType(DynamicCommandBase):
    name = "PREAMP_TYPE"

    base = "04f0410004000000043012600400005107****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampType.name, int("".join(listifiedInput[34:35 +1]), 16)))
        except:
            pass

        return ret


class DynamicCommandPreampGain(DynamicCommandBase):
    name = "PREAMP_GAIN"
    base = "04f0410004000000043012600400005207****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampGain.name, int("".join(listifiedInput[34:35 +1]), 16)))
        except:
            pass

        return ret


class DynamicCommandPreampLevel(DynamicCommandBase):
    name = "PREAMP_LEVEL"
    base = "04f0410004000000043012600400005807****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampLevel.name, int("".join(listifiedInput[34:35 +1]), 16)))
        except:
            pass

        return ret

class DynamicCommandPreampBass(DynamicCommandBase):
    name = "PREAMP_BASS"
    base = "04f0410004000000043012600400005407****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampBass.name, int("".join(listifiedInput[34:35 +1]), 16)))
        except:
            pass

        return ret

class DynamicCommandPreampMiddle(DynamicCommandBase):
    name = "PREAMP_MIDDLE"
    base = "04f0410004000000043012600400005507****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampMiddle.name, int("".join(listifiedInput[34:35 +1]), 16)))
        except:
            pass

        return ret


class DynamicCommandPreampTreble(DynamicCommandBase):
    name = "PREAMP_TREBLE"
    base = "04f0410004000000043012600400005607****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampTreble.name, int("".join(listifiedInput[34:35 +1]), 16)))
        except:
            pass

        return ret

class DynamicCommandPreampPresence(DynamicCommandBase):
    name = "PREAMP_PRESENCE"
    base = "04f0410004000000043012600400005707****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampPresence.name, int("".join(listifiedInput[34:35 +1]), 16)))
        except:
            pass

        return ret

class DynamicCommandPreampBright(DynamicCommandBase):
    name = "PREAMP_BRIGHT"
    base = "04f0410004000000043012600400005907****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampBright.name, "OFF" if str(listifiedInput[35]) == str(0) else "ON"))
        except:
            pass

        return ret


class DynamicCommandPreampSpeakerType(DynamicCommandBase):
    name = "PREAMP_SP_TYPE"

    base = "04f0410004000000043012600400005d07****f7"

    maskIndices = [34, 35, 36, 37]

    def getValues(self, listifiedInput):
        ret = []

        try:
            ret.append(valDict(DynamicCommandPreampSpeakerType.name, int("".join(listifiedInput[34:35 +1]), 16)))
        except:
            pass

        return ret