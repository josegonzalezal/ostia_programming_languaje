#!/usr/bin/env sh
# Genera ./dist/ostia: un ejecutable portable que no necesita Python.
python3 -m pip install --quiet pyinstaller
python3 -m PyInstaller --onefile --name ostia ostia.py
echo
echo "Listo: dist/ostia"
