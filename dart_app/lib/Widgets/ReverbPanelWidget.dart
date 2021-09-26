import 'package:dart_app/Pedal/PedalBloc.dart';
import 'package:dart_app/Pedal/PedalState.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'PedalNumericControlWidget.dart';
import 'PedalTextMappedControlWidget.dart';

class ReverbPanelWidget extends StatefulWidget {
  @override
  State<StatefulWidget> createState() => ReverbPanelWidgetState();
}

class ReverbPanelWidgetState extends State<ReverbPanelWidget> {
  @override
  Widget build(BuildContext context) {
    var pedalBloc = BlocProvider.of<PedalBloc>(context);

    /* * * * * * * * * * * * * * * * * * * * */

    Map<int, String> typeValueMapping = {
      0: "Ambience",
      1: "Room",
      2: "Hall1",
      3: "Hall2",
      4: "Plate",
      5: "Spring",
      6: "Modulate",
      7: "Delay",
    };

    Map<int, String> lowCutValueMapping = {
      0: "Flat",
      1: "20.0Hz",
      2: "25.0Hz",
      3: "31.5Hz",
      4: "40.0Hz",
      5: "50.0Hz",
      6: "63.0Hz",
      7: "80.0Hz",
      8: "100Hz",
      9: "125Hz",
      10: "160Hz",
      11: "200Hz",
      12: "250Hz",
      13: "315Hz",
      14: "400Hz",
      15: "500Hz",
      16: "630Hz",
      17: "800Hz",
    };

    Map<int, String> highCutValueMapping = {
      0: "630Hz",
      1: "800Hz",
      2: "1.00KHz",
      3: "1.25KHz",
      4: "1.60KHz",
      5: "2.00KHz",
      6: "2.50KHz",
      7: "3.15KHz",
      8: "4.00KHz",
      9: "5.00KHz",
      10: "6.30KHz",
      11: "8.00KHz",
      12: "10.00KHz",
      13: "12.50KHz",
      14: "Flat",
    };

    /* * * * * * * * * * * * * * * * * * * * */

    String timeMappingFunc(int value) {
      var doubleValue = (value + 1) * 0.1;
      return doubleValue.toStringAsFixed(1) + "s";
    }

    print(" -- Building Stream");

    return StreamBuilder(
        stream: pedalBloc.getState,
        initialData: pedalBloc.getCurrentState(),
        builder: (context, snapshot) {
          var pedalState = snapshot.data as PedalState;

          var currentType =
              pedalState.getCommandConfigWithValue("REVERB.TYPE").value;

          List<Widget> controlColumnChildren = [
            /* CP: This mapping belongs in the config/loader */
            PedalTextMappedControlWidget(
              commandConfigWithValue:
                  pedalState.getCommandConfigWithValue("REVERB.TYPE"),
              valueMapping: typeValueMapping,
            ),
          ];

          if (currentType != 7 /* Delay */) {
            controlColumnChildren.addAll([
              PedalTextMappedControlWidget(
                    commandConfigWithValue:
                        pedalState.getCommandConfigWithValue("REVERB.TIME"),
                    valueMappingFunc: timeMappingFunc,
                  ),
              PedalNumericControlWidget(
                  commandConfigWithValue:
                      pedalState.getCommandConfigWithValue("REVERB.ELEVEL")),
              PedalTextMappedControlWidget(
                commandConfigWithValue:
                    pedalState.getCommandConfigWithValue("REVERB.LOWCUT"),
                valueMapping: lowCutValueMapping,
              ),
              PedalTextMappedControlWidget(
                commandConfigWithValue:
                    pedalState.getCommandConfigWithValue("REVERB.HIGHCUT"),
                valueMapping: highCutValueMapping,
              ),
            ]);
            if (currentType == 5 /* Spring */) {
              controlColumnChildren.add(PedalNumericControlWidget(
                  commandConfigWithValue:
                      pedalState.getCommandConfigWithValue("REVERB.SPRING")));
            }
          } else {
            controlColumnChildren.addAll([
              PedalNumericControlWidget(
                  commandConfigWithValue:
                      pedalState.getCommandConfigWithValue("REVERB.DTIME")),
              PedalNumericControlWidget(
                  commandConfigWithValue: pedalState
                      .getCommandConfigWithValue("REVERB.ELEVEL_DELAY")),
              PedalNumericControlWidget(
                  commandConfigWithValue:
                      pedalState.getCommandConfigWithValue("REVERB.FEEDBACK")),
              PedalNumericControlWidget(
                  commandConfigWithValue: pedalState
                      .getCommandConfigWithValue("REVERB.HIGHCUT_DELAY")),
              PedalNumericControlWidget(
                  commandConfigWithValue:
                      pedalState.getCommandConfigWithValue("REVERB.DLEVEL")),
            ]);
          }

          return Card(
              child: new SingleChildScrollView(
                  child: Column(
                      children: <Widget>[
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
                            )
                          ] +
                          controlColumnChildren)));
        });
  }
}
