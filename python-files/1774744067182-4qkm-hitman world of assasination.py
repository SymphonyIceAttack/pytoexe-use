@echo off
start "" "D:\Games\HITMAN\Peacock\PeacockPatcher.exe"
timeout /t 5 /nobreak
start "" "D:\Games\HITMAN\Peacock\StartServer.cmd"
timeout /t 10 /nobreak
start "" "D:\Games\HITMAN\Launcher.exe"