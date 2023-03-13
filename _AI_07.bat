@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM produces a video of a folder

set "vs_path=C:\SOFTWARE\Vapoursynth-x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

REM set "pth=G:\DVD\PAT-SLIDESHOWS\_AI_07_in_development"
REM if /I NOT "%pth:~-1%" == "\" (set "pth=%pth%\")

set "pwd=%CD%"
if /I NOT "%pwd:~-1%" == "\" (set "pwd=%pwd%\")

set   "script=%pwd%_AI_07.vpy"
set "ini_file=%pwd%SLIDESHOW_PARAMETERS.ini"
set "mp4_file=%pwd%_AI_07.mp4"

set bv=9000000
set bv_min=3000000
set bv_max=15000000
set bv_buf=15000000

DEL "%ini_file%">NUL 2>&1
IF NOT EXIST "%ini_file%" (
	echo [slideshow]>>"%ini_file%"
	echo directory = G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\1TEST>>"%ini_file%"
	echo temp_directory = D:\TEMP>>"%ini_file%"
	echo recursive = False>>"%ini_file%"
	echo debug_mode = True>>"%ini_file%"
	echo duration_max_video_sec = 10.0
	type "%ini_file%"
)


call :like_04
PAUSE
goto :eof 

REM call :using_python_only
REM goto :eof

REM call :using_vspipe_input
REM goto :eof

REM call :using_vapoursynth_input
REM goto :eof

REM call :convert_to_dvd_mpg
REM goto :eof

pause
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

set "mp4_file=G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\_AI_07.mp4"
set  "script=G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\_AI_07.vpy"

"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose ^
-f vapoursynth -i "%script%" -an ^
-map 0:v:0 ^
-vf "setdar=16/9" ^
-fps_mode passthrough ^
-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp ^
-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc -strict experimental ^
-c:v h264_nvenc -pix_fmt nv12 -preset p7 -multipass fullres -forced-idr 1 -g 25 ^
-coder:v cabac -spatial-aq 1 -temporal-aq 1 ^
-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 ^
-rc:v vbr -cq:v 0 -b:v 3500000 -minrate:v 100000 -maxrate:v 9000000 -bufsize 9000000 ^
-profile:v high -level 5.2 ^
-movflags +faststart+write_colr ^
-y "%mp4_file%"

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
"%vs_path%python.exe" "%script%"
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
"%vs_path%ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats ^
-f vapoursynth -i "%script%" ^
-probesize 200M ^
-analyzeduration 200M ^
-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp ^
-filter_complex "colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" ^
-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc -strict experimental ^
-c:v h264_nvenc -preset p7 -multipass fullres -forced-idr 1 -g 25 -coder:v cabac -spatial-aq 1 -temporal-aq 1 ^
-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 -rc:v vbr ^
-b:v %bv% -minrate:v %bv_min% -maxrate:v %bv_max% -bufsize %bv_buf% ^
-profile:v high -level 5.2 -movflags +faststart+write_colr ^
-an ^
-y "%mp4_file%"
REM popd
goto :eof


:using_vspipe_input
@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
REM +++ try a run using a CMD and vspipe

echo pushd "%vs_path%">.\vspipe.txt
echo cd>>.\vspipe.txt

pushd "%vs_path%"
cd

type "%ini_file%"

pause

REM nvenc parameters suitable for an nvidia 2060Super and will fail on a lesser card eg 1050Ti, eg bf:v 3 -spatial-aq 1 -temporal-aq 1
REM the script *should* have converted everythng to bt.709
REM cannot put pipe symbol where I need it, so separate the commands and use the pipe symbol  later
set "cmd1="
set "cmd1=%cmd1%"%vs_path%VSPipe.exe" --container y4m "%script%" - "
REM set "cmd1=%cmd1%"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --filter-time --container y4m "%script%" - "

echo %cmd1%
echo %cmd1%>>.\vspipe.txt

pause

set "cmd2="
set "cmd2=%cmd2%"%vs_path%ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats "
set "cmd2=%cmd2%-f yuv4mpegpipe -i pipe: "
set "cmd2=%cmd2%-probesize 200M "
set "cmd2=%cmd2%-analyzeduration 200M "
set "cmd2=%cmd2%-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
set "cmd2=%cmd2%-filter_complex 'colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9' "
set "cmd2=%cmd2%-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc -strict experimental "
set "cmd2=%cmd2%-c:v h264_nvenc -preset p7 -multipass fullres -forced-idr 1 -g 25 -coder:v cabac -spatial-aq 1 -temporal-aq 1 "
set "cmd2=%cmd2%-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 -rc:v vbr "
set "cmd2=%cmd2%-b:v %bv% -minrate:v %bv_min% -maxrate:v %bv_max% -bufsize %bv_buf% "
set "cmd2=%cmd2%-profile:v high -level 5.2 -movflags +faststart+write_colr "
set "cmd2=%cmd2%-an "
set "cmd2=%cmd2%-y "%mp4_file%" "

echo %cmd2%
echo %cmd2%>>.\vspipe.txt

pause

echo %cmd1% "pipe" %cmd2% >>.\vspipe.txt

pause

%cmd1% | %cmd2%

pause

echo popd>>.\vspipe.txt

pause


goto :eof



pause
goto :eof




REM CONVERT TO DVD

# SD DVD is -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv
# 3900x with nvidia 2060 Super uses -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 # otherwise omit these 5 parameters

"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats ^
-f vapoursynth -i "%script%" ^
-probesize 200M ^
-analyzeduration 200M ^
-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp ^
-filter_complex "colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9" ^
-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc -strict experimental ^
-c:v h264_nvenc -preset p7 -multipass fullres -forced-idr 1 -g 25 -coder:v cabac -spatial-aq 1 -temporal-aq 1 ^
-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 -rc:v vbr ^
-b:v 9000000 -minrate:v 3000000 -maxrate:v 15000000 -bufsize 15000000 ^
-profile:v high -level 5.2 -movflags +faststart+write_colr ^
-an ^
-y "%mp4_file%"




"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_07_in_development\_AI_07.vpy" - >NUL
"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_07_in_development\_AI_04.vpy" - >NUL

"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "%script%" -
