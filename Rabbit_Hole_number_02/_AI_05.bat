@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM produces a video of a folder

set   "script=G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\_AI_05.vpy"
set "mp4_file=G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\_AI_05.mp4"

"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe --progress --filter-time --container y4m "%script"% - | ^
"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose -stats ^
-f yuv4mpegpipe -i pipe: ^
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

