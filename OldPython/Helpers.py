import json

from BossUSBManager import BossUSBManager


class DeFramer:
    SOF_TOKEN = 127
    EOF_TOKEN = 126

    IDLE = 1
    IN_FRAME = 2
    IN_FRAME_EOF_CANDIDATE = 3

    packetFeedState = IDLE

    currentFrameData = bytearray()
    lastFourBytes = [0, 0, 0, 0]

    eofTokensSeen = 0

    def __init__(self, bossManager):
        self.bossManager = bossManager

    def giveBytes(self, data):

        for nextChar in data:
            b = nextChar #bytearray(nextChar.encode("utf-8"))[0].to_bytes(1, byteorder='big')
            byteToFeed = self.lastFourBytes[0]
            self.lastFourBytes = self.lastFourBytes[1:] + [b]

            if self.packetFeedState == DeFramer.IDLE:
                if all(self.lastFourBytes) and self.lastFourBytes[0] == DeFramer.SOF_TOKEN:
                    self.packetFeedState = DeFramer.IN_FRAME

            elif self.packetFeedState == DeFramer.IN_FRAME:
                if b == DeFramer.EOF_TOKEN:
                    self.packetFeedState = DeFramer.IN_FRAME_EOF_CANDIDATE
                    self.eofTokensSeen = 1
                else:
                    self.currentFrameData += b.to_bytes(1, "big")
            elif self.packetFeedState == DeFramer.IN_FRAME_EOF_CANDIDATE:
                if b != DeFramer.EOF_TOKEN:
                    self.packetFeedState = DeFramer.IN_FRAME
                    self.currentFrameData += self.lastFourBytes[0:self.eofTokensSeen + 1]
                else:
                    self.eofTokensSeen += 1
                    if self.eofTokensSeen == 4:
                        self.packetFeedState = DeFramer.IDLE

                        payloadString = str(self.currentFrameData.decode('utf-8'))
                        print("Got PACKET:: " + payloadString)
                        self.processCommand(payloadString)

                        self.currentFrameData = bytearray()
                        self.eofTokensSeen = 0


    # DOES NOT BELONG HERE
    def processJSONCommand(self, jsonCommand):

        target = jsonCommand["target"]
        command = jsonCommand["type"]

        values = {}
        for v in jsonCommand["values"]:
            values[v["name"]] = v["value"]

        if command == "TUNER_ON":
            try:
                self.bossManager.tunerOn()
            except Exception as e:
                print(e)
            print(" >> Turning Tuner on")

        elif command == "TUNER_OFF":
            try:
                self.bossManager.tunerOff()
            except Exception as e:
                print(e)
            print(" >> Turning Tuner Off")

        elif command == "SELECT_USER_PATCH":
            try:
                id = values["PATCH_ID"].split("-")[0][0]
                type = values["PATCH_TYPE"]
                if type == "U":
                    self.bossManager.selectUserPatchById(int(id))
                else:
                    self.bossManager.selectPermenantPatchById(int(id))

            except Exception as e:
                print(e)
            print(" >> Selecting {} Patch: {}".format(type, id))


        elif command == "SET_OUTPUT_LEVEL":
            try:
                level = values["OUTPUT_LEVEL"]
                self.bossManager.runCommand(BossUSBManager.SET_OUTPUT_LEVEL, level)
            except Exception as e:
                print(e)
            print(" >> Setting output level to {} ".format(level))

        elif command == "SET_PATCH_LEVEL":
            try:
                level = values["PATCH_LEVEL"]
                self.bossManager.runCommand(BossUSBManager.SET_PATCH_LEVEL, level)
            except Exception as e:
                print(e)
            print(" >> Setting patch level to {} ".format(level))

        elif command == "REQUEST_PATCH_LISTS":
            self.bossManager.getPatchNames()
            print(" >> Updating Patch Lists")

        elif command == "REQUEST_STATE":
            self.bossManager.requestState()
            print(" >> Updating State")


        elif command == "FX1_ON":
            self.bossManager.runCommand(BossUSBManager.FX1_ON)
            print(" >> Set FX1 ON")

        elif command == "FX1_OFF":
            self.bossManager.runCommand(BossUSBManager.FX1_OFF)
            print(" >> Set FX1 OFF")




        elif command == "ODDS_ON":
            self.bossManager.runCommand(BossUSBManager.ODDS_ON)
            print(" >> Set ODDS ON")

        elif command == "ODDS_OFF":
            self.bossManager.runCommand(BossUSBManager.ODDS_OFF)
            print(" >> Set ODDS OFF")




        elif command == "PREAMP_ON":
            self.bossManager.runCommand(BossUSBManager.PREAMP_ON)
            print(" >> Set PREAMP ON")

        elif command == "PREAMP_OFF":
            self.bossManager.runCommand(BossUSBManager.PREAMP_OFF)
            print(" >> Set PREAMP OFF")

        elif command == "SET_PREAMP_LEVEL":
            try:
                level = values["PREAMP_LEVEL"]
                self.bossManager.runCommand(BossUSBManager.SET_PREAMP_LEVEL, level)
            except Exception as e:
                print(e)
            print(" >> Setting preamp level to {} ".format(level))




        elif command == "FX2_ON":
            self.bossManager.runCommand(BossUSBManager.FX2_ON)
            print(" >> Set FX2 ON")

        elif command == "FX2_OFF":
            self.bossManager.runCommand(BossUSBManager.FX2_OFF)
            print(" >> Set FX2 OFF")



        elif command == "DELAY_ON":
            self.bossManager.runCommand(BossUSBManager.DELAY_ON)
            print(" >> Set DELAY ON")

        elif command == "DELAY_OFF":
            self.bossManager.runCommand(BossUSBManager.DELAY_OFF)
            print(" >> Set DELAY OFF")



        elif command == "REVERB_ON":
            self.bossManager.runCommand(BossUSBManager.REVERB_ON)
            print(" >> Set REVERB ON")

        elif command == "REVERB_OFF":
            self.bossManager.runCommand(BossUSBManager.REVERB_OFF)
            print(" >> Set REVERB OFF")

        else:
            print(" >> No matching commend")


    def processCommand(self, command):

        try:
            jsonCommand = json.loads(command)
            self.processJSONCommand(jsonCommand)
        except Exception as e:
            print("Unable to parse command: {}".format(str(command)))
            print(e)

