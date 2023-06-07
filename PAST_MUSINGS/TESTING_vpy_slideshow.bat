@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM produces a video of a folder

set "vs_path=D:\ssTEST\Vapoursynth_x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

REM set "pth=G:\DVD\PAT-SLIDESHOWS\vpy_slideshow_in_development"
REM if /I NOT "%pth:~-1%" == "\" (set "pth=%pth%\")

set "pwd=%CD%"
if /I NOT "%pwd:~-1%" == "\" (set "pwd=%pwd%\")

set   "script=%pwd%vpy_slideshow.vpy"
set "ini_file=%pwd%SLIDESHOW_PARAMETERS.ini"
set "mp4_file=%pwd%vpy_slideshow.mp4"

set bv=9000000
set bv_min=3000000
set bv_max=15000000
set bv_buf=15000000

DEL "%ini_file%">NUL 2>&1
REM IF 0 equ 1 (
IF NOT EXIST "%ini_file%" (
	echo [slideshow]>>"%ini_file%"
	echo directory_list = ['.\\ssTEST\\TEST_VIDS_IMAGES']>>"%ini_file%"
	echo temp_directory_list = ['.\\temp',]>>"%ini_file%"
	echo recursive = True>>"%ini_file%"
	echo debug_mode = False>>"%ini_file%"
	echo duration_pic_sec = 3.0>>"%ini_file%"
	echo duration_max_video_sec = 15.0>>"%ini_file%"
	type "%ini_file%"
)
REM

call :libx264

REM call :like_04
REM PAUSE
REM goto :eof 

REM call :using_python_only
REM PAUSE
REM goto :eof

REM call :using_vspipe_input
REM pause
REM goto :eof

REM call :using_vapoursynth_input
REM PAUSE
REM goto :eof

REM call :convert_to_dvd_mpg
REM PAUSE
REM goto :eof

pause
goto :eof


:libx264
@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM echo "D:\ssTEST\Vapoursynth_x64\VSPipe.exe" --progress --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.vpy" - 2>.\using_libx264.txt
REM "D:\ssTEST\Vapoursynth_x64\VSPipe.exe" --progress --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.vpy" ->NUL 2>>.\using_libx264.txt

REM rem -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=1
echo "D:\ssTEST\Vapoursynth_x64\VSPipe.exe" --progress --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.vpy" - >>.\using_libx264.txt 2>&1
echo "D:\ssTEST\Vapoursynth_x64\ffmpeg.exe" -hide_banner -v verbose -stats -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc -f yuv4mpegpipe -i pipe: -probesize 200M -analyzeduration 200M -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp -filter_complex "format=yuv420p,setdar=16/9" -strict experimental -c:v libx264 -preset fast -crf 20 -maxrate 15M -bufsize 15M -tune stillimage -profile:v high -level 5.2 -movflags +faststart+write_colr -an -y "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.mp4" >>.\using_libx264.txt 2>&1
"D:\ssTEST\Vapoursynth_x64\VSPipe.exe" --progress --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.vpy" -  | "D:\ssTEST\Vapoursynth_x64\ffmpeg.exe" -hide_banner -v verbose -stats -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc -f yuv4mpegpipe -i pipe: -probesize 200M -analyzeduration 200M -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp -filter_complex "format=yuv420p,setdar=16/9" -strict experimental -c:v libx264 -preset fast -crf 20 -maxrate 15M -bufsize 15M -tune stillimage -profile:v high -level 5.2 -movflags +faststart+write_colr -an -y "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.mp4" >>.\using_libx264.txt 2>&1
"D:\ssTEST\Vapoursynth_x64\mediainfo.exe" -full "%mp4_file%" >>  ".\using_libx264.txt" 2>&1
goto :eof


:like_04
@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
set "fol_images=G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\1TEST"
set "fol=.\_AI_folder_to_process.txt"
DEL "%fol%"
echo %fol_images%>"%fol%"
TYPE "%fol%"

set "mp4_file=G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.mp4"
set  "script=G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.vpy"

"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose ^
-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc ^
-f vapoursynth -i "%script%" -an ^
-map 0:v:0 ^
-vf "setdar=16/9" ^
-fps_mode passthrough ^
-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp ^
-strict experimental ^
-c:v h264_nvenc -pix_fmt nv12 -preset p7 -multipass fullres -forced-idr 1 -g 25 ^
-coder:v cabac -spatial-aq 1 -temporal-aq 1 ^
-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 ^
-rc:v vbr -cq:v 0 -b:v 3500000 -minrate:v 100000 -maxrate:v 9000000 -bufsize 9000000 ^
-profile:v high -level 5.2 ^
-movflags +faststart+write_colr ^
-y "%mp4_file%" 2> "%script%.debug.log"
"C:\SOFTWARE\mediainfo\mediainfo.exe" -full "%mp4_file%" >>  "%script%.debug.log" 2>&1
goto :eof

:using_python_only
@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM +++ just run python over it to see debug output
REM pushd "%vs_path%"
REM cd
type "%ini_file%"
REM the script *should* have converted everythng to bt.709
"%vs_path%python.exe" "%script%" >using_python_only.txt 2>&1
REM popd
goto :eof


:using_vapoursynth_input
@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM +++ try a raw run with vapoursynth input
REM pushd "%vs_path%"
REM cd
type "%ini_file%"
REM nvenc parameters suitable for an nvidia 2060Super and will fail on a lesser card eg 1050Ti, eg bf:v 3 -spatial-aq 1 -temporal-aq 1
REM the script *should* have converted everythng to bt.709

set "cmd2="
set "cmd2=%cmd2%"%vs_path%ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats "
set "cmd2=%cmd2%-f vapoursynth -i "%script%" "
set "cmd2=%cmd2%-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc "
set "cmd2=%cmd2%-probesize 200M "
set "cmd2=%cmd2%-analyzeduration 200M "
set "cmd2=%cmd2%-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
REM set "cmd2=%cmd2%-filter_complex "colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" "
set "cmd2=%cmd2%-filter_complex "format=yuv420p,setdar=16/9" "
set "cmd2=%cmd2%-strict experimental "
set "cmd2=%cmd2%-c:v h264_nvenc -preset p7 -multipass fullres -forced-idr 1 -g 25 -coder:v cabac -spatial-aq 1 -temporal-aq 1 "
set "cmd2=%cmd2%-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 -rc:v vbr "
set "cmd2=%cmd2%-b:v %bv% -minrate:v %bv_min% -maxrate:v %bv_max% -bufsize %bv_buf% "
set "cmd2=%cmd2%-profile:v high -level 5.2 -movflags +faststart+write_colr "
set "cmd2=%cmd2%-an "
set "cmd2=%cmd2%-y "%mp4_file%" "

REM "%vs_path%ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats ^
REM -f vapoursynth -i "%script%" ^
REM -probesize 200M ^
REM REM -analyzeduration 200M ^
REM -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp ^
REM -filter_complex "colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" ^
REM -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc -strict experimental ^
REM -c:v h264_nvenc -preset p7 -multipass fullres -forced-idr 1 -g 25 -coder:v cabac -spatial-aq 1 -temporal-aq 1 ^
REM -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 -rc:v vbr ^
REM -b:v %bv% -minrate:v %bv_min% -maxrate:v %bv_max% -bufsize %bv_buf% ^
REM -profile:v high -level 5.2 -movflags +faststart+write_colr ^
REM -an ^
REM -y "%mp4_file%">>.\using_vapoursynth_input.txt 2>&1
REM popd

echo %cmd2% >.\using_vapoursynth_input.txt 2>&1
%cmd2%  >>.\using_vapoursynth_input.txt 2>&1
"C:\SOFTWARE\mediainfo\mediainfo.exe" -full "%mp4_file%" >>  ".\using_vapoursynth_input.txt" 2>&1
goto :eof


:using_vspipe_input
@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
REM +++ try a run using a CMD and vspipe

echo.>.\using_vspipe.txt
REM  echo pushd "%vs_path%">.\using_vspipe.txt
echo cd>>.\using_vspipe.txt

REM pushd "%vs_path%"
REM cd
type "%ini_file%"

REM nvenc parameters suitable for an nvidia 2060Super and will fail on a lesser card eg 1050Ti, eg bf:v 3 -spatial-aq 1 -temporal-aq 1
REM the script *should* have converted everythng to bt.709
REM cannot put pipe symbol where I need it, so separate the commands and use the pipe symbol  later
set "cmd1="
set "cmd1=%cmd1%"%vs_path%VSPipe.exe" --container y4m "%script%" - "
REM set "cmd1=%cmd1%"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --container y4m "%script%" - "
REM set "cmd1=%cmd1%"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --filter-time --container y4m "%script%" - "
REM echo %cmd1%
REM echo %cmd1%>>.\using_vspipe.txt
REM %cmd1%>NUL 2>>.\using_vspipe.txt
REM %cmd1%>NUL

set "cmd2="
set "cmd2=%cmd2%"%vs_path%ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats "
set "cmd2=%cmd2%-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc "
set "cmd2=%cmd2%-f yuv4mpegpipe -i pipe: "
set "cmd2=%cmd2%-probesize 200M "
set "cmd2=%cmd2%-analyzeduration 200M "
set "cmd2=%cmd2%-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
REM set "cmd2=%cmd2%-filter_complex "colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" "
set "cmd2=%cmd2%-filter_complex "format=yuv420p,setdar=16/9" "
set "cmd2=%cmd2%-strict experimental "
set "cmd2=%cmd2%-c:v h264_nvenc -preset p7 -multipass fullres -forced-idr 1 -g 25 -coder:v cabac -spatial-aq 1 -temporal-aq 1 "
set "cmd2=%cmd2%-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 -rc:v vbr "
set "cmd2=%cmd2%-b:v %bv% -minrate:v %bv_min% -maxrate:v %bv_max% -bufsize %bv_buf% "
set "cmd2=%cmd2%-profile:v high -level 5.2 -movflags +faststart+write_colr "
set "cmd2=%cmd2%-an "
set "cmd2=%cmd2%-y "%mp4_file%" "

echo %cmd1% 'pipe' %cmd2% >.\using_vspipe_to_ffmpeg.txt

pause

%cmd1%  | %cmd2% >>.\using_vspipe_to_ffmpeg.txt 2>&1
"C:\SOFTWARE\mediainfo\mediainfo.exe" -full "%mp4_file%" >>  "using_vspipe_to_ffmpeg.txt" 2>&1
REM echo popd>>.\vspipe.txt
REM popd
REM pause
goto :eof




REM CONVERT TO DVD

# SD DVD is -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv
# 3900x with nvidia 2060 Super uses -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 # otherwise omit these 5 parameters

"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats ^
-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc ^
-f vapoursynth -i "%script%" ^
-probesize 200M ^
-analyzeduration 200M ^
-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp ^
-filter_complex "format=yuv420p,setdar=16/9" ^
-strict experimental ^
-c:v h264_nvenc -preset p7 -multipass fullres -forced-idr 1 -g 25 -coder:v cabac -spatial-aq 1 -temporal-aq 1 ^
-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 -rc:v vbr ^
-b:v 9000000 -minrate:v 3000000 -maxrate:v 15000000 -bufsize 15000000 ^
-profile:v high -level 5.2 -movflags +faststart+write_colr ^
-an ^
-y "%mp4_file%"
#-filter_complex "colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" ^




"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\vpy_slideshow.vpy" - >NUL

"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "%script%" -
