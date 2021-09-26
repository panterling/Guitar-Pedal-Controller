from abc import ABC, abstractmethod
from typing import Optional

import bluetooth

from Helpers.Logging import LoggerFactory


class ClientDisconnected(Exception):
    def __init__(self):
        super().__init__(self.__class__.__name__)

class UnknownError(Exception):
    def __init__(self):
        super().__init__(self.__class__.__name__)



class AbstractBluetoothAdapter(ABC):


    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def acceptConnectionBlocking(self):
        pass

    @abstractmethod
    def getMessageBlocking(self):
        pass

    @abstractmethod
    def sendMessage(self, msg: str):
        pass

    @abstractmethod
    def terminateClient(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass


class BluetoothAdapter(AbstractBluetoothAdapter):
    SERVER_UUID = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

    def __init__(self):
        self.logger = LoggerFactory.getNamedLogger("BluetoothAdapter")

        self.serverSocket: Optional[bluetooth.bluez.BluetoothSocket] = None
        self.serverPort: Optional[int] = None

        self.clientInfo: Optional[tuple] = None
        self.clientSocket: Optional[bluetooth.bluez.BluetoothSocket] = None

    def acceptConnectionBlocking(self):
        self.clientSocket, self.clientInfo = self.serverSocket.accept()  # Blocking

        # try:
        #     print(self.clientSocket.connected)
        # except:
        #     print("Nope")
        #
        # try:
        #     print(self.clientSocket.connected())
        # except:
        #     print("Nope")
        #
        # try:
        #     print(self.clientSocket._sock)
        # except:
        #     print("Nope")
        #
        # try:
        #     print(self.clientSocket._sock.__dict__)
        # except:
        #     print("Nope")

        self.logger.info("BluetoothManager:: Accepted connection from <{self.clientInfo}>")

        self.clientSocket.setblocking(False)

    def start(self):
        self.serverSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.serverSocket.bind(("", bluetooth.PORT_ANY))
        self.serverSocket.listen(1)

        self.serverPort = self.serverSocket.getsockname()[1]

        bluetooth.advertise_service(self.serverSocket, "BossControllerServer",
                                    service_id=BluetoothAdapter.SERVER_UUID,
                                    service_classes=[BluetoothAdapter.SERVER_UUID, bluetooth.SERIAL_PORT_CLASS],
                                    profiles=[bluetooth.SERIAL_PORT_PROFILE])

    def getMessageBlocking(self) -> bytes:
        msg: bytes = None
        while msg is None:
            try:

                msg = self.clientSocket.recv(1024)

                if len(msg) == 0:
                    continue

            except bluetooth.BluetoothError as e:
                try:
                    errNo = int(e.args[0][1:-1].split(",")[0])
                except:
                    errNo = e.args[0]

                if errNo == 11:
                    pass
                elif errNo == 104:
                    raise ClientDisconnected()
                else:
                    print(e)
                    raise UnknownError()

        return msg

    def sendMessage(self, msg: str):
        self.clientSocket.send(msg)

    def terminateClient(self):
        if self.clientSocket is not None:
            self.clientSocket.close()

    def shutdown(self):
        self.terminateClient()

        if self.serverSocket is not None:
            self.serverSocket.close()


class BluetoothAdapterFactory:
    class UnknownAdapter(Exception):
        def __init__(self):
            super().__init__(self.__class__.__name__)

    REGULAR_BLUETOOTH_ADAPTER = 0
    MOCK_BLUETOOTH_ADAPTER = 1
    _ADAPTERS = {
        REGULAR_BLUETOOTH_ADAPTER: BluetoothAdapter(),
        MOCK_BLUETOOTH_ADAPTER: MOCK_BLUETOOTH_ADAPTER
    }
    def getAdapter(adapterId: int):
        if adapterId not in BluetoothAdapterFactory._ADAPTERS:
            raise BluetoothAdapterFactory.UnknownAdapter()

        else:
            return BluetoothAdapterFactory._ADAPTERS[adapterId]

# ba = BluetoothAdapter()
#
# ba.start()
#
# ba.acceptConnectionBlocking()
#
# msg = ba.getMessageBlocking()
#
# print(msg)
# ba.sendMessage("Test")
# i = 0