@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

set "mp4_folder=G:\HDTV\TEST\_AI_\"
set "script=G:\HDTV\TEST\_AI_\_AI_04.vpy"

set "fol_images=G:\HDTV\TEST\_AI_\busted_vids"
set "fol=.\_AI_folder_to_process.txt"

for /f "tokens=*" %%G in ('dir /b /s /a:d "!fol_images!\*"') do (
	call :toidi "%%G"
)
DEL "!fol!"
pause
exit

:toidi
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
set "mp4=%~n1.mp4"
DEL "!fol!"
echo %~1>"!fol!"
echo DIR !script!
DIR !script!
echo TYPE "!fol!"
TYPE "!fol!"
echo.
set "cmd1="
set "cmd1=!cmd1!"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose "
set "cmd1=!cmd1!	-f vapoursynth -i "!script!" -an "
set "cmd1=!cmd1!	-map 0:v:0 "
set "cmd1=!cmd1!	-vf "setdar=16/9" "
set "cmd1=!cmd1!	-fps_mode passthrough "
set "cmd1=!cmd1!	-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp "
set "cmd1=!cmd1!	-strict experimental "
set "cmd1=!cmd1!	-c:v h264_nvenc -pix_fmt nv12 -preset p7 -multipass fullres -forced-idr 1 -g 25 "
set "cmd1=!cmd1!	-coder:v cabac -spatial-aq 1 -temporal-aq 1 "
set "cmd1=!cmd1!	-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 "
set "cmd1=!cmd1!	-rc:v vbr -cq:v 0 -b:v 3500000 -minrate:v 100000 -maxrate:v 9000000 -bufsize 9000000 "
set "cmd1=!cmd1!	-profile:v high -level 5.2 "
set "cmd1=!cmd1!	-movflags +faststart+write_colr "
set "cmd1=!cmd1!	-y "!mp4_folder!!mp4!" "
echo !cmd1!
!cmd1!
DEL "!fol!"
goto :eof

