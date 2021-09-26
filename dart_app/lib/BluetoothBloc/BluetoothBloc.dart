import 'package:dart_app/Bluetooth/BluetoothManager.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'Events.dart';
import 'States.dart';

class BluetoothBloc extends Bloc<BluetoothBlocEvent, BluetoothBlocState> {

  BluetoothManager bluetoothManager;

  BluetoothBloc({this.bluetoothManager}){
    bluetoothManager.eventStream.listen((BluetoothManagerState event){
      if(event is BluetoothManagerStateConnected) {
        this.add(BluetoothBlocEventConnected());
        print("Added: Connected");
      }
      if(event is BluetoothManagerStateSearching) {
        this.add(BluetoothBlocEventSearching());
        print("Added: Searching");
      }
      if(event is BluetoothManagerStateConnecting) {
        this.add(BluetoothBlocEventConnecting());
        print("Added: Connecting");
      }

      if(event is BluetoothManagerStateDisconnected) {
        this.add(BluetoothBlocEventDisconnected(reason: (event as BluetoothManagerStateDisconnected).reason ));
        print("Added: Disconnected");
      }
    });
  }

  void connect() {
    this.bluetoothManager.connectToPedal();
  }

  void disonnect() {
    this.bluetoothManager.disconnectFromPedal();
  }

  @override
  // TODO: implement initialState
  BluetoothBlocState get initialState => BluetoothBlocStateDisconnected();


  @override
  Stream<BluetoothBlocState> mapEventToState(BluetoothBlocEvent event) async* {

    if (event is BluetoothBlocEventConnect) {
      this.bluetoothManager.connectToPedal();
      yield BluetoothBlocStateSearching();
    }

    else if (event is BluetoothBlocEventConnecting) {
      yield BluetoothBlocStateConnecting();
    }

    else if (event is BluetoothBlocEventConnected) {
      yield BluetoothBlocStateConnected();
    }

    else if (event is BluetoothBlocEventDisconnected) {
      yield BluetoothBlocStateDisconnected(reason: event.reason);
    }

    else if (event is BluetoothBlocEventDisconnect) {
      this.bluetoothManager.disconnectFromPedal();
      yield BluetoothBlocStateDisconnected();
    }

    else if (event is BluetoothBlocEventSendMessage) {
      var payload = (event as BluetoothBlocEventSendMessage).payload;
      this.bluetoothManager.sendMessage(payload);
    }
  }
}