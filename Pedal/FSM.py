import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any, Callable, Union

import os

from Helpers.Logging import LoggerFactory
from Pedal.CommandCatalogue import CommandCatalogue
from Pedal.DataModels import PedalFSMState, PedalFSMActionSendCommand, PedalFSMAction, PedalFSMActionConnect, \
    PedalFSMStateDisconnected, PedalFSMStateConnecting, PedalFSMStateInitialising, PedalFSMStateConnected, \
    PedalFSMActionDisconnect, PedalFSMActionSendStaticCommand, BluetoothRxMessage, UnmappedPedalResponse
from Pedal.Device import Device, DeviceRxThread, PedalRequest, DeviceTxThread, PedalResponse


class PedalFSMSubscriber(ABC):
    @abstractmethod
    def notifyOfPedalResponse(self, pedalResponse: PedalResponse):
        pass

    @abstractmethod
    def notifyOfStateChange(self, newState: PedalFSMState):
        pass


class PedalFSM(threading.Thread):

    # CP: TODO: This belongs in a more Helper/General namespace
    @dataclass(order=True)
    class PrioritizedItem:
        priority: int
        item: Any = field(compare=False)

    # Exceptions
    class IllegalStateChangeRequest(Exception):
        pass

    def notifyOfBluetoothRx(self, payload: dict):
        self.logger.info(f"Got Bluetooth RX - what now?")

        # Process and validate
        # CP: TODO: Validation logic
        try:
            commandFullName = payload["name"]
            value = int(payload["value"])

            # Take Action
            self.doAction(PedalFSMActionSendCommand().attachCommand(commandFullName, {"value": value}))
        except Exception as e:
            self.logger.error(f"notifyOfBluetoothRx: Unhandled Exception: {e}")

    # Type Hints
    # N/A

    def __init__(self, rxQueue = None):
        super().__init__()

        self.shutdownFlag = threading.Event()

        self.logger = LoggerFactory.getUniqueLogger("PedalFSM")
        [x.setFormatter(logging.Formatter('%(asctime)s - <%(PID)s> %(name)s::[%(currentState)15s] %(message)s')) for x in self.logger.handlers]
        self.logger.addFilter(ContextFilter(self))

        self.currentState: PedalFSMState = PedalFSMStateDisconnected()
        self._declareStateActionMapping()

        # Communication channels
        self.rxQueue = rxQueue or queue.PriorityQueue()
        self.deviceTxQueue = queue.Queue()
        self.deviceTxThread = None
        self.rxThread = None


        self.subscribers: List[PedalFSMSubscriber] = []

    def run(self):
        # Not on main thread
        self.logger.info("Worker Thread Srarted")
        try:
            while not self.shutdownFlag.is_set():
                msg = self.rxQueue.get().item
                self.logger.info(f"Rx [{type(msg)}]: {msg}")

                if isinstance(msg, Device.DeviceDisconnected):
                    self.logger.warning("DeviceTx notified of DeviceDisconnected")
                    self.disconnect(None)

                elif isinstance(msg, PedalFSMAction):
                    self.logger.info(f"Got TX[Action]: {msg}")
                    action = msg

                    if isinstance(msg, PedalFSMActionSendCommand):
                        action = msg
                        if action == PedalFSMActionSendCommand():
                            self.sendCommand(action)

                        elif action == PedalFSMActionSendStaticCommand():
                            self.sendStaticCommand(action)
                        else:
                            raise Exception(f"Unknown PedalFSMActionSendCommand actionName: {action.actionName}")

                    elif action in self.STATE_ACTION_MAP[self.currentState]:
                        self.logger.info(f"Calling Action [{action}] in State [{self.currentState}]")
                        self.STATE_ACTION_MAP[self.currentState][action](action)
                    else:
                        self.logger.warning(f"Invalid Action [{action}] in State [{self.currentState}]")



                elif isinstance(msg, PedalResponse):
                    if isinstance(msg, UnmappedPedalResponse):
                        self.logger.info(f"Swallowing Unmapped Response [{msg}]")
                    else:
                        self.logger.info(f"Forwarding [{msg}] to subscribers")
                        msg.notificationTimestamp = time.time()
                        for s in self.subscribers:
                            s.notifyOfPedalResponse(msg)
                elif isinstance(msg, BluetoothRxMessage):
                    # CP: TODO: This logic does not belong here
                    cmdFullName = msg.payload["name"]
                    value = msg.payload["value"]

                    action = PedalFSMActionSendCommand().attachCommand(cmdFullName=cmdFullName, cmdPayload={"value": value})
                    self.sendCommand(action)
                else:
                    self.logger.error(f"Unexpected message: {type(msg)}")

        except Exception as e:
            self.logger.error(f"Unexpected Exception: {e}")

        self.logger.error("Worker Thread Terminated")


    def _declareStateActionMapping(self):
        self.STATE_ACTION_MAP = {
            PedalFSMStateDisconnected(): {
                PedalFSMActionConnect(): self.connect
            },
            PedalFSMStateConnecting(): {
                PedalFSMActionDisconnect(): self.disconnect
            },
            PedalFSMStateInitialising(): {
                PedalFSMActionDisconnect(): self.disconnect
            },
            PedalFSMStateConnected(): {
                PedalFSMActionDisconnect(): self.disconnect,
                PedalFSMActionSendCommand(): self.sendCommand,
                PedalFSMActionSendStaticCommand(): self.sendStaticCommand,
            },
        }

        self.TRANSIITON_MAP = {
            PedalFSMStateDisconnected(): {PedalFSMStateConnecting()},
            PedalFSMStateConnecting(): {PedalFSMStateDisconnected(), PedalFSMStateInitialising()},
            PedalFSMStateInitialising(): {PedalFSMStateDisconnected(), PedalFSMStateConnected()},
            PedalFSMStateConnected(): {PedalFSMStateDisconnected()},
        }

    def setState(self, newState: PedalFSMState):
        if newState in self.TRANSIITON_MAP[self.currentState]:
            self.logger.info(f"Changing State and notifying subscribers: [{self.currentState}] -> [{newState}]")
            self.currentState = newState

            for s in self.subscribers:
                s.notifyOfStateChange(newState)

        else:
            raise PedalFSM.IllegalStateChangeRequest()

    def connect(self, triggerAction: PedalFSMAction):
        self.setState(PedalFSMStateConnecting())

        try:
            self.device = Device()
            self.setState(PedalFSMStateInitialising())
            self.logger.info("Connected. Initialising...")

            # Setup Rx/Tx threads
            self.rxThread = DeviceRxThread(txCallback=self.putRxQueue, device=self.device)
            self.rxThread.start()

            # Setup Rx/Tx threads
            self.deviceTxThread = DeviceTxThread(txQueue=self.deviceTxQueue, txCallback=self.putRxQueue, device=self.device)
            self.deviceTxThread.start()

            # Fire off 'init' commands
            # CP: Should be via the sendCommand interface!
            import time
            self.doAction(PedalFSMActionSendStaticCommand().attachCommand("STARTUP.FIRST"))
            time.sleep(0.2)
            self.doAction(PedalFSMActionSendStaticCommand().attachCommand("STARTUP.SECOND"))
            time.sleep(0.2)
            self.doAction(PedalFSMActionSendStaticCommand().attachCommand("STARTUP.THIRD"))
            time.sleep(0.2)
            self.doAction(PedalFSMActionSendStaticCommand().attachCommand("STARTUP.FOURTH"))
            time.sleep(0.2)

            # Wait for confirmation (async)
            import time
            time.sleep(1)

            # CP: TODO: Confirm all 4 STARTUP responses to declare initialisation successful and w're ready to proceed to CONNECTED state.

            self.setState(PedalFSMStateConnected())


        except Exception as e:
            self.setState(PedalFSMStateDisconnected())
            self.logger.error(f"Connection Error: {e}")


    def disconnect(self, triggerAction: PedalFSMAction):
        #self.device.shutdown()
        self.setState(PedalFSMStateDisconnected())

        self.rxThread.shutdownFlag.set()
        self.deviceTxThread.shutdownFlag.set()

        # Reset State
        self.device = None
        self.rxThread = None
        self.deviceTxThread = None

        self.logger.info("Shutting Down - waiting 5 seconds for threads to terminate")
        time.sleep(5)

        # Purge Queues
        while not self.deviceTxQueue.empty():
            self.deviceTxQueue.get()


    def sendStaticCommand(self, triggerAction: PedalFSMActionSendCommand):
        cmdFullName = triggerAction.extra["cmdFullName"]

        cmd = CommandCatalogue.getStaticCommand(cmdFullName)

        pedalRequest = PedalRequest(name=cmdFullName,
                                    hexPayload=cmd["request"])  # CP: Don't like use of dictionary key here - remodel!

        self.deviceTxQueue.put(pedalRequest)
        self.logger.info(f"Sent Static command [{cmdFullName}] to device")

    def sendCommand(self, triggerAction: PedalFSMActionSendCommand):
        cmdPayload = triggerAction.extra["cmdPayload"]


        cmdFullName = triggerAction.extra["cmdFullName"]
        cmd = CommandCatalogue.getCommand(cmdFullName)

        value = cmdPayload["value"]

        #############
        #def toHex():

        cmdTemplate = CommandCatalogue.getCmdBaseTemplate(cmd["base_template"])
        idHex = cmd["idHex"]
        trackerHex = cmd["trackerHex"]
        trackerMinInt = int(trackerHex, 16)

        if False: #4 digit value
            trackerHex = hex((128 - (((value) % 128) - trackerMinInt) if ((value) % 128) > trackerMinInt else trackerMinInt - ((value) % 128)) - (int(value / 128) - 1))[2:].rjust(2, "0")
            valueHex = hex(int(value / 128))[2:].rjust(2, "0") + hex(value % 128)[2:].rjust(2, "0")
        else:
            valueHex = hex(value)[2:].rjust(2, "0")
            trackerHex = hex(128 - (value - trackerMinInt) if value > trackerMinInt else trackerMinInt - value)[2:].rjust(2, "0")

        templateStr = cmdTemplate["template"]
        hexPayload = templateStr.format(idHex=idHex, valueHex=valueHex, trackerHex=trackerHex)
        #return = hexPayload
        #############

        pedalRequest = PedalRequest(name = cmdFullName, hexPayload=hexPayload) # CP: Don't like use of dictionary key here - remodel!

        self.deviceTxQueue.put(pedalRequest)
        self.logger.info(f"Sent command [{cmdFullName} = {value}] to device")

    def putRxQueue(self, obj: Union[PedalFSMAction, PedalResponse, Device.DeviceDisconnected]):
        priority = 0

        if isinstance(obj, PedalFSMAction):
            priority = -1

        elif isinstance(obj, PedalResponse):
            priority = -2

        elif isinstance(obj, Device.DeviceDisconnected):
            priority = -3

        self.rxQueue.put(PedalFSM.PrioritizedItem(priority, item=obj))
    # Public
    def subscribe(self, subscriber: PedalFSMSubscriber):
        self.subscribers.append(subscriber)

    def doAction(self, action: PedalFSMAction) -> bool:
        self.putRxQueue(action)

    def shutdown(self):
        self.deviceTxThread.shutdownFlag.set()
        self.rxThread.shutdownFlag.set()
        self.shutdownFlag.set()

        self.logger.info("Shutting Down - Waiting 5 seconds for threads to terminate")
        time.sleep(5)


class ContextFilter(logging.Filter):
    def __init__(self, pedalFSM: PedalFSM):
        super().__init__()
        self.pedalFSM = pedalFSM

    def filter(self, record):
        record.currentState = self.pedalFSM.currentState
        record.PID = os.getpid()
        return True



