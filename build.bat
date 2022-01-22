set version=1.0.0

pyinstaller -F --specpath .\build\%version% -n copy-writer-%version%  --clean .\app\main.py