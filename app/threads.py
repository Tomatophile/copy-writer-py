import ctypes
import random
import threading
import time
from logging import Logger
from threading import Thread
from typing import Callable, Any

import PySimpleGUI
import keyboard
import win32clipboard

from app import broker
from app.actions import Actions
from app.broker import Message
from app.layout import layout

logger = Logger('treads')


class InterruptedException(Exception):
    pass


class InterruptableThread(Thread):
    @staticmethod
    def _interrupt(thread) -> bool:
        tid = thread.get_id()
        logger.debug("Trying to interrupt thread with id = %s", tid)
        if not isinstance(thread, InterruptableThread):
            return False
        thread.interrupted = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(InterruptedException)) < 1
        if thread.interrupted:
            logger.debug("Interrupted thread with id = %s", tid)
            return True
        else:
            return False

    def __init__(self, target: Callable = None, name: str = None):
        super().__init__(target=target, name=name)
        self.interrupted = False

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for tid, thread in threading._active.items():
            if thread is self:
                return tid

    def interrupt(self) -> bool:
        return InterruptableThread._interrupt(self)

    def exit(self) -> None:
        logger.debug("Starting exit interrupt chain from thread with id = %s", self.get_id())
        for thread in threading._active.values():
            if thread is self:
                continue
            if isinstance(thread, InterruptableThread):
                InterruptableThread._interrupt(thread)
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
        if self.init_method is not None:
            self.init_method()

    def handle_message(self, message: Message) -> None:
        if self.message_handler is not None:
            self.message_handler(message)

    def loop(self) -> None:
        if self.loop_method is not None:
            self.loop_method()


class Worker(MessagingThread):
    @staticmethod
    def write():
        try:
            win32clipboard.OpenClipboard()
            data: str = win32clipboard.GetClipboardData()
            if data is not None:
                for char in data:
                    time.sleep(random.uniform(0, 0.2))
                    keyboard.write(char)
        except TypeError | InterruptedException:
            pass
        finally:
            win32clipboard.CloseClipboard()

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
        self.writing_thread = None

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
        hotkey: str = keyboard.read_hotkey()  # FIXME - First released key staying pressed
        self.hotkeys[self.callbacks[action]] = hotkey
        self.update_hotkeys()
        broker.send(Message(Message.Type.HOTKEY_SET, action=action, hotkey=hotkey), self.output_queue)

    def action_write(self):
        keyboard.release(self.hotkeys[self.action_write])
        if self.writing_thread is None or self.writing_thread.interrupted:
            self.writing_thread = InterruptableThread(Worker.write)
            self.writing_thread.start()

    def action_interrupt(self):
        keyboard.release(self.hotkeys[self.action_interrupt])
        if self.writing_thread is not None and not self.writing_thread.interrupted:
            self.writing_thread.interrupt()


class Application(MessagingThread):
    def __init__(self, input_queue: str, output_queue: str, title: str):
        super().__init__(input_queue, output_queue)
        self.message_handles: dict[Message.Type, list[Callable]] = {
            Message.Type.HOTKEY_SET: [self.handle_hotkey_set]
        }
        self.window = PySimpleGUI.Window(title, layout, use_default_focus=False)
        self.window_handlers: dict[Any, list[Callable]] = {
            None: [self.window_exit],
            'Exit': [self.window_exit],
            Actions.WRITE: [self.set_hotkey],
            Actions.INTERRUPT: [self.set_hotkey]
        }
        self.worker = Worker('worker', self.input_queue)

    def init(self) -> None:
        self.worker.start()

    def handle_message(self, message: Message) -> None:
        handlers = self.message_handles.get(message.type)
        if handlers is not None:
            for handler in handlers:
                handler(message)

    def handle_hotkey_set(self, message: Message) -> None:
        action: Actions = message.kwargs.get('action')
        if action is None:
            raise ValueError('Action must be defined for hotkey')
        hotkey: str = message.kwargs.get('hotkey')
        self.window.Element(action).update(hotkey)

    def loop(self) -> None:
        self.handle_window()

    def handle_window(self):
        event, values = self.window.read(50, ('Timeout', None))
        handlers = self.window_handlers.get(event)
        if handlers is not None:
            for handler in handlers:
                handler(event, values)

    def window_exit(self, event, values):
        self.exit()

    def set_hotkey(self, event, values):
        self.window.Element(event).update('...')
        broker.send(Message(Message.Type.SET_HOTKEY, action=event), self.worker.input_queue)
