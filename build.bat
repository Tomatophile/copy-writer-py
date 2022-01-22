set artifactId=copy-writer
set version=1.0.1

set buildName=%artifactId%-%version%

pyinstaller -F --specpath ./dist/%version%  -n %buildName% -w --distpath ./dist/%version%  --clean .\src\main.py