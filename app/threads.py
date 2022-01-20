import ctypes
import threading
from logging import Logger
from threading import Thread
from typing import Callable

from app import broker
from app.broker import Message

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


class MessagingThread(InterruptableThread):
    def __init__(self, queue: str):
        super().__init__()
        self.queue = queue

    def run(self) -> None:
        try:
            self.init()
            while True:
                message = broker.read(self.queue)
                if message.type == Message.Type.INTERRUPT:
                    self.interrupt()
                self.handle_message(message)
                self.loop()
        except InterruptedException:
            pass

    def init(self) -> None:
        pass

    def handle_message(self, message: Message) -> None:
        pass

    def loop(self) -> None:
        pass
