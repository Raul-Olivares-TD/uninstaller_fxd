@echo off
timeout /t 2 /nobreak >nul
if "%~1"=="" (
    del "%~f0"
    exit /b 1
)
rmdir /s /q "%~1"
del "%~f0"