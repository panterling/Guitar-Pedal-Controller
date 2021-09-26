import 'package:dart_app/BluetoothBloc/Events.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:loading/indicator/ball_pulse_indicator.dart';
import 'package:loading/loading.dart';

import 'BluetoothBloc.dart';

class ConnectingWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    void cancel() {
      BlocProvider.of<BluetoothBloc>(context).add(BluetoothBlocEventDisconnect());
    }

    return Center(
        child: Column(
      children: <Widget>[
        Text('Connecting'),
        Loading(
            indicator: new BallPulseIndicator(),
            size: 100.0,
            color: Colors.blue),
        RaisedButton(
          child: Text("Cancel"),
          onPressed: cancel,
        )
      ],
      mainAxisAlignment: MainAxisAlignment.center,
    ));
  }

  void connect() {
    print("TOOO");
  }
}
