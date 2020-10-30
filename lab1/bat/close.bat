@echo off
taskkill /fi "imagename eq cmd.exe" /fi "Windowtitle ne cmd.exe - taskkill*"
:: taskkill /im cmd.exe
:: exit