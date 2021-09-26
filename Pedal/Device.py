import binascii
import queue
import threading
import time
from threading import Thread
from typing import Union, Callable

import usb

from Helpers.Logging import LoggerFactory
from Pedal.CommandCatalogue import CommandCatalogue
from Pedal.DataModels import PedalFSMAction, UnmappedPedalResponse, PedalResponse, PedalRequest


class Device:
    class DeviceNotFound(Exception):
        def __init__(self):
            super().__init__(self.__class__.__name__)

    class DeviceInUse(Exception):
        def __init__(self):
            super().__init__(self.__class__.__name__)

    class DeviceDisconnected(Exception):
        def __init__(self):
            super().__init__(self.__class__.__name__)

    class UnknownUSBError(Exception):
        def __init__(self):
            super().__init__(self.__class__.__name__)

    def __init__(self):
        self.device = usb.core.find(idVendor=0x0582, idProduct=0x01d6)

        if self.device is None:
            raise Device.DeviceNotFound()

        for i in range(4):
            if self.device.is_kernel_driver_active(i):
                self.device.detach_kernel_driver(i)

        # Has Endpoints
        interfaceIdx = 3

        # claim the device
        try:
            usb.util.claim_interface(self.device, interfaceIdx)
            self.endpointWriteRef = self.device[0][(interfaceIdx, 0)][0]
            self.endpointReadRef = self.device[0][(interfaceIdx, 0)][1]
        except usb.USBError as e:
            if e.errno == 16:
                raise Device.DeviceInUse()
            else:
                raise Device.UnknownUSBError(e)

        except Exception as e:
            raise e

    def send(self):
        pass


class PedalResponseMapper:
    def __init__(self):
        pass

    def extractPedalResponse(self, rx: str):
        ret = None

        # CP: TODO: Invalid use of private method here
        cmd = CommandCatalogue._findCmdInConfig(rx)

        if cmd is not None:
            # CP: don't couple here
            valueHexIdxs = CommandCatalogue.templateMapping[cmd["base_template"]]["valueHexIdxs"]
            valueHex = rx[valueHexIdxs[0]: valueHexIdxs[1] + 1]
            value = int(valueHex, 16)

            ret = PedalResponse(name=cmd["name"], value=value)

        if ret is None:
            ret = UnmappedPedalResponse(rx)

        return ret



class DeviceTxThread(Thread):
    def __init__(self, txQueue: queue.Queue, txCallback: Callable[[Union[PedalFSMAction, PedalResponse, Device.DeviceDisconnected]], None], device: Device):
        super().__init__()

        self.shutdownFlag = threading.Event()

        self.logger = LoggerFactory.getNamedLogger("DeviceTxThread")

        self.device: Device = device

        self.txCallback = txCallback
        self.txQueue = txQueue

    def run(self):
        # Not on main thread
        self.logger.info("Started")

        while not self.shutdownFlag.is_set():
            try:
                pedalRequest: PedalRequest = self.txQueue.get(timeout=2)

                hexPayload = pedalRequest.toHex()

                self.device.endpointWriteRef.write(bytearray.fromhex(hexPayload))

                time.sleep(0.1)

                self.logger.info(f"Tx [{type(pedalRequest)}]: {hexPayload}")

            except queue.Empty as e:
                pass
            except usb.USBError as e:
                if e.errno == 19:
                    self.logger.warning("Device Disconnected")
                    self.shutdownFlag.set()
                    self.txCallback(Device.DeviceDisconnected())
                else:
                    self.logger.error(f"Unexpected USBError ({e.errno}): {e}")
            except Exception as e:
                self.logger.error(f"Unable to Tx [{hexPayload}] - Exception: {e}")

        self.logger.error("Terminated")



class DeviceRxThread(Thread):
    def __init__(self, txCallback: Callable[[Union[PedalFSMAction, PedalResponse, Device.DeviceDisconnected]], None], device: Device):
        super().__init__()

        self.shutdownFlag = threading.Event()

        self.logger = LoggerFactory.getNamedLogger("DeviceRxThread")

        self.device: Device = device

        self.responseMapper = PedalResponseMapper()

        self.txCallback = txCallback

    def run(self):
        self.logger.info('Started')

        while not self.shutdownFlag.is_set():
            try:
                data = self.device.device.read(self.device.endpointReadRef.bEndpointAddress, self.device.endpointReadRef.wMaxPacketSize)

                rxTimestamp = time.time()

                if sum(data) > 0:
                    payload = binascii.hexlify(bytearray(data))

                    # Map to command dictionary (or otherwise)
                    rx = str(payload)[2:-1]
                    mappedPayload = self.responseMapper.extractPedalResponse(rx)

                    # DEBUG: Add timing for latency monitoring
                    mappedPayload.pedalRxTimestamp = rxTimestamp

                    # Pass to manager
                    self.txCallback(mappedPayload)

            except usb.core.USBError as e:
                data = None
                if e.args == ('Operation timed out',):
                    self.logger.error("Read timeout....")
                    self.logger.error(e)
                    continue
            except Exception as e:
                self.logger.error("Other exception")
                self.logger.error(e)
                break

        self.logger.info('Terminated')