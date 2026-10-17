@echo off
rem Genera ostia.exe: un ejecutable portable que no necesita Python.
python -m pip install --quiet pyinstaller
python -m PyInstaller --onefile --name ostia ostia.py
echo.
echo Listo: dist\ostia.exe
pause