@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM produces a video of a folder

set "vs_path=C:\SOFTWARE\Vapoursynth-x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

set "pwd=%CD%"
if /I NOT "%pwd:~-1%" == "\" (set "pwd=%pwd%\")

set   "script=%pwd%test_mediainfo.vpy"
"%vs_path%python.exe" "%script%"
REM "%vs_path%python.exe" "%script%" >"%script%.log"

pause
exit
