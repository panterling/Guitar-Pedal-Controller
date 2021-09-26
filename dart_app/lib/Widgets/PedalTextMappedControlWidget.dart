import 'package:dart_app/Helpers/YamlHelpers.dart';
import 'package:dart_app/Pedal/PedalState.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

class PedalTextMappedControlWidget extends StatelessWidget {
  PedalCommandConfigWithValue commandConfigWithValue;

  Map<int, String> valueMapping;
  String Function(int) valueMappingFunc;

  PedalTextMappedControlWidget(
      {this.commandConfigWithValue, this.valueMapping, this.valueMappingFunc});

  String get mappedValue {
    String ret;

    if (valueMappingFunc != null) {
      return valueMappingFunc(this.commandConfigWithValue.value);
    } else if (valueMapping != null &&
        valueMapping.containsKey(this.commandConfigWithValue.value)) {
      ret = this.valueMapping[this.commandConfigWithValue.value];
    } else {
      ret = this.commandConfigWithValue.value.toString();
    }

    return ret;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
        padding: EdgeInsets.all(12.0),
        child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: <Widget>[
              Expanded(
                  child: Text(this
                      .commandConfigWithValue
                      .commandConfig
                      .displayName),
                  flex: 3),
              Expanded(
                  child: Slider(
                    min: this
                        .commandConfigWithValue
                        .commandConfig
                        .minValue
                        .toDouble(),
                    max: this
                        .commandConfigWithValue
                        .commandConfig
                        .maxValue
                        .toDouble(),
                    value: this.commandConfigWithValue.value.toDouble(),
                    onChanged: (value) {
//              setState(() {
//                // CP: TODO:
//              });
                    },
                  ),
                  flex: 5),
              Expanded(child: Text(this.mappedValue), flex: 2),
            ]));
  }
}
