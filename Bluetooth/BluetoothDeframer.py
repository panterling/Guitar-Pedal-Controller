import json
from typing import Optional

from Helpers.Logging import LoggerFactory


class BluetoothDeframer:
    SOF_TOKEN = 127
    EOF_TOKEN = 126

    IDLE = 1
    IN_FRAME = 2
    IN_FRAME_EOF_CANDIDATE = 3

    packetFeedState = IDLE

    currentFrameData = bytearray()
    lastFourBytes = [0, 0, 0, 0]

    eofTokensSeen = 0

    def __init__(self):
        self.logger = LoggerFactory.getNamedLogger("BluetoothDeframer")

    @staticmethod
    def frame(payload: str):
        return chr(BluetoothDeframer.SOF_TOKEN) * 4 + payload + chr(BluetoothDeframer.EOF_TOKEN) * 4

    def giveBytes(self, data):
        ret = None

        for nextChar in data:
            b = nextChar #bytearray(nextChar.encode("utf-8"))[0].to_bytes(1, byteorder='big')
            byteToFeed = self.lastFourBytes[0]
            self.lastFourBytes = self.lastFourBytes[1:] + [b]

            if self.packetFeedState == BluetoothDeframer.IDLE:
                if all(self.lastFourBytes) and self.lastFourBytes[0] == BluetoothDeframer.SOF_TOKEN:
                    self.packetFeedState = BluetoothDeframer.IN_FRAME

            elif self.packetFeedState == BluetoothDeframer.IN_FRAME:
                if b == BluetoothDeframer.EOF_TOKEN:
                    self.packetFeedState = BluetoothDeframer.IN_FRAME_EOF_CANDIDATE
                    self.eofTokensSeen = 1
                else:
                    self.currentFrameData += b.to_bytes(1, "big")
            elif self.packetFeedState == BluetoothDeframer.IN_FRAME_EOF_CANDIDATE:
                if b != BluetoothDeframer.EOF_TOKEN:
                    self.packetFeedState = BluetoothDeframer.IN_FRAME
                    self.currentFrameData += self.lastFourBytes[0:self.eofTokensSeen + 1]
                else:
                    self.eofTokensSeen += 1
                    if self.eofTokensSeen == 4:
                        self.packetFeedState = BluetoothDeframer.IDLE

                        payloadString = str(self.currentFrameData.decode('utf-8'))
                        self.logger.debug("Got PACKET:: " + payloadString)

                        # Validate
                        ret = self.validatePayload(payloadString)

                        self.currentFrameData = bytearray()
                        self.eofTokensSeen = 0

        return ret

    def validatePayload(self, command) -> Optional[dict]:
        ret = None

        try:
            ret = json.loads(command)
        except Exception as e:
            self.logger.error(f"validatePayload:: unknown Exception: {e}")

        return ret

