#PYTHON3
#
#	this_script_encoder.py
#	
#	https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page2#post2678789
#	use this script to encode output video, where it mixed images, mp4 and m2ts videos and rotated images, so this was encode.py:
#
import vapoursynth as vs
from vapoursynth import core
from subprocess import Popen, PIPE
from pathlib import Path
import sys
import os

def main(video_script, audio_script_or_file, output_path):
	#
	# this ONLY works if VSPip.exe and FFMPEG are in the same folder as portable vapoursynth
	# however the .py and .vpy scripts can be of other folders
	#
    PATH					= Path(os.getcwd())					#??? #Path(sys._MEIPASS) #if frozen
    #script					= str(PATH / 'python_modules' / f'{script}')	# {script} is the SOURCES script
    #script					= str(PATH / f'{script}')				# {script} is the SOURCES script in the current folder
    video_script			= str(f'{video_script}')				# {video_script} is a fully qualified SOURCES script filename
    audio_script_or_file	= str(f'{audio_script_or_file}')				# {audio_script_or_file} is a fully qualified SOURCES script filename
    VSPipe					= str(r'C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe')
    ffmpeg					= str(r'C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe')
    x264					= str(r'C:\SOFTWARE\ffmpeg\0-homebuilt-x64\x264.exe')
    neroAacEnc				= str(r'C:\SOFTWARE\NeroAAC\neroAacEnc.exe')
    Mp4box					= str(r'C:\SOFTWARE\mp4box\MP4Box.exe')
    #
	##import loadDLL #if frozen
    ##VS_PLUGINS_DIR = PATH / 'vapoursynth64/plugins'
    ##isDLLS_LOADED, DLLS_LOG = loadDLL.vapoursynth_dlls(core, VS_PLUGINS_DIR)
    #
	path       = Path(output_path)						# TURN A filename STRING INTO A PATH without the filename
    #temp_video = str(path.parent / f'{path.stem}.264')
    temp_video = str(path.parent / f'{path.stem}.tmp.mp4')
    temp_audio = str(path.parent / f'{path.stem}.tmp.m4a')

    vspipe_video = [VSPipe, '--container',  		'y4m',
                            video_script,
                            '-']

    x264_cmd = [x264,       #'--frames',           f'{len(video)}',
                            '--demuxer',           'y4m',  
                            '--crf',               '18',
                            '--vbv-maxrate',       '30000',
                            '--vbv-bufsize',       '30000',
                            '--keyint',            '60',
                            '--tune',              'film',
                            '--colorprim',         'bt709',
                            '--transfer',          'bt709',
                            '--colormatrix',       'bt709',
                            '--output',             temp_video,
                            '-']
	ffmpeg_vid_HQ_cmd = [	ffmpeg,
							'-hide_banner',			'',
							'-v',					'info',
							'-stats',				'',
							'-f',					'yuv4mpegpipe',
							'-i',					'pipe:',
							'-probesize',			'200M',
							'-analyzeduration',		'200M',
							'-sws_flags',			'lanczos+accurate_rnd+full_chroma_int+full_chroma_inp',
							'-filter_complex',		'"colorspace=all=bt709:space=bt709:trc=bt709:primaries=bt709:range=pc:format=yuv420p:fast=0,format=yuv420p,setdar=16/9"',
							# SD DVD is -colorspace bt470bg -color_primaries bt470bg -color_trc gamma28 -color_range tv
							'-colorspace',			'bt709',
							'-color_primaries',		'bt709',
							'-color_trc',			'bt709',
							'-color_range',			'pc',		# use tv or mpeg for limited range
							'-strict experimental',	'',
							'c:v',					'h264_nvenc',
							'-preset',				'p7',
							'-multipass',			'fullres',
							'-forced-idr',			'1',
							'-g',					'25',		# based on 25 fps
							'-coder:v',				'cabac',
							'-spatial-aq',			'1',		# 3900x with nvidia 2060 Super uses -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 # otherwise omit these 5 parameters
							'-temporal-aq',			'1',		# 3900x with nvidia 2060 Super uses -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 # otherwise omit these 5 parameters
							'-dpb_size',			'0',		# 3900x with nvidia 2060 Super uses -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 # otherwise omit these 5 parameters
							'-bf:v',				'3',		# 3900x with nvidia 2060 Super uses -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 # otherwise omit these 5 parameters
							'-b_ref_mode:v',		'0',		# 3900x with nvidia 2060 Super uses -spatial-aq 1 -temporal-aq 1 -dpb_size 0 -bf:v 3 -b_ref_mode:v 0 # otherwise omit these 5 parameters
							'-rc:v',				'vbr',
							'-b:v',					'9000000',
							'-minrate:v',			'3000000',
							'-maxrate:v',			'15000000',
							'-bufsize',				'15000000',
							'-profile:v',			'high',
							'-level',				'5.2',
							'-movflags',			'+faststart+write_colr',
							'-an',					'',	# NO AUDIO
							'-y',					temp_video]

    vspipe_audio_script = [	VSPipe, 
							'--outputindex',		'1',
                            '--container',			'wav',
                            audio_script_or_file,
                            '-']

    aac_cmd = [				neroAacEnc,
							'-ignorelength',		'',
                            '-lc',					'',
                            '-cbr',					'96000',
                            '-if',					'-',
                            '-of',					temp_audio]

    ffmpeg_script_to_aac_cmd = [
							ffmpeg,
							'-hide_banner',			'',
							'-v',					'info',
							'-stats',				'',
							'-f',					'yuv4mpegpipe',
							'-i',					'pipe:',
							'-vn',					'',
							'-c:a',					'libfdk_aac',
							'-ac',					'2',
							'-b:a',					'224K',
							'-ar',					'44100',
							'-cutoff',				'18000',
							'-y',					temp_audio]

	ffmpeg_audio_file_to_aac_cmd = [
							ffmpeg,
							'-hide_banner',			'',
							'-v',					'info',
							'-stats',				'',
							'-f',					'yuv4mpegpipe',
							'-i',					audio_script_or_file,
							'-vn',					'',	# NO VIDEO
							'-c:a',					'libfdk_aac',
							'-ac',					'2',
							'-b:a',					'224K',
							'-ar',					'44800',
							'-cutoff',				'18000',
							'-y',					temp_audio]

    mp4box_cmd = [			Mp4box,	
							'-add',					temp_video',
                            '-add',					f'{temp_audio}#audio',
                            '-new',					output_path]

    ffmpeg_mux_cmd = [		ffmpeg,
							'-hide_banner',			'',
							'-v',					'info',
							'-stats',				'',
							'-i',					temp_video,
							'-c:v',					'copy',
                            '-i',					temp_audio',
							'-c:a',					'copy',
							'-movflags',			'+faststart+write_colr',
                            '-y',					output_path]

	# ENCODE THE VIDEO
    p1 = Popen(vspipe_video, stdout=PIPE, stderr=PIPE)
    #p2 = Popen(x264_cmd, stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
    p2 = Popen(ffmpeg_vid_HQ_cmd, stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
    p1.stdout.close()
    p2.communicate()

	# ENCODE THE AUDIO, using a method depending on the .EXT in the incoming filename
	if audio_script_or_file[-3:].lower() == '.py'.lower() or audio_script_or_file[-4:].lower() == '.vpy'.lower():
		# create the audio .aac from a script via vspipe into ffmpeg
		p1 = Popen(vspipe_audio_script, stdout=PIPE, stderr=PIPE)
		#p2 = Popen(aac_cmd, stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
		p2 = Popen(ffmpeg_script_to_aac_cmd, stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
		p1.stdout.close()
		p2.communicate()
	else:
		# create the audio .aac from an existing audio file via ffmpeg directly
		p1 = Popen(ffmpeg_audio_file_to_aac_cmd)
		p1.communicate()

	# MUX THE VIDEO AND AUDIO USING FFMPEG DIRECTLY
    #p1 = Popen(mp4box_cmd)
    p1 = Popen(ffmpeg_mux_cmd)
    p1.communicate()

if __name__=='__main__':
    #
	# Scripts and outputs have full paths
	#
	# Called like:
	#
    #	python "this_script_encoder.py" "media_to_show_video.vpy" "media_to_show_audio.vpy" "output.mp4"
	#
	#		"this_script_encoder"		this script which encodes then muxes the video then the audio
	#
	#		"media_to_show_video.vpy"	is a python script to deliver a slideshow video of the images
	#
	#		"media_to_show_audio.vpy"	is a python script to deliver audio to be used as background music to the slideshow
	#			OR ...
	#		"media_to_show_audio.aac"	is an existing audio file of some kind and extension .EXT, to be used as background music to the slideshow
	#									if the file does NOT end with ".vpy" or ".py" then assume an audio file consumable by ffmpeg
	#
    if len(sys.argv) > 3:	# must be at least 3 arguments (plus one for the script name)
        main(sys.argv[1], sys.argv[2], sys.argv[3])	# argv[0]=???, argv[1]=script delivering video, argv[2]=script or file delivering audio, argv[3]=output .mp4 filename
