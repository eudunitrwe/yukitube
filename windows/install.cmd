@echo off
rem Double-click to install YukiTube for this user.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
pause
