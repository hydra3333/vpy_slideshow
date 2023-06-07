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

set   "script=%vs_CD%vpy_slideshow.vpy"
set "ini_file=%vs_CD%SLIDESHOW_PARAMETERS.ini"

REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
REM You easily can edit the stuff in this area
REM
REM bitrates seem to average out at 3Mbs
set bv=4000000
set bv_min=2000000
set bv_max=10000000
set bv_buf=10000000
REM
rem "directory_list" 			a list of quoted paths (double-backslashed) separated by commas; .\\ by itself means current default path
rem "temp_directory_list"		a list of paths (for coding convenience) however only the first path in the list will be used
rem "recursive"					is true or false; if true, it also walks the sub-directory tree(s) looking for images/videos
rem "duration_pic_sec"			a real number; the number of seconds a pic is displayed in trhe slideshow
rem duration_max_video_sec"		a real number; the maximum number of seconds a video runs before it is clipped off
rem "subtitle_depth" 			an integer; it makes subtitles with the path/filename of the image/video from the right up to the nominated depth; 0 turns it off
rem "debug_mode"				is true or false; if true, an unbelievable volume of debug messages will appear for debugging (to stderr)
rem "silent_mode"				is true or false; if true, no status messages are produced (to stderr)
rem 

REM set "list=none random fade wipe push slide_expand squeeze_slide squeeze_expand cover reveal curtain_cover curtain_reveal peel pixellate cube_rotate"
rem You need to enable delayed expansion, otherwise the new line will interfere rem with the for command.
rem The following three lines escape a new line and put it in a variable for later.
rem *** THE NEXT 2 EMPTY LINES ARE IMPORTANT! ***
set newline=^



REM do NOT add quotes to the string itself after the = sign.
REM set "list=none random fade wipe push slide_expand squeeze_slide squeeze_expand cover reveal curtain_cover curtain_reveal peel pixellate cube_rotate"
REM set "list=none random fade wipe push slide_expand squeeze_slide squeeze_expand cover reveal peel pixellate cube_rotate"
set "list=random"
REM set "directionlist=left right up down"
set "directionlist=left"
for /F %%T in ("%list: =!newline!%") do (
for /F %%D in ("%directionlist: =!newline!%") do (
	set "output_mp4_file=%vs_CD%z.%%T-%%D.mp4"
	set "log_file=.\z.%%T-%%D.log"
	del /F "!log_file!">NUL 2>&1
	echo *************************** Running %%T %%D ***************************
	echo *************************** Running %%T %%D ***************************>>"!log_file!" 2>&1
	echo *************************** Running %%T %%D ***************************>>"!log_file!" 2>&1
	echo *************************** Running %%T %%D ***************************>>"!log_file!" 2>&1
	echo *************************** Running %%T %%D ***************************>>"!log_file!" 2>&1
	DEL /F "!ini_file!">NUL 2>&1
	IF NOT EXIST "!ini_file!" (
		echo [slideshow] >>"!ini_file!"
		REM echo directory_list = ['.\\TEST_VIDS_IMAGES\\0TEST', ] >>"!ini_file!"
		REM echo directory_list = ['.\\TEST_VIDS_IMAGES\\1TEST', ] >>"!ini_file!"
		REM echo directory_list = ['.\\TEST_VIDS_IMAGES\\2TEST_rotations', '.\\TEST_VIDS_IMAGES\\2003', ] >>"!ini_file!"
		REM echo directory_list = ['.\\TEST_VIDS_IMAGES\\2TEST_rotations', ] >>"!ini_file!"
		REM echo directory_list = ['G:\\DVD\\PAT-SLIDESHOWS\\2005' ] >>"!ini_file!"
		echo directory_list = ['.\\TEST_VIDS_IMAGES\\2TEST_rotations', '.\\TEST_VIDS_IMAGES\\1TEST', ] >>"!ini_file!"
		echo temp_directory_list = ['.\\temp',] >>"!ini_file!"
		echo recursive = True >>"!ini_file!"
		echo duration_pic_sec = 4.0 >>"!ini_file!"
		echo duration_max_video_sec = 15.0>>"!ini_file!"
		echo denoise_small_size_clips = True>>"!ini_file!"
		echo duration_crossfade_secs = 0.5>>"!ini_file!"
		echo subtitle_depth = 3 >>"!ini_file!"
		echo subtitle_fontsize = 18 >>"!ini_file!"
		echo subtitle_fontscale = 1.5 >>"!ini_file!"
		echo debug_mode = False >>"!ini_file!"
		echo silent_mode = False>>"!ini_file!"
		echo crossfade_type = %%T>>"!ini_file!"
		echo crossfade_direction = %%D>>"!ini_file!"
		REM type "!ini_file!"  >>"!log_file!"
	)
	@echo Running with output redirected to: "!log_file!"
	REM call :using_python_only >>"!log_file!" 2>&1
	REM call :using_vspipe_only >>"!log_file!" 2>&1
	call :libx264 >>"!log_file!" 2>&1
	REM call :convert_to_dvd_mpeg2 >>"!log_file!" 2>&1
)
)
echo "Finished runs %list% using %directionlist%"
pause
exit

	
REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

call :using_vspipe_only
pause
goto :eof

call :using_python_only
pause
goto :eof

call :libx264
rem call :convert_to_dvd_mpeg2
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
set "cmd_vspipe=%cmd_vspipe%"%vs_path%VSPipe.exe" --progress --filter-time --container y4m "%script%" - "
set "cmd_ffmpeg="
set "cmd_ffmpeg=%cmd_ffmpeg%"%vs_path%ffmpeg.exe" -hide_banner -v verbose -stats "
set "cmd_ffmpeg=%cmd_ffmpeg% -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc "
set "cmd_ffmpeg=%cmd_ffmpeg% -f yuv4mpegpipe -i pipe: "
set "cmd_ffmpeg=%cmd_ffmpeg% -probesize 200M -analyzeduration 200M "
set "cmd_ffmpeg=%cmd_ffmpeg% -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
set "cmd_ffmpeg=%cmd_ffmpeg% -filter_complex "format=yuv420p,setdar=16/9" "
set "cmd_ffmpeg=%cmd_ffmpeg% -strict experimental "
set "cmd_ffmpeg=%cmd_ffmpeg% -c:v libx264 -preset fast -crf 20 -b:v %bv% -minrate %bv_min% -maxrate %bv_max% -bufsize %bv_buf% "
REM set "cmd_ffmpeg=%cmd_ffmpeg% -tune stillimage "
REM set "cmd_ffmpeg=%cmd_ffmpeg% -bsf:v h264_metadata=video_full_range_flag=1 "
REM video_full_range_flag=1 is full range
set "cmd_ffmpeg=%cmd_ffmpeg% -profile:v high -level 5.2 "
set "cmd_ffmpeg=%cmd_ffmpeg% -movflags +faststart+write_colr "
set "cmd_ffmpeg=%cmd_ffmpeg% -an "
set "cmd_ffmpeg=%cmd_ffmpeg% -y "%output_mp4_file%" "
echo libs264 encode:
echo %cmd_vspipe%
echo %cmd_ffmpeg%
@echo on
%cmd_vspipe% | %cmd_ffmpeg%
@echo off
dir "%output_mp4_file%"
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
set "cmd_vspipe=%cmd_vspipe%"%vs_path%VSPipe.exe" --progress --filter-time --container y4m "%script%" - "
echo %cmd_vspipe%
@echo on
%cmd_vspipe%>NUL
REM %cmd_vspipe%>NUL
@echo off
goto :eof


:using_python_only
@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
REM type "%ini_file%"
echo "%vs_path%python.exe" "%script%"
@echo on
"%vs_path%python.exe" "%script%"
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
set "cmd_DVD=!cmd_DVD! -hide_banner -v verbose -stats "
set "cmd_DVD=!cmd_DVD! -i "%output_mp4_file%" -probesize 200M -analyzeduration 200M "
set "cmd_DVD=!cmd_DVD! -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp -strict experimental "
REM set "cmd_DVD=%cmd_DVD% -filter_complex "scale=in_range=full:out_range=limited,colorspace=all=bt470bg:space=bt470bg:trc=gamma28:primaries=bt470bg:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" "
set "cmd_DVD=%cmd_DVD% -filter_complex "scale=in_range=full:out_range=limited,colorspace=all=bt470bg:space=bt470bg:trc=bt470bg:primaries=bt470bg:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" "
set "cmd_DVD=!cmd_DVD! -target pal-dvd -r %v_rate% -g %v_gop_size% "
REM set "cmd_DVD=%cmd_DVD% -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv "
set "cmd_DVD=!cmd_DVD! -b:v %v% -minrate:v %v_min% -maxrate:v %v_max% -bufsize %v_buf% -packetsize %v_pkt% -muxrate %v_mux% "
set "cmd_DVD=%cmd_DVD% -movflags +faststart+write_colr "
REM set "cmd_DVD=!cmd_DVD! -c:a ac3 -ac 2 -b:a %a_b% -ar %a_freq%
set "cmd_DVD=!cmd_DVD! -an"
set "cmd_DVD=!cmd_DVD! -y "!output_DVD_file!" "
REM
echo %cmd_DVD%
@echo on
%cmd_DVD%
@echo off
dir "%output_DVD_file%" 
"%vs_path%mediainfo.exe" -full "%output_DVD_file%"
goto :eof



REM -------------------------------------------------------
REM for nvidia NVENC ...
REM With nvidia 2060 Super or better use:
REM 	-spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 
REM otherwise, eg on a 1050Ti, omit these 5 parameters

set "list=none random fade wipe slide_expand squeeze_slide squeeze_expand reveal curtain_cover curtain_reveal pixellate cube_rotate"
rem You need to enable delayed expansion, otherwise the new line will interfere
rem with the for command.
setlocal ENABLEDELAYEDEXPANSION
rem The following three lines escape a new line and put it in a variable for
rem later.
rem The empty lines are important!
set newline=^


set "list=none random fade wipe slide_expand squeeze_slide squeeze_expand reveal curtain_cover curtain_reveal pixellate cube_rotate"
for /F %%i in ("%list: =!newline!%") do (echo item is %%i)
pause
exit
