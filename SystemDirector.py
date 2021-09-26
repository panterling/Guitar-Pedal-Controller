import signal
from multiprocessing.managers import SyncManager
from queue import PriorityQueue

from Bluetooth.BluetoothManager import BluetoothManager
from GPIO.GPIOManager import GPIOManager
from Helpers.Logging import LoggerFactory
from Pedal.DataModels import PedalFSMActionConnect
from Pedal.FSM import PedalFSM


## Graceful Management of Signals
class SignalExit(Exception):
    pass








class SystemDirector:
    # These are on seperate processes - Shared Memory needs careful handling
    class CrossProcessMemoryManager(SyncManager):
        pass

    CrossProcessMemoryManager.register("PriorityQueue", PriorityQueue)  # Register a shared PriorityQueue


    def __init__(self):
        self.logger = LoggerFactory.getNamedLogger(self.__class__.__name__)

        ## Register signal handlers
        signal.signal(signal.SIGTERM, self._shutdownCallback)
        signal.signal(signal.SIGINT, self._shutdownCallback)

        ## Cross Process Memory Management
        self.crossProccessMemoryManager = SystemDirector.CrossProcessMemoryManager()

        self.crossProccessMemoryManager.start()
        rxQueue = self.crossProccessMemoryManager.PriorityQueue()
        rxQueues = [rxQueue]

        ## Setup Components
        self.pedalFsm = PedalFSM(rxQueue=rxQueue)

        self.bluetoothManager = BluetoothManager(rxQueues)

        self.gpioManager = GPIOManager()

        # Subscribe to PedalResponses
        self.pedalFsm.subscribe(self.bluetoothManager)
        self.pedalFsm.subscribe(self.gpioManager)

        # Subscribe to Incoming over Bluetooth
        # bluetoothManager.attachRxQueue()

    def start(self):
        try:

            self.gpioManager.start()
            self.logger.info("GPIO Manager Started")

            self.pedalFsm.start()
            self.logger.info("Pedal FSM Started")

            self.bluetoothManager.start()
            self.logger.info("Bluetooth Manager Started")

            # Safe from the MAIN thread
            self.pedalFsm.doAction(PedalFSMActionConnect())
            # pedalFsm.doAction(PedalFSMActionSendCommand().attachCommand("REVERB.ELEVEL", {"value": 17}))
            # pedalFsm.doAction(PedalFSMActionDisconnect())

            # pedalFsm.join()
            self.bluetoothManager.serverThread.join()
        except SignalExit as e:
            self.logger.info("SHUTTING DOWN - SIGNAL RECEIVED")

            self.bluetoothManager.shutdown()
            self.pedalFsm.shutdown()
            self.gpioManager.shutdown()
        except Exception as e:
            self.logger.error(f"Unexpected Exception: {e}")

    def _shutdownCallback(self, signum, frame):
        print(f"SYS:: Caught signal {signum}")
        raise SignalExit()
