from app.threads.events import Event

events: list[(type, Event)] = []


def fire(event: Event) -> None:
    events.append((type(event), event))


def read() -> (type, Event):
    if len(events) < 1:
        return None, None
    return events[0]


def handled(event: Event) -> None:
    events.remove((type(event), event))
