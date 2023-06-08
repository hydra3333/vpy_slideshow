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


cd 

dir /b *load*.py

echo %PYTHONPATH%

set "script=.\do_test_load_settings_3333.py"
"!python_exe!" "!script!"

pause
exit


I have portable python installed and use PYTHONPATH environment variable to point to it.
In a different folder "D:\ssTEST\" I have 2 files: do_test_load_settings_3333.py and load_settings_3333.py
do_test_load_settings_3333.py has this line 'import load_settings_3333' and yet it fails:

Traceback (most recent call last):
  File "D:\ssTEST\do_test_load_settings_3333.py", line 29, in <module>
    import load_settings_3333
ModuleNotFoundError: No module named 'load_settings_3333'

why ?
