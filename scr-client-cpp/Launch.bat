@echo off
setlocal enabledelayedexpansion

REM === Load .env file ===
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

REM === Use the variables ===


cd /d %TORCS_DIR%
start "" wtorcs.exe -r %TORCS_CONFIG%  

cd /d %CLIENT_DIR%
start "" client.exe
echo Client started.
echo %CLIENT_DIR%

