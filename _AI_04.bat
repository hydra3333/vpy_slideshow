@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM set "fol_images=G:\HDTV\TEST\_AI_\Family_Photos"
set "fol_images=G:\HDTV\TEST\_AI_\test_images"
set "fol=.\_AI_folder_to_process.txt"
DEL "!fol!"
echo !fol_images!>"!fol!"
TYPE "!fol!"

set "mp4_file=G:\HDTV\TEST\_AI_\_AI_04.mp4"
set "script=G:\HDTV\TEST\_AI_\_AI_04.vpy"

"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose ^
-f vapoursynth -i "!script!" -an ^
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
-y "!mp4_file!"

DEL "!fol!"
pause
exit
