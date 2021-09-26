import queue
import time
from threading import Thread

from bluetooth import *
import RPi.GPIO as GPIO

from BossUSBManager import BossUSBManager
from Config import GPIO_PINS
from GPIOManager import GPIOManager
from Helpers import DeFramer


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

class BluetoothManager:


    def __init__(self, bossManager):
        self.deframer = DeFramer(bossManager)

        self.bluetoothTxQueue = queue.Queue()

        print("BluetoothManager:: Starting....")
        # Manager Thread
        self.connectionManagerThread = Thread(target=BluetoothManager.connectionManagerThreadFunc, args=[self.deframer, self.bluetoothTxQueue])
        self.connectionManagerThread.setName("connectionManager Thread")
        self.connectionManagerThread.start()

    def getTxQueue(self):
        return self.bluetoothTxQueue

    @staticmethod
    def connectionManagerThreadFunc(deframer, bluetoothTxQueue):

        print("BluetoothManager:: connectionManagerThread Started")

        taskQueue = queue.Queue()

        server_sock = BluetoothSocket(RFCOMM)
        server_sock.bind(("", PORT_ANY))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]
        server_uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

        advertise_service(server_sock, "BossControllerServer",
                          service_id=server_uuid,
                          service_classes=[server_uuid, SERIAL_PORT_CLASS],
                          profiles=[SERIAL_PORT_PROFILE])

        client_sock = None
        txThread = None
        rxThread = None

        alive = True

        state = BluetoothManagerStates.AWAITING_CONNECTION

        while alive:
            if state == BluetoothManagerStates.AWAITING_CONNECTION:

                print("BluetoothManager:: Waiting for connection on RFCOMM channel " + str(port) + " - server_uuid [" + str(server_uuid) + "]")
                client_sock, client_info = server_sock.accept() # Blocking

                try:
                    print(client_sock.connected)
                except:
                    print("Nope")


                try:
                    print(client_sock.connected())
                except:
                    print("Nope")


                try:
                    print(client_sock._sock)
                except:
                    print("Nope")

                try:
                    print(client_sock._sock.__dict__)
                except:
                    print("Nope")



                print("BluetoothManager:: Accepted connection from ", client_info)

                client_sock.setblocking(False)

                print("BluetoothManager:: Starting Tx Thread ")
                txThread = Thread(target=BluetoothManager.txThreadFunc, args=[client_sock, taskQueue, bluetoothTxQueue])
                txThread.setName('bluetooth Tx Thread')
                txThread.start()

                print("BluetoothManager:: Starting Rx Thread ")
                rxThread = Thread(target=BluetoothManager.rxThreadFunc, args=[client_sock, taskQueue, deframer])
                rxThread.setName('bluetooth Rx Thread')
                rxThread.start()


                state = BluetoothManagerStates.CONNECTED
                print("BluetoothManager::   Started Tx/Rx Threads", client_info)



            elif state == BluetoothManagerStates.CONNECTED:
                nextTask = taskQueue.get(block = True)

                print("BluetoothManager:: Got Next Task: {}".format(nextTask))

                if isinstance(nextTask, BluetoothManagerTasks.RxThreadDead):
                    ## If Rx Dies, kill Tx and assume idle state
                    client_sock.close()
                    bluetoothTxQueue.put("DIE")

                    state = BluetoothManagerStates.AWAITING_TX_THREAD_DEATH

                elif isinstance(nextTask, BluetoothManagerTasks.TxThreadDead):
                    ## If Tx Dies, kill Rx and assume idle state
                    client_sock.close()

                    state = BluetoothManagerStates.AWAITING_RX_THREAD_DEATH

                else:
                    raise Exception("BluetoothManager:: Unknown Task: {}".format(nextTask))


            elif state == BluetoothManagerStates.AWAITING_TX_THREAD_DEATH:
                nextTask = taskQueue.get(block=True)
                print("BluetoothManager:: Got Next Task: {}".format(nextTask))

                if isinstance(nextTask, BluetoothManagerTasks.TxThreadDead):
                    state = BluetoothManagerStates.AWAITING_CONNECTION

                else:
                    raise Exception("BluetoothManager:: Unknown Task: {}".format(nextTask))

            elif state == BluetoothManagerStates.AWAITING_RX_THREAD_DEATH:
                nextTask = taskQueue.get(block=True)
                print("BluetoothManager:: Got Next Task: {}".format(nextTask))

                if isinstance(nextTask, BluetoothManagerTasks.RxThreadDead):
                    state = BluetoothManagerStates.AWAITING_CONNECTION

                else:
                    raise Exception("BluetoothManager:: Unknown Task: {}".format(nextTask))

            else:
                raise Exception("BluetoothManager:: Unknown State: {}".format(state))


        print("BluetoothManager:: connectionManagerThread DEAD")
        server_sock.close()



    @staticmethod
    def rxThreadFunc(client_sock, taskQueue, deframer):

        while True:
            try:

                data = client_sock.recv(1024)  # Blocking it would seem

                if len(data) == 0:
                    continue
                else:
                    # Pass to frame-extraction
                    deframer.giveBytes(data)
                    client_sock.send(data)

            except BluetoothError as e:
                try:
                    errNo = int(e.args[0][1:-1].split(",")[0])
                except:
                    errNo = e.args[0]

                if errNo == 11:
                    pass
                elif errNo == 104:
                    print("BluetoothManager:: RX Thread Connection Reset By Peer")
                    break
                else:
                    print(e)
                    break

        taskQueue.put(BluetoothManagerTasks.RxThreadDead())
        print("BluetoothManager:: RX Thread DEAD")



    @staticmethod
    def txThreadFunc(client_sock, taskQueue, bluetoothTxQueue):

        # Drain the queue when starting to prevent flood?
        # CP: TODO...

        print("BluetoothManager:: TX Thread STARTING")
        GPIOManager.outputHigh(GPIO_PINS.BLUETOOTH_STATUS_PIN)

        while True:
            try:
                nextMsg = bluetoothTxQueue.get(block=True)
                if nextMsg == "DIE":
                    break
                print("BluetoothManager:: TX Thread Sending:: {}".format(nextMsg))

                client_sock.send(nextMsg)

                GPIOManager.outputHigh(GPIO_PINS.TX_STATUS_PIN)
                time.sleep(0.006)  # 6 ms
                GPIOManager.outputLow(GPIO_PINS.TX_STATUS_PIN)

            except Exception as e:
                print("BluetoothManager:: TX Thread EXCEPTION")
                print(e)
                break

        taskQueue.put(BluetoothManagerTasks.TxThreadDead())

        GPIOManager.outputLow(GPIO_PINS.BLUETOOTH_STATUS_PIN)
        print("BluetoothManager:: TX Thread DEAD")

