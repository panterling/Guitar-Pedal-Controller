import queue

from BossUSBManager import BossUSBManager

q =  queue.Queue()

bossManager = BossUSBManager(bossNotificationQueues = [q])

bossManager.start()

def cmp(a, b):
    if len(a) != len(b):
        print("len(a) != len(b)")
        return

    for i in range(len(a)):
        if a[i] != b[i]:
            print("diff @ {}  [{}] -> [{}]".format(i, a[i], b[i]))

lastSeenNext = ["", "", "", "", ""]
firstPass = True
def go():
    global firstPass, lastSeenNext
    bossManager.requestState()

    next = [0, 0, 0, 0, 0, 0]
    attemptsLeft = 5
    while attemptsLeft > 0:
        attemptsLeft -= 1
        payload = bossManager.rxQueue.get()
        tmpAsString = str(payload)[2:-1]

        if   tmpAsString[0:34] == "04f0410004000000043012600400000004":
            next[0] = tmpAsString
            if not firstPass:
                cmp(lastSeenNext[0], tmpAsString)

        elif tmpAsString[0:34] == "04f0410004000000043012600400017104":
            next[1] = tmpAsString
            if not firstPass:
                cmp(lastSeenNext[1], tmpAsString)

        elif tmpAsString[0:34] == "04f0410004000000043012600400036204":
            next[2] = tmpAsString
            if not firstPass:
                cmp(lastSeenNext[2], tmpAsString)

        elif tmpAsString[0:34] == "04f0410004000000043012600400055304":
            next[3] = tmpAsString
            if not firstPass:
                cmp(lastSeenNext[3], tmpAsString)

        elif tmpAsString[0:34] == "04f0410004000000043012600400074404":
            next[4] = tmpAsString
            if not firstPass:
                cmp(lastSeenNext[4], tmpAsString)

        else:
            print("Ignore: {}".format(tmpAsString[0:34]))
            attemptsLeft += 1

    #if not firstPass:
    #    for i in range(5):
    #        print("Msg: {}".format(i))
    #        cmp(lastSeenNext[i], next[i])

    lastSeenNext[0] = next[0]
    lastSeenNext[1] = next[1]
    lastSeenNext[2] = next[2]
    lastSeenNext[3] = next[3]
    lastSeenNext[4] = next[4]

    firstPass = False



# Fake to-bluetooth Rx -> Tx
#while True:
#    if not q.empty():
#        print(q.get(block=False))


while True:
    f = input("""Select Option: """)

    value = None
    if int(f) in [BossUSBManager.SELECT_PRESET_PATCH,
                  BossUSBManager.SELECT_USER_PATCH,
                  BossUSBManager.SET_OUTPUT_LEVEL,
                  BossUSBManager.GET_USER_PATCH_NAME,
                  BossUSBManager.SET_PATCH_LEVEL]:
        value = input()

    bossManager.runCommand(f, value)
    print(f)