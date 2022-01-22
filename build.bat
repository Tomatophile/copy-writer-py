set artifactId=copy-writer
set version=1.0.0

set buildName=%artifactId%-%version%

pyinstaller -F --specpath ./dist  -n %buildName% -w  --clean .\src\main.py