import random
import time
from typing import Callable

import keyboard
import win32clipboard

from app.layout import default_hotkeys, Actions
from app.threads import bus
from app.threads.EventHandlerThread import EventHandlerThread
from app.threads.events import HotkeyRecordEvent, HotkeyRecordedEvent


class Worker(EventHandlerThread):
    def __init__(self):
        super().__init__()
        self.hotkeys: dict[Actions, str] = {
            Actions.write: default_hotkeys[Actions.write],
            Actions.interrupt: default_hotkeys[Actions.interrupt]
        }
        self.callbacks: dict[Actions, Callable] = {
            Actions.write: self.write,
            Actions.interrupt: self.interrupt
        }

    def init(self) -> None:
        self.handlers.update({
            HotkeyRecordEvent: self.handle_hotkey_record_event
        })
        for action, hotkey in self.hotkeys:
            keyboard.add_hotkey(hotkey, self.callbacks[action])

    def handle_hotkey_record_event(self, event: HotkeyRecordEvent) -> None:
        hotkey: str = keyboard.read_hotkey()
        keyboard.remove_hotkey(self.callbacks[event.action])
        keyboard.add_hotkey(hotkey, self.callbacks[event.action])
        self.hotkeys[event.action] = hotkey
        bus.fire(HotkeyRecordedEvent(event.action, hotkey))

    def write(self) -> None:
        try:
            keyboard.add_hotkey(self.hotkeys[Actions.interrupt], self.callbacks[Actions.interrupt])
            win32clipboard.OpenClipboard()
            data: str = win32clipboard.GetClipboardData()
            if data is not None:
                for char in data:
                    time.sleep(random.uniform(0, 0.2))
                    keyboard.write(char)
        except TypeError:
            pass
        finally:
            win32clipboard.CloseClipboard()
            keyboard.release(self.hotkeys[Actions.write])

    def interrupt(self) -> None:
        # TODO
        pass
