import PySimpleGUI as Gui

from actions import Actions

layout = [
    [Gui.Text('Helps you to paste copied value emulating keyboard typing.')],

    [Gui.Text('Copy text to clipboard and then use write hotkey')],

    [Gui.Text('Write'),
     Gui.Text(Actions.WRITE.value,
              text_color='black',
              background_color='white',
              enable_events=True,
              key=Actions.WRITE)],

    [Gui.Text('Interrupt'),
     Gui.Text(Actions.INTERRUPT.value,
              text_color='black',
              background_color='white',
              enable_events=True,
              key=Actions.INTERRUPT)],

    [Gui.Button('Stop', key='Exit')]
]
