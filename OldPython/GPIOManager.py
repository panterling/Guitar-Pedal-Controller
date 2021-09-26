gpioAvailable = False
try:
    import RPi.GPIO as GPIO
except Exception as e:
    print("WARN: BossUSBManager: Failed to load RPi: " + str(e))

from Config import GPIO_PINS

class GPIOManager:
    @staticmethod
    def outputLow(pin):
        if gpioAvailable:
            GPIO.output(pin, GPIO.LOW)

    @staticmethod
    def outputHigh(pin):
        if gpioAvailable:
            GPIO.output(pin, GPIO.HIGH)

    @staticmethod
    def setupWithDefaults():
        if gpioAvailable:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(GPIO_PINS.GLOBAL_STATUS_PIN, GPIO.OUT)
            GPIO.setup(GPIO_PINS.BLUETOOTH_STATUS_PIN, GPIO.OUT)
            GPIO.setup(GPIO_PINS.GT1_STATUS_PIN, GPIO.OUT)
            GPIO.setup(GPIO_PINS.TX_STATUS_PIN, GPIO.OUT)

            # Set State - GPIO_PINS.
            GPIO.output(GPIO_PINS.GLOBAL_STATUS_PIN, GPIO.HIGH)
            GPIO.output(GPIO_PINS.BLUETOOTH_STATUS_PIN, GPIO.LOW)
            GPIO.output(GPIO_PINS.GT1_STATUS_PIN, GPIO.LOW)
            GPIO.output(GPIO_PINS.TX_STATUS_PIN, GPIO.LOW)

    @staticmethod
    def turnOffPins():
        GPIO.output(GPIO_PINS.GLOBAL_STATUS_PIN, GPIO.LOW)
        GPIO.output(GPIO_PINS.BLUETOOTH_STATUS_PIN, GPIO.LOW)
        GPIO.output(GPIO_PINS.GT1_STATUS_PIN, GPIO.LOW)
        GPIO.output(GPIO_PINS.TX_STATUS_PIN, GPIO.LOW)
