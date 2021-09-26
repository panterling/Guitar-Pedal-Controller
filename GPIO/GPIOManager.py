import queue
import threading

from Helpers.Logging import LoggerFactory
from Pedal.DataModels import PedalFSMStateDisconnected, PedalFSMStateConnected
from Pedal.Device import PedalResponse
from Pedal.FSM import PedalFSMSubscriber, PedalFSMState

from Config import GPIO_PINS

class GPIOManager(threading.Thread, PedalFSMSubscriber):
    def __init__(self):
        super().__init__()

        self.logger = LoggerFactory.getNamedLogger("GPIOManager")

        self.gpioAvailable = False

        self.shutdownFlag = threading.Event()

        self.taskQueue = queue.Queue()

        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.gpioAvailable = True
        except Exception as e:
            print("WARN: BossUSBManager: Failed to load RPi: " + str(e))

    def run(self):
        self.logger.info("Started")

        if not self.gpioAvailable:
            self.logger.warning("GPIO Not available!")
        else:
            self.setupWithDefaults()
            while not self.shutdownFlag.is_set():
                try:
                    msg = self.taskQueue.get(timeout=5)

                    if isinstance(msg, PedalFSMState):
                        pedalState = msg
                        if msg == PedalFSMStateConnected(): # CP: use instanceof
                            self.outputHigh(GPIO_PINS.GT1_STATUS_PIN)
                            self.logger.debug("GT1_STATUS_PIN = ON")

                        elif msg == PedalFSMStateDisconnected(): # CP: use instanceof
                            self.outputLow(GPIO_PINS.GT1_STATUS_PIN)
                            self.logger.debug("GT1_STATUS_PIN = OFF")

                    elif isinstance(msg, PedalResponse):
                        pass
                    else:
                        self.logger.debug(f"No action for: {msg}")

                except queue.Empty as e:
                    pass
                except Exception as e:
                    self.logger.error(f"Unknown Exception: {e}")

        self.logger.info("Terminated")


    def notifyOfPedalResponse(self, pedalResponse: PedalResponse):
        self.taskQueue.put(pedalResponse)

    def notifyOfStateChange(self, newState: PedalFSMState):
        self.taskQueue.put(newState)

    def outputLow(self, pin):
        if self.gpioAvailable:
            self.GPIO.output(pin, self.GPIO.LOW)

    def outputHigh(self, pin):
        if self.gpioAvailable:
            self.GPIO.output(pin, self.GPIO.HIGH)

    def setupWithDefaults(self):
        if self.gpioAvailable:
            self.GPIO.setmode(self.GPIO.BCM)
            self.GPIO.setup(GPIO_PINS.GLOBAL_STATUS_PIN, self.GPIO.OUT)
            self.GPIO.setup(GPIO_PINS.BLUETOOTH_STATUS_PIN, self.GPIO.OUT)
            self.GPIO.setup(GPIO_PINS.GT1_STATUS_PIN, self.GPIO.OUT)
            self.GPIO.setup(GPIO_PINS.TX_STATUS_PIN, self.GPIO.OUT)

            # Set State - GPIO_PINS.
            self.GPIO.output(GPIO_PINS.GLOBAL_STATUS_PIN, self.GPIO.HIGH)
            self.GPIO.output(GPIO_PINS.BLUETOOTH_STATUS_PIN, self.GPIO.LOW)
            self.GPIO.output(GPIO_PINS.GT1_STATUS_PIN, self.GPIO.LOW)
            self.GPIO.output(GPIO_PINS.TX_STATUS_PIN, self.GPIO.LOW)

    def turnOffPins(self):
        if self.gpioAvailable:
            self.GPIO.output(GPIO_PINS.GLOBAL_STATUS_PIN, self.GPIO.LOW)
            self.GPIO.output(GPIO_PINS.BLUETOOTH_STATUS_PIN, self.GPIO.LOW)
            self.GPIO.output(GPIO_PINS.GT1_STATUS_PIN, self.GPIO.LOW)
            self.GPIO.output(GPIO_PINS.TX_STATUS_PIN, self.GPIO.LOW)

    def shutdown(self):
        self.shutdownFlag.set()
