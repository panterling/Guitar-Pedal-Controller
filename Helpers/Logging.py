import logging
import sys


class LoggerFactory:

    _LOGGERS = {}

    @staticmethod
    def getNamedLogger(name: str) -> logging.Logger:
        if name not in LoggerFactory._LOGGERS:
            logger = LoggerFactory.getUniqueLogger(name)
            LoggerFactory._LOGGERS[name] = logger

        return LoggerFactory._LOGGERS[name]

    @staticmethod
    def getUniqueLogger(name: str):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s:: %(message)s'))
        logger.addHandler(handler)

        return logger