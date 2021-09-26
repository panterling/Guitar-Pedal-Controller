import 'dart:async';


import 'package:dart_app/BluetoothBloc/Events.dart';
import 'package:dart_app/Widgets/PedalNumericControlWidget.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'PedalState.dart';



abstract class PedalEvent{}

class PedalResponse extends PedalEvent {
  String commandFullName;
  int value;

  PedalResponse({this.commandFullName, this.value});

  @override
  // TODO: implement props
  List<Object> get props => null;
}


class PedalBloc extends Bloc<PedalEvent, PedalState> {
  final pedalStateController = StreamController<PedalState>.broadcast();

  Stream<PedalState> get getState => pedalStateController.stream;

  var pedalControlBlocs = Map<String, /*CommandValueChangeSubscribers*/PedalControlBloc>();

  PedalControlBloc getPedalControlBloc(String commandFullName) {
    if(!this.pedalControlBlocs.containsKey(commandFullName)){
      throw CommandNotRegisteredException("Not Registered: ${commandFullName}");
    }

    return this.pedalControlBlocs[commandFullName];
  }

  PedalState currentState;
  PedalBloc(PedalState currentState) {
    this.currentState = currentState;

    // Create PedalControlBocs for registered commands
    for(var commandFullName in this.currentState.registeredCommandsFullNameList) {
      this.pedalControlBlocs[commandFullName] = PedalControlBloc(commandFullName);
    }
  }

  void dispose() {
    pedalStateController.close();
  }

  @override
  get initialState => PedalState();

  @override
  Stream<PedalState> mapEventToState(event) async* {

    if(event is PedalResponse) {
      var pedalResponse = event;

      var commandFullName = pedalResponse.commandFullName;
      if(this.pedalControlBlocs.containsKey(commandFullName)) {
        this.pedalControlBlocs[commandFullName].add(PedalControlEventValueChange(newValue: pedalResponse.value));
      }

      // CP: Invalid use of state modification in=place prior to yield
      //     Violating contract of the BLoC mechanism!
      this.currentState.setValue(commandFullName, pedalResponse.value);

      pedalStateController.add(this.currentState);

      yield this.currentState;
    }
  }


  getCurrentState() {
    return this.currentState;
  }
}

/*
class PedalBloc extends Bloc<PedalEvent, PedalState> {

  BluetoothManager bluetoothManager;

  PedalBloc({this.bluetoothManager}){
    bluetoothManager.eventStream.listen((event){
      if(event == PedalResponse) {
        this.add(Connected());
        print("Added: Connected");
      }

    });
  }

  @override
  // TODO: implement initialState
  BluetoothBlocState get initialState => BluetoothDisconnected();


  @override
  Stream<BluetoothBlocState> mapEventToState(BluetoothBlocEvent event) async* {

    if (event is PedalResponse) {
      yield this.state;
    }


    if (event is Connect) {
      this.bluetoothManager.connectToPedal();
      yield BluetoothSearching();
    }
    if (event is Connecting) {
      yield BluetoothConnecting();
    }
    else if (event is Connected) {
      yield BluetoothConnected();
    }
    else if (event is Disconnected) {
      yield BluetoothDisconnected();
    }

    if (event is Disconnect) {
      this.bluetoothManager.disconnectFromPedal();
      yield BluetoothDisconnected();
    }
  }
}
*/