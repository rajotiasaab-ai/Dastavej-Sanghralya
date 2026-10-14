@echo off
title Build DOCX Database Windows Installer
cd /d "%~dp0"
python build_installer.py
pause

