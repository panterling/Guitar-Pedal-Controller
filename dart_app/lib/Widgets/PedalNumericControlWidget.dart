import 'package:dart_app/BluetoothBloc/BluetoothBloc.dart';
import 'package:dart_app/BluetoothBloc/Events.dart';
import 'package:dart_app/Pedal/PedalBloc.dart';
import 'package:dart_app/Pedal/PedalState.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

abstract class PedalControlState {
  //}extends Equatable {
  //final String commandFullName;
  final int currentValue;

  PedalControlState(/*this.commandFullName, */ this.currentValue);

//  @override
//  List<Object> get props => [];
}

class PedalControlStateIdle extends PedalControlState {
  PedalControlStateIdle(int currentValue) : super(currentValue);
}

class PedalControlStateUserInteraction extends PedalControlState {
  PedalControlStateUserInteraction(int currentValue) : super(currentValue);
}

class PedalControlStateSyncing extends PedalControlState {
  int syncValue;

  PedalControlStateSyncing(int currentValue, {this.syncValue}) : super(currentValue);
}

abstract class PedalControlEvent {}

class PedalControlEventUserInteraction extends PedalControlEvent {}

class PedalControlEventIdle extends PedalControlEvent {}

class PedalControlEventValueChange extends PedalControlEvent {
  int newValue;

  PedalControlEventValueChange({this.newValue});
}

class PedalControlEventUserChangeRequest extends PedalControlEvent {
  int requestedValue;

  PedalControlEventUserChangeRequest({this.requestedValue});
}

class PedalControlBloc extends Bloc<PedalControlEvent, PedalControlState> {
  String commandFullName;

  PedalControlBloc(this.commandFullName) {
    print("PedalControlBloc Created: ${commandFullName}");
  }

  @override
  // TODO: implement initialState
  PedalControlState get initialState => PedalControlStateIdle(0);

  @override
  Stream<PedalControlState> mapEventToState(PedalControlEvent event) async* {

    PedalControlState yieldRet = null;

    if (event is PedalControlEventValueChange) {
      var newValue = event.newValue;
      if (this.state is PedalControlStateUserInteraction || this.state is PedalControlStateIdle) {
        yieldRet = PedalControlStateIdle(newValue);

      } else if (this.state is PedalControlStateSyncing) {
        if (event.newValue == (this.state as PedalControlStateSyncing).syncValue) {
          yieldRet = PedalControlStateIdle(newValue);
        } else {
          // CP: TODO: Notify of 'failed sync' somehow?
          print("FAILED SYNC");
          yieldRet = PedalControlStateIdle(newValue);
        }
      }
    } else if (event is PedalControlEventIdle) {
      print("WARN: Received Idle Event whilst already in Idle State - unexpected state change attempt?");

    } else if (event is PedalControlEventUserInteraction) {
      yieldRet = PedalControlStateUserInteraction(this.state.currentValue);

    } else if (event is PedalControlEventUserChangeRequest) {
      yieldRet = PedalControlStateSyncing(this.state.currentValue, syncValue: event.requestedValue);

    } else {
      var i = 0;
    }


    if(yieldRet != null) {
      print("[${this.commandFullName}] ${this.state} -> ${yieldRet}");
      yield yieldRet;
    }
  }

  @override
  void dispose() {
    print("Disposed??!?!!?!?!?!?!?!?!");
  }

  @override
  Future<void> close() {
    //cancel streams
    super.close();
  }
}

class PedalNumericControlWidget extends StatelessWidget {
  PedalCommandConfigWithValue commandConfigWithValue;

  PedalNumericControlWidget({this.commandConfigWithValue});

  @override
  Widget build(BuildContext context) {
    PedalControlBloc pedalControlBloc = BlocProvider.of<PedalBloc>(context).getPedalControlBloc(commandConfigWithValue.commandConfig.fullName);


    var builder = BlocBuilder<PedalControlBloc, PedalControlState>(builder: (context, state) {

      /* * * * * * * * * * * * * * * * * * * * * * * */
      double getValue() {
        double ret;
        if (state is PedalControlStateSyncing) {
          ret = (state as PedalControlStateSyncing).syncValue.toDouble();
        } else {
          ret = this.commandConfigWithValue.value.toDouble();
        }
        return ret;
      }

      Widget getValueWidget() {
        Widget ret;
        if (state is PedalControlStateSyncing) {
          ret = Text((state as PedalControlStateSyncing).syncValue.toString(),
              style: TextStyle(color: Colors.lightBlueAccent, fontStyle: FontStyle.italic));
        } else {
          ret = Text(state.currentValue.toString());
        }
        return Center(child: ret);
      }

      Widget getControlWidget() {
        Widget ret;
        if (state is PedalControlStateSyncing) {
          ret = Center(child: Text(".. Syncing ..", style: TextStyle(color: Colors.blue)));
        } else {
          ret = RaisedButton(
              child: Text("Change"),
              onPressed: () {
                pedalControlBloc.add(PedalControlEventUserInteraction());

                //this.userValue = this.commandConfigWithValue.value;
                showDialog(
                    context: context,
                    builder: (BuildContext context) {

                      var builder =  BlocBuilder<PedalControlBloc, PedalControlState>(
                        builder: (context, state) => ChangeValueDialog(
                          // CP: TODO: Just pass the commandConfig object!
                          commandFullName: this.commandConfigWithValue.commandConfig.fullName,
                          title: this.commandConfigWithValue.commandConfig.displayName,
                          minValue: this.commandConfigWithValue.commandConfig.minValue,
                          maxValue: this.commandConfigWithValue.commandConfig.maxValue,
                          currentValue: state.currentValue,
                        ),
                      );
                      return BlocProvider.value(
                        value: BlocProvider.of<PedalBloc>(context).getPedalControlBloc(commandConfigWithValue.commandConfig.fullName),
                        child: builder,
                      );
                    });
              });
        }
        return ret;
      }
      /* * * * * * * * * * * * * * * * * * * * * * * */

      return Padding(
          padding: EdgeInsets.all(12.0),
          child: Row(children: <Widget>[
            Expanded(child: Text(this.commandConfigWithValue.commandConfig.displayName), flex: 3),
            Expanded(child: getControlWidget(), flex: 5),
            Expanded(child: getValueWidget(), flex: 2),
          ]));
    });

    return BlocProvider.value(
      value: pedalControlBloc,
      child: builder,
    );
  }
}

class ChangeValueDialog extends StatefulWidget {
  String commandFullName;
  String title;
  int minValue;
  int maxValue;
  int initialValue;
  int currentValue;

  ChangeValueDialog({this.commandFullName, this.title, this.minValue, this.maxValue, this.currentValue}) {
    this.initialValue = this.currentValue;
  }

  @override
  State<StatefulWidget> createState() {
    // TODO: implement createState
    return ChangeValueDialogState(
        commandFullName: this.commandFullName, title: this.title, minValue: this.minValue, maxValue: this.maxValue, currentValue: this.currentValue);
  }
}

class ChangeValueDialogState extends State<ChangeValueDialog> {
  String commandFullName;
  String title;
  int minValue;
  int maxValue;
  int currentValue;

  bool _isDialogShowing = false;

  ChangeValueDialogState({this.commandFullName, this.title, this.minValue, this.maxValue, this.currentValue});

  @override
  Widget build(BuildContext context) {
    print("Widget BUILDING");
    return BlocListener<PedalControlBloc, PedalControlState>(
        condition: (previousState, state) {
          print("Widget: ${previousState.runtimeType} != ${state.runtimeType} => ${state.runtimeType != previousState.runtimeType}");

          // CP: This (was) should be in the listener, but we need to know the previous state to dictate the action to take! What is the correct pattern?
          if(previousState.runtimeType != state.runtimeType){
            if (previousState is PedalControlStateUserInteraction && state is PedalControlStateIdle) {
              // CP: Only trigger the pop if the Dialog is showing.
              //     The dialog needs to 'pop' if the previous state was UserInteraction
              print("Dialog Closing - Server-Triggered Hide:: ${state}");
              Navigator.of(context, rootNavigator: true).pop('dialog');
            }
          }
          ////////////////////////////////////////////

          return (previousState.runtimeType != state.runtimeType) || (previousState.currentValue != state.currentValue);
        },
      listener: (context, state) {
        // CP Logic moved (perhaps, incorrectly) to condition() above.

      }, child: Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20.0)),
        child: Container(
          child: Wrap(children: [
            Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(this.title),
                  Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
                    Expanded(
                        child: Slider(
                          min: this.minValue.toDouble(),
                          max: this.maxValue.toDouble(),
                          value: this.currentValue.toDouble(),
                          onChanged: (value) {
                            setState(() {
                              this.currentValue = value.toInt();
                              print("Setting to ${this.currentValue}");
                            });
                          },
                        ),
                        flex: 3),
                    Expanded(child: Text(this.currentValue.toString()), flex: 1)
                  ]),
                  SizedBox(
                    width: 320.0,
                    child: RaisedButton(
                      onPressed: () {
                        var pedalControlBloc = BlocProvider.of<PedalControlBloc>(context);
                        pedalControlBloc.add(PedalControlEventUserChangeRequest(requestedValue: this.currentValue));

                        // Pass to bluetooth for Transmit
                        // CP: TODO: value->command->payload mapping logic belongs up-stream/elsewhere - PedalBloc?
                        String payload = "{\"name\": \"${this.commandFullName}\", \"value\": ${this.currentValue.toString()}}";
                        BlocProvider.of<BluetoothBloc>(context).add(BluetoothBlocEventSendMessage(payload:payload));

                        Navigator.of(context).pop();
                        print("Dialog Closing - Reactive");
                      },
                      child: Text(
                        "Set",
                        style: TextStyle(color: Colors.white),
                      ),
                      color: Colors.lightBlueAccent,
                    ),
                  )
                ],
              ),
            )
          ]),
        ),
      )
    );
  }
}
