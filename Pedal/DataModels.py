from dataclasses import dataclass
from typing import Optional, List, Union

from Helpers import Misc


class PedalCommand:
    def __init__(self, commandName: str):
        self.commandName = commandName

    def __str__(self):
        return self.commandName

class PedalFSMAction:
    def __init__(self, actionName: str):
        self.actionName = actionName
        self.extra = {}

    def __str__(self):
        return self.actionName

    def __hash__(self):
        return Misc.stringToNumericHash(self.actionName)

    def __eq__(self, other: "PedalFSMAction"):
        return other.actionName == self.actionName and other.__class__.__name__ == self.__class__.__name__


class PedalFSMState:
    def __init__(self, stateName: str, validActions: Optional[List[PedalFSMAction]] = None):
        self.stateName = stateName
        self.validActions = validActions if validActions is not None else []

    def __str__(self):
        return self.stateName

    def __hash__(self):
        return Misc.stringToNumericHash(self.stateName)

    def __eq__(self, other: "PedalFSMState"):
        return other.stateName == self.stateName and other.__class__.__name__ == self.__class__.__name__




# Actions
class PedalFSMActionConnect(PedalFSMAction):
    def __init__(self):
        super().__init__("CONNECT")

class PedalFSMActionDisconnect(PedalFSMAction):
    def __init__(self):
        super().__init__("DISCONNECT")

#PedalFSMAction.CONNECT = PedalFSMAction("CONNECT")
#PedalFSMAction.DISCONNECT = PedalFSMAction("DISCONNECT")

class PedalFSMActionSendCommand(PedalFSMAction):
    def __init__(self, actionName = "SEND_COMMAND"):
        super().__init__(actionName)

    def attachCommand(self, cmdFullName: str, cmdPayload: Optional[dict] = None) -> "PedalFSMActionSendCommand":
        ret = PedalFSMActionSendCommand(self.actionName)
        ret.extra["cmdFullName"] = cmdFullName
        ret.extra["cmdPayload"] = cmdPayload
        return ret

class PedalFSMActionSendStaticCommand(PedalFSMActionSendCommand):
    def __init__(self):
        super().__init__("SEND_STATIC_COMMAND")

    def attachCommand(self, cmdFullName: str, cmdPayload: Optional[dict] = None) -> "PedalFSMActionSendStaticCommand":
        ret = PedalFSMActionSendStaticCommand()
        ret.extra["cmdFullName"] = cmdFullName
        ret.extra["cmdPayload"] = cmdPayload
        return ret

# PedalFSMAction.SEND_COMMAND = PedalFSMActionSendCommand("SEND_COMMAND")
# PedalFSMAction.SEND_STATIC_COMMAND = PedalFSMActionSendCommand("SEND_STATIC_COMMAND")


# States
class PedalFSMStateDisconnected(PedalFSMState):
    def __init__(self):
        super().__init__("DISCONNECTED")

class PedalFSMStateConnecting(PedalFSMState):
    def __init__(self):
        super().__init__("CONNECTING")

class PedalFSMStateInitialising(PedalFSMState):
    def __init__(self):
        super().__init__("INITIALISING")

class PedalFSMStateConnected(PedalFSMState):
    def __init__(self):
        super().__init__("CONNECTED")

# PedalFSMState.DISCONNECTED = PedalFSMState("DISCONNECTED")
# PedalFSMState.CONNECTING = PedalFSMState("CONNECTING")
# PedalFSMState.INITIALISING = PedalFSMState("INITIALISING")
# PedalFSMState.CONNECTED = PedalFSMState("CONNECTED")



########################################

class PedalResponse:
    def __init__(self, name: str, value: Union[int, str]):
        self.name = name
        self.value = value
        self.pedalRxTimestamp: float = None
        self.notificationTimestamp: float = None

    def __str__(self):
        return f"{self.name} = {self.value}"

class PedalRequest:
    def __init__(self, name, hexPayload):
        self.name = name
        self.hexPayload = hexPayload

    def toHex(self):
        return self.hexPayload


class UnmappedPedalResponse(PedalResponse):
    def __init__(self, value: Union[int, str]):
        super().__init__("Unmapped", value)




@dataclass
class BluetoothRxMessage:
    payload: str