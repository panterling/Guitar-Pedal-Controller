import 'dart:convert';

import 'package:dart_app/Pedal/PedalBloc.dart';
import 'package:dart_app/Pedal/PedalState.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'Bluetooth/BluetoothManager.dart';
import 'BluetoothBloc/BluetoothBloc.dart';
import 'BluetoothBloc/Events.dart';
import 'BluetoothBloc/Main.dart';
import 'Helpers/YamlHelpers.dart';
import 'Widgets/PedalNumericControlWidget.dart';

class CommandRegistry {
  static Map<String, PedalCommandConfig> commandMap = Map();

  static void setCommandConfig(PedalCommandConfig pedalCommandConfig) {
    if(commandMap.containsKey(pedalCommandConfig.fullName)) {
      throw CommandAlreadyRegisteredException("Command Already Registered: ${pedalCommandConfig.fullName}");
    }
    commandMap[pedalCommandConfig.fullName] = pedalCommandConfig;
  }

  static PedalCommandConfig getCommandConfig(String commandFullName) {
    if (!commandMap.containsKey(commandFullName)) {
      throw CommandNotRegisteredException("Command not registered: ${commandFullName}");
    }
    return commandMap[commandFullName];
  }
}

void main() async {
  // Init BLoC
  BlocSupervisor.delegate = PrintingBlocDelegate();

  // Load Command Config
  PedalConfig pedalConfig = await YamlHelpers.loadPedalConfig();

  // Init Bluetooth
  var bluetoothManager = BluetoothManager();

  // Init PedalState
  PedalState pedalState = PedalState();

  var availableCommandFullNames = [
    "REVERB.TYPE",
    "REVERB.ELEVEL",
    "REVERB.DLEVEL",
    "REVERB.ELEVEL_DELAY",
    "REVERB.TIME",
    "REVERB.DTIME",
    "REVERB.LOWCUT",
    "REVERB.HIGHCUT",
    "REVERB.HIGHCUT_DELAY",
    "REVERB.SPRING",
    "REVERB.FEEDBACK",
  ];
  for (var commandFullName in availableCommandFullNames) {
    pedalState.registerCommand(pedalConfig.getCommand(commandFullName));
    CommandRegistry.setCommandConfig(pedalConfig.getCommand(commandFullName));
  }

  // Subscribe PedalState to BluetoothManager msgStream
  PedalBloc pedalBloc = PedalBloc(pedalState);

  bluetoothManager.msgStream.listen((String msg) {
    // CP: TODO: Refactor into a dedicated [Raw message -> Parsed message] mechanism
    print("BluetoothManager Rx: ${msg}");

    Map<String, dynamic> msgJson = jsonDecode(msg);

    //bluetoothMessages.add(BluetoothMessage(1, msg));
    if (pedalConfig.hasCommand(msgJson["name"])) {
      String commandFullName = msgJson["name"] as String;
      int value = msgJson["value"] as int;
      pedalBloc.add(PedalResponse(commandFullName: commandFullName, value: value));
    }
  });

  var bluetoothBloc = BluetoothBloc(bluetoothManager: bluetoothManager)..add(BluetoothBlocEventDisconnected());

  //// All UI-State-Agnostic Providers
  // PedalControlBloc(s)
//  var pedalControlBlocProviders = List<BlocProvider<PedalControlBloc>>();
//  var p = BlocProvider.value(value: pedalBloc.getPedalControlBloc("REVERB.TYPE"));
//  pedalControlBlocProviders.add(p);

  // Pass Map for named-lookup within components?
  Map<String, PedalControlBloc> pedalBlocProvidorMap = Map();
  pedalBlocProvidorMap["REVERB.TYPE"] = pedalBloc.getPedalControlBloc("REVERB.TYPE");
  pedalBlocProvidorMap["REVERB.ELEVEL"] = pedalBloc.getPedalControlBloc("REVERB.ELEVEL");

  var pedalControlBlocProviders = BlocProvider.value(value: pedalBloc);

  runApp(MultiBlocProvider(
    providers: [
          BlocProvider<BluetoothBloc>(
            create: (context) {
              return bluetoothBloc;
            },
          ),
          BlocProvider<PedalBloc>(
            create: (context) {
              return pedalBloc;
            },
          )
        ],
        //+ pedalControlBlocProviders,
    child: App(),
  ));
}
