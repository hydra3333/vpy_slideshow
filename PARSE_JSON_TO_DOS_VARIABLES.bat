@echo on
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

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

set PYTHONPATH=.\Vapoursynth_x64
REM import sys
REM sys.path.insert(0,".\Vapoursynth_x64")


set "f=.\a.json"
set "f_bb=!f:\=\\!"
del /f "!f!"
echo { >> "!f!"
echo "var_a" : "Content for variable a", >> "!f!"
echo "var_20" : 20, >> "!f!"
echo "var_21" : 20.1, >> "!f!"
echo "var_true" : true, >> "!f!"
echo "var_false" : false, >> "!f!"
echo "var_list" : [ false, true, "a", 1, 2, 2.5 ] >> "!f!"
echo } >> "!f!"

REM use Powershell to Parse a .JSON file and put the top-level of it into ODS variables having the names of the keys.

set "j=.\json_to_environment.py"
set "j_bb=!j:\=\\!"
set "b=.\json_to_environment_run_after_the_py.bat"
set "b_bb=!j:\=\\!"
del /f "!j!"
del /f "!b!"
echo import json >> "!j!"
echo import os >> "!j!"
echo json_file = r'!f!' >> "!j!"
echo bat_file = r'!b!' >> "!j!"
echo with open(json_file) as file: >> "!j!"
echo     data = json.load(file) >> "!j!"
echo with open(bat_file, 'w') as file: >> "!j!"
echo     file.write(f'@echo off\n') >> "!j!"
echo     for key, value in data.items(): >> "!j!"
echo         if isinstance(value, list): >> "!j!"
echo             value_string = '[' + (', '.join('"' + str(item) + '"' if isinstance(item, str) else str(item) for item in value)) + ']' >> "!j!"
echo         else: >> "!j!"
echo             value_string = '"' + str(value) + '"' if isinstance(value, str) else str(value) >> "!j!"
echo         file.write(f'set "{key}={value_string}"\n') >> "!j!"
echo     file.write(f'goto :eof\n') >> "!j!"
echo #print(f'{bat_file} generated.') >> "!j!"
@echo on

dir /b "!j!"
type "!j!"

"!python_exe!" "!j!"

dir /b "!b!"
type "!b!"

call "!b!"
REM del /f "!j!"
REM del /f "!b!"
echo call "!b!" yielded:
echo var_a: !var_a!
echo var_20: !var_20!
echo var_21: !var_21!
echo var_true: !var_true!
echo var_false: !var_false!
echo var_list: !var_list!
set var_

pause
goto :eof
