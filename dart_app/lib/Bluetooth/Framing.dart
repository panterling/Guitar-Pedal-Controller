import 'dart:convert';
import 'dart:ffi';
import 'dart:typed_data';


class Framer {
  static const int SOF_TOKEN = 127;
  static const int EOF_TOKEN = 126;

  static Uint8List frame(String payload){
    // CP: TODO: Neater/more concise way to create this?
    var frameStart = String.fromCharCode(127)+String.fromCharCode(127)+String.fromCharCode(127)+String.fromCharCode(127);
    var frameEnd = String.fromCharCode(126)+String.fromCharCode(126)+String.fromCharCode(126)+String.fromCharCode(126);

    return utf8.encode(frameStart + payload + frameEnd);
  }
}

enum FrameState {
  IDLE,
  IN_FRAME,
  IN_FRAME_EOF_CANDIDATE,

}
class Deframer {

  static const int SOF_TOKEN = 127;
  static const int EOF_TOKEN = 126;

  List<int> currentFrameData = List<int>();

  List<int> lastFourBytes = [0, 0, 0, 0];
  int eofTokensSeen = 0;

  FrameState frameState = FrameState.IDLE;

  Deframer(){

  }

  bool _lastFourBytesSet() {
    var ret = !lastFourBytes.any((b) { return b == 0; });
    return ret;
  }

  String givePayload(Uint8List dataRaw) {
    String ret;

    for (int i = 0; i < dataRaw.length; i++) {
      var b = dataRaw[i];
      this.lastFourBytes = this.lastFourBytes.sublist(1);
      this.lastFourBytes.add(b);

      if(this.frameState == FrameState.IDLE) {
        if(this._lastFourBytesSet() && this.lastFourBytes[0] == Deframer.SOF_TOKEN) {
          this.frameState = FrameState.IN_FRAME;
        }

      } else if (this.frameState == FrameState.IN_FRAME) {
        if(b == Deframer.EOF_TOKEN) {
          this.frameState = FrameState.IN_FRAME_EOF_CANDIDATE;
          this.eofTokensSeen = 1;
        } else {
          this.currentFrameData.add(b);
        }

      } else if (this.frameState == FrameState.IN_FRAME_EOF_CANDIDATE) {
        if(b != Deframer.EOF_TOKEN) {
          this.frameState = FrameState.IN_FRAME;
          this.currentFrameData += this.lastFourBytes.sublist(0, this.eofTokensSeen + 1);

        } else {
          this.eofTokensSeen++;
          if(this.eofTokensSeen == 4) {
            this.frameState = FrameState.IDLE;

            ret = String.fromCharCodes(this.currentFrameData);
            print("DEFRAMED: ${ret}");

            this.currentFrameData.clear();
            this.eofTokensSeen = 0;
          }
        }
      }
    }
    return ret;
  }
}