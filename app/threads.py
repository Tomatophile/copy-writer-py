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


class Worker(MessagingThread):
    def __init__(self, input_queue: str, output_queue: str):
        super().__init__(input_queue, output_queue)
        self.message_handles: dict[Message.Type, list[Callable]] = {
            Message.Type.SET_HOTKEY: [self.handle_set_hotkey]
        }
        self.callbacks: dict[Actions, Callable] = {
            Actions.WRITE: self.action_write,
            Actions.INTERRUPT: self.action_interrupt
        }
        self.hotkeys: dict[Callable, str] = {
            self.action_write: Actions.WRITE.value,
            self.action_interrupt: Actions.INTERRUPT.value
        }

    def update_hotkeys(self) -> None:
        for callback, hotkey in self.hotkeys.items():
            try:
                keyboard.remove_hotkey(callback)
            except KeyError:
                pass
            keyboard.add_hotkey(hotkey, callback)

    def init(self) -> None:
        self.update_hotkeys()

    def handle_message(self, message: Message) -> None:
        handlers = self.message_handles.get(message.type)
        if handlers is not None:
            for handler in handlers:
                handler(message)

    def handle_set_hotkey(self, message: Message) -> None:
        action: Actions = message.kwargs.get('action')
        if action is None:
            raise ValueError('Action must be defined for hotkey')
        hotkey: str = keyboard.read_hotkey()
        self.hotkeys[self.callbacks[action]] = hotkey
        self.update_hotkeys()
        broker.send(Message(Message.Type.HOTKEY_SET, action=action, hotkey=hotkey), self.output_queue)

    def action_write(self):
        #TODO
        pass

    def action_interrupt(self):
        #TODO
        pass
