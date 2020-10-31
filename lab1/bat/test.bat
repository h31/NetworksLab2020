@echo off
start close.bat /wait
start cmd.exe /k server_start.bat
for /l %%i in (1,1,3) do start cmd.exe /k client_start.bat %%i