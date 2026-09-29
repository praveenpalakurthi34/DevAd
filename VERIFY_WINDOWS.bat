@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0VERIFY_WINDOWS.ps1"
if errorlevel 1 pause
