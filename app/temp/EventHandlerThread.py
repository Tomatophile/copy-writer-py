from threading import Thread
from typing import Callable

from app.threads import bus
from app.threads.events import ExitEvent


class EventHandlerThread(Thread):
    def __init__(self):
        super().__init__()
        self.go: bool = True
        self.handlers: dict[type, Callable] = {
            ExitEvent: self.exit
        }

    def run(self) -> None:
        try:
            self.init()
            while self.go:
                self.handle_events()
                self.loop()
        except:
            self.exit(ExitEvent())

    def init(self) -> None:
        pass

    def loop(self) -> None:
        pass

    def handle_events(self) -> None:
        event_type, event = bus.read()
        for expected_type, handler in self.handlers.items():
            if event_type == expected_type:
                handler(event)
                bus.handled(event)

    def exit(self, event: ExitEvent) -> None:
        bus.fire(event)
        self.go = False
