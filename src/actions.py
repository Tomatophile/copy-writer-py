import enum


class Actions(enum.Enum):
    WRITE = 'ctrl+shift+right'
    INTERRUPT = 'end' #TODO - Need constraint for single keys
