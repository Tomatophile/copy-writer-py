import ctypes
import threading
from logging import Logger
from threading import Thread
from typing import Callable

logger = Logger('treads')


class InterruptedException(Exception):
    pass


class InterruptableThread(Thread):
    def __init__(self, target: Callable = None, name: str = None):
        super().__init__(target=target, name=name)

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for tid, thread in threading._active.items():
            if thread is self:
                return tid

    def interrupt(self) -> bool:
        return ctypes.pythonapi.PyThreadState_SetAsyncExc(self.get_id(), ctypes.py_object(InterruptedException)) < 1
