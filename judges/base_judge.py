from abc import ABC, abstractmethod

class BaseJudge(ABC):

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def evaluate(self, text):
        pass
