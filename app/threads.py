import ctypes
import threading
from logging import Logger
from threading import Thread
from typing import Callable

import keyboard

from app import broker
from app.actions import Actions
from app.broker import Message

logger = Logger('treads')


class InterruptedException(Exception):
    pass


class InterruptableThread(Thread):
    @staticmethod
    def _interrupt(tid) -> bool:
        logger.debug("Trying to interrupt thread with id = %s", tid)
        return ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(InterruptedException)) < 1

    def __init__(self, target: Callable = None, name: str = None):
        super().__init__(target=target, name=name)

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for tid, thread in threading._active.items():
            if thread is self:
                return tid

    def interrupt(self) -> bool:
        return InterruptableThread._interrupt(self.get_id())

    def exit(self) -> None:
        logger.debug("Starting exit interrupt chain from thread with id = %s", self.get_id())
        for tid, thread in threading._active.items():
            if thread is self:
                continue
            if isinstance(thread, InterruptableThread):
                InterruptableThread._interrupt(tid)
        self.interrupt()


class MessagingThread(InterruptableThread):
    def __init__(self, input_queue: str, output_queue: str,
                 init_method: Callable = None, loop_method: Callable = None,
                 message_handler: Callable = None):
        super().__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.init_method = init_method
        self.loop_method = loop_method
        self.message_handler = message_handler

    def run(self) -> None:
        try:
            self.init()
            while True:
                message = broker.read(self.input_queue)
                if message.type == Message.Type.INTERRUPT:
                    self.interrupt()
                if message.type == Message.Type.EXIT:
                    self.exit()
                self.handle_message(message)
                self.loop()
        except InterruptedException:
            pass

    def init(self) -> None:
        self.init_method()

    def handle_message(self, message: Message) -> None:
        self.message_handler(message)

    def loop(self) -> None:
        self.loop_method()
