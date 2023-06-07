@echo off
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM Run the vpy_slideshow on nominated directories.
REM
REM Alternatively, roll your own by 
REM 	editing "VPY_SLIDESHOW.ini" yourself and saving it in thsi folder
REM 	and running your own VSPipe/ffmpeg a la the example method below.
REM		If you do, remember to use the VSPipe and ffmpeg in the
REM 	Vapoursynth_x64" subfolder here so that it will find both portable
REM 	vapoursynth and portable python and related imports and filters !
REM

set "vs_CD=%CD%"
if /I NOT "%vs_CD:~-1%" == "\" (set "vs_CD=%vs_CD%\")

set "vs_temp=%vs_CD%temp"
if /I NOT "%vs_temp:~-1%" == "\" (set "vs_temp=%vs_temp%\")

set "vs_path=%vs_CD%Vapoursynth_x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

REM py_path and vs_path should ALWAYS be the same
set "py_path=%vs_path%"

set "py_exe=%py_path%python.exe"
set "ffmpeg_exe=C:\SOFTWARE\ffmpeg\ffmpeg.exe"
set "mediainfo_exe=C:\SOFTWARE\ffmpeg\mediainfo.exe"

set "py_vs_CD=%vs_CD:\=\\%"

set "script=!py_vs_CD!001_preparation.py"

set PYTHONPATH=.\Vapoursynth_x64
REM import sys
REM sys.path.insert(0,".\Vapoursynth_x64")

REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
REM You easily can edit the stuff in this area
REM
if %NUMBER_OF_PROCESSORS% LEQ 2 ( set use_cores=1 ) else ( set /a use_cores=%NUMBER_OF_PROCESSORS%/2 )

set "log=!script!.log"
del "!log!" >NUL 2>&1
echo. > "!log!" 2>&1

set "root_folder=!vs_CD!"
set "root_folder_bb=!root_folder:\=\\!"

set "snippets_file_list=!root_folder!vpy_slideshow.000-tasmania-renamed.list_of_snippets_files.txt"
set "snippets_file_list_bb=!root_folder_bb!vpy_slideshow.000-tasmania-renamed.list_of_snippets_files.txt"

set "background_music=!root_folder!background_music_concatenated_ebur128_final.m4a"
set "background_music_bb=!root_folder_bb!background_music_concatenated_ebur128_final.m4a"

set "output_mp4_file=!root_folder!vpy_slideshow.000-tasmania-renamed.FINAL_MUXED.mp4"
set "output_mp4_file_bb=!root_folder_bb!vpy_slideshow.000-tasmania-renamed.FINAL_MUXED.mp4"

set vs_CD
set py_vs_CD
set root_folder
set snippets_file
set output_mp4_file


REM ECHO "%vs_path%python.exe" "!script!" >> "!log!" 2>&1
REM "%vs_path%python.exe" "!script!" >> "!log!" 2>&1

REM "%vs_path%python.exe" "!script!" -i main_video_path.mp4 -s snippets_file_list.txt -b background_music.m4a -o destination_video_path.mp4

"%py_exe%" "!script!" >> "!log!" 2>&1
	
pause
goto :eof

