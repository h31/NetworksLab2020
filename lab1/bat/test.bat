@echo off
:: cd /d D:\Projects\py\NetworksLab2020\lab1\bat
start close.bat /wait
start cmd.exe /c server_start.bat
for /l %%i in (1,1,3) do start cmd.exe /c client_start.bat %%i
:: exit