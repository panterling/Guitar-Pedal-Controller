import time
import unittest

import queue

from Helpers.Logging import LoggerFactory
from OldPython.BossRxThread import BossTxCommands
from Pedal.CommandCatalogue import CommandCatalogue
from Pedal.ProtocolSniffing.Helpers import setupDevice, BossSnifferRxProcess, getStateHex, loadConfig


class Test__CommandDictionary(unittest.TestCase):

    def setUp(self):
        self.logger = LoggerFactory.getNamedLogger(self.__class__.__name__)

        # Load Config
        templateMapping, commandLookup, originalConfig, commandConfig = loadConfig()

        # Start RX Thread
        device, endpointReadRef, endpointWriteRef = setupDevice()
        rxQueue = queue.Queue()
        bossRxThread = BossSnifferRxProcess(device, endpointReadRef, rxQueue, templateMapping)

        # Start running the threads!
        bossRxThread.start()

        # Send Startup Messages to initialise the device
        endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_FIRST))
        time.sleep(0.5)
        endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_SECOND))
        time.sleep(0.5)
        endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_THIRD))
        time.sleep(0.5)
        endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_FOURTH))
        time.sleep(0.5)
        # endpointWriteRef.write(bytearray.fromhex(BossTxCommands.STARTUP_FIFTH))
        time.sleep(0.5)

        try:
            while True:
                rxQueue.get_nowait()
        except:
            pass
        getStateHex(rxQueue, endpointWriteRef)

        i = 0

    def tearDown(self):
        self.bossRxThread.shutdownFlag.set()


    def verifyCommand(self, commandConfig):

        def setValue(value):
            self.logger.info(f"Setting Value: {value}")

            trackerHex = commandConfig["trackerHex"]
            idHex = commandConfig["idHex"]
            cmdTemplate = CommandCatalogue.templateMapping[commandConfig["base_template"]]

            trackerMinInt = int(trackerHex, 16)

            valueHex = hex(value)[2:].rjust(2, "0")
            trackerHex = hex(128 - (value - trackerMinInt) if value > trackerMinInt else trackerMinInt - value)[
                         2:].rjust(2, "0")
            hexPayloadStr = cmdTemplate["template"].format(idHex=idHex, valueHex=valueHex, trackerHex=trackerHex)
            payload = bytearray.fromhex(hexPayloadStr)
            self.endpointWriteRef.write(payload)


        def getStateValue(commandConfig):
            self.logger.info(f"Getting State value")
            state = getStateHex(self.rxQueue, self.endpointWriteRef)

            # Check state is correct
            return int(str(state[commandConfig["stateConfig"]["pageId"]])[2:-1][commandConfig["stateConfig"]["idx"][0]:commandConfig["stateConfig"]["idx"][1] + 1], 16)

        # Extract Values
        highValueInt = commandConfig["maxValue"]
        lowValueInt = commandConfig["minValue"]

        # Set to Min Value using config
        setValue(lowValueInt)
        time.sleep(1)
        setStateValuue = getStateValue(commandConfig)
        self.assertEqual(lowValueInt, setStateValuue)

        # Set to Mid Value using config
        midValueInt = int((highValueInt - lowValueInt) / 2)
        setValue(midValueInt)
        time.sleep(1)
        setStateValuue = getStateValue(commandConfig)
        self.assertEqual(midValueInt, setStateValuue)


    def test__Commands(self):

        # Load CommandDictionary
        CommandCatalogue.loadConfig()

        for commandFullName, commandConfig in CommandCatalogue.commandLookup.items():
            self.verifyCommand(commandConfig)


        # Check GetState is correct

        assert(False)