import copy
import pathlib

import yaml


class CommandCatalogue:

    LOADED = False

    templateMapping = {}
    commandLookup = {}
    staticCommandLookup = {}

    @staticmethod
    def loadConfig():
        if CommandCatalogue.LOADED:
            return

        originalConfig = yaml.load(open(pathlib.Path(__file__).parent.absolute().joinpath("../").joinpath("BossRxCommands/CommandDictionary.yaml").absolute()))
        commandConfig = copy.deepcopy(originalConfig)


        for bt in commandConfig["boss"]["base_templates"]:
            templateInfo = commandConfig["boss"]["base_templates"][bt]

            pattern = templateInfo["template"].format(
                idHex="*" * (templateInfo["idIdxs"][1] - templateInfo["idIdxs"][0] + 1),
                valueHex="*" * (templateInfo["valueHexIdxs"][1] - templateInfo["valueHexIdxs"][0] + 1),
                trackerHex="*" * (templateInfo["trackerHexIdxs"][1] - templateInfo["trackerHexIdxs"][0] + 1))
            templateInfo["name"] = bt
            templateInfo["pattern"] = pattern
            templateInfo["commands"] = []
            CommandCatalogue.templateMapping[bt] = templateInfo

        # Store commands for quick Rx/Tx Lookup
        for category in commandConfig["boss"]["commands"]:
            if commandConfig["boss"]["commands"][category] is not None:
                for name in commandConfig["boss"]["commands"][category]:
                    cmd = commandConfig["boss"]["commands"][category][name]

                    fullName = f"{category.upper()}.{name.upper()}"
                    cmd["name"] = fullName

                    CommandCatalogue.templateMapping[cmd["base_template"]]["commands"].append(cmd)
                    CommandCatalogue.commandLookup[fullName] = cmd

        for category in commandConfig["boss"]["static_commands"]:
            if commandConfig["boss"]["static_commands"][category] is not None:
                for name in commandConfig["boss"]["static_commands"][category]:
                    cmd = commandConfig["boss"]["static_commands"][category][name]

                    fullName = f"{category.upper()}.{name.upper()}"
                    cmd["name"] = fullName

                    CommandCatalogue.staticCommandLookup[fullName] = cmd

    @staticmethod
    def _findCmdInConfig(rx: str):
        def getTemplateForRx(rx):
            ret = None
            for templateName, templateInfo in CommandCatalogue.templateMapping.items():
                if all([a == b for a, b in zip(templateInfo["pattern"], rx) if a != "*"]):
                    ret = templateInfo
            return ret

        ret = None

        templateInfo = getTemplateForRx(rx)

        if templateInfo is not None:
            idHex = rx[templateInfo["idIdxs"][0]:templateInfo["idIdxs"][1]+1]
            for cmd in templateInfo["commands"]:
                if cmd["idHex"] == idHex:
                    ret = cmd

        return ret

    @staticmethod
    def getCommand(commandFullName: str):
        ret = None

        if commandFullName in CommandCatalogue.commandLookup:
            ret = CommandCatalogue.commandLookup[commandFullName]

        return ret

    @staticmethod
    def getCmdBaseTemplate(templateName: str):
        return CommandCatalogue.templateMapping[templateName]


    @staticmethod
    def getStaticCommand(cmdName: str):
        ret = None

        if cmdName in CommandCatalogue.staticCommandLookup:
            ret = CommandCatalogue.staticCommandLookup[cmdName]

        return ret


# Singleton-esc one-time-init
if not CommandCatalogue.LOADED:
    CommandCatalogue.loadConfig()
