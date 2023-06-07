@echo off
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

set "vs_CD=%CD%"
if /I NOT "%vs_CD:~-1%" == "\" (set "vs_CD=%vs_CD%\")

set "vs_temp=%vs_CD%temp"
if /I NOT "%vs_temp:~-1%" == "\" (set "vs_temp=%vs_temp%\")

set "vs_path=%vs_CD%Vapoursynth_x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

REM py_path and vs_path should ALWAYS be the same
set "py_path=%vs_path%"

set "py_exe=%py_path%python.exe"
set "ffmpeg_exe=%vs_path%ffmpeg.exe"
set "MediaInfo_exe=%vs_path%MediaInfo.exe"

set "script=.\HowToUse_MediaInfoDLL3.py"
set "f=D:\ssTEST\TEST_VIDS_IMAGES\0TEST\20221116_111821.mp4"
set "log=.\HowToUse_MediaInfoDLL3.log"

del "%log%">NUL 2>&1

echo "%MediaInfo_exe%" --help >>"%log%" 2>&1
"%MediaInfo_exe%" --help >>"%log%" 2>&1
echo.>>"%log%" 2>&1

REM --Info-Parameters Display list of Inform= parameters
echo "%MediaInfo_exe%" --Info-Parameters >>"%log%" 2>&1
"%MediaInfo_exe%" --Info-Parameters >>"%log%" 2>&1
echo.>>"%log%" 2>&1

echo "%MediaInfo_exe%" -full "%f%" >>"%log%" 2>&1
"%MediaInfo_exe%" -full "%f%" >>"%log%" 2>&1
echo.>>"%log%" 2>&1

echo.>>"%log%" 2>&1
echo "%vs_path%python.exe" "%script%" >>"%log%" 2>&1
@echo on
"%vs_path%python.exe" "%script%" >>"%log%" 2>&1
@echo off

pause
goto :eof



