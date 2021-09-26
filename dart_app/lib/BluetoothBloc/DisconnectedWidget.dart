import 'package:dart_app/BluetoothBloc/Events.dart';
import 'package:dart_app/BluetoothBloc/States.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'BluetoothBloc.dart';

class DisconnectedWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    var bluetoothBloc = BlocProvider.of<BluetoothBloc>(context);

    void connect() => bluetoothBloc.add(BluetoothBlocEventConnect());

    // Disconnect reason message
    Widget disconnectReasonWidget = Text("");
    if (bluetoothBloc.state is BluetoothBlocStateDisconnected) {
      var reasonStr = (bluetoothBloc.state as BluetoothBlocStateDisconnected).reason;

      if(reasonStr == null) {
        reasonStr = "NULL";
      }

      if (reasonStr != "") {
        disconnectReasonWidget = Container(
          margin: const EdgeInsets.all(15.0),
          padding: const EdgeInsets.all(3.0),
          decoration: BoxDecoration(
              border: Border.all(color: Colors.blueAccent),
              borderRadius: BorderRadius.circular(8.0)),
          child: Row(
            children: [Icon(Icons.warning), Text(reasonStr)],
            mainAxisAlignment: MainAxisAlignment.center,
          ),
        );
      }
    }
    return Center(
        child: Column(
      children: <Widget>[
        RaisedButton(
          child: Text('Connect',),
          color: Colors.lightBlueAccent,
          padding: EdgeInsets.all(30.0),
          shape: RoundedRectangleBorder(
              borderRadius: new BorderRadius.circular(18.0),
          ),
          onPressed: connect,
        ),
        disconnectReasonWidget,
      ],
      mainAxisAlignment: MainAxisAlignment.center,
    ));
  }
}
