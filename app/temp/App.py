from typing import Callable

import PySimpleGUI as Gui

from app.layout import Actions
from app.threads import bus
from app.threads.EventHandlerThread import EventHandlerThread
from app.threads.Worker import Worker
from app.threads.events import HotkeyRecordEvent, ExitEvent, HotkeyRecordedEvent


class App(EventHandlerThread):
    def __init__(self, title: str, layout: list, params: dict):
        super().__init__()
        self.window = Gui.Window(title, layout, params)
        self.window_handlers: dict[str, Callable] = {
            None: self.window_exit,
            'Exit': self.window_exit,
            Actions.write.value: self.set_write_hotkey,
            Actions.interrupt.value: self.set_interrupt_hotkey
        }

    def init(self) -> None:
        Worker().start()
        self.handlers.update({
            HotkeyRecordedEvent: self.handle_hotkey_recorded_event
        })

    def loop(self) -> None:
        self.handle_window_events()

    def handle_hotkey_recorded_event(self, event: HotkeyRecordedEvent) -> None:
        self.window.Element(event.action.value).update(event.hotkey)

    def handle_window_events(self) -> None:
        event_type, event = self.window.read(100, ('Timeout', None))
        for expected_type, handler in self.window_handlers.items():
            if event_type == expected_type:
                handler(event)

    def window_exit(self, event) -> None:
        self.exit(ExitEvent())

    def set_write_hotkey(self, event) -> None:
        self.window.Element(Actions.write.value).update('...')
        bus.fire(HotkeyRecordEvent(Actions.write))

    def set_interrupt_hotkey(self, event) -> None:
        self.window.Element(Actions.interrupt.value).update('...')
        bus.fire(HotkeyRecordEvent(Actions.interrupt))
