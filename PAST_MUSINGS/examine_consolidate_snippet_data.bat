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
set   "script=!py_vs_CD!examine_consolidate_snippet_data.py"

set PYTHONPATH=.\Vapoursynth_x64
REM import sys
REM sys.path.insert(0,".\Vapoursynth_x64")

REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
REM You easily can edit the stuff in this area
REM
if %NUMBER_OF_PROCESSORS% LEQ 4 ( set use_cores=1 ) else ( set /a use_cores=%NUMBER_OF_PROCESSORS%/4 )

set "log=!script!.log"
del "!log!" >NUL 2>&1
echo. > "!log!" 2>&1

set "root_folder=!vs_CD!TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\"
set "root_folder_bb=!root_folder:\=\\!"

set "main_video_file=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed-CONCATENATED_NO_AUDIO.mp4"
set "main_video_file_bb=!root_folder_bb!vpy_slideshow.2022-11-Tasmania_renamed-CONCATENATED_NO_AUDIO.mp4"

set "snippets_file_list=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed.list_of_snippets_files.txt"
set "snippets_file_list_bb=!root_folder_bb!vpy_slideshow.2022-11-Tasmania_renamed.list_of_snippets_files.txt"

set "background_music=!root_folder!background_music_concatenated_ebur128_final.doubled.m4a"
set "background_music_bb=!root_folder_bb!background_music_concatenated_ebur128_final.doubled.m4a"

set "output_mp4_file=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed-CONCATENATED_WITH_AUDIO.mp4"
set "output_mp4_file_bb=!root_folder_bb!vpy_slideshow.2022-11-Tasmania_renamed-CONCATENATED_WITH_AUDIO.mp4"

set vs_CD >> "!log!" 2>&1
set py_vs_CD >> "!log!" 2>&1
set root_folder >> "!log!" 2>&1
set snippets_file >> "!log!" 2>&1
set background_music >> "!log!" 2>&1
set main_video_file >> "!log!" 2>&1
set output_mp4_file >> "!log!" 2>&1

echo. >> "!log!" 2>&1
ECHO "!snippets_file_list!" contains >> "!log!" 2>&1
type "!snippets_file_list!" >> "!log!" 2>&1
echo. >> "!log!" 2>&1

echo. >> "!log!" 2>&1
echo !DATE! !TIME! >> "!log!" 2>&1
ECHO "!py_exe!" "!script!" -i "%main_video_file_bb%" -s "%snippets_file_list_bb%" -b "%background_music_bb%" -o "%output_mp4_file_bb%" >> "!log!" 2>&1
"%vs_path%python.exe" "!script!" -i "%main_video_file_bb%" -s "%snippets_file_list_bb%" -b "%background_music_bb%" -o "%output_mp4_file_bb%" >> "!log!" 2>&1
echo !DATE! !TIME! >> "!log!" 2>&1
echo. >> "!log!" 2>&1

type "!log!"
	
pause
goto :eof

