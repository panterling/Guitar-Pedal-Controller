import 'package:dart_app/BluetoothBloc/ConnectedWidget.dart';
import 'package:dart_app/BluetoothBloc/States.dart';
import 'package:flutter/material.dart';

import 'package:bloc/bloc.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'BluetoothBloc.dart';
import 'ConnectingWidget.dart';
import 'DisconnectedWidget.dart';
import 'Events.dart';

class PrintingBlocDelegate extends BlocDelegate {
  @override
  void onEvent(Bloc bloc, Object event) {
    super.onEvent(bloc, event);
    //print(event);
  }

  @override
  void onTransition(Bloc bloc, Transition transition) {
    super.onTransition(bloc, transition);
    //print(transition);
  }

  @override
  void onError(Bloc bloc, Object error, StackTrace stacktrace) {
    super.onError(bloc, error, stacktrace);
    print("PrintingBlocDelegate - Error: ${error}");
  }
}

class App extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: BlocBuilder<BluetoothBloc, BluetoothBlocState>(
        builder: (context, state) {
          Widget currentWidget = Text("I'm not meant to be visible... ever.");

          List<Widget> appBarWidgets = [Text("Pedal Studio")];


          if (state is BluetoothBlocStateDisconnected) {
            currentWidget = DisconnectedWidget();
          }
          else if (state is BluetoothBlocStateSearching || state is BluetoothBlocStateConnecting) {
            currentWidget = ConnectingWidget();
          }
          else if (state is BluetoothBlocStateConnected) {
            currentWidget = ConnectedWidget();

            void disconnect() {
              BlocProvider.of<BluetoothBloc>(context).add(BluetoothBlocEventDisconnect());
            }

            appBarWidgets.add(RaisedButton(
              child: Text('Disconnect'),
              color: Colors.orangeAccent,
              onPressed: disconnect,
            ));
          }

          return Scaffold(
              appBar: AppBar(
                // Here we take the value from the MyHomePage object that was created by
                // the App.build method, and use it to set our appbar title.
                title: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: appBarWidgets),
              ),
              body: //currentWidget
              AnimatedSwitcher(
                duration: Duration(milliseconds: 500),
                child: currentWidget,
              ));
        },
      ),
    );
  }
}
