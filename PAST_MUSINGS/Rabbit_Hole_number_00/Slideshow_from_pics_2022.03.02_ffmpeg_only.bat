@ECHO on
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM Parse a source folder tree
REM and convert images to a slideshow, PAL 25fps 
REM
REM parse full folder name to grab the rightmost foldername and use that
REM as the destination as well as the filename for the video
REM
REM In explorer, drag and drop a folder name onto this .bat and it jus
REM
REM There remain real issues, per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page2#post2682862
REM eg
REM Uses native ffmpeg "-f concat" using the "scale" and "pad" filters ... HOWEVER
REM as soon as it saw an odd dimension then the image was stretched either 
REM horizontally or vertically no matter what options I tried ... and I tried a lot.
REM It is also less than forgiving by delivering bt470gb colorspace etc and
REM inconsistent "range" (TV or PC) perhaps depending on the first image it encountered.
REM Plenty of advice on the net with basically the same options however 
REM the authors must not have tried a range of old and new and odd-dimensioned images.
REM I did not spend enough time to find out how to subtitle each image with aspects of its path and name.
REM
REM Ended up giving up on ffmpeg -f concat et al directly, and moving to using
REM irfanview to resize all the images correctly and THEN using ffmpeg -f concat on those
REM using an input file of filenames.
REM Still issues with delivered inconsistent colorspace etc and inconsistent
REM "range" (TV or PC) but better than it was. 
REM Also still not looked into subtitle each image with aspects of its path and name.
REM And there's no possibility of including the first few seconds of any video clips
REM (of arbitrary sizes, eg old/new/portrait/landscape etc) in the mix.
REM 

Set "slideshow_ffmpegexe64=C:\SOFTWARE\ffmpeg\0-homebuilt-x64\ffmpeg_OpenCL.exe"
Set "slideshow_mediainfoexe64=C:\SOFTWARE\MediaInfo\MediaInfo.exe"
Set "slideshow_ffprobeexe64=C:\SOFTWARE\ffmpeg\0-homebuilt-x64\ffprobe_OpenCL.exe"
Set "slideshow_Insomniaexe64=C:\SOFTWARE\Insomnia\64-bit\Insomnia.exe"

REM https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678121

call :maketempheader
REM ECHO after call --- !COMPUTERNAME! !DATE! !TIME! tempheader="!tempheader!"

set "inp=%~1"
set "leftmost_character=!inp:~,1!"
if /I "!leftmost_character!" == "C" (
	echo Cannot run this over any folders on the C: drive : '!inp!'
	pause
	exit
)

REM Ensure there's a single trailing backslash on the input
REM add a (another?) trailing backslash in case not at top level of drive or the user hasn't dropped something with one
set "source_folder=!inp!\"
REM change any trailing double backslash to a single backslash (in case already at top level folder) by optionally removing the last character
set "rightmost_character=!source_folder:~-2!"
if /I "!rightmost_character!" == "\\" (
	set "source_folder=!source_folder:~0,-1!"
)

REM get the rightmost folder name and use that as out output filename for the slideshow result
REM get the rightmost folder name, eg for "C:\FOLDER1\FOLDER2\FOLDER3\" return "FOLDER3" ... what happens if it's "g:\" ?
set "source_folder_noslash=!source_folder!"
if /I "!source_folder_noslash:~-1!" == "\" (
	set "source_folder_noslash=!source_folder_noslash:~0,-1!"
)
for %%f in ("%source_folder_noslash%") do (
	set "rightmost_foldername=%%~nxf"
)

if /I "!rightmost_foldername!" == "" (
	echo Cannot run this over a root folder : '!inp!'
	pause
	exit
)

REM echo leftmost_character="!leftmost_character!"
REM echo rightmost_foldername="!rightmost_foldername!"
REM echo source_folder="!source_folder!"
REM echo source_folder_noslash="!source_folder_noslash!"

set /a "picture_duration=4"

REM set the bitrates or HQ
set /a "bitrate_target=9000000"
set /a "bitrate_min=3000000"
set /a "bitrate_max=15000000"
set /a "bitrate_bufsize=15000000"
REM set the time base (PAL country)
set /a "timebase_numerator=1" 
set /a "timebase_denominator=25"
REM set picture duration via the PTS as an integer multiple of the timebase_denominator, so 1*25 = 25 (1 second)
set /a "gop_size=!timebase_denominator!"
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
set    "a_b=224k"
set /a "a_freq=44100"
set /a "a_cutoff=18000"


REM ---------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------
set "ffmpeg_concat_input_file=!source_folder!!rightmost_foldername!-!tempheader!-ffmpeg-concat-input.txt"
set "ffmpeg_concat_log_file=!source_folder!!rightmost_foldername!-!tempheader!-ffmpeg-concat-log.log"
set "ffmpeg_concat_slideshow_HQ=!source_folder!!rightmost_foldername!-!tempheader!.slideshow.HQ.mp4"
set "ffmpeg_concat_slideshow_DVD=!source_folder!!rightmost_foldername!-!tempheader!.slideshow.DVD.mpg"

DEL /F "!ffmpeg_concat_input_file!"
DEL /F "!ffmpeg_concat_log_file!"
DEL /F "!ffmpeg_concat_slideshow_HQ!"
DEL /F "!ffmpeg_concat_slideshow_DVD!"

REM overwrite any existing ffmpeg_concat_input_file in the echo :- no extra characters before the greater than character, not even a space !
echo ffconcat version 1.0> "!ffmpeg_concat_input_file!"
REM parse the files, specifically excludsing directory type files "/a:-d"
@echo off
echo Finding files, populating file "!ffmpeg_concat_input_file!"
set "x="
set "xe="
set "y="
for /f "tokens=*" %%G in ('dir /b /s /a:-d "!source_folder!"') DO (
	REM first, "escape" all backslashes in the full path name
	set "y=%%G"
	set ext4=!y:~-4!
	set ext5=!y:~-5!
	set ext6=!y:~-6!
	set "vid="
	set "pic="
	IF /I "!ext4!" == ".png"   set "pic=y"
	IF /I "!ext4!" == ".jpg"   set "pic=y"
	IF /I "!ext5!" == ".jpeg"  set "pic=y"
	IF /I "!ext4!" == ".gif"   set "pic=y"
	IF /I "!ext4!" == ".pdf"   set "pic=y"
	REM IF /I "!ext4!" == ".mp4"   set "vid=y"
	REM IF /I "!ext6!" == ".mpeg4" set "vid=y"
	REM IF /I "!ext4!" == ".mpg"   set "vid=y"
	REM IF /I "!ext5!" == ".mpeg"  set "vid=y"
	REM IF /I "!ext4!" == ".avi"   set "vid=y"
	REM IF /I "!ext6!" == ".mjpeg" set "vid=y"
	REM IF /I "!ext4!" == ".3gp"   set "vid=y"
	IF /I NOT "!vid!!pic!" == "" (
		set "x0=%%G"
		set "x=%%G"
		set "x=!x:\=\\!"
		set "xe=!x::=\:!"
		echo file '!x!'>> "!ffmpeg_concat_input_file!"
		REM echo duration !picture_duration!>> "!ffmpeg_concat_input_file!"
		echo file_packet_meta img_source_unescaped '%%G'>> "!ffmpeg_concat_input_file!"
		echo file_packet_meta img_source_escaped '!xe!'>> "!ffmpeg_concat_input_file!"
	)
)
REM Repeat final picture as apparently -f concat can ignore it or so someone said and it happened to me
IF /I NOT "!x!!xe!!x0!" == "" (
	echo file '!x!'>> "!ffmpeg_concat_input_file!"
	REM echo duration !picture_duration!>> "!ffmpeg_concat_input_file!"
	echo file_packet_meta img_source_unescaped '!x0!'>> "!ffmpeg_concat_input_file!"
	echo file_packet_meta img_source_escaped '!xe!'>> "!ffmpeg_concat_input_file!"
)
echo Finished finding files, populating file "!ffmpeg_concat_input_file!"
@echo on
REM type "!ffmpeg_concat_input_file!"

REM
REM changed to format=nv12 from format=yuv420p"
REM assume -temporal-aq 1 helps, since we run a second or so of frames all containing same image in all those frames
REM not preferred :
REM 	-vf "scale=1920:1080:eval=frame:flags=lanczos+accurate_rnd+full_chroma_int+full_chroma_inp:force_original_aspect_ratio=decrease:out_color_matrix=bt709:out_range=full,pad=1920:1080:-1:-1:eval=frame:color=black,settb=expr=!timebase_numerator!/!timebase_denominator!,setpts=!picture_duration!*N/TB,drawtext=box=0:fontsize=30:text='Frame %%{frame_num}':x=(w-text_w)/2:y=(h-text_h)/2:fix_bounds=1:fontcolor=black,setdar=16/9,format=nv12" ^
REM this version of the command is preferred in https://trac.ffmpeg.org/wiki/Slideshowy :
REM 	-vf "scale=1920:1080:eval=frame:flags=lanczos+accurate_rnd+full_chroma_int+full_chroma_inp:force_original_aspect_ratio=decrease:out_color_matrix=bt709:out_range=full,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:eval=frame:color=black,settb=expr=!timebase_numerator!/!timebase_denominator!,setpts=!picture_duration!*N/TB,drawtext=box=0:fontsize=30:text='Frame %%{frame_num}':x=(w-text_w)/2:y=(h-text_h)/2:fix_bounds=1:fontcolor=black,setdar=16/9,format=nv12" ^
REM
REM -concat sometimes produces bt470bg with ?PC? full range (also DVD compatible) and its no use playing with bt701 etc so comment that stuff out
REM 
set "cmd2="
set "cmd2=!cmd2!"!slideshow_ffmpegexe64!" "
set "cmd2=!cmd2! -hide_banner -v verbose"
set "cmd2=!cmd2! -stats"
set "cmd2=!cmd2! -reinit_filter 0 -safe 0 -auto_convert 1"
set "cmd2=!cmd2! -f concat -i "!ffmpeg_concat_input_file!""
REM NOTE: -f concat produces -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range indeterminate, sometimes tv sometimes pc
REM NOTE: gamma28 is the substitute for bt470bg in -trc
set "cmd2=!cmd2! -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp"
REM set "cmd2=!cmd2! -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv "
set "cmd2=!cmd2! -filter_complex ""
set "cmd2=!cmd2!format=yuv420p,"
REM set "cmd2=!cmd2!scale=1920x1080:eval=frame:force_original_aspect_ratio=decrease:flags=lanczos+accurate_rnd+full_chroma_int+full_chroma_inp:out_color_matrix=bt470bg:out_range=pc,"
    set "cmd2=!cmd2!scale=1920x1080:eval=frame:force_original_aspect_ratio=decrease:flags=lanczos+accurate_rnd+full_chroma_int+full_chroma_inp,"
set "cmd2=!cmd2!pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black:eval=frame,"
set "cmd2=!cmd2!settb=expr=!timebase_numerator!/!timebase_denominator!,setpts=!picture_duration!*N/TB,"
REM set "cmd2=!cmd2!drawtext=box=0:fontsize=30:text='Frame %%{frame_num}':x=(w-text_w)/2:y=(h-text_h)/2:fix_bounds=1:fontcolor=black,"
REM set "cmd2=!cmd2!colorspace=all=bt470bg:space=bt470bg:trc=bt470bg:primaries=bt470bg:range=tv:format=yuv420p:fast=0,"
set "cmd2=!cmd2!setdar=16/9"
set "cmd2=!cmd2!""
REM gamma28 is the substitute for bt470bg in -trc
set "cmd2=!cmd2! -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv "
set "cmd2=!cmd2! -strict experimental -c:v h264_nvenc -preset p7 -multipass fullres"
set "cmd2=!cmd2! -forced-idr 1 -g !gop_size!"
set "cmd2=!cmd2! -coder:v cabac -spatial-aq 1 -temporal-aq 1 -dpb_size 0"
set "cmd2=!cmd2! -bf:v 3 -b_ref_mode:v 0 -rc:v vbr -cq:v 0 -b:v %bitrate_target% -minrate:v %bitrate_min% -maxrate:v %bitrate_max% -bufsize %bitrate_bufsize%"
set "cmd2=!cmd2! -profile:v high -level 5.2"
set "cmd2=!cmd2! -movflags +faststart+write_colr"
REM if we had an audio source and mapped it, convert to aac like this
REM set "cmd2=!cmd2! -c:a libfdk_aac -ac 2 -b:a %a_b% -ar %a_freq% -cutoff %a_cutoff% 
set "cmd2=!cmd2! -an"
set "cmd2=!cmd2! -y "!ffmpeg_concat_slideshow_HQ!""
REM set "cmd2=!cmd2! -f null -"
REM

REM "C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe"  -hide_banner -v verbose -stats -reinit_filter 0 -safe 0 -auto_convert 1 -f concat -i "!ffmpeg_concat_input_file!"  -f null - >>"!ffmpeg_concat_log_file!" 2>&1
REM ah. -f concat sometimes produces this: Stream #0:0: Video: mjpeg (Baseline), 1 reference frame, yuvj420p(pc, bt470bg/unknown/unknown, center), 2032x1524, 25 fps, 25 tbr, 25 tbn
REM and sometimes yuvj420p(tv, bt470bg/unknown/unknown, center) dependong on the source images and their order.

echo !cmd2! >>"!ffmpeg_concat_log_file!" 2>&1
echo !cmd2!
!cmd2! >>"!ffmpeg_concat_log_file!" 2>&1
REM !cmd2!

pause

REM re-convert the new video produced above into DVD spec. It's quicker than re-doing -f concat again.
set "cmd_NO_color_conversion="
set "cmd_NO_color_conversion=!cmd_NO_color_conversion!"!slideshow_ffmpegexe64!" "
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -hide_banner -v verbose"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -stats"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -i "!ffmpeg_concat_slideshow_HQ!" -probesize 200M -analyzeduration 200M"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp -strict experimental"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -filter_complex ""
set "cmd_NO_color_conversion=!cmd_NO_color_conversion!pad=0:1080:0:-1,scale=720:576:flags='lanczos+accurate_rnd+full_chroma_int+full_chroma_inp',"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion!format=yuv420p,"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion!setdar=16/9"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion!""
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -target pal-dvd -r %v_rate% -g %v_gop_size%"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -b:v %v% -minrate:v %v_min% -maxrate:v %v_max% -bufsize %v_buf% -packetsize %v_pkt% -muxrate %v_mux%"
REM if we had an audio source and mapped it, convert to aac like this
REM set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -c:a ac3 -ac 2 -b:a %a_b% -ar %a_freq%
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -an"
set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -y "!ffmpeg_concat_slideshow_DVD!""
REM set "cmd_NO_color_conversion=!cmd_NO_color_conversion! -f null -"
REM

echo !cmd_NO_color_conversion! >>"!ffmpeg_concat_log_file!" 2>&1
echo !cmd_NO_color_conversion!
!cmd_NO_color_conversion! >>"!ffmpeg_concat_log_file!" 2>&1
REM !cmd_NO_color_conversion!

pause
exit

REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
REM --- start set a temp header to date and time
:maketempheader
@echo off
set "Datex=%DATE: =0%"
set yyyy=!Datex:~10,4!
set mm=!Datex:~7,2!
set dd=!Datex:~4,2!
set "Timex=%time: =0%"
set hh=!Timex:~0,2!
set min=!Timex:~3,2!
set ss=!Timex:~6,2!
set ms=!Timex:~9,2!
ECHO !DATE! !TIME! As at !yyyy!.!mm!.!dd!_!hh!.!min!.!ss!.!ms!  COMPUTERNAME="!COMPUTERNAME!"
set tempheader=!yyyy!.!mm!.!dd!.!hh!.!min!.!ss!.!ms!-!COMPUTERNAME!
REM --- end set a temp header to date and time
@echo on
goto :eof
REM +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

pause
exit


MISCELLANEOUS NOTES :

https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678121

https://superuser.com/questions/1661735/pattern-type-glob-or-other-jpg-wildcard-input-file-support-for-windows-10
ffmpeg -reinit_filter 0 -f concat -safe 0 -i "Test-ffmpeg.Txt" -vf "scale=1280:720:force_original_aspect_ratio=decrease:eval=frame,pad=1280:720:-1:-1:color=black:eval=frame,settb=AVTB,setpts=2*N/TB,format=yuv420p" -r 30 -movflags +faststart output.mp4

https://ffmpeg.org/ffmpeg-all.html#settb_002c-asettb
Set the default timebase value: settb=AVTB
https://ffmpeg.org/ffmpeg-all.html#setpts_002c-asetpts
N = The count of the input frame for video or the number of consumed samples, not including the current frame for audio, starting from 0.
TB = The timebase of the input timestamps.
Change the PTS (presentation timestamp) of the input frames: setpts=2*N/TB

https://ffmpeg.org/ffmpeg.html
-reinit_filter[:stream_specifier] integer (input,per-stream)
This boolean option determines if the filtergraph(s) to which this stream is fed gets reinitialized when input frame parameters change mid-stream. 
This option is enabled by default as most video and all audio filters cannot handle deviation in input frame properties. 
Upon reinitialization, existing filter state is lost, like e.g. the frame count n reference available in some filters. 
Any frames buffered at time of reinitialization are lost. 
The properties where a change triggers reinitialization are, for video, frame resolution or pixel format; for audio, sample format, sample rate, channel count or channel layout.
Set to 0 to disable reinitialization upon dimension change.

https://ffmpeg.org/ffmpeg-formats.html
-safe 0
If set to 1, reject unsafe file paths and directives.  The default is 1.
If set to 0, any file name is accepted.

https://ffmpeg.org/ffmpeg-formats.html#concat-1
file_packet_meta key value - Metadata of the packets of the file. The specified metadata will be set for each file packet. You can specify this directive multiple times to add multiple metadata entries.
option key value - Option to access, open and probe the file. Can be present multiple times.

stream_meta key value
Metadata for the stream. Can be present multiple times.

https://ffmpeg.org/ffmpeg-filters.html#drawtext
11.76 drawtext
Draw a text string or text from a specified file on top of a video, using the libfreetype library.

drawtext=box=0:fontsize=10:text='Frame \%{frame_num}':x=(w-text_w)/2:y=(h-text_h)/2:fix_bounds=1:fontcolor=black
drawtext=box=0:fontsize=10:text='Frame \%{frame_num}':x=(w-text_w)/2:y=h-(2*text_h):fix_bounds=1:fontcolor=black


-------------------------

This now works well for the crossfading: -reinit_filter 0 -r .2 -f concat -safe 0 -i concat_image_list_JPG.txt -c:v libx264 -crf 22 -pix_fmt yuv420p -vf zoompan=d=(4+2)/2:s=1920x1080:fps=1/2,framerate=25:interp_start=0:interp_end=255:scene=100 -r 25 -f mp4 "Slideshow 1080.mkv" -y but in the meantime I figured out how to more elegantly scale images of diffrent aspect ratios and came up with this video filter command: -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:color=black". How can I merge this command into the other video filter command? – 
				 
			   
																																								 
														 
				
			  
																												
																						  
			
			  
  
														  
					 
																																						  
																						
						   
								
													 
																						
						   
								
													 



					 



Try: ffmpeg -reinit_filter 0 -r .2 -f concat -safe 0 -i concat_image_list_JPG.txt -c:v libx264 -crf 22 -pix_fmt yuv420p -vf "scale=1920:1080,setsar=1:1,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:color=black,framerate=25:interp_start=0:interp_end=255:scene=100" -r 25 "Slideshow 1080.mkv" -y – 


Why are you using -f mp4 for MKV file? – 
Rotem
 Jan 17, 2022 at 6:34
It got copied from someone elses solution for some other issue I had. Should I remove it? I put all my commands together by trial and error and copying other people's commands. Your new solution does create a slideshow, however, I can't figure out how to parametrize the crossfades which are initiated too fast. I'd prefer them like with the former solution but set to zoompan=d=(6+2)/2. Also, images do not keep their aspect ratio as expected with your new solution. The solution in my first comment works well for crossfades and the second vf command for scaling and AR. Can they be combined? – 
Sonic
 Jan 17, 2022 at 9:19
Regarding -f mp4, remove it, since the output is MP4 container with .mkv extension. Regarding the aspect ration, you may try removing setsar=1:1. I can't see your issue since I don't have your input images. Regarding parametrizing the crossfades, I don't know the answer (I never used crossfades, I just used the filters from your question). You may post a new question regarding crossfades specifically. – 
Rotem
 Jan 17, 2022 at 11:51
Unfortunately, removing setsar=1:1 doesn't help. Please save this as a bat file cd /d "%~dp1" CHCP 1252 (for %%1 in (*.jpg) do @echo file '%%1') > "%~d1\%~p1\concat_image_list_JPG.txt" exit, put a few jpg files of different dimensions into the same folder with that batch file and drop one of the images onto it. The list of images in the folder will be saved as concat_image_list_JPG.txt. Then, you can try the commands we have discussed earlier. – 
Sonic
 Jan 17, 2022 at 12:25
I have tested it with sample frames. It looked OK considered the aspect ratio of the input and output is different. Please post a new question. Add few sample images to the post. Explain the desired output. – 
Rotem
 Jan 17, 2022 at 13:01
I think the thread title says it all. I want a slideshow of images incl. resizing to 1080, preserving correct aspect ratio plus crossfade between images. My first comment includes your working solution for the crossfading part as well as my separate command for proper resizing. Now we only need to combine the two -vf commands properly. – 
Sonic
 Jan 17, 2022 at 13:18
Crossfade in the title is too general. My answer addresses the specific issue you have descibred. If you don't like my answer it's fine... – 
Rotem
 Jan 17, 2022 at 13:39
If you want me to delete my answer, please let me know. – 
Rotem
 Jan 17, 2022 at 13:41
Your answer solves part of what I wanna accomplish. Don't delete it, it might be helpful for others, too. Thanks for your effort, much appreciated! – 
Sonic
 Jan 17, 2022 at 15:57
 