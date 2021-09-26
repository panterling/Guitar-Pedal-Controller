import 'package:flutter/material.dart';
import 'package:yaml/yaml.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'dart:io';

class DuplicateCommandException implements Exception {
  String cause;
  DuplicateCommandException(this.cause);
}

class CommandDoesNotExistException implements Exception {
  String cause;
  CommandDoesNotExistException(this.cause);
}

class PedalCommandConfig {
  String category;
  String name;
  String prettyName;
  int minValue;
  int maxValue;
  PedalCommandConfig({this.category, this.name, this.minValue, this.maxValue, this.prettyName});

  String get fullName => "${this.category.toUpperCase()}.${this.name.toUpperCase()}";
  String get displayName => this.prettyName != null ? this.prettyName : this.fullName.toLowerCase();

}

class PedalConfig {
  Map<String, PedalCommandConfig> commandMap = Map();

  void addCommand(String category,  String name,  int minValue, int maxValue, String prettyName) {
    var fullName = "${category.toUpperCase()}.${name.toUpperCase()}";

    if(this.commandMap.containsKey(fullName)) {
      throw DuplicateCommandException("Command [${fullName}] already exists.");
    }

    this.commandMap[fullName] = PedalCommandConfig(category: category, name: name, minValue: minValue, maxValue: maxValue, prettyName: prettyName);
  }

  bool hasCommand(String fullName) {
    return this.commandMap.containsKey(fullName);
  }

  PedalCommandConfig getCommand(String fullName) {
    if(this.hasCommand(fullName)) {
      return this.commandMap[fullName];
    } else {
      throw CommandDoesNotExistException("Command doesn't exist: ${fullName}");
    }
  }
}

class YamlHelpers {
  static Future<PedalConfig> loadPedalConfig() async {
    WidgetsFlutterBinding.ensureInitialized();

    PedalConfig pedalConfig = PedalConfig();
    
    return rootBundle.loadString("assets/CommandDictionary.yaml").then((yamlStr) {
      YamlMap doc = loadYaml(yamlStr);

      doc.forEach((key, value) {
        if(key == "boss") {
          value.forEach((groupingKey, groupingValue) {
            if(["commands"].contains(groupingKey)) {
              groupingValue.forEach((categoryKey, categoryValue) {
                if(categoryValue != null) {
                  categoryValue.forEach((commandKey, commandValue) {
                    YamlMap commandMap = commandValue;

                    var minValue = commandMap["minValue"];
                    var maxValue = commandMap["maxValue"];
                    var prettyName = commandMap.containsKey("prettyName") ? commandMap["prettyName"] : null;

                    pedalConfig.addCommand(categoryKey, commandKey, minValue, maxValue, prettyName);
                  });
                }

              });
            }
          });
        }
      });

      return pedalConfig;
    });
  }
}