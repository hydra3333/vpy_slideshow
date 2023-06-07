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
set "ffmpeg_exe=%vs_path%ffmpeg.exe"

set "PYTHONPATH=!vs_path!"

REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
REM You easily can edit the stuff in this area
REM
if %NUMBER_OF_PROCESSORS% LEQ 4 ( set use_cores=1 ) else ( set /a use_cores=%NUMBER_OF_PROCESSORS%/4 )
REM
REM bitrates seem to average out at 3Mbs
set bv=4000000
set bv_min=2000000
set bv_max=10000000
set bv_buf=10000000

rem "directory_list" 			a list of quoted paths (double-backslashed) separated by commas; .\\ by itself means current default path
rem "temp_directory_list"		a list of paths (for coding convenience) however only the first path in the list will be used
rem "recursive"					is true or false; if true, it also walks the sub-directory tree(s) looking for images/videos
rem "duration_pic_sec"			a real number; the number of seconds a pic is displayed in trhe slideshow
rem duration_max_video_sec"		a real number; the maximum number of seconds a video runs before it is clipped off
rem "subtitle_depth" 			an integer; it makes subtitles with the path/filename of the image/video from the right up to the nominated depth; 0 turns it off
rem "debug_mode"				is true or false; if true, an unbelievable volume of debug messages will appear for debugging (to stderr)
rem "silent_mode"				is true or false; if true, no status messages are produced (to stderr)

REM **********
REM This .bat does NOT do looping to encode intermediate ffv1 files and transcode them into a single .mp4.
REM Instead, it just encodes one slideshow directly into a .mp4.  
REM See the Tassie .bat for an incomplete example with looping.
REM **********

REM no _bb for files not going into python
set   "script=%vs_CD%vpy_slideshow.vpy"
set "ini_file=%vs_CD%SLIDESHOW_PARAMETERS.ini"
set "log_file=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed.log"
set "snippets_file_list=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed.list_of_snippets_files.txt"
set "video_mkv_file_list=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed.video_mkv_file_list.txt"
set "concatenated_output_mp4_file=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed-CONCATENATED_NO_AUDIO.mp4"

set "root_folder=!vs_CD!TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\"
REM input files/folders to python need _bb
set "root_folder_bb=!root_folder:\=\\!"

set "directories='D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\01', 'D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\02'"
REM input files/folders to python need _bb
set "directories_bb=!temp_directory:\=\\!"

set "temp_directory='.\temp'"
if not exist "!temp_directory!" (
	mkdir "!temp_directory!"
	echo Folder !temp_directory! created successfully.
)
REM input files/folders to python need _bb
set "temp_directory_bb=!temp_directory:\=\\!"

set "snippets_file=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed.snippets.txt"
REM input files/folders to python need _bb
set "snippets_file_bb=!snippets_file:\=\\!"

set "snippets_file_list=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed.snippets.txt"
REM input files/folders to python need _bb
set "snippets_file_list_bb=!snippets_file_list:\=\\!"

set "intermediate_output_mkv_file=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed.mkv"
REM input files/folders to python need _bb
set "intermediate_output_mkv_file_bb=!intermediate_output_mkv_file:\=\\!"

set "intermediate_output_mkv_file_list=!root_folder!vpy_slideshow.2022-11-Tasmania_renamed.mkv"
REM input files/folders to python need _bb
set "intermediate_output_mkv_file_list_bb=!intermediate_output_mkv_file_list:\=\\!"

del /f /q "!snippets_file!" >NUL 2>&1
del /f /q "!snippets_file_list!" >NUL 2>&1
del /f /q "!intermediate_output_mkv_file!" 2>NUL
del /f /q "!intermediate_output_mkv_file_list!" 2>NUL
del /f /q "!log_file!">NUL 2>&1
del /f /q "!ini_file!">NUL 2>&1

echo ------------------------ START encode single slideshow  ------------ >> "!log_file!" 2>&1
REM This .bat does NOT do looping to encode intermediate ffv1 files and transcode them into a single .mp4.
REM Instead, it just encodes one slideshow directly into a .mp4.  
REM snippets_file_list and intermediate_output_mkv_file_list are useless outputs from single slideshow
REM since these lists will contain a single filename,
REM however one or more are needed for a later step which caters for other bats which do looping
REM so keep the names as if we were (i.e. mkv rather than mp4)
echo. >> "!log_file!" 2>&1
echo script=!script! >> "!log_file!" 2>&1
echo ini_file=!ini_file! >> "!log_file!" 2>&1
echo log_file=!log_file! >> "!log_file!" 2>&1
echo directories=!directories! >> "!log_file!" 2>&1
echo temp_directory=!temp_directory! >> "!log_file!" 2>&1
echo snippets_file=!snippets_file! >> "!log_file!" 2>&1
echo snippets_file_list=!snippets_file_list! >> "!log_file!" 2>&1
echo intermediate_output_mkv_file=!intermediate_output_mkv_file! >> "!log_file!" 2>&1
echo intermediate_output_mkv_file_list=!intermediate_output_mkv_file_list! >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1

IF NOT EXIST "%ini_file%" (
	echo [slideshow] >>"%ini_file%"
	echo directory_list = [ !directories_bb! ] >>"%ini_file%"
	echo temp_directory_list = [ !temp_directory_bb! ]  >>"%ini_file%"
	echo snippets_filename_path_list = ['!snippets_file_bb!',] >>"%ini_file%"
	echo intermediate_output_mkv_filename_path_list = ['!intermediate_output_mkv_file_bb!',] >>"%ini_file%"
	echo recursive = True >>"%ini_file%"
	echo duration_pic_sec = 3.0 >>"%ini_file%"
	echo duration_max_video_sec = 120.0 >>"%ini_file%"
	echo duration_crossfade_secs = 0.5 >>"%ini_file%"
	echo subtitle_depth = 0 >>"%ini_file%"
	echo debug_mode = False >>"%ini_file%"
	echo silent_mode = False >>"%ini_file%"
	REM echo crossfade_type = none >>"%ini_file%"
	echo crossfade_type = random >>"%ini_file%"
	REM echo crossfade_type = fade >>"%ini_file%"
	REM echo crossfade_type = wipe >>"%ini_file%"
	REM echo crossfade_type = slide_expand >>"%ini_file%"
	REM echo crossfade_type = squeeze_slide >>"%ini_file%"
	REM echo crossfade_type = squeeze_expand >>"%ini_file%"
	REM echo crossfade_type = reveal >>"%ini_file%"
	REM echo crossfade_type = curtain_cover >>"%ini_file%"
	REM echo crossfade_type = curtain_reveal >>"%ini_file%"
	REM REM echo crossfade_type = pixellate >>"%ini_file%"
	REM echo crossfade_type = cube_rotate >>"%ini_file%"
	echo crossfade_direction = left >>"%ini_file%"
	REM echo crossfade_direction = right >>"%ini_file%"
	REM echo crossfade_direction = up >>"%ini_file%"
	REM echo crossfade_direction = down >>"%ini_file%"
	REM echo crossfade_direction = horizontal >>"%ini_file%"
	REM echo crossfade_direction = vertical >>"%ini_file%"
	echo type "%ini_file%" >> "!log_file!" 2>&1
	type "%ini_file%" >> "!log_file!" 2>&1
)

REM ---------------------------------------------------------------------------------------------------------------





REM ---------------------------------------------------------------------------------------------------------------

goto :eof
REM if it gets here then there e is something wrong

REM This .bat does NOT do looping to encode intermediate ffv1 files and transcode them into a single .mp4.
REM Instead, it just encodes one slideshow directly into a .mp4.

REM This bit of code is retained ONLY as an example of what encoding to ffv1 looks like if you put it and the above in a single loop.

echo. >> "!log_file!" 2>&1
echo ********** start process of encoding into an intermediate ffv1: >> "!log_file!" 2>&1
set "cmd_vspipe="
set "cmd_vspipe=%cmd_vspipe%"%vs_path%VSPipe.exe" --progress --container y4m "%script%" - "

set "cmd_ffmpeg="
set "cmd_ffmpeg="%ffmpeg_exe%" "
set "cmd_ffmpeg=%cmd_ffmpeg% -hide_banner -loglevel info -nostats -threads %use_cores% "
set "cmd_ffmpeg=%cmd_ffmpeg% -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc "
set "cmd_ffmpeg=%cmd_ffmpeg% -f yuv4mpegpipe -i pipe: "
set "cmd_ffmpeg=%cmd_ffmpeg% -probesize 200M -analyzeduration 200M "
set "cmd_ffmpeg=%cmd_ffmpeg% -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
set "cmd_ffmpeg=%cmd_ffmpeg% -filter_complex "format=yuv420p,setdar=16/9" "
set "cmd_ffmpeg=%cmd_ffmpeg% -c:v ffv1 -level 3 -coder 1 -context 1 -slicecrc 1 "
set "cmd_ffmpeg=%cmd_ffmpeg% -an "
set "cmd_ffmpeg=%cmd_ffmpeg% -y "%intermediate_output_mkv_file%" "

echo. >> "!log_file!" 2>&1
echo cmd_vspipe=%cmd_vspipe%>> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1
echo cmd_ffmpeg=%cmd_ffmpeg%>> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1
@echo on
echo !DATE! !TIME! STARTING FFMPEG ENCODE USING "!script!" TO INTERMEDIATE ffv1 video file "%intermediate_output_mkv_file%" >> "!log_file!" 2>&1
%cmd_vspipe% | %cmd_ffmpeg%>> "!log_file!" 2>&1
@echo off
echo !DATE! !TIME! FINISHED FFMPEG ENCODE USING "!script!" TO INTERMEDIATE ffv1 video file "%intermediate_output_mkv_file%" >> "!log_file!" 2>&1

echo. >> "!log_file!" 2>&1
echo Adding "!snippets_file!" to "!snippets_file_list!" >> "!log_file!" 2>&1
echo !snippets_file!>>"!snippets_file_list!"
echo. >> "!log_file!" 2>&1
echo Adding "file '!intermediate_output_mkv_file!'" to "!video_mkv_file_list!" >> "!log_file!" 2>&1
echo file '!intermediate_output_mkv_file!'>> "!video_mkv_file_list!"
echo. >> "!log_file!" 2>&1
echo type "!snippets_file_list!" >> "!log_file!" 2>&1
type "!snippets_file_list!" >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1
echo type "!video_mkv_file_list!" >> "!log_file!" 2>&1
type "!video_mkv_file_list!" >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1

echo ********** finished process of encoding into an intermediate ffv1: >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1

REM now concatenate interim intermedia slideshow .mkv files into a final video-only .mp4

echo. >> "!log_file!" 2>&1
echo type "!snippets_file_list!" >> "!log_file!" 2>&1
type "!snippets_file_list!" >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1
echo "type !video_mkv_file_list!" >> "!log_file!" 2>&1
type "!video_mkv_file_list!" >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1

set c_crf=22
set c_bv=4000000
set c_bv_min=2000000
set c_bv_max=10000000
set c_bv_buf=10000000

set "cmd_ffmpeg_libx="
set "cmd_ffmpeg_libx="%ffmpeg_exe%" "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -hide_banner -loglevel info -nostats "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -f concat -safe 0 -threads %use_cores% "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -i "!video_mkv_file_list!" "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -filter_complex "format=yuv420p,setdar=16/9" "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -strict experimental "
REM set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -c:v libx264 -preset slow -crf %c_crf% -b:v %c_bv% -minrate %c_bv_min% -maxrate %c_bv_max% -bufsize %c_bv_buf% "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -c:v libx264 -preset slow -crf %c_crf% "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -profile:v high -level 5.2 "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -movflags +faststart+write_colr "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -an "
set "cmd_ffmpeg_libx=%cmd_ffmpeg_libx% -y "!concatenated_output_mp4_file!" "

set "cmd_ffmpeg_NV="
set "cmd_ffmpeg_NV="%ffmpeg_exe%" "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -hide_banner -loglevel info -nostats "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -f concat -safe 0 -threads %use_cores% "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -i "!video_mkv_file_list!" "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -vf "setdar=16/9" "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -fps_mode passthrough "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -strict experimental "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -c:v h264_nvenc -pix_fmt nv12 -preset p7 -multipass fullres -forced-idr 1 -g 50 -coder:v cabac "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -b_ref_mode:v 0 -rc:v vbr -cq:v 0 "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -b:v %c_bv% -minrate:v %c_bv_min% -maxrate:v %c_bv_max% -bufsize %c_bv_buf% "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -profile:v high -level 5.2 "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -movflags +faststart+write_colr "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -an "
set "cmd_ffmpeg_NV=%cmd_ffmpeg_NV% -y "!concatenated_output_mp4_file!.nv.MP4" "

echo. >> "!log_file!" 2>&1
echo ------------------------ START encode CONSOLIDATED slideshow -c:v libx264 ------------ >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1
echo !DATE! !TIME! >> "!log_file!" 2>&1
echo %cmd_ffmpeg_libx%>> "!log_file!" 2>&1
%cmd_ffmpeg_libx%>> "!log_file!" 2>&1
echo !DATE! !TIME! >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1
echo ------------------------ END encode CONSOLIDATED slideshow -c:v libx264 ------------ >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1

REM ---------------------------------------------------------------------------------------------------------------










echo ------------------------ END encode single slideshow %%~N  %directory_list% ------------ >> "!log_file!" 2>&1
echo. >> "!log_file!" 2>&1


	
REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

call :libx264
call :convert_to_dvd_mpeg2
pause
goto :eof


call :using_vspipe_only
pause
goto :eof


call :using_python_only
pause
goto :eof



call :convert_to_dvd_mpeg2
pause
goto :eof


:libx264
@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
REM type "%ini_file%"
REM for testing: "%vs_path%VSPipe.exe" --progress --filter-time --container y4m "%script%" ->NUL
REM otherwise  : "%vs_path%VSPipe.exe" --container y4m "%script%" ->NUL
REM handy option not needed: -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=1
set "cmd_vspipe="
set "cmd_vspipe=%cmd_vspipe%"%vs_path%VSPipe.exe" --progress --container y4m "%script%" - "
set "cmd_ffmpeg="
set "cmd_ffmpeg=%cmd_ffmpeg%"%vs_path%ffmpeg.exe" -hide_banner -v verbose -stats -threads 2 "
set "cmd_ffmpeg=%cmd_ffmpeg% -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc "
set "cmd_ffmpeg=%cmd_ffmpeg% -f yuv4mpegpipe -i pipe: "
set "cmd_ffmpeg=%cmd_ffmpeg% -probesize 200M -analyzeduration 200M "
set "cmd_ffmpeg=%cmd_ffmpeg% -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
set "cmd_ffmpeg=%cmd_ffmpeg% -filter_complex "format=yuv420p,setdar=16/9" "
set "cmd_ffmpeg=%cmd_ffmpeg% -strict experimental "
REM set "cmd_ffmpeg=%cmd_ffmpeg% -c:v libx264 -threads 2 -preset fast -crf 20 -b:v %bv% -minrate %bv_min% -maxrate %bv_max% -bufsize %bv_buf% "
set "cmd_ffmpeg=%cmd_ffmpeg% -c:v libx264 -threads 2 -preset slow -crf 20 -b:v %bv% -minrate %bv_min% -maxrate %bv_max% -bufsize %bv_buf% "
REM set "cmd_ffmpeg=%cmd_ffmpeg% -tune stillimage "
REM set "cmd_ffmpeg=%cmd_ffmpeg% -bsf:v h264_metadata=video_full_range_flag=1 "
REM video_full_range_flag=1 is full range
set "cmd_ffmpeg=%cmd_ffmpeg% -profile:v high -level 5.2 "
set "cmd_ffmpeg=%cmd_ffmpeg% -movflags +faststart+write_colr "
set "cmd_ffmpeg=%cmd_ffmpeg% -an "
set "cmd_ffmpeg=%cmd_ffmpeg% -y "%output_mp4_file%" "
REM use for testing: %cmd_vspipe%>NUL 2>".\using_libx264.txt"
REM use for testing: %cmd_vspipe%>NUL
echo libs264 encode:>".\using_libx264.txt"
echo %cmd_vspipe%>>".\using_libx264.txt"
echo %cmd_ffmpeg%>>".\using_libx264.txt"
@echo on
%cmd_vspipe% | %cmd_ffmpeg%>>".\using_libx264.txt" 2>&1
@echo off
dir "%output_mp4_file%" >>".\using_libx264.txt" 2>&1
REM use for testing: "%vs_path%mediainfo.exe" -full "%output_mp4_file%"
goto :eof

:using_vspipe_only
@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
REM type "%ini_file%"
REM for testing: "%vs_path%VSPipe.exe" --progress --filter-time --container y4m "%script%" ->NUL
REM handy option not needed: -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=1
set "cmd_vspipe="
set "cmd_vspipe=%cmd_vspipe%"%vs_path%VSPipe.exe" --progress --container y4m "%script%" - "
echo %cmd_vspipe%>".\using_vspipe_only.txt"
@echo on
%cmd_vspipe%>NUL 2>>".\using_vspipe_only.txt"
REM %cmd_vspipe%>NUL
@echo off
goto :eof


:using_python_only
@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
REM type "%ini_file%"
echo "%vs_path%python.exe" "%script%">".\using_python_only.txt" 2>&1
@echo on
"%vs_path%python.exe" "%script%">>".\using_python_only.txt" 2>&1
@echo off
goto :eof


:convert_to_dvd_mpeg2
@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
REM
set "output_DVD_file=!output_mp4_file!.dvd.mpg"
REM
REM set audio parameters
set    "a_b=224k"
set /a "a_freq=44100"
set /a "a_cutoff=18000"
REM set the bitrates or DVD
set /a "v=9000000"
set /a "v_min=3000000"
set /a "v_max=9200000"
set /a "v_buf=1835008"
set /a "v_pkt=2048"
set /a "v_mux=10080000"
set /a "v_gop_size=15"
set /a "v_rate=25"
REM
REM SD DVD is -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv
REM SD DVD colorspace=all=bt470bg:space=bt470bg:trc=gamma28:primaries=bt470bg:range=pc:format=yuv420p:fast=0
set "cmd_DVD="
set "cmd_DVD=%cmd_DVD%"%vs_path%ffmpeg.exe" "
set "cmd_DVD=!cmd_DVD! -hide_banner -v verbose -stats -threads 2 "
set "cmd_DVD=!cmd_DVD! -i "%output_mp4_file%" -probesize 200M -analyzeduration 200M "
set "cmd_DVD=!cmd_DVD! -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp -strict experimental "
REM set "cmd_DVD=%cmd_DVD% -filter_complex "scale=in_range=full:out_range=limited,colorspace=all=bt470bg:space=bt470bg:trc=gamma28:primaries=bt470bg:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" "
set "cmd_DVD=%cmd_DVD% -filter_complex "scale=in_range=full:out_range=limited,colorspace=all=bt470bg:space=bt470bg:trc=bt470bg:primaries=bt470bg:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" "
set "cmd_DVD=!cmd_DVD! -target pal-dvd -threads 2 -r %v_rate% -g %v_gop_size% "
REM set "cmd_DVD=%cmd_DVD% -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv "
set "cmd_DVD=!cmd_DVD! -b:v %v% -minrate:v %v_min% -maxrate:v %v_max% -bufsize %v_buf% -packetsize %v_pkt% -muxrate %v_mux% "
set "cmd_DVD=%cmd_DVD% -movflags +faststart+write_colr "
REM set "cmd_DVD=!cmd_DVD! -c:a ac3 -ac 2 -b:a %a_b% -ar %a_freq%
set "cmd_DVD=!cmd_DVD! -an"
set "cmd_DVD=!cmd_DVD! -y "!output_DVD_file!" "
REM
@echo on
%cmd_DVD%
@echo off
dir "%output_DVD_file%" 
REM use for testing: "%vs_path%mediainfo.exe" -full "%output_DVD_file%"
"%vs_path%mediainfo.exe" -full "%output_DVD_file%"
goto :eof



REM -------------------------------------------------------
REM for nvidia NVENC ...
REM With nvidia 2060 Super or better use:
REM 	-spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 
REM otherwise, eg on a 1050Ti, omit these 5 parameters

