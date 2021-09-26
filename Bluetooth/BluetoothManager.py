import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from queue import Empty
from typing import Optional, List

import json

from multiprocessing import Process, Queue

from Bluetooth.BluetoothAdapter import BluetoothAdapter, ClientDisconnected, UnknownError, BluetoothAdapterFactory
from Bluetooth.BluetoothDeframer import BluetoothDeframer
from Helpers.Logging import LoggerFactory
from Pedal.DataModels import BluetoothRxMessage
from Pedal.Device import PedalResponse
from Pedal.FSM import PedalFSMSubscriber, PedalFSMState, PedalFSM


class BluetoothManagerTasks:
    class RxThreadDead:
        pass

    class TxThreadDead:
        pass

class BluetoothManagerStates:
    AWAITING_CONNECTION = 1
    CONNECTED = 2
    AWAITING_TX_THREAD_DEATH = 3
    AWAITING_RX_THREAD_DEATH = 4



class BluetoothServer(Process):
    class RxThread(Process):
        def __init__(self, bluetoothAdapter: BluetoothAdapter, serverTaskQueue: Queue, rxQueue: Queue):
            super().__init__()

            self.logger = LoggerFactory.getNamedLogger("BluetoothRxThread")

            self.shutdownFlag = threading.Event()

            self.deframer = BluetoothDeframer()

            self.bluetoothAdapter = bluetoothAdapter
            self.serverTaskQueue = serverTaskQueue

            self.rxQueue = rxQueue



        def run(self):

            self.logger.info("Started")

            while not self.shutdownFlag.is_set():
                try:
                    data = self.bluetoothAdapter.getMessageBlocking()

                    if len(data) == 0:
                        continue
                    else:
                        # Pass to frame-extraction
                        payload = self.deframer.giveBytes(data)

                        if payload is not None:
                            self.rxQueue.put(payload)


                except ClientDisconnected as e:
                    self.logger.info("RX Thread Connection Reset By Peer")
                    break
                except UnknownError as e:
                    self.logger.error(f"UnknownError: {e}")
                    break
                except Exception as e:
                    self.logger.error(e)
                    break

            self.serverTaskQueue.put(BluetoothManagerTasks.RxThreadDead())
            self.logger.info("Terminated")

    class TxThread(Process):
        def __init__(self, bluetoothAdapter: BluetoothAdapter, serverTaskQueue: Queue, txQueue: Queue):
            super().__init__()

            self.logger = LoggerFactory.getNamedLogger("BluetoothTxThread")

            self.shutdownFlag = threading.Event()

            self.bluetoothAdapter = bluetoothAdapter
            self.serverTaskQueue = serverTaskQueue
            self.txQueue = txQueue

        def run(self):

            # Drain the queue when starting to prevent flood?
            # CP: TODO...

            self.logger.info("Started")

            while not self.shutdownFlag.is_set():
                try:
                    nextMsg = self.txQueue.get(block=True)
                    retrievedTimestamp = time.time()

                    if nextMsg == "DIE":
                        break

                    pedalResponse = nextMsg
                    self.logger.info(f"Got PedalResponse: {pedalResponse}")
                    self.logger.warning(f"\t TEMPORARY IMPLEMENTATION - SENT!")
                    temp = {
                        "name": pedalResponse.name,
                        "value": pedalResponse.value,
                    }
                    rawPayload = BluetoothDeframer.frame(json.dumps(temp))

                    self.bluetoothAdapter.sendMessage(rawPayload)
                    sentTimestamp = time.time()
                    self.logger.info(f"Sent: {nextMsg}")
                    self.logger.info(f"    Rx: {nextMsg.pedalRxTimestamp}")
                    self.logger.info(f"Notify: {nextMsg.notificationTimestamp} [{nextMsg.notificationTimestamp - nextMsg.pedalRxTimestamp}]")
                    self.logger.info(f" Rtrve: {retrievedTimestamp} [{retrievedTimestamp - nextMsg.pedalRxTimestamp}]")
                    self.logger.info(f"  Sent: {sentTimestamp} [{sentTimestamp - nextMsg.pedalRxTimestamp}]")

                except Exception as e:
                    self.logger.error(f"UnknownException: {e}")
                    break

            self.serverTaskQueue.put(BluetoothManagerTasks.TxThreadDead())

            self.logger.info("Terminated")


    def __init__(self, bluetoothTxQueue, bluetoothRxQueue):
        super().__init__()
        self.logger = LoggerFactory.getNamedLogger("BluetoothServer")

        self.shutdownFlag = threading.Event()

        self.logger.info("Started")

        if True: #MOCK_BLUEOOTH_MODE:
            self.bluetoothAdapter = BluetoothAdapterFactory.getAdapter(BluetoothAdapterFactory.REGULAR_BLUETOOTH_ADAPTER)
        else:
            self.bluetoothAdapter = BluetoothAdapterFactory.getAdapter(BluetoothAdapterFactory.MOCK_BLUETOOTH_ADAPTER)

        self.taskQueue = Queue()
        self.bluetoothTxQueue = bluetoothTxQueue
        self.bluetoothRxQueue = bluetoothRxQueue

        self.txThread: Optional[BluetoothServer.TxThread] = None
        self.rxThread: Optional[BluetoothServer.RxThread] = None

        self.alive = True



    def run(self):

        self.bluetoothAdapter.start()

        state = BluetoothManagerStates.AWAITING_CONNECTION

        while self.alive and not self.shutdownFlag.is_set():
            if state == BluetoothManagerStates.AWAITING_CONNECTION:

                self.logger.info("Waiting for Bluetooth connection")
                self.bluetoothAdapter.acceptConnectionBlocking()

                self.logger.info("Starting Tx Thread ")
                txThread = BluetoothServer.TxThread(self.bluetoothAdapter, serverTaskQueue=self.taskQueue, txQueue=self.bluetoothTxQueue)
                txThread.start()

                self.logger.info("Starting Rx Thread ")
                rxThread = BluetoothServer.RxThread(self.bluetoothAdapter, serverTaskQueue=self.taskQueue, rxQueue=self.bluetoothRxQueue)
                rxThread.start()

                state = BluetoothManagerStates.CONNECTED



            elif state == BluetoothManagerStates.CONNECTED:
                nextTask = self.taskQueue.get(block=True)

                self.logger.info("Got Next Task: {}".format(nextTask))

                if isinstance(nextTask, BluetoothManagerTasks.RxThreadDead):
                    # If Rx Dies, kill Tx and assume idle state
                    self.bluetoothAdapter.terminateClient()
                    self.bluetoothTxQueue.put("DIE")

                    state = BluetoothManagerStates.AWAITING_TX_THREAD_DEATH

                elif isinstance(nextTask, BluetoothManagerTasks.TxThreadDead):
                    # If Tx Dies, kill Rx and assume idle state
                    self.bluetoothAdapter.terminateClient()

                    state = BluetoothManagerStates.AWAITING_RX_THREAD_DEATH

                else:
                    # CP: Encode this exception
                    raise Exception("BluetoothManager:: Unknown Task: {}".format(nextTask))


            elif state == BluetoothManagerStates.AWAITING_TX_THREAD_DEATH:
                nextTask = self.taskQueue.get(block=True)
                self.logger.info("Got Next Task: {}".format(nextTask))

                if isinstance(nextTask, BluetoothManagerTasks.TxThreadDead):
                    state = BluetoothManagerStates.AWAITING_CONNECTION

                else:
                    raise Exception("BluetoothManager:: Unknown Task: {}".format(nextTask))

            elif state == BluetoothManagerStates.AWAITING_RX_THREAD_DEATH:
                nextTask = self.taskQueue.get(block=True)
                self.logger.info("Got Next Task: {}".format(nextTask))

                if isinstance(nextTask, BluetoothManagerTasks.RxThreadDead):
                    state = BluetoothManagerStates.AWAITING_CONNECTION

                else:
                    raise Exception("BluetoothManager:: Unknown Task: {}".format(nextTask))

            else:
                raise Exception("BluetoothManager:: Unknown State: {}".format(state))


        self.bluetoothAdapter.shutdown()

        if self.shutdownFlag.is_set():
            if self.rxThread is not None:
                self.rxThread.shutdownFlag.set()

            if self.txThread is not None:
                self.txThread.shutdownFlag.set()

        self.logger.info("Terminated")

    def shutdown(self):
        self.bluetoothAdapter.shutdown()
        self.shutdownFlag.set()





class BluetoothManager(Process, PedalFSMSubscriber):


    def notifyOfPedalResponse(self, pedalResponse: PedalResponse):
        self.bluetoothTxQueue.put(pedalResponse)

    def notifyOfStateChange(self, newState: PedalFSMState):
        pass

    def __init__(self, rxQuques: List[Queue] ):
        super().__init__(name="DoesThisWork")

        self.logger = LoggerFactory.getNamedLogger("BluetoothManager")

        self.bluetoothTxQueue = Queue()
        self.bluetoothRxQueue = Queue()

        self.serverThread: Optional[BluetoothServer] = None

        self.shutdownFlag = threading.Event()

        self.subscriberQueues: List[Queue] = rxQuques


    def run(self):
        self.logger.info("Started")

        self.serverThread = BluetoothServer(self.bluetoothTxQueue, self.bluetoothRxQueue)
        self.serverThread.start()

        while not self.shutdownFlag.is_set():
            try:
                payload = self.bluetoothRxQueue.get_nowait()
                msg = BluetoothRxMessage(payload=payload)
                for q in self.subscriberQueues:

                    q.put(PedalFSM.PrioritizedItem(priority=0, item=msg))
            except Empty:
                pass

        if self.serverThread is not None:
            self.serverThread.shutdown()
            self.logger.info("Shutting Down - Waiting 5 seconds for threads to terminate")
            time.sleep(5)


        self.logger.info("Terminated")


    def getTxQueue(self):
        return self.bluetoothTxQueue

    def shutdown(self):
        self.shutdownFlag.set()

    def attachRxQueue(self, rxQueue: Queue):
        self.subscriberQueues.append(rxQueue)
