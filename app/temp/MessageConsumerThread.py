import threading
from threading import Thread
from typing import Callable

from app.threads.messages import Message, InterruptMessage


class MessageConsumerThread(Thread):
    def __init__(self, init: Callable, loop: Callable, handlers: dict[type, Callable]):
        super().__init__()
        self.go: bool = True
        self.messages: list[Message] = []
        self.init: Callable = init
        self.loop: Callable = loop
        self.handlers: dict[type, Callable] = {
            InterruptMessage: self.interrupt
        }
        self.handlers.update(handlers)

    def run(self) -> None:
        threading.Event
        self.init()
        while self.go:
            self.handle_messages()
            self.loop()

    def message(self, message: Message) -> None:
        self.messages.append(message)

    def handle_messages(self) -> None:
        for message in self.messages:
            handler = self.handlers.get(type(message))
            if handler is not None:
                handler(message)
                self.messages.remove(message)

    def interrupt(self, message: Message) -> None:
        self.go = False
