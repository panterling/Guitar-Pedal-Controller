import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/services.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';

import 'Framing.dart';

abstract class BluetoothManagerState {}
class BluetoothManagerStateDisconnected extends BluetoothManagerState {
  String reason;
  BluetoothManagerStateDisconnected({this.reason});
}
class BluetoothManagerStateSearching extends BluetoothManagerState {}
class BluetoothManagerStateConnecting extends BluetoothManagerState {}
class BluetoothManagerStateConnected extends BluetoothManagerState {}


class BluetoothMessage {
  int whom;
  String text;

  BluetoothMessage(this.whom, this.text);
}

class BluetoothManager {
  //static const String PEDAL_SERVER_NAME = "raspberrypi";
  static const String PEDAL_SERVER_NAME = "chris-desktop";
//  static const String PEDAL_SERVER_NAME = "BossControlServer";

  BluetoothManagerState state = BluetoothManagerStateDisconnected();

  StreamController<BluetoothManagerState> _eventStreamController = StreamController();
  Stream<BluetoothManagerState> _eventStream;

  StreamController<String> _msgStreamController = StreamController();
  Stream<String> _msgStream;

  BluetoothDevice pedalDevice;
  BluetoothConnection connection;

  Deframer deframer = Deframer();

  BluetoothManager() {
    _eventStream = _eventStreamController.stream;
    _msgStream = _msgStreamController.stream;
  }

  get connected => this.state == BluetoothManagerStateConnected();

  get eventStream => _eventStream;

  get msgStream => _msgStream;

  void connectToPedal() {
    findPedalServer();
  }

  void disconnectFromPedal() {
    connection.dispose();
  }

  void setState(BluetoothManagerState newState) {
    // CP: TODO: Validate state transitions
    this.state = newState;
    this._eventStreamController.add(newState);
  }

  void findPedalServer() {
    this.setState(BluetoothManagerStateSearching());
    print("Discovering Pedal Server");

    FlutterBluetoothSerial.instance
        .getBondedDevices()
        .then((List<BluetoothDevice> bondedDevices) {
              BluetoothDevice pedalDevice;
              bondedDevices.forEach((BluetoothDevice bd) {
                print("${bd.name} = ${bd.address}");
                if (bd.name == PEDAL_SERVER_NAME) {
                  print(
                      "Found Paired Pedal Server: ${PEDAL_SERVER_NAME} == ${bd.address}");
        
                  pedalDevice = bd;
                }
              });
        
              /*
              devices = bondedDevices.map(
                      (device) => _DeviceWithAvailability(device, widget.checkAvailability ? _DeviceAvailability.maybe : _DeviceAvailability.yes)
              ).toList();
               */
        
              return pedalDevice;
            }).then((BluetoothDevice pedalDevice) {
                if (pedalDevice == null) {
                  this.setState(BluetoothManagerStateDisconnected(reason: "Pedal Server Not Found/Not Paired"));
                } else {
                  this.pedalDevice = pedalDevice;
                  connect();
                }
            }).catchError((error) {
              print('Cannot connect, exception occured');
            });

    /*
    List<BluetoothDiscoveryResult> results = List<BluetoothDiscoveryResult>();
    var _streamSubscription = FlutterBluetoothSerial.instance.startDiscovery().listen((r) {
      print("${r.device.name} = ${r.device.address}");
      setState(() {
        results.add(r);
      });
    });

    _streamSubscription.onDone(() {
      setState(() {
        print("Done discovering");
        _streamSubscription?.cancel();
      });
    });
    */
  }

  void connect() {
    this.setState(BluetoothManagerStateConnecting());
    try {
      BluetoothConnection.toAddress(pedalDevice.address).then((_connection) {
        print('Connected to the device');
        this.connection = _connection;
        this.setState(BluetoothManagerStateConnected());

        _connection.input.listen(_onDataReceived).onDone(() {
          // Example: Detect which side closed the connection
          // There should be `isDisconnecting` flag to show are we are (locally)
          // in middle of disconnecting process, should be set before calling
          // `dispose`, `finish` or `close`, which all causes to disconnect.
          // If we except the disconnection, `onDone` should be fired as result.
          // If we didn't except this (no flag set), it means closing by remote.
          //if (isDisconnecting) {
          //  print('Disconnecting locally!');
          //}
          //else {
          print('Disconnected remotely!');
          this.setState(BluetoothManagerStateDisconnected(reason: "Server Disconnected"));
          this.connection = null;
          //}
        });
      }).catchError((error) {
        print('Cannot connect, exception occured');

        String reason = "Exception on Connect: Unknown";

        if(error is PlatformException) {
          if(error.code == "connect_error") {
            reason = "Unable to Connect to Server";
          } else {
            reason = "PlatformException on Connect: ${error.code}";
          }
        }

        this.setState(BluetoothManagerStateDisconnected(reason: reason));
        //print(error);
      });
    } catch (e) {
      print(e);
    }
  }

  void _onDataReceived(Uint8List data) {
    String dataString = String.fromCharCodes(data);
    var output = deframer.givePayload(data);
    if (output != null) {
      print("Rx: ${output}");
      this._msgStreamController.add(output);
    }
  }

  void sendMessage(String payload) {
    if(this.state is BluetoothManagerStateConnected) {

      print("BT - Send: ${payload}");

      Uint8List framedPayload = Framer.frame(payload);
      this.connection.output.add(framedPayload);

      //await connection.output.allSent;
    }

  }
}