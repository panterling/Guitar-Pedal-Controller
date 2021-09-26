import 'package:meta/meta.dart';
import 'package:equatable/equatable.dart';

abstract class BluetoothBlocEvent extends Equatable {
  // CP: TODO: Review Equitable contract and need for this declaration!
  //const BluetoothBlocEvent();

  @override
  List<Object> get props => [];
}


class BluetoothBlocEventDisconnected extends BluetoothBlocEvent {
  String reason;
  BluetoothBlocEventDisconnected({this.reason});
}

class BluetoothBlocEventConnect extends BluetoothBlocEvent {}

class BluetoothBlocEventSearching extends BluetoothBlocEvent {}
class BluetoothBlocEventConnecting extends BluetoothBlocEvent {}

class BluetoothBlocEventConnected extends BluetoothBlocEvent {}

class BluetoothBlocEventSendMessage extends BluetoothBlocEvent {
  String payload;
  BluetoothBlocEventSendMessage({this.payload});
}

class BluetoothBlocEventDisconnect extends BluetoothBlocEvent {}
