@echo on
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

set "vs_CD=%CD%"
if /I NOT "%vs_CD:~-1%" == "\" (set "vs_CD=%vs_CD%\")

set "vs_temp=%vs_CD%temp"
if /I NOT "%vs_temp:~-1%" == "\" (set "vs_temp=%vs_temp%\")

set "vs_path=%vs_CD%Vapoursynth_x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

REM set "git_path=%vs_CD%PortableGit_x64"
REM if /I NOT "%git_path:~-1%" == "\" (set "git_path=%git_path%\")

REM py_path and vs_path should ALWAYS be the same as should PYTHONPATH
set "py_path=%vs_path%"
set "PYTHONPATH=%py_path%"

set "py_exe=%py_path%python.exe"
set "ffmpeg_exe=C:\SOFTWARE\ffmpeg\ffmpeg.exe"
set "mediainfo_exe=C:\SOFTWARE\ffmpeg\mediainfo.exe"

ECHO DO NOT NOT ever run this as admin %%%% or it will install python stuff into an inaccessible admin user's folder
ECHO DO NOT NOT ever run this as admin %%%% or it will install python stuff into an inaccessible admin user's folder
ECHO DO NOT NOT ever run this as admin %%%% or it will install python stuff into an inaccessible admin user's folder

IF NOT EXIST "%vs_CD%wget.exe" (
	echo Also, Please download wget.exe into this folder "%vs_CD%" first.
	echo Exiting without success.
	pause
	exit
)

CD "%vs_CD%"

set "INPUT_FOLDER=D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\0-CONVERTED-SLIDESHOW\selected-music"
set "OUTPUT_FOLDER=D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\0-CONVERTED-SLIDESHOW\selected-music\concatenated"
set TARGET_LOUDNESS=-16
set "fdk=-c:a libfdk_aac -b:a 256k -ar 48000"

if not exist "%OUTPUT_FOLDER%" mkdir "%OUTPUT_FOLDER%"

REM Delete and previously exist existing intermediate and output files from a previous run
del "%OUTPUT_FOLDER%\*_ebur128.m4a" 2>NUL
del "%OUTPUT_FOLDER%\background_music_concatenated_ebur128.txt" 2>NUL
del "%OUTPUT_FOLDER%\background_music_concatenated_ebur128_final.m4a" 2>NUL

REM level using ebur128
for %%I in ("%INPUT_FOLDER%\*.m4a") do (
  "%ffmpeg_exe%" -hide_banner -loglevel info -nostats -threads 1 -i "%%I" -af "ebur128=peak=true:target=!TARGET_LOUDNESS!:dualmono=true" !fdk! -y "%OUTPUT_FOLDER%\%%~nI_ebur128.m4a"
)

rem Concatenate the EBU R128 normalized files.
REM do it 5 times so we get a nice loong backgruond music
@echo off
del "%OUTPUT_FOLDER%\background_music_concatenated_ebur128.txt" 2>NUL
FOR %%H in (1 2 3 4 5) do (
(for %%I in ("%OUTPUT_FOLDER%\*_ebur128.m4a") do (
  echo file '%%~fI'
))
) >> "%OUTPUT_FOLDER%\background_music_concatenated_ebur128.txt"
@echo on
type "%OUTPUT_FOLDER%\background_music_concatenated_ebur128.txt"

"%ffmpeg_exe%" -hide_banner -loglevel info -stats -f concat -safe 0 -threads 1 -i "%OUTPUT_FOLDER%\background_music_concatenated_ebur128.txt" !fdk! -y "%OUTPUT_FOLDER%\background_music_concatenated_ebur128_final.m4a"

del "%OUTPUT_FOLDER%\*_ebur128.m4a" 2>NUL
del "%OUTPUT_FOLDER%\background_music_concatenated_ebur128.txt" 2>NUL

pause

exit


REM -------------------------------

to re-mux audio with trimming and silence padding as required:

ffmpeg -i video.mp4 -i audio.m4a 
-filter_complex "[1:a]adelay=0|0,apad=whole_dur=video_duration[audio];[audio]atrim=0:[video_duration],asetpts=PTS-STARTPTS[volume_adjusted_audio]" 
-map 0:v -map "[volume_adjusted_audio]" 
-c:v copy -c:a libfdk_aac -b:a 256k -ar 48000 final.mp4
```

1. `[1:a]adelay=0|0,apad=whole_dur=video_duration[audio]`
	This part of the command delays the audio stream by 0 milliseconds using `adelay` 
	and pads it with silence until its duration matches the duration of the video using `apad`. 
	If the audio is already longer than the video, the `apad` filter will not add any additional silence 
	since there is no need for padding. 
	The resulting audio stream is labeled `[audio]`.

2. `[audio]atrim=0:[video_duration],asetpts=PTS-STARTPTS[volume_adjusted_audio]`
	This section applies the `atrim` filter to trim the audio stream to match the duration of the video. 
	Since the audio is longer than the video, the `atrim` filter will trim the audio stream, 
	starting from the beginning (`0`) and ending at the duration of the video (`[video_duration]`). 
	The `asetpts=PTS-STARTPTS` filter ensures that the trimmed audio stream's timestamps are reset to start from 0. 
	The modified audio stream is labeled `[volume_adjusted_audio]`.

3. `-map 0:v -map "[volume_adjusted_audio]"`
	This part ensures that the video stream from the first input (`video.mp4`) 
	and the modified audio stream `[volume_adjusted_audio]` 
	are included in the output.

4. `-c:v copy -c:a libfdk_aac -b:a 256k -ar 48000`
	This specifies that the video stream should be copied without re-encoding (`copy`), 
	while the audio stream should be encoded by libfdk_aac as `aac`. 
	It also sets the audio bitrate to 256k and the audio sampling rate to 48000 Hz.

5. `final.mp4` is the name of the output file.

With this command, you can achieve the desired result of 
padding the audio with silence if it's shorter than the video and 
trimming the audio if it's longer than the video, 
all while preserving the video quality.
