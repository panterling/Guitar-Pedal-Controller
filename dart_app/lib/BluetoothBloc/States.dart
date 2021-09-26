import 'package:equatable/equatable.dart';

abstract class BluetoothBlocState extends Equatable {
  @override
  List<Object> get props => [];
}

class BluetoothBlocStateDisconnected extends BluetoothBlocState {
  String reason;
  BluetoothBlocStateDisconnected({this.reason = ""});
}

class BluetoothBlocStateSearching extends BluetoothBlocState {}

class BluetoothBlocStateConnecting extends BluetoothBlocState {}

class BluetoothBlocStateConnected extends BluetoothBlocState {}