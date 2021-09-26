import 'package:dart_app/Helpers/YamlHelpers.dart';
import 'package:dart_app/Pedal/PedalBloc.dart';
import 'package:dart_app/Pedal/PedalState.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../main.dart';
import 'PedalNumericControlWidget.dart';
import 'PedalTextMappedControlWidget.dart';

class ReverbPanelBlocWidget extends StatefulWidget {
  @override
  State<StatefulWidget> createState() => ReverbPanelBlocWidgetState();
}

class ReverbPanelBlocWidgetState extends State<ReverbPanelBlocWidget> {
  @override
  Widget build(BuildContext context) {
    return Card(
        child: Column(children: <Widget>[
      ListTile(
        //leading: Icon(Icons.album),
        leading: Switch(
          value: true,
          onChanged: (value) {
            //setState(() {});
          },
          //activeTrackColor: Colors.lightGreenAccent,
          //activeColor: Colors.green,
        ),
        title: Text(
          'Reverb',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
          PedalNumericControlWidget(
            commandConfigWithValue: PedalCommandConfigWithValue(commandConfig: CommandRegistry.getCommandConfig("REVERB.TYPE"), value: 0),
          ),
          PedalNumericControlWidget(
            commandConfigWithValue: PedalCommandConfigWithValue(commandConfig: CommandRegistry.getCommandConfig("REVERB.ELEVEL"), value: 0),
          )
    ]));
  }
}
