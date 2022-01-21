import enum


class Message:
    class Type(enum.Enum):
        QUEUE_EMPTY = 0
        INFO = 1
        INTERRUPT = 2
        SET_HOTKEY = 3
        HOTKEY_SET = 4
        EXIT = -1

    def __init__(self, message_type: Type = Type.INFO, text: str = '', **kwargs):
        self.type = message_type
        self.text = text
        self.kwargs = kwargs


queues: dict[str, list[Message]] = {}


def create_if_absent(queue: str):
    if queues.get(queue) is None:
        queues[queue] = []


def has_hext(queue: str) -> bool:
    create_if_absent(queue)
    if len(queues[queue]) < 1:
        return False
    else:
        return True


def read(queue: str) -> Message:
    if has_hext(queue):
        message = queues[queue][0]
        queues[queue].remove(message)
        return message
    else:
        return Message(Message.Type.QUEUE_EMPTY)


def send(message: Message, queue: str):
    create_if_absent(queue)
    queues[queue].append(message)
