from abc import ABC, abstractmethod
from typing import List, Callable

class PedalCommand:
    pass

class PedalNotification:
    pass


class PedalSubscriber(ABC):
    pass

    @abstractmethod
    def notify(self, notification: PedalNotification):
        pass

class BluetoothPedalSubscriber(PedalSubscriber):
    pass

class TestPedalSubscriber(PedalSubscriber):
    pass

class PedalManager:
    def __init__(self):
        self.subscribers: List[PedalSubscriber] = []

    def registerSubscriber(self, subscriber: PedalSubscriber) -> Callable[[PedalCommand], None]:
        self.subscribers.append(subscriber)

    def start(self):
        pass