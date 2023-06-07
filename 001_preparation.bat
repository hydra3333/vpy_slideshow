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

set PYTHONPATH=.\Vapoursynth_x64
REM import sys
REM sys.path.insert(0,".\Vapoursynth_x64")

REM
REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
REM

set "script_filename=001_preparation.py"

set "script=!vs_CD!!script_filename!"
set "script_bb=!script:\=\\!"

set "PIC_EXTENSIONS=".png", ".jpg", ".jpeg", ".gif""
set "VID_EXTENSIONS=".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov""
set "EEK_EXTENSIONS=".m2ts""
set "VID_EEK_EXTENSIONS=!VID_EXTENSIONS! , !VID_EXTENSIONS!"
set "EXTENSIONS=!PIC_EXTENSIONS! , !VID_EXTENSIONS! , !EEK_EXTENSIONS!"


set "log=!script!.log"
del /F /Q "!log!" >NUL 2>&1
echo. !DATE! !TIME! log of running !script! > "!log!" 2>&1

set "root_folder_sources_list_for_images_pics=[ "D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\ORIGINALS\01", "D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\ORIGINALS\02" ]"
set "root_folder_sources_list_for_images_pics_bb=!root_folder_sources_list_for_images_pics:\=\\!"

set "root_folder_for_outputs=!vs_CD!"
set "root_folder_for_outputs_bb=!root_folder_for_outputs:\=\\!"

set "preparation_json_input_file=!root_folder_for_outputs!!script_filename!.json"
set "preparation_json_input_file_bb=!preparation_json_input_file:\=\\!"

REM the next one will be used by this python to create sequential chunks files named: "!chunks_files_common_name!_00001.json" etc
set "all_chunks_output_file=!root_folder_for_outputs!!script_filename!.chunks.json"
set "all_chunks_output_file_bb=!all_chunks_output_file:\=\\!"

REM and this one will be used to save files ready for the .bat FOR loop/ the script will add a 5 nigit number and ".json"
set "chunks_output_files_common_name=!root_folder_for_outputs!!script_filename!.chunk_"
set "chunks_output_files_common_name_bb=!chunks_output_files_common_name:\=\\!"

REM and this one will be used to iterate through those files in a .bat FOR loop
set "chunks_output_files_common_name_glob=!root_folder_for_outputs!!script_filename!.chunk_*.json"
set "chunks_output_files_common_name_glob_bb=!chunks_output_files_common_name_glob:\=\\!"

set "snippets_output_file_list=!root_folder_for_outputs!!script_filename!.list_of_snippets_files.txt"
set "snippets_output_file_list_bb=!snippets_output_file_list:\=\\!"

set "background_audio_input=!root_folder_for_outputs!background_music_concatenated_ebur128_final.doubled.m4a"
set "background_audio_input_bb=!background_audio_input:\=\\!"

set "final_output_mp4_file=!root_folder_for_outputs!vpy_slideshow.000-tasmania-renamed.FINAL_MUXED.mp4"
set "final_output_mp4_file_bb=!final_output_mp4_file:\=\\!"

set "temp_folder=!vs_temp!"
set "temp_folder_bb=!temp_folder:\=\\!"

set "FFMPEG_PATH=!ffmpeg_exe!"
set "FFMPEG_PATH_bb=!ffmpeg_exe:\=\\!"

REM lowerecase for true and false or json crashes
set MAX_VIDEO_FILES_PER_CHUNK=150
set TOLERANCE_PERCENT_FINAL_CHUNK=20
set RECURSIVE=true
set DEBUG=true

echo. >> "!log!" 2>&1
set vs_ >> "!log!" 2>&1
set py_ >> "!log!" 2>&1
set ffmpeg_exe >> "!log!" 2>&1
set mediainfo_exe >> "!log!" 2>&1
set root_folder_sources_list_for_images_pics >> "!log!" 2>&1
set preparation_json_input_file >> "!log!" 2>&1
set all_chunks_output_file >> "!log!" 2>&1
set chunks_output_files_common_name >> "!log!" 2>&1
set snippets_output_file_list >> "!log!" 2>&1
set background_audio_input >> "!log!" 2>&1
set final_output_mp4_file >> "!log!" 2>&1
set PIC_EXTENSIONS >> "!log!" 2>&1
set VID_EXTENSIONS >> "!log!" 2>&1
set EEK_EXTENSIONS >> "!log!" 2>&1
set VID_EEK_EXTENSIONS >> "!log!" 2>&1
set EXTENSIONS >> "!log!" 2>&1
set MAX_VIDEO_FILES_PER_CHUNK >> "!log!" 2>&1
set TOLERANCE_PERCENT_FINAL_CHUNK >> "!log!" 2>&1
echo. >> "!log!" 2>&1

goto :looping

echo del /F "!preparation_json_input_file!" >> "!log!" 2>&1
del /F "!preparation_json_input_file!" >> "!log!" 2>&1
echo { >> "!preparation_json_input_file!"
echo "this_json_file" : "!preparation_json_input_file_bb!", >> "!preparation_json_input_file!"
echo "root_folder_sources_list_for_images_pics" : !root_folder_sources_list_for_images_pics_bb!, >> "!preparation_json_input_file!"
echo "root_folder_for_outputs" : "!root_folder_for_outputs_bb!", >> "!preparation_json_input_file!"
echo "all_chunks_output_file" : "!all_chunks_output_file_bb!", >> "!preparation_json_input_file!"
echo "chunks_output_files_common_name" : "!chunks_output_files_common_name_bb!", >> "!preparation_json_input_file!"
echo "chunks_output_files_common_name_glob" : "!chunks_output_files_common_name_glob_bb!", >> "!preparation_json_input_file!"
echo "snippets_output_file_list" : "!snippets_output_file_list_bb!", >> "!preparation_json_input_file!"
echo "background_audio_input" : "!background_audio_input_bb!", >> "!preparation_json_input_file!"
echo "final_output_mp4_file" : "!final_output_mp4_file_bb!", >> "!preparation_json_input_file!"
echo "temp_folder" : "!temp_folder_bb!", >> "!preparation_json_input_file!"
echo "PIC_EXTENSIONS" : [ !PIC_EXTENSIONS! ], >> "!preparation_json_input_file!"
echo "VID_EXTENSIONS" : [ !VID_EXTENSIONS! ], >> "!preparation_json_input_file!"
echo "EEK_EXTENSIONS" : [ !EEK_EXTENSIONS! ], >> "!preparation_json_input_file!"
echo "VID_EEK_EXTENSIONS" : [ !VID_EEK_EXTENSIONS! ], >> "!preparation_json_input_file!"
echo "EXTENSIONS" : [ !EXTENSIONS! ], >> "!preparation_json_input_file!"
echo "MAX_VIDEO_FILES_PER_CHUNK" : !MAX_VIDEO_FILES_PER_CHUNK!, >> "!preparation_json_input_file!"
echo "TOLERANCE_PERCENT_FINAL_CHUNK" : !TOLERANCE_PERCENT_FINAL_CHUNK!, >> "!preparation_json_input_file!"
echo "RECURSIVE" : !RECURSIVE!, >> "!preparation_json_input_file!"
echo "FFMPEG_PATH" : "!FFMPEG_PATH_bb!", >> "!preparation_json_input_file!"
REM this must be the LAST item in the json since it has no comma on the end
echo "DEBUG" : !DEBUG! >> "!preparation_json_input_file!"
echo } >> "!preparation_json_input_file!"

echo. >> "!log!" 2>&1
echo TYPE "!preparation_json_input_file!" >> "!log!" 2>&1
TYPE "!preparation_json_input_file!" >> "!log!" 2>&1
echo. >> "!log!" 2>&1

echo del /F "!all_chunks_output_file!" >> "!log!" 2>&1
del /F "!all_chunks_output_file!" >> "!log!" 2>&1
echo. >> "!log!" 2>&1

echo del /F "!chunks_output_files_common_name_glob!" >> "!log!" 2>&1
del /F "!chunks_output_files_common_name_glob!" >> "!log!" 2>&1
echo. >> "!log!" 2>&1

echo. >> "!log!" 2>&1
echo "!python_exe!" "!script!" -p "!preparation_json_input_file!" >> "!log!" 2>&1
"!python_exe!" "!script!" -p "!preparation_json_input_file!"  >> "!log!" 2>&1
echo. >> "!log!" 2>&1

REM echo. >> "!log!" 2>&1
REM echo TYPE "!preparation_json_input_file!" >> "!log!" 2>&1
REM TYPE "!preparation_json_input_file!" >> "!log!" 2>&1
REM echo. >> "!log!" 2>&1

REM echo. >> "!log!" 2>&1
REM echo TYPE "!all_chunks_output_file!">> "!log!" 2>&1
REM TYPE "!all_chunks_output_file!">> "!log!" 2>&1
REM echo. >> "!log!" 2>&1

REM echo. >> "!log!" 2>&1
REM echo. Individual Chunk files:>> "!log!" 2>&1
REM echo. >> "!log!" 2>&1
REM echo TYPE "!chunks_output_files_common_name_glob!">> "!log!" 2>&1
REM TYPE "!chunks_output_files_common_name_glob!">> "!log!" 2>&1
REM echo. >> "!log!" 2>&1
REM echo. >> "!log!" 2>&1

echo. >> "!log!" 2>&1
echo Loop through the .json chunk files and tun the script for each, to create slideshow chunks >> "!log!" 2>&1
echo. >> "!log!" 2>&1
echo. >> "!log!" 2>&1

:looping

echo Start of processing chunk files >> "!log!" 2>&1
dir /b
for /f "delims=" %%F in ('dir /b /a-d /on "!chunks_output_files_common_name_glob!"') do (
	set "FullFile=%%~fF
	set "FullFile=%%~dpnxF
    set "disk=%%~dF"
    set "Directory=%%~pF"
    set "File=%%~nF"
    set "Extension=%%~xF"
    set "diskDirectory=%%~dpF"
    set "diskDirectoryFile=%%~dpnF"
	
	set "current_chunk_file=!FullFile!"
	set "current_chunk_fixed_file=!diskDirectory!chunk_fixed_filename.json"
	
	echo current_chunk_file=!current_chunk_file!
	echo current_chunk_fixed_file=!current_chunk_fixed_file!
	
	echo dir /b "!FullFile!"
	dir /b "!FullFile!"
	echo dir /b "!current_chunk_file!"
	dir /b "!current_chunk_file!"
	echo.
	echo copy /y /v "!current_chunk_file!" "!current_chunk_fixed_file!"
	copy /y /v "!current_chunk_file!" "!current_chunk_fixed_file!"
	echo.

	REM echo "Creating slideshow video chunk based on Chunk file, and creating a related snippets ffmpeg_exe ..."
)
echo End of processing chunk files >> "!log!" 2>&1

@ECHO off

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
REM echo         if isinstance(value, list): >> "!j!"
REM echo             value_string = '[' + (', '.join(str(item) for item in value)) + ']' >> "!j!"
REM echo         else: >> "!j!"
REM echo             value_string =  str(value) >> "!j!"
echo         if isinstance(value, list): >> "!j!"
echo             value_string = '[' + (', '.join('"' + str(item) + '"' if isinstance(item, str) else str(item) for item in value)) + ']' >> "!j!"
echo         else: >> "!j!"
echo             value_string = '"' + str(value) + '"' if isinstance(value, str) else str(value) >> "!j!"
echo         file.write(f'set "{key}={value_string}"\n') >> "!j!"
echo     file.write(f'goto :eof\n') >> "!j!"
echo #print(f'{bat_file} generated.') >> "!j!"
@echo on

type "!f!"

type !j!"
"!python_exe!" "!j!"
type "!b!"

call "!b!"
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

import json
import os

json_file = r'.\a.json'
bat_file = r'.\json_to_environment_run_after_the_py.bat'
with open(json_file) as file:
    data = json.load(file)
with open(bat_file, 'w') as file:
    file.write('@echo off\n')
    for key, value in data.items():
        if isinstance(value, list):
            value_string = '[' + (', '.join('"' + str(item) + '"' if isinstance(item, str) else str(item) for item in value)) + ']'
        else:
            value_string = '"' + str(value) + '"' if isinstance(value, str) else str(value)
        file.write(f'set "{key}={value_string}"\n')
    file.write('goto :eof\n')

# Call the generated .bat file
os.system(bat_file)

