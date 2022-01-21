from app.layout import Actions


class Event(object):
    pass


class ExitEvent(Event):
    pass


class HotkeyRecordEvent(Event):
    def __init__(self, action: Actions):
        self.action = action


class HotkeyRecordedEvent(Event):
    def __init__(self, action: Actions, hotkey: str):
        self.action = action
        self.hotkey = hotkey
