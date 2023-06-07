@ECHO off
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

set "ffprobeexe64=C:\SOFTWARE\ffmpeg\ffprobe.exe"
set "mediainfoexe=C:\SOFTWARE\MediaInfo\MediaInfo.exe"

set "tempfile=.\tempfile.tmp"

Call :get_mediainfo_parameter "Video" "Duration" "V_Duration_ms" "%~f1" 
Call :get_mediainfo_parameter "Video" "Width" "V_Width" "%~f1" 
Call :get_mediainfo_parameter "Video" "Height" "V_Height" "%~f1" 
Call :get_mediainfo_parameter "Video" "PixelAspectRatio" "V_PixelAspectRatio" "%~f1" 
Call :get_mediainfo_parameter "Video" "DisplayAspectRatio" "V_DisplayAspectRatio" "%~f1" 
Call :get_mediainfo_parameter "Video" "Rotation" "V_Rotation" "%~f1" 
Call :get_mediainfo_parameter "Video" "FrameRate_Mode" "V_FrameRate_Mode" "%~f1" 
Call :get_mediainfo_parameter "Video" "FrameRate" "V_FrameRate" "%~f1" 
Call :get_mediainfo_parameter "Video" "FrameRate_Num" "V_FrameRate_Num" "%~f1" 
Call :get_mediainfo_parameter "Video" "FrameRate_Den" "V_FrameRate_Den" "%~f1" 
Call :get_mediainfo_parameter "Video" "FrameCount" "V_FrameCount" "%~f1" 

Call :get_ffprobe_video_stream_parameter "codec_name" "V_CodecID_FF" "%~f1" 
Call :get_ffprobe_video_stream_parameter "codec_tag_string" "V_CodecID_String_FF" "%~f1" 
Call :get_ffprobe_video_stream_parameter "width" "V_Width_FF" "%~f1" 
Call :get_ffprobe_video_stream_parameter "height" "V_Height_FF" "%~f1" 
Call :get_ffprobe_video_stream_parameter "duration" "V_Duration_s_FF" "%~f1" 
Call :get_ffprobe_video_stream_parameter "bit_rate" "V_BitRate_FF" "%~f1" 
Call :get_ffprobe_video_stream_parameter "max_bit_rate" "V_BitRate_Maximum_FF" "%~f1"
Call :get_ffprobe_video_stream_parameter "r_frame_rate" "V_Frame_Rate_r_FF" "%~f1"
Call :get_ffprobe_video_stream_parameter "avg_frame_rate" "V_Average_Frame_Rate_FF" "%~f1"

@echo on

"%ffprobeexe64%" -v error -select_streams v:0 -of default=noprint_wrappers=1 -show_entries stream=r_frame_rate,avg_frame_rate,time_base,nb_frames "%~f1"
pause

"%ffprobeexe64%" -v quiet -select_streams v:0 -of default=noprint_wrappers=1 -show_format -show_streams "%~f1"
REM :nokey=1 yields a raw value
REM "%ffprobeexe64%" -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate "%~f1"
pause

"!mediainfoexe!" --full "%~f1"
pause

goto :eof

REM def get_video_frame_rate_from_ffprobe_stream(filename):
REM 	result = subprocess.run(
REM     	[
REM         	"ffprobe",
REM             "-v",
REM             "error",
REM             "-select_streams",
REM             "v",
REM             "-of",
REM             "default=noprint_wrappers=1:nokey=1",
REM             "-show_entries",
REM             "stream=r_frame_rate",	# returns eg "25/1" 
REM             #could do similar same for avg_frame_rate
REM             filename,
REM         ],
REM         stdout=subprocess.PIPE,
REM         stderr=subprocess.STDOUT,
REM     )
REM     result_string = result.stdout.decode('utf-8').split()[0].split('/')
REM    fps = float(result_string[0])/float(result_string[1])
REM    return fps


:get_mediainfo_parameter
REM DO NOT SET @setlocal ENABLEDELAYEDEXPANSION
REM DO NOT SET @setlocal enableextensions
REM ensure no trailing spaces in any of the lines in this routine !!
set mi_Section=%~1
set mi_Parameter=%~2
set mi_Variable=%~3
set mi_Filename=%~4
set "mi_var="
DEL /F "!tempfile!" >NUL 2>&1
REM Note \r\n is Windows new-line, which is for the case of multiple audio streams, 
REM it outputs a result for each stream on a new line, the first stream being the first entry,
REM and the first audio stream should be the one we need. 
REM Set /p from an input file reads the first line.
"!mediainfoexe!" "--Inform=!mi_Section!;%%!mi_Parameter!%%\r\n" "!mi_Filename!" > "!tempfile!"
set /p mi_var=<"!tempfile!"
set !mi_Variable!=!mi_var!
ECHO !DATE! !TIME! "!mi_Variable!=!mi_var!" from "!mi_Section!" "!mi_Parameter!"
DEL /F "!tempfile!" >NUL 2>&1
goto :eof
REM
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM
:get_mediainfo_parameter_legacy
REM DO NOT SET @setlocal ENABLEDELAYEDEXPANSION
REM DO NOT SET @setlocal enableextensions
REM ensure no trailing spaces in any of the lines in this routine !!
set mi_Section=%~1
set mi_Parameter=%~2
set mi_Variable=%~3
set mi_Filename=%~4
set "mi_var="
DEL /F "!tempfile!" >NUL 2>&1
REM Note \r\n is Windows new-line, which is for the case of multiple audio streams, 
REM it outputs a result for each stream on a new line, the first stream being the first entry,
REM and the first audio stream should be the one we need. 
REM Set /p from an input file reads the first line.
"!mediainfoexe!" --Legacy "--Inform=!mi_Section!;%%!mi_Parameter!%%\r\n" "!mi_Filename!" > "!tempfile!"
set /p mi_var=<"!tempfile!"
set !mi_Variable!=!mi_var!
ECHO !DATE! !TIME! "!mi_Variable!=!mi_var!" from Legacy "!mi_Section!" "!mi_Parameter!"
DEL /F "!tempfile!" >NUL 2>&1
goto :eof
REM
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM
:get_ffprobe_video_stream_parameter
REM DO NOT SET @setlocal ENABLEDELAYEDEXPANSION
REM DO NOT SET @setlocal enableextensions
REM ensure no trailing spaces in any of the lines in this routine !!
set mi_Parameter=%~1
set mi_Variable=%~2
set mi_Filename=%~3
set "mi_var="
DEL /F "!tempfile!" >NUL 2>&1
REM Note \r\n is Windows new-line, which is for the case of multiple audio streams, 
REM it outputs a result for each stream on a new line, the first stream being the first entry,
REM and the first audio stream should be the one we need. 
REM Set /p from an input file reads the first line.
REM see if -probesize 5000M  makes any difference
"!ffprobeexe64!" -hide_banner -v quiet -select_streams v:0 -show_entries stream=!mi_Parameter! -of default=noprint_wrappers=1:nokey=1 "!mi_Filename!" > "!tempfile!"
set /p mi_var=<"!tempfile!"
set !mi_Variable!=!mi_var!
ECHO !DATE! !TIME! "!mi_Variable!=!mi_var!" from ffprobe "!mi_Parameter!"
DEL /F "!tempfile!" >NUL 2>&1
goto :eof
REM
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM
:LoCase
:: Subroutine to convert a variable VALUE to all lower case.
:: The argument for this subroutine is the variable NAME.
FOR %%i IN ("A=a" "B=b" "C=c" "D=d" "E=e" "F=f" "G=g" "H=h" "I=i" "J=j" "K=k" "L=l" "M=m" "N=n" "O=o" "P=p" "Q=q" "R=r" "S=s" "T=t" "U=u" "V=v" "W=w" "X=x" "Y=y" "Z=z") DO CALL SET "%1=%%%1:%%~i%%"
goto :eof

:UpCase
:: Subroutine to convert a variable VALUE to all UPPER CASE.
:: The argument for this subroutine is the variable NAME.
FOR %%i IN ("a=A" "b=B" "c=C" "d=D" "e=E" "f=F" "g=G" "h=H" "i=I" "j=J" "k=K" "l=L" "m=M" "n=N" "o=O" "p=P" "q=Q" "r=R" "s=S" "t=T" "u=U" "v=V" "w=W" "x=X" "y=Y" "z=Z") DO CALL SET "%1=%%%1:%%~i%%"
goto :eof

:TCase
:: Subroutine to convert a variable VALUE to Title Case.
:: The argument for this subroutine is the variable NAME.
FOR %%i IN (" a= A" " b= B" " c= C" " d= D" " e= E" " f= F" " g= G" " h= H" " i= I" " j= J" " k= K" " l= L" " m= M" " n= N" " o= O" " p= P" " q= Q" " r= R" " s= S" " t= T" " u= U" " v= V" " w= W" " x= X" " y= Y" " z= Z") DO CALL SET "%1=%%%1:%%~i%%"
goto :eof
REM
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM -------------------------------------------------------------------------------------------------------------------------------------
REM

