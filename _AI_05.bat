@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM produces a video of a folder

set      "pth=G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development"
set   "script=%pth%\_AI_05.vpy"
set "ini_file=.\SLIDESHOW_PARAMETERS.ini"
set "mp4_file=%pth%\_AI_05.mp4"

set "cmd1="
set "cmd1=%cmd1%"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "%script%" - "
REM set "cmd1=%cmd1%"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --filter-time --container y4m "%script%" - "

set "cmd2="
set "cmd2=%cmd2%"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats "
set "cmd2=%cmd2%-f yuv4mpegpipe -i pipe: "
set "cmd2=%cmd2%-probesize 200M "
set "cmd2=%cmd2%-analyzeduration 200M "
set "cmd2=%cmd2%-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
set "cmd2=%cmd2%-filter_complex 'colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9' "
set "cmd2=%cmd2%-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range pc -strict experimental "
set "cmd2=%cmd2%-c:v h264_nvenc -preset p7 -multipass fullres -forced-idr 1 -g 25 -coder:v cabac -spatial-aq 1 -temporal-aq 1 "
set "cmd2=%cmd2%-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 -rc:v vbr "
set "cmd2=%cmd2%-b:v 9000000 -minrate:v 3000000 -maxrate:v 15000000 -bufsize 15000000 "
set "cmd2=%cmd2%-profile:v high -level 5.2 -movflags +faststart+write_colr "
set "cmd2=%cmd2%-an "
set "cmd2=%cmd2%-y "%mp4_file%" "

@echo on

pushd C:\SOFTWARE\Vapoursynth-x64
cd

DEL "%ini_file%">NUL 2>&1
echo [slideshow]>>"%ini_file%"
echo directory = G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\0TEST>>"%ini_file%"
echo temp_directory = D:\TEMP>>"%ini_file%"
echo recursive = True>>"%ini_file%"
type "%ini_file%"

.\python.exe "%script%"

popd

pause
exit

pushd C:\SOFTWARE\Vapoursynth-x64
cd

DEL "%ini_file%">NUL 2>&1
echo [slideshow]>>"%ini_file%"
echo directory = G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\0TEST>>"%ini_file%"
echo temp_directory = D:\TEMP>>"%ini_file%"
echo recursive = True>>"%ini_file%"
type "%ini_file%"

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

popd

@echo off

pause
exit

echo %cmd1% ^| %cmd2%

pushd C:\SOFTWARE\Vapoursynth-x64
cd

DEL "%ini_file%">NUL 2>&1
echo [slideshow]>>"%ini_file%"
echo directory = G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\0TEST>>"%ini_file%"
echo temp_directory = D:\TEMP>>"%ini_file%"
echo recursive = True>>"%ini_file%"
type "%ini_file%"

%cmd1% | %cmd2%

popd

pause
exit

# SD DVD is -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv
# 3900x with nvidia 2060 Super uses -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 # otherwise omit these 5 parameters

"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats ^
-f vapoursynth -i "!script!" ^
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




"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\_AI_05.vpy" - >NUL
"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\_AI_04.vpy" - >NUL

"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --container y4m "%script%" -
