@echo off
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

if %NUMBER_OF_PROCESSORS% LEQ 2 ( set use_cores=1 ) else ( set /a use_cores=%NUMBER_OF_PROCESSORS%/2 )

set "vs_CD=%CD%"
if /I NOT "%vs_CD:~-1%" == "\" (set "vs_CD=%vs_CD%\")
set "vs_CD_bb=%vs_CD:\=\\%"

set "vs_path=%vs_CD%Vapoursynth_x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")
set "vs_path_bb=%vs_path:\=\\%"

set "vs_temp=%vs_CD%temp"
if /I NOT "%vs_temp:~-1%" == "\" (set "vs_temp=%vs_temp%\")
set "vs_temp_bb=%vs_temp:\=\\%"

REM py_path and vs_path should ALWAYS be the same
set "py_path=%vs_path%"

REM ffmpeg and mediainfo exes located elsewhere are more up to date
set "python_exe=%py_path%python.exe"
set "ffmpeg_exe=C:\SOFTWARE\ffmpeg\ffmpeg.exe"
set "mediainfo_exe=C:\SOFTWARE\ffmpeg\mediainfo.exe"

set "PYTHONPATH=.\Vapoursynth_x64"
REM import sys
REM sys.path.insert(0,".\Vapoursynth_x64")

REM
REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
REM

@ECHO ON

set "script=.\slideshow_CONTROLLER.py"
set "log=!script!.log"
del /f "!log!"

REM del /f .\slideshow_settings.py
REM copy /y ".\slideshow_settings_template.py" ".\slideshow_settings.py"

REM echo type ".\slideshow_settings.py" >>"!log!" 2>&1
REM type ".\slideshow_settings.py" >>"!log!" 2>&1
REM type ".\slideshow_settings.py"

rem echo "!python_exe!" "!script!" >>"!log!" 2>&1
"!python_exe!" "!script!" >>"!log!" 2>&1

REM "D:\ssTEST\Vapoursynth_x64\vspipe.exe" --progress --filter-time --container y4m ".\slideshow_ENCODER_legacy.vpy" NUL  >>"!log!" 2>&1


type "!log!"

pause
exit

