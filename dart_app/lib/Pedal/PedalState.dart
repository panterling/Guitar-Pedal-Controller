import 'package:dart_app/Helpers/YamlHelpers.dart';

class CommandNotRegisteredException implements Exception {
  String cause;
  CommandNotRegisteredException(this.cause);
}

class CommandAlreadyRegisteredException implements Exception {
  String cause;
  CommandAlreadyRegisteredException(this.cause);
}



class PedalCommandConfigWithValue {
  PedalCommandConfig commandConfig;
  int value;

  PedalCommandConfigWithValue({this.commandConfig, this.value});
}

class PedalState {
  Map<String, PedalCommandConfigWithValue> pedalStateValues = Map();

  PedalState(){}

  void registerCommand(PedalCommandConfig commandConfig, {int initialValue = 0}) {
    if(pedalStateValues.containsKey(commandConfig.fullName)){
      throw CommandAlreadyRegisteredException("PedalState:: registerCommand - Command already registered: ${commandConfig.fullName}");
    } else {
      pedalStateValues[commandConfig.fullName] = PedalCommandConfigWithValue(commandConfig: commandConfig, value: initialValue);
    }
  }

  PedalCommandConfigWithValue getCommandConfigWithValue(String commandFullName) {
    if(pedalStateValues.containsKey(commandFullName)){
      return pedalStateValues[commandFullName];
    } else {
      throw CommandNotRegisteredException("PedalState:: getValue - Command not registered: ${commandFullName}");
    }
  }

  List<String> get registeredCommandsFullNameList => this.pedalStateValues.keys.toList();

  void setValue(String commandFullName, int newValue) {
    if(!pedalStateValues.containsKey(commandFullName)){
      print("PedalState:: WARNING: setValue - Command not registered: ${commandFullName}");
    } else {
      pedalStateValues[commandFullName].value = newValue;
    }
  }
}