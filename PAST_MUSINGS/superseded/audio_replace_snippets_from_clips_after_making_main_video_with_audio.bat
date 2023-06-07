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
set   "script=!py_vs_CD!audio_replace_snippets_from_clips_after_making_main_video_with_audio.py"

set PYTHONPATH=.\Vapoursynth_x64
REM import sys
REM sys.path.insert(0,".\Vapoursynth_x64")

REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
REM You easily can edit the stuff in this area
REM
if %NUMBER_OF_PROCESSORS% LEQ 4 ( set use_cores=1 ) else ( set /a use_cores=%NUMBER_OF_PROCESSORS%/4 )

REM for %%N in ("01" "02" "03" "04" "05" "06" "07" "08" "09" "10") do (
for %%N in ("01") do (
	set "source_mp4_file=!py_vs_CD!vpy_slideshow.2022-11-Tasmania_renamed-%%~N.mp4"
	set "destination_file=!py_vs_CD!vpy_slideshow.2022-11-Tasmania_renamed-%%~N.with-background-music.mp4"
	set "snippets_file=!py_vs_CD!vpy_slideshow.2022-11-Tasmania_renamed-snippets-%%~N.txt"
	set "background_audio=!py_vs_CD!background_music_concatenated_ebur128_final.m4a"
	echo "log of %vs_path%python.exe"> "!script!.log" 2>&1
	echo "%vs_path%python.exe" "!script!" >> "!script!.log" 2>&1
	"%vs_path%python.exe" "!script!" >> "!script!.log" 2>&1
	echo. >> "!script!.log" 2>&1
	echo "%vs_path%python.exe" "!script!" -i "!source_mp4_file!" -s "!snippets_file!" -o "!destination_file!" -b "!background_audio!"  >> "!script!.log" 2>&1
	"%vs_path%python.exe" "!script!" -i "!source_mp4_file!" -s "!snippets_file!" -o "!destination_file!" -b "!background_audio!" >> "!script!.log" 2>&1
	echo. >> "!script!.log" 2>&1
)
	
pause
goto :eof
