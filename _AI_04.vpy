# PYTHON3
# Version:
#	as at 2023.01.20
#
# Description:
#	Attempt to create a HD video slideshow of images and hopefully video clips from a folder tree.
#	Does 8-bit only, does not handle HDR conversions etc.
#	This script is consumed directly by ffmpeg as a .vpy input file, eg '-f vapoursynth -i "G:\folder\filename.vpy"'
#
# Acknowledgements:
#	With all due respect to _AI_
#	Original per _AI_ as updated in this thread and below
#		https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678241
#
# Environment:
#	Not wanting to run installers (well, I don't, anyhow) ... one has to setup a suitable environment ... eg
#		portable python into a nominated folder
#		portable vapoursynth overlaid in the same folder
#		an ffmpeg build with options for vapoursynth and NVenc enabled, copied into the same folder
#		portable pip downloaded into the same folder
#		a pip install of Pillow (refer below)
#		Donald Graft's DGDecNV extracted into the subfolder DGIndex (refer below)
#		suitable filters (refer below)
#	Thread for interest https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678484
#
# Filters:
#	Choose your own vapoursynth Filters, however here's the ones (actually or potentially) currently used in this script ...
#	Filter Dependencies with example installs into portable vapoursynth x64:
#		cd C:\SOFTWARE\Vapoursynth-x64\
#		REM after vsrepo.py and vsrupdate.py from https://github.com/vapoursynth/vsrepo into .\
#		.\python.exe .\vsrepo.py -p -t win64 -f -b vapoursynth64\plugins -s vapoursynth64\scripts install "FFTW3 Library"
#		.\python.exe .\vsrepo.py -p -t win64 -f -b vapoursynth64\plugins -s vapoursynth64\scripts install AssRender
#		.\python.exe .\vsrepo.py -p -t win64 -f -b vapoursynth64\plugins -s vapoursynth64\scripts install LSMASHSource
#		.\python.exe .\vsrepo.py -p -t win64 -f -b vapoursynth64\plugins -s vapoursynth64\scripts install FFmpegSource2
#		.\python.exe .\vsrepo.py -p -t win64 -f -b vapoursynth64\plugins -s vapoursynth64\scripts install imwri
#	And then mediainfo readings for a media file using MediaInfo.dll
#		REM per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
#		cd C:\SOFTWARE\Vapoursynth-x64\
#		pushd C:\TEMP
#		del MediaInfo*.dll
#		del MediaInfo*.py
#		del MediaInfo*.zip
#		REM check for latest version per REM https://mediaarea.net/en/MediaInfo/Download/Windows
#		set f="MediaInfo_DLL_22.12_Windows_x64_WithoutInstaller"
#		c:\software\wget\wget.exe -v -t 1 --server-response --timeout=360 -nd -np -nH --no-cookies --output-document="%f%.zip" "https://mediaarea.net/download/binary/libmediainfo0/22.12/%f%.zip" 
#		"C:\Program Files\WinZip\WZUNZIP.EXE" -e -o -^^ "%f%.zip" "C:\SOFTWARE\Vapoursynth-x64\" MediaInfo.dll Developers\Source\MediaInfoDLL\MediaInfoDLL.py Developers\Source\MediaInfoDLL\MediaInfoDLL3.py
#		popd
#		copy /b /y /z ".\MediaInfo*.py" vapoursynth64\scripts
#	And then DGDenoise as a part of DGDecodeNV in the DGDecNV package which is Donald Graft's very handy GPU-accelerated toolset 
#		per https://www.rationalqm.us/dgdecnv/dgdecnv.html and https://www.rationalqm.us/board/viewforum.php?f=8
#			which can be installed by extracting dgdecnv_???.zip into C:\SOFTWARE\Vapoursynth-x64\DGIndex\ per LoadPlugin usage below.
#	Finally
#		copy /Y /V vapoursynth64\scripts\*.py .\
#		.\python.exe .\vsrepo.py -p -t win64 -f -b vapoursynth64\plugins -s vapoursynth64\scripts installed | SORT > .\run_vsrepo_installed.txt
#		.\python.exe .\vsrepo.py -p -t win64 -f -b vapoursynth64\plugins -s vapoursynth64\scripts available | SORT > .\run_vsrepo_available.txt
#
# Usage:
#	Example usage with ffmpeg built with vapoursynth and NVEnc options enabled and using this .vpy as an input ...
#		set "f=_AI_03_no_crossfade"
#		"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -hide_banner -v verbose ^
#			-f vapoursynth -i "G:\HDTV\TEST\_AI_\!f!.vpy" -an ^
#			-map 0:v:0 ^
#			-vf "setdar=16/9" ^
#			-fps_mode passthrough ^
#			-sws_flags lanczos+accurate_rnd+full_chroma_int+full_chroma_inp ^
#			-strict experimental ^
#			-c:v h264_nvenc -pix_fmt nv12 -preset p7 -multipass fullres -forced-idr 1 -g 25 ^
#			-coder:v cabac -spatial-aq 1 -temporal-aq 1 ^
#			-dpb_size 0 -bf:v 3 -b_ref_mode:v 0 ^
#			-rc:v vbr -cq:v 0 -b:v 3500000 -minrate:v 100000 -maxrate:v 9000000 -bufsize 9000000 ^
#			-profile:v high -level 5.2 ^
#			-movflags +faststart+write_colr ^
#			-y "G:\HDTV\TEST\_AI_\!f!.mp4"

import vapoursynth as vs
from vapoursynth import core
from functools import partial
from pathlib import Path, PureWindowsPath
from ctypes import *		# for mediainfo ... load via ctypes.CDLL('.\MediaInfo.dll')
from typing import Union	# for mediainfo
import itertools
import math
import sys
import os
import glob
# To install Pillow in portable Python using Portable pip
# see https://pip.pypa.io/en/latest/installation/  for the portable version of pip, then eg
# cd C:\SOFTWARE\Vapoursynth-x64
# c:\software\wget\wget.exe -v -t 1 --server-response --timeout=360 -nd -np -nH --no-cookies --output-document="pip.pyz" "https://bootstrap.pypa.io/pip/pip.pyz"
# python pip.pyz --help
# python pip.pyz install --target .\ Pillow --force-reinstall --upgrade --upgrade-strategy eager  --verbose 
from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.ExifTags import TAGS
core.std.LoadPlugin(r'C:\SOFTWARE\Vapoursynth-x64\DGIndex\DGDecodeNV.dll') 	# note the hard-coded folder
core.avs.LoadPlugin(r'C:\SOFTWARE\Vapoursynth-x64\DGIndex\DGDecodeNV.dll') 	# note the hard-coded folder
CDLL(r'C:\SOFTWARE\Vapoursynth-x64\MediaInfo.dll')				# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372

DIRECTORY = r'G:\HDTV\TEST\_AI_\test_images'	# note the hard-coded folder we are going to process
########################################################################################################################################################
# We could read the folder name to process from a single line in file named ".\_AI_folder_to_process.txt"
# instead of it being the fixed string DIRECTORY above.
# Perhaps we should leave this un-commented since a missing file will mean just using the default DIRECTORY
#
DEFAULT_FILE_SPECIYING_A_FOLDER_TO_PROCESS = r'.\_AI_folder_to_process.txt' # no need for escaping the backslashes in a proper path, NOT ALWAYS THE CASE
try:
	txtfile = open(DEFAULT_FILE_SPECIYING_A_FOLDER_TO_PROCESS, 'r')
except OSError as err:
	#print(f'DEBUG: cannot Open file {DEFAULT_FILE_SPECIYING_A_FOLDER_TO_PROCESS}')
	#print(f"DEBUG: Unexpected {err=}, {type(err)=}")
	#raise
	pass
except Exception as err:
	#print(f'DEBUG: cannot Open file {DEFAULT_FILE_SPECIYING_A_FOLDER_TO_PROCESS}')
	#print(f"DEBUG: Unexpected {err=}, {type(err)=}")
	#raise
	pass
else:
	ll = len(txtfile.readlines())
	if ll!=1:
		#print(f'DEBUG: {DEFAULT_FILE_SPECIYING_A_FOLDER_TO_PROCESS} has {ll} lines which should only ever be "1"')
		pass
	else:
		txtfile.seek(0)	# rewind the file
		DIRECTORY = txtfile.readline().rstrip('\n')
		txtfile.close()
		print(f'INFO: As read from "{DEFAULT_FILE_SPECIYING_A_FOLDER_TO_PROCESS}" the incoming folder to process="{DIRECTORY}"')
########################################################################################################################################################

RECURSIVE			= True						# iterate all subfolders as well
PIC_EXTENSIONS		= [".png", ".jpg", ".jpeg", ".gif"]								# always lower case
VID_EXTENSIONS		= [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov"]	# always lower case
EEK_EXTENSIONS		= [".m2ts"]														# always lower case
EXTENSIONS			= PIC_EXTENSIONS + VID_EXTENSIONS + EEK_EXTENSIONS
VID_EEK_EXTENSIONS	= VID_EXTENSIONS + EEK_EXTENSIONS

TARGET_PIXEL_FORMAT	= vs.YUV420P8				# pixel format of the target video
DG_PIXEL_FORMAT		= vs.YUV420P16				# pixel format of the video for use by DG tools
TARGET_COLOURSPACE_MATRIX = r'709'				# HD, used by resize filter
TARGET_COLOURSPACE	= r'BT.709'					# HD, used by assrender.Subtitle filter
TARGET_WIDTH		= 1920						# target width,  watch for subsampling, it has to fit
TARGET_HEIGHT		= 1080						# target height, watch for subsampling, it has to fit
TARGET_FPSNUM		= 25						# for fps numerator		... PAL world bias
TARGET_FPSDEN		= 1							# for fps denominator	... PAL world bias
TARGET_FPS			= round(TARGET_FPSNUM / TARGET_FPSDEN,3)
DURATION_SEC		= 1							# seconds duration for images not videos
BLANK_CLIP_LENGTH	= int(math.ceil(0.1*TARGET_FPS))	# leading and trailing blank clip duration in frames with round-up. int(round(0.1*TARGET_FPS)) will round up/down
MIN_DURATION_SEC	= 0.75											### duration of display of an image, in seconds
MIN_DURATION_FRAMES	= int(math.ceil(MIN_DURATION_SEC * TARGET_FPS))	### duration of display of an image, in frames
MAX_DURATION_SEC	= 5											### max duration of display of a video, in seconds
MAX_DURATION_FRAMES	= int(math.ceil(MAX_DURATION_SEC * TARGET_FPS))	### max duration of display of a video, in frames
#
CROSS_DUR			= 0							# crossfade duration in frames, eg 5, 0 means so crossfade (0 looks good and doesn't chew extra space)
#CROSS_DUR			= 5							# crossfade duration in frames, eg 5, 0 means so crossfade (0 looks good and doesn't chew extra space)
BOX					= True						# True would initiate letterboxing or pillarboxing. False fills to TARGET_WIDTH,TARGET_HEIGHT
ADD_SUBTITLE		= True						# True adds a subtitle in the bottom right corner containing the last few parts of the path to the image/video
DOT_FFINDEX			= ".ffindex".lower()		# for removing temporary *.ffindex files at the end
#
UPSIZE_KERNEL   = 'Lanczos'
DOWNSIZE_KERNEL = 'Spline36'
#
MODX				= 2	   # mods for letterboxing calculations, example, for 411 YUV as an extreme
MODY				= 2	   # mods would have to be MODX=4, MODY=1 as minimum
#
MI					= MediaInfo()	# initialize per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372

###
def mediainfo_value(stream:int, track:int, param:str, path: Union[Path,str]) -> Union[int,float,str]:
	# NOTE: global MI is already setup as if a "constant" global variable
    if not stream in range(0,8):
        raise ValueError(f'ERROR: mediainfo_value: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
    if not isinstance(track, int) or track<0:
        raise ValueError(f'ERROR: mediainfo_value: track must be a positive integer')
    if not isinstance(param, str):
        raise ValueError(f'ERROR: mediainfo_value: param must be a string for particular stream, print(MI.Option_Static("Info_Parameters")')
    if not isinstance(path, (Path, str)):
        raise ValueError(f'ERROR: mediainfo_value: path must be Path or str class')    
    MI.Open(str(path))
    str_value = MI.Get(stream, track, param)
    info_option =  MI.Get(stream, track, param, InfoKind=Info.Options)
    MI.Close()
    if not str_value:
        return None
    if info_option:
        #returning a proper value type, int, float or str for particular parameter
        type_ = info_option[InfoOption.TypeOfValue] #type_=info_option[3] #_type will be 'I', 'F', 'T', 'D' or 'B'
        val = {'I':int, 'F':float, 'T':str, 'D':str, 'B':str}[type_](str_value)
        return val
    else:
        raise ValueError(f'ERROR: mediainfo_value: wrong parameter: "{param}" for given stream: {stream}')

###
def boxing(clip, W=TARGET_WIDTH, H=TARGET_HEIGHT):
	source_width, source_height = clip.width, clip.height
	if W/H > source_width/source_height:
		w = source_width*H/source_height
		x = int((W-w)/2)
		x = x - x%MODX
		x = max(0, min(x,W))
		clip = resize_clip(clip, W-2*x, H)
		if x: return clip.std.AddBorders(left=x, right=x, color=(16,128,128))  #RGB is out then (16,16,16)
		else: return clip
	else:
		h = source_height*W/source_width
		y = int((H-h)/2)
		y = y - y%MODY
		y = max(0, min(y,H))
		clip = resize_clip(clip, W, H-2*y)
		if y: return clip.std.AddBorders(top=y, bottom=y, color=(16,128,128))
		else: return clip

###
def resize_clip(clip,w,h, W=TARGET_WIDTH, H=TARGET_HEIGHT):
	if w>W or h>H:	resize = getattr(clip.resize, DOWNSIZE_KERNEL)	# get the resize function object ?handle? with the nominated kernel
	else:			resize = getattr(clip.resize, UPSIZE_KERNEL)	# get the resize function object ?handle? with the nominated kernel
	if clip.format.color_family==vs.RGB:
		#rgb to YUV, perhaps only for png images, figure out what matrix out is needed ... use the HD one REC.709
		#print("DEBUG: clip.format.color_family==vs.RGB")
		c =  resize(width=w, height=h, format=TARGET_PIXEL_FORMAT, matrix_s='709')
		return c
	else:
		#YUV to YUV
		#print("DEBUG: clip.format.color_family==vs.YUV?")
		c = resize(width=w, height=h, format=TARGET_PIXEL_FORMAT)
		# AH !!! the next line with matrix_s='709' can cause this:
		#		Error getting frame: Resize error: Resize error 3074: no path between colorspaces (2/2/2 => 1/2/2).
		# it seems missing "Matrix coefficients" metadata in the source may be the culprit
		#c = resize(width=w, height=h, format=TARGET_PIXEL_FORMAT, matrix_s='709')
		return c

###
def get_clip(path):
	if path.suffix.lower()   in EEK_EXTENSIONS:
		#print(f'DEBUG: get_clip: lsmas Video: {path.name}')
		clip = core.lsmas.LWLibavSource(str(path))
		#print(f'DEBUG: get_clip: Video info:\n{clip}')
	elif path.suffix.lower() in VID_EXTENSIONS:
		#print(f'DEBUG: get_clip: ffms2 Video: {path.name}')
		clip = core.ffms2.Source(str(path))	#ffms2 leaves *.ffindex files everywhere in folders.
		#clip = core.lsmas.LibavSMASHSource(str(path))
		#print(f'DEBUG: get_clip: Video info:\n{clip}')
	elif path.suffix.lower() in PIC_EXTENSIONS:
		#print(f'DEBUG: get_clip: ffms2 Video: {path.name}')
		clip = core.ffms2.Source(str(path))
	#	clip = core.imwri.Read(str(path)) # ImageWriter, if installed into vapoursynth folder
		#print(f'DEBUG: get_clip: Video info:\n{clip}')
	else:
		#print(f'DEBUG: get_clip: ffms2 Video: {path.name}')
		clip = core.ffms2.Source(str(path))	# if file extension not recognised, use this reader
		#print(f'DEBUG: get_clip: Video info:\n{clip}')

	# check for and picture/video rotation specified perhaps in EXIF but not auto-processed here by the file openers
	if path.suffix.lower()   in VID_EEK_EXTENSIONS:
		clip = rotation_check_MediaInfo(clip, path, save_rotated_image=False)	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678326
	else: # source is not a video type, i.e. an image
		clip = rotation_check_PIL(clip, path, save_rotated_image=False)	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678326

	# do video-specific or picture-specific changes
	if path.suffix.lower()   in VID_EEK_EXTENSIONS:	#if any sort of video, probably an old hand-held camera or phone, sometimes variable fps ...
		#print(f'DEBUG: get_clip: opened Video: {path.name}')
		#print(f'DEBUG: get_clip: opened Video: {path.name}\nVideo info:\n{clip}')
		#clip = core.text.Text(clip, path.name, alignment=3, scale=1)
		#clip = core.text.FrameNum(clip, alignment=5, scale=1)
		#clip = core.text.ClipInfo(clip, alignment=8, scale=1)
		#clip = core.text.FrameProps(clip, alignment=2, scale=1)
		source_fpsnum = clip.fps.numerator		# eg 25	# numerator   is 0 when the clip has a variable framerate.
		source_fpsden = clip.fps.denominator	# eg 1	# denominator is 1 when the clip has a variable framerate.
		source_fps = round(source_fpsnum / source_fpsden,3)
		source_duration_frames = clip.num_frames
		source_duration_secs = round((source_duration_frames / source_fps),3)
		source_width, source_height = clip.width, clip.height
		#print(f'DEBUG: get_clip: {source_width}x{source_height}\nsource_fpsnum:{source_fpsnum} source_fpsden:{source_fpsden}\nsource_fps:{source_fps}\nsource_duration_frames:{source_duration_frames}\nsource_duration_secs:{source_duration_secs}')
		# change framerate ? too hard for a small simple video sample, just "assume" target fps and ignore consequences of speed-up or slow-down or VFR
		clip = clip.std.AssumeFPS(fpsnum=TARGET_FPSNUM, fpsden=TARGET_FPSDEN)
		# if duration greater than out review maximum, clip it
		if source_duration_frames>(MAX_DURATION_FRAMES-1):
			clip = core.std.Trim(clip, first=0, last=(MAX_DURATION_FRAMES-1))
		# denoise ANY "small" dimension video clips, older videos likely to be noisy
		if source_width<TARGET_WIDTH or source_height<TARGET_HEIGHT:	 
			#print(f'INFO: applying DGDenoise to small {source_width}x{source_height} video {path.name}')
			# clip must be YUV420P16 for DGDenoise etc
			clip = clip.resize.Point(format=DG_PIXEL_FORMAT)		# convert to DG_PIXEL_FORMAT via resizer which does no resizing
			#clip = core.avs.DGDenoise(clip, strength=0.06, cstrength=0.06)
			clip = core.avs.DGDenoise(clip, strength=0.15, cstrength=0.15)
			clip = clip.resize.Point(format=TARGET_PIXEL_FORMAT)	# convert to TARGET_PIXEL_FORMAT via resizer which does no resizing
	else: # source is not a video type, i.e. an image
		# extend duration of a clip of an image
		clip = clip[0]*MIN_DURATION_FRAMES if len(clip)<MIN_DURATION_FRAMES else clip # make clip at least MIN_DURATION_FRAMES frames long if less than MIN_DURATION_FRAMES frames
	
	# either add borders to maintain aspect ratio (boxing), or just stretch to fit (yuk)
	if BOX:
		clip = boxing(clip, TARGET_WIDTH, TARGET_HEIGHT)
	else:
		clip = resize_clip(clip, TARGET_WIDTH, TARGET_HEIGHT)

	# Add a subtitle being the trailing 3 parts of the path
	if ADD_SUBTITLE:	# Add a subtitle being the trailing 3 parts of the path
		pwp = PureWindowsPath(path)
		n = len(pwp.parts)
		text_subpath_for_subtitles = "/" + pwp.parts[n-3] + "/" + pwp.parts[n-2] + "/" +  pwp.parts[n-1]
		# To tinker with .ass subs, see https://snapcraft.io/install/aegisub-procles/ubuntu
		# Also note from an aegisub created .ass file
		#	Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
		#	Style: h3333,Arial,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0.9,0.5,3,2,2,2,1
		# whereas default .assrender.Subtitle style="sans-serif,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,7,10,10,10,1"
		clip = core.assrender.Subtitle(clip, text_subpath_for_subtitles, style="sans-serif,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0.9,0.5,3,2,2,2,1", colorspace=TARGET_COLOURSPACE) # frame_width=TARGET_WIDTH, frame_height=TARGET_HEIGHT, 

	return clip

###
def get_path(path_generator):
	#get next path of desired extensions from generator, ignoring extensions we have not specified
	while 1:	# loop until we do a "return", hitting past the end of the iterator returns None
		try:
			path = next(path_generator)
			#print('DEBUG: get_path: get success, path.name=' + path.name)
		except StopIteration:
			return None
		if path.suffix.lower() in EXTENSIONS:	# only return files which are in known extensions
			#print('DEBUG: get_path: in EXTENSIONS success, path.name=' + path.name)
			return path
		  
###
def crossfade(a, b, duration):
	#gets crosfade part from end of clip a and start of clip b
	def fade_image(n, a, b):
		return core.std.Merge(a, b, weight=n/duration)
	if a.format.id != b.format.id or a.height != b.height or a.width != b.width:
		raise ValueError('crossfade: Both clips must have the same dimensions and format.')
	return core.std.FrameEval(a[-duration:], partial(fade_image, a=a[-duration:], b=b[:duration]))

###
def print_exif_data(exif_data):
	for tag_id in exif_data:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_data.get(tag_id)
	print(f'DEBUG: {tag:25}: {content}')
		
###
def print_exif_data2(exif_data):
	for tag_id in exif_data:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_data.get(tag_id)
		if isinstance(content, bytes):
			content = content.decode()
		print(f'DEBUG: {tag:25}: {content}')
	print()

###
def rotation_check_PIL(clip, path, save_rotated_image=False):
	# from PIL import Image, ExifTags, UnidentifiedImageError   # pip install Pillow, or equivalent
	# PIL Pillow module loads an image, checks if EXIF data, checks for 'Orientation'
	# The Python Pillow library is a fork of an older library called PIL. 
	# Older PIL stands for Python Imaging Library, and it's the original library that enabled Python to deal with images. 
	# PIL was discontinued in 2011 (that author died) and only supports Python 2.23 ... so use Pillow instead.
	# https://python-pillow.org/
	#print('DEBUG: rotation_check_PIL entered')
	try:
		image = Image.open(str(path))
	except UnidentifiedImageError:
		#print(f'DEBUG: rotation_check_PIL except UnidentifiedImageError immediate return now')
		return clip
	except PermissionError:
		#print(f'DEBUG: rotation_check_PIL except PermissionError Permission denied to load: {path} immediate return now')
		return clip
	except Exception as e:
		#print(f'DEBUG: rotation_check_PIL except Exception {e} immediate return now')
		return clip
	#print('DEBUG: rotation_check_PIL try on Image.open succeeded',flush=True)
	try:		
		for key in ExifTags.TAGS.keys():
			if ExifTags.TAGS[key] == 'Orientation':
				break
		exif = dict(image.getexif().items())
		value = exif[key]
	except (AttributeError, KeyError, IndexError):
		#print('DEBUG: rotation_check_PIL except AttributeError during for key in ExifTags.TAGS.keys(), immediate return now')
		return clip
	else:
		if   value == 3:
			print(f'INFO: PIL says auto-Rotating by 180 degrees {path}')
			clip = clip.std.Turn180()
		elif value == 8:
			print(f'INFO: PIL says auto-Rotating by  90 degrees {path}')
			clip = clip.std.Transpose().std.FlipVertical()
		elif value == 6:
			print(f'INFO: PIL says auto-Rotating by 270 degrees {path}')
			clip = clip.std.Transpose().std.FlipHorizontal()
		if save_rotated_image and value in [3,8,6]:
			#rotation degrees are in counterclockwise direction!
			rotate = {3:Image.ROTATE_180, 6:Image.ROTATE_270, 8:Image.ROTATE_90}
			image = image.transpose(rotate[value])
			path2 = path.parent / f'{path.stem}_rotated{path.suffix}'
			##image.save(str(path2))	# comment this out ... no writing new images, please
			#print(f'INFO: Rotated image {path} was NOT saved as requested into {path2}')
	#exif = image.getexif()
	#print_exif_data(exif)
	#print()
	#print_exif_data(exif.get_ifd(0x8769))
	#print()
	#
	#print_exif_data2(image.getexif())
	#print()
	#print_exif_data(image._getexif())
	#print()
	image.close()	
	return clip

###
def rotation_check_MediaInfo(clip, path, save_rotated_image=False):
	#print('DEBUG: rotation_check_MediaInfo entered')
	param = 'Rotation'
	value = mediainfo_value(Stream.Video, 0, param, path)
	if param == 'Rotation':
		if value is None:
			value = 0
		else:
			value = int(float(value)) # for some reason Rotation value type mediainfo carries as a string,  like: '180.00'
	#print(f'DEBUG: rotation_check_MediaInfo: value={value} for {path}')
	if   value == 180:
		print(f'INFO: MediaInfo says auto-Rotating by 180 degrees {path}')
		clip = clip.std.Turn180()
	elif value == 90:
		print(f'INFO: MediaInfo says auto-Rotating by 90 degrees {path}')
		clip = clip.std.Transpose().std.FlipVertical()
	elif value == 270:
		print(f'INFO: MediaInfo says auto-Rotating by 270 degrees {path}')
		clip = clip.std.Transpose().std.FlipHorizontal()
	else:
		clip = clip
	return clip

###################################################################################################################################################

### MAIN 
if RECURSIVE:
	glob_var="**/*.*"			# recursive
	ff_glob_var="**/*.ffindex"	# for .ffindex file deletion recursive
else:
	glob_var="*.*"				# non-recursive
	ff_glob_var="*.ffindex"		# for .ffindex file deletion non-recursive
print(f'INFO: Processing {DIRECTORY} with recursive={RECURSIVE} glob_var={glob_var} ...\nwith Extensions {EXTENSIONS}',flush=True)
Count_of_files = 0
paths = Path(DIRECTORY).glob(glob_var) #generator of all paths in a directory, files starting with . won't be matched by default
#sys.exit(0)
path = get_path(paths)	#pre-fetch first path
if path is None:
	raise ValueError(f'Extensions: {EXTENSIONS}, not found in {DIRECTORY}')
blank_clip = core.std.BlankClip(format=TARGET_PIXEL_FORMAT, width=TARGET_WIDTH, height=TARGET_HEIGHT, length=BLANK_CLIP_LENGTH, color=(16,128,128))
clips = blank_clip	# initialize the accumulated clips with a starting small blank clip
if CROSS_DUR>0:	
	crossfade_blank_clip = blank_clip[0]*MIN_DURATION_FRAMES if len(blank_clip)<MIN_DURATION_FRAMES else blank_clip
	prior_clip_for_crossfade = crossfade_blank_clip
#---
while not (path is None):	# first clip already pre-retrieved ready for this while loop
	Count_of_files = Count_of_files + 1
	print(f'INFO: processing {Count_of_files} {str(path)}')
	#if (Count_of_files % 10)==0:
	#	print(f'{Count_of_files},',end="",flush=True)
	#	if (Count_of_files % (10*10*3))==0:
	#		print("",flush=True)
	this_clip = get_clip(path)
	#this_clip = core.text.Text(this_clip, text_subpath_for_subtitles, alignment=9, scale=1)
	#this_clip = core.text.FrameNum(this_clip, alignment=2, scale=1)
	#this_clip = core.text.ClipInfo(this_clip, alignment=8, scale=1)
	#this_clip = core.text.FrameProps(this_clip, alignment=2, scale=1)
	if CROSS_DUR>0:	
		#print(f'DEBUG: doing crossfade in while loop')
		crossfade_clip = crossfade(prior_clip_for_crossfade, this_clip, CROSS_DUR)
		# for now, don't do equivalent of this from _AI_ ... right  = right_clip[CROSS_DUR:-CROSS_DUR]
		clips = clips + crossfade_clip + this_clip
		prior_clip_for_crossfade = this_clip
	else:
		clips = clips + this_clip
	path = get_path(paths)		# get next path to process in this while loop
#---
# perhaps a finishing crossfade to black ?
if CROSS_DUR>0:	
	#print(f'DEBUG: doing final crossfade after while loop')
	crossfade_clip = crossfade(prior_clip_for_crossfade, crossfade_blank_clip, CROSS_DUR)
	# for now, don't do equivalent of this from _AI_ ... right  = right_clip[CROSS_DUR:-CROSS_DUR]
	clips = clips + crossfade_clip + this_clip
clips = clips + blank_clip		# end the accumulated clips with a finishing small blank clip
clips = clips.std.AssumeFPS(fpsnum=TARGET_FPSNUM, fpsden=TARGET_FPSDEN)
print("")
print(f'INFO: Finished processing {Count_of_files} image/video files.',flush=True)
# Cleanup any temporary .ffindex files created by ffms2
print(f'INFO: Removing temporary *.ffindex files from folder {DIRECTORY} with recursive={RECURSIVE} ...',flush=True)
pp = DIRECTORY + "/" + ff_glob_var
ffindex_files = glob.glob(pp, recursive=RECURSIVE)
Count_of_files_removed = 0
for ff in ffindex_files:
	if ff.lower()[-len(DOT_FFINDEX):] == DOT_FFINDEX:	# double check the file really does have ext .ffindex
		try:
			Count_of_files_removed = Count_of_files_removed + 1
			print(f'INFO: removing {Count_of_files_removed} {ff}',flush=True)
			os.remove(ff)
			#if (Count_of_files_removed % (10))==0:
			#	print(f'{Count_of_files_removed},',end="",flush=True)
			#	if (Count_of_files_removed % (10*10*3))==0:
			#		print("",flush=True)
		except OSError as ee:
			print("Error: %s : %s" % (ff, ee.strerror),flush=True)
print("")
print(f'INFO: Finished removing {Count_of_files_removed} .ffindex files.',flush=True)
# hmm, audio ? maybe later using source filter "bas" ?
print(f'INFO: Done.',flush=True)
clips.set_output()
#------
