@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions


set "vs_CD=%CD%"
if /I NOT "%vs_CD:~-1%" == "\" (set "vs_CD=%vs_CD%\")
set "pwd=%vs_CD%"

set "vs_temp=%vs_CD%temp"
if /I NOT "%vs_temp:~-1%" == "\" (set "vs_temp=%vs_temp%\")

set "vs_path=%vs_CD%Vapoursynth_x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

REM py_path and vs_path should ALWAYS be the same
set "py_path=%vs_path%"

set "py_exe=%py_path%python.exe"
set "ffmpeg_exe=%vs_path%ffmpeg.exe"
set "ffprobe_exe=%vs_path%ffprobe.exe"

set "script=%pwd%show_unique_properties.vpy"
set "log=%script%.log"

REM "%vs_path%python.exe" "%script%" "[ 'D:\\ssTEST\\TEST_VIDS_IMAGES\\0TEST', ]"  >>"%log%"
REM "%vs_path%python.exe" "%script%" "[ 'E:\\MULTIMEDIA', ]"  >>"%log%" 2>&1
"%vs_path%python.exe" "%script%"  >"%log%" 2>&1
dir "%log%"


REM find unique occurrences of interesting properties in the fields of interest
REM https://www.computerhope.com/findstr.htm#:~:text=The%20findstr%20(short%20for%20find,specific%20string%20of%20plain%20text.

call :find_unique_thing "codec_name"
call :find_unique_thing "color_space"
call :find_unique_thing "color_matrix"
call :find_unique_thing "color_transfer"
call :find_unique_thing "color_primaries"
call :find_unique_thing "color_range"
call :find_unique_thing "field_order"
call :find_unique_thing "pix_fmt"
call :find_unique_thing "probe_score"
call :find_unique_thing "chroma_location"
call :find_unique_thing "frame_rate"
call :find_unique_thing "r_frame_rate"
call :find_unique_thing "avg_frame_rate"
call :find_unique_thing "rotation"
call :find_unique_thing "FrameRate_Mode"
call :find_unique_thing "ERROR"

pause
goto :eof


:find_unique_thing
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
echo.
set "f=%~1"
set "f=%f: =%"
set "f=%f:'=%"
set "f=%f:"=%"
set "f=%f:/=%"
set "f=%f:\=%"
set "f=%script%.unique.%f%.log"
@echo on
findstr /L /I /c:"%~1" "%log%" | sort /unique > "%f%"
@echo off
echo Unique "%~1"
type "%f%"
echo.
goto :eof

