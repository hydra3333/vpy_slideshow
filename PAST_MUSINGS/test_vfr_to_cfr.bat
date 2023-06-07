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


set "script=%pwd%test_vfr_to_cfr.vpy"
set "log=%script%.log"

REM run it

REM "%vs_path%python.exe" "%script%" "D:\\ssTEST\\TEST_VIDS_IMAGES\\0TEST"
REM "%vs_path%python.exe" "%script%" "D:\\ssTEST\\TEST_VIDS_IMAGES\\1TEST"
REM "%vs_path%python.exe" "%script%" "D:\\ssTEST\\TEST_VIDS_IMAGES\\0TEST"  >>"%log%"
REM "%vs_path%python.exe" "%script%" "E:\\MULTIMEDIA"  >>"%log%"

set "output_mp4_file=%script%.mp4"

call :libx264  >>"%log%" 2>&1

pause
goto :eof


:libx264
@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
REM bitrates seem to average out at 3Mbs
set bv=4000000
set bv_min=2000000
set bv_max=10000000
set bv_buf=10000000
REM
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
REM dir "%output_mp4_file%"
REM use for testing: "%vs_path%mediainfo.exe" -full "%output_mp4_file%"
goto :eof




