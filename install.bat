@echo off
pip install -r dependencies.txt
del /F LICENSE
del /F README.MD
del /F .gitignore
del /F dependencies.txt
echo You're all set, you can delete this file. To start the script open start.bat
pause