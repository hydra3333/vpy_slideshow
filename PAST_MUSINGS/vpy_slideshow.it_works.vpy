# PYTHON3
#
# "C:\SOFTWARE\MediaInfo\MediaInfo.exe" --full "G:\DVD\PAT-SLIDESHOWS\vpy_slideshow_in_development\20180801_125800.mp4"
#
# Version:	as at 2023.03.04
#
# Description:
#
#	Attempt to create a 'HD' video slideshow of images and hopefully video clips from a directory tree.
#	Is 8-bit only. Does not handle HDR conversions etc.  Does not handle framerate conversions.
#	This script is consumed by vspipe as a .vpy input file and delivered to ffmpeg
#
#		VSPipe.exe --container y4m video_script.vpy - | ffmpeg -f yuv4mpegpipe -i pipe: ...
#
#	CRITICAL NOTE:
#		When piping a YUV format, the vspipe --y4m flag conveys the header info,
#		pixel type, fps from the script; But the receiving ffmpeg pipe also NEEDS to
#		indicate -f yuv4mpegpipe , OTHERWISE it will be considered a raw video pipe.
#		See https://forum.videohelp.com/threads/397728-ffmpeg-accepting-vapoursynth-vpy-input-directly-and-gpu-accelerated-speed?highlight=vspipe#post2679858
#
# Acknowledgements:
#	With all due significant respect to _AI_
#	Original per _AI_ as updated in this thread and below
#		https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678241
#
# Environment:
#
#	One has to setup a suitable environment ... eg
#		portable python into a nominated directory
#		portable vapoursynth overlaid in the same directory ... Assume vapoursynth API4 using release >= R60
#		an ffmpeg build with options for vapoursynth and NVenc enabled, copied into the same directory
#		portable pip downloaded into the same directory
#		a pip install of Pillow etc (refer below)
#		suitable filters (refer below)
#	There's a 'run_once' to set things up initially.
#	Thread for interest https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678484
#
# Usage:
#
#	Notes:
#		When piping a YUV format, the vspipe --container y4m  flag conveys the header info,
#		pixel type, fps from the script; But the receiving ffmpeg pipe also has to
#		indicate -f yuv4mpegpipe , otherwise it will be considered a raw video pipe
#		(in that latter cause you wouldn't use --y4m).  
#		Example:
#			"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --filter-time --container y4m SCRIPT.vpy - | "C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -f yuv4mpegpipe -i pipe: ...
#			"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --filter-time --container y4m ".\vpy_slideshow.vpy" - | "C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -f yuv4mpegpipe -i pipe: -f null NUL
#			"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --filter-time --container y4m ".\vpy_slideshow.vpy" - > NUL
#			"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -f vapoursynth -i ".\vpy_slideshow.vpy" -f null NUL
#	or for non-vapoursynth testing:
#			"C:\SOFTWARE\Vapoursynth-x64\python.exe" "G:\DVD\PAT-SLIDESHOWS\vpy_slideshow_in_development\vpy_slideshow.vpy"
#
#		All Information and Debug mesages are printed to stderr
#
import vapoursynth as vs
#from vapoursynth import core
core = vs.core
#core.num_threads = 1

from datetime import datetime, date, time, timezone
from fractions import Fraction
from functools import partial
from pathlib import Path, PureWindowsPath
from ctypes import *		# for mediainfo ... load via ctypes.CDLL(r'.\MediaInfo.dll')
from typing import Union	# for mediainfo
from collections import defaultdict, OrderedDict
from enum import Enum
from enum import auto
#from strenum import StrEnum
#from strenum import LowercaseStrEnum
#from strenum import UppercaseStrEnum
import itertools
import math
import random
import sys
import os
import glob
import configparser	# or in v3: configparser 
import yaml
import pprint
import ast
import uuid
import gc	# for inbuilt garbage collection
# THE NEXT STATEMENT IS ONLY FOR DEBUGGING AND WILL CAUSE EXTRANEOUS OUTPUT TO STDERR
#gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS)	# for debugging, additional garbage collection settings, writes to stderr https://docs.python.org/3/library/gc.html to help detect leaky memory issues
num_unreachable_objects = gc.collect()	# collect straight away

from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.ExifTags import TAGS

CDLL(r'MediaInfo.dll')				# note the hard-coded folder	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption		# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372

#core.std.LoadPlugin(r'DGDecodeNV.dll')
#core.avs.LoadPlugin(r'DGDecodeNV.dll')

# A Special function needed at the top DEFAULT_INI_FILE_SPECIFYING_PARAMETERS and DEFAULT_DIRECTORY_LIST
def fully_qualified_directory_no_trailing_backslash(directory_name):
	# make into a fully qualified directory string stripped and without a trailing backslash
	# also remove extraneous backslashes which get added by things like abspath
	new_directory_name = os.path.abspath(directory_name)
	if directory_name[-1:] == (r'\ '.strip()):		# r prefix means the string is treated as a raw string so all escape codes will be ignored. EXCEPT IF THE \ IS THE LAST CHARACTER IN THE STRING !
		new_directory_name = directory_name[:-1]		# remove any trailing backslash
	new_directory_name = new_directory_name.replace(r'\\\\ '.strip(), r'\\ '.strip())	# trailing spaces in the r'' are required here andwill be stripped or it fails
	new_directory_name = new_directory_name.strip()
	return new_directory_name

###
# Define GLOBALS and initialize them
#
global IS_SILENT
IS_SILENT = True						# start silently
global IS_DEBUG
IS_DEBUG = False						# default DEBUG to False
global IS_DEBUG_SYSTEM_OVERRIDE
IS_DEBUG_SYSTEM_OVERRIDE = False		# for major debugging ONLY: this is always FALSE otherwide ...
#
# 2022.03.19, see what happens with multi [ "MI = MediaInfo()" and matching "del MI" ] instead of one global declaration
#global MI
#MI = MediaInfo()	# initialize a global for mediainfo per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
#
global TERMINAL_WIDTH					# for use by PrettyPrinter
TERMINAL_WIDTH = 160
global objPrettyPrint
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc

##########
global DEFAULT_INI_FILE_SPECIFYING_PARAMETERS
DEFAULT_INI_FILE_SPECIFYING_PARAMETERS = fully_qualified_directory_no_trailing_backslash(r'.\SLIDESHOW_PARAMETERS.ini')	# r prefix means the string is treated as a raw string so all escape codes will be ignored. EXCEPT IF THE \ is the last character in the string ! So don't put one there.

global DEFAULT_DIRECTORY_LIST	# NOTE: make values into fully qualified paths in list DEFAULT_DIRECTORY_LIST
pre_default_directories_list =	[	os.getcwd() ,		# current working directory
								#	r'.\ ' ,			# (notice a trailing space is required with r'' path strings attempting to end with a backslash)
								]
DEFAULT_DIRECTORY_LIST = []
for ddl in pre_default_directories_list:
	DEFAULT_DIRECTORY_LIST.append(fully_qualified_directory_no_trailing_backslash(ddl))
	
global DEFAULT_TEMP_DIRECTORY_LIST
DEFAULT_TEMP_DIRECTORY_LIST = [ fully_qualified_directory_no_trailing_backslash(os.getcwd()+r'\\temp') ]

##########
# some "working" globals
global last_file_opened_with_ffms2
global last_file_opened_with_imwri
global last_file_opened_with_LWLibavSource
global last_file_opened_with_LibavSMASHSource
global Count_of_files
#
# https://github.com/vapoursynth/vapoursynth/issues/940#issuecomment-1465041338
# When calling rezisers etc, ONLY use these values:
#	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
#	ZIMG_RANGE_FULL     = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
# but when obtaining from frame properties and comparing etc, use the vs values from
# frame properties even though the vapoursynth values are incorrect (opposite to the spec)
global ZIMG_RANGE_LIMITED
ZIMG_RANGE_LIMITED  = 0		# /**< Studio (TV) legal range, 16-235 in 8 bits. */
global ZIMG_RANGE_FULL
ZIMG_RANGE_FULL     = 1		# /**< Full (PC) dynamic range, 0-255 in 8 bits. */


###
# Public Domain software: vs_transitions
#		https://github.com/OrangeChannel/vs-transitions
# vs-transitions SOURCE CODE:
#		https://raw.githubusercontent.com/OrangeChannel/vs-transitions/master/vs_transitions/__init__.py
# vs-transitions DOCUMENTATION:
#		https://vapoursynth-transitions.readthedocs.io/en/latest/api.html
# modified and saved as vs_transitions.py from
#		https://raw.githubusercontent.com/OrangeChannel/vs-transitions/master/vs_transitions/__init__.py
import vs_transitions

###
global crossfade_type_list
crossfade_type_list = list(map(str.lower,[		'none',
												'random',
												'fade', 
												'fade_to_black',
												'fade_from_black',
												'wipe',
												'push', 
												'slide_expand',
												'squeeze_slide', 
												'squeeze_expand', 
												'cover', 
												'reveal', 
												'curtain_cover', 
												'curtain_reveal', 
												'peel', 
												'pixellate',
												'cube_rotate', 
												#'linear_boundary', 
												]))
global crossfade_type_list_no_black_fades
crossfade_type_list_no_black_fades = list(map(str.lower,[
												'none',
												#'random',
												'fade', 
												#'fade_to_black',
												#'fade_from_black',
												'wipe',
												'push', 
												'slide_expand',
												'squeeze_slide', 
												'squeeze_expand', 
												'cover', 
												'reveal', 
												'curtain_cover', 
												'curtain_reveal', 
												'peel', 
												'pixellate',
												'cube_rotate', 
												#'linear_boundary', 
												]))

global crossfade_direction_list
crossfade_direction_list = []
for v in vs_transitions.Direction:
	crossfade_direction_list.append(v.value)

###
def print_DEBUG(*args, **kwargs):	# PRINT TO stderr
	# per https://stackoverflow.com/questions/5574702/how-do-i-print-to-stderr-in-python
	if (not IS_SILENT) or IS_DEBUG_SYSTEM_OVERRIDE:
		if IS_DEBUG or IS_DEBUG_SYSTEM_OVERRIDE:
			right_now = datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
			print(f'{right_now} DEBUG:', *args, **kwargs, file=sys.stderr, flush=True)

###
def print_NORMAL(*args, **kwargs):	# PRINT TO stderr
	# per https://stackoverflow.com/questions/5574702/how-do-i-print-to-stderr-in-python
	if (not IS_SILENT) or IS_DEBUG_SYSTEM_OVERRIDE:
		right_now = datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
		print(f'{right_now}', *args, **kwargs, file=sys.stderr, flush=True)

###
def get_mediainfo_specs(path: Union[Path,str]):
	mi_video_params = [
	'Format',                                        # : Format used
	'Format/String',                                 # : Format used + additional features
	'Format_Profile',                                # : Profile of the Format (old XML Profile@Level@Tier format
	'Format_Level',                                  # : Level of the Format (only MIXML)
	'Format_Tier',                                   # : Tier of the Format (only MIXML)
	'HDR_Format',                                    # : Format used
	'HDR_Format_Version',                            # : Version of this format
	'HDR_Format_Profile',                            # : Profile of the Format
	'HDR_Format_Level',                              # : Level of the Format
	'HDR_Format_Settings',                           # : Settings of the Format
	'HDR_Format_Compatibility',                      # : Compatibility with some commercial namings
	'MaxCLL',                                        # : Maximum content light level
	'MaxFALL',                                       # : Maximum frame average light level
	'Duration',                                      # : Play time of the stream in ms
	'Width',                                         # : Width (aperture size if present) in pixel
	'Height',                                        # : Height in pixel
	'PixelAspectRatio',                              # : Pixel Aspect ratio
	'DisplayAspectRatio',                            # : Display Aspect ratio
	'Rotation',                                      # : Rotation as a real number eg 180.00	# CLOCKWISE in mediainfo
	'FrameRate',                                     # : Frames per second
	'FrameRate_Num',                                 # : Frames per second, numerator
	'FrameRate_Den',                                 # : Frames per second, denominator
	'FrameCount',                                    # : Number of frames
	'Standard',                                      # : NTSC or PAL
	'ColorSpace',                                    # : 
	'ChromaSubsampling',                             # : 
	'BitDepth',                                      # : 16/24/32
	'ScanType',                                      # : 
	'colour_description_present',                    # : Presence of colour description "Yes" or not "Yes" if not None
	'colour_range',                                  # : Colour range for YUV colour space
	'colour_primaries',                              # : Chromaticity coordinates of the source primaries
	'transfer_characteristics',                      # : Opto-electronic transfer characteristic of the source picture
	'matrix_coefficients',                           # : Matrix coefficients used in deriving luma and chroma signals from the green, blue, and red primaries
	]
	#print_DEBUG(f'get_mediainfo_specs: path={path} type(path)={type(path)} mi_video_params=\n{objPrettyPrint.pformat(mi_video_params)}')
	mi_video_dict = mediainfo_value_dict(Stream.Video, 0, mi_video_params, path)
	#print_DEBUG(f'get_mediainfo_specs: mediainfo specs=\n{objPrettyPrint.pformat(mi_video_dict)}')
	return mi_video_dict

###
def mediainfo_value_dict(stream:int, track:int, param:list, path: Union[Path,str]) -> Union[int,float,str]:
	# A wrapper for mediainfo_value_worker
	# Given a LIST of parameter names, return a dict of names/values of properties
	# eg
	#	param:
	#	[ 	'ColorSpace',                                    # : 
	#		'ChromaSubsampling',                             # : 
	#		'BitDepth',                                      # : 16/24/32
	#		'ScanType',                                      # : 
	#		'colour_description_present',                    # : Presence of colour description "Yes" or not "Yes" if not None
	#		'colour_range',                                  # : Colour range for YUV colour space
	#		'colour_primaries',                              # : Chromaticity coordinates of the source primaries
	#		'transfer_characteristics',                      # : Opto-electronic transfer characteristic of the source picture
	#		'matrix_coefficients',                           # : Matrix coefficients used in deriving luma and chroma signals from the green, blue, and red primaries
	#	]
	#	returns something like this (some values can be None):
	#		{'ColorSpace': 'YUV', 'ChromaSubsampling': '4:2:0', 'BitDepth': 8, 'ScanType': 'Progressive', 
	#		'colour_description_present': 'Yes', 'colour_range': 'Limited', 'colour_primaries': 'BT.709',
	#		'transfer_characteristics': 'BT.709', 'matrix_coefficients': 'BT.709'}
	#global MI
	if not stream in range(0,8):
		raise ValueError(f'ERROR: mediainfo_value_dict: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
	if not isinstance(track, int) or track<0:
		raise ValueError(f'ERROR: mediainfo_value_dict: track must be a positive integer')
	if not isinstance(param, list):
		raise ValueError(f'ERROR: mediainfo_value_dict: param must be a list of str parameters for a particular stream, ion_Static("Info_Parameters")')
	if not isinstance(path, (Path, str)):
		raise ValueError(f'ERROR: mediainfo_value_dict: path must be Path or str class')
	MI = MediaInfo()
	MI.Open(str(path))
	local_dict = {}
	for p in param:
		value = mediainfo_value_worker(MI, stream, track, p, path)
		local_dict[p] = value	# any of str, int, float, or None
		#print_DEBUG(f'"{p}" = \t\t\t\t"{value}"\t\t\ttype={type(value)}\t\t\tisinstance(value,str)={isinstance(value,str)}\t\tisinstance(value,int)={isinstance(value,int)}\t\tisinstance(value,bool)={isinstance(value,bool)}\t\tisinstance(value,float)={isinstance(value,float)}')
	MI.Close()
	del MI	# free the object
	return local_dict

###
def mediainfo_value(stream:int, track:int, param:str, path: Union[Path,str]) -> Union[int,float,str]:
	# A wrapper for mediainfo_value_worker, which gets and returns a single parameter
	# This function permits mediainfo_value_worker to be recycled elsewhere to be called mutiple times per a single MI.open
	#global MI
	if not stream in range(0,8):
		raise ValueError(f'ERROR: mediainfo_value: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
	if not isinstance(track, int) or track<0:
		raise ValueError(f'ERROR: mediainfo_value: track must be a positive integer')
	if not isinstance(param, str):
		raise ValueError(f'ERROR: mediainfo_value: param must be a string for particular stream, ion_Static("Info_Parameters")')
	if not isinstance(path, (Path, str)):
		raise ValueError(f'ERROR: mediainfo_value: path must be Path or str class')   
	MI = MediaInfo()
	MI.Open(str(path))
	val = mediainfo_value_worker(MI, stream, track, param, path)
	MI.Close()
	del MI	# free the object
	return val

###
def mediainfo_value_worker(MI, stream:int, track:int, param:str, path: Union[Path,str]) -> Union[int,float,str]:
	# gets and returns a single parameter
	#global MI
	if not stream in range(0,8):
		raise ValueError(f'ERROR: mediainfo_value_worker: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
	if not isinstance(track, int) or track<0:
		raise ValueError(f'ERROR: mediainfo_value_worker: track must be a positive integer')
	if not isinstance(param, str):
		raise ValueError(f'ERROR: mediainfo_value_worker: param must be a string for particular stream, ion_Static("Info_Parameters")')
	if not isinstance(path, (Path, str)):
		raise ValueError(f'ERROR: mediainfo_value_worker: path must be Path or str class')    
	#MI = MediaInfo()
	#MI.Open(str(path)) # CHANGED: open/close in calling routine, allowing this to be called mutiple times
	str_value = MI.Get(stream, track, param)
	info_option =  MI.Get(stream, track, param, InfoKind=Info.Options)
	#MI.Close() 		# CHANGED: open/close in calling routine, allowing this to be called mutiple times
	#del MI	# free the object
	if not str_value:
		del str_value
		del info_option
		return None
	if info_option:
		#returning a proper value type, int, float or str for particular parameter
		type_ = info_option[InfoOption.TypeOfValue] #type_=info_option[3] #_type will be 'I', 'F', 'T', 'D' or 'B'
		try:	# sometimes mediainfo flags an INT or a FLOAT which cannou be ocnverted, so catch those
			val = {'I':int, 'F':float, 'T':str, 'D':str, 'B':str}[type_](str_value)
		except Exception as e:
			print_DEBUG(f'CONVERSION EXCEPTION ON val =["I":int, "F":float, "T":str, "D":str, "B":str][type_](str_value) ... type_="{type_}" param="{param}" str_value="{str_value}" path={path}')
			print_DEBUG(f"Unexpected Error {e=}, {type(e)=} {str(e)=}")
			val = None
			#raise
			pass
	else:
		raise ValueError(f'ERROR: mediainfo_value_worker: wrong parameter: "{param}" for given stream: {stream}')
	del str_value
	del info_option
	return val
###
def boxing(clip, W, H):
	# ensure aspect ratio of an original image/video is preserved by adding black bars where necessary
	source_width, source_height = clip.width, clip.height
	if W/H > source_width/source_height:
		w = source_width*H/source_height
		x = int((W-w)/2)
		x = x - x%calc_ini["MODX"]
		x = max(0, min(x,W))
		clip = resize_clip(clip, W-2*x, H)
		if x:
			return clip.std.AddBorders(left=x, right=x, color=(16,128,128))  #RGB is out then (16,16,16)
		else:
			return clip
	else:
		h = source_height*W/source_width
		y = int((H-h)/2)
		y = y - y%calc_ini["MODY"]
		y = max(0, min(y,H))
		clip = resize_clip(clip, W, H-2*y)
		if y:
			return clip.std.AddBorders(top=y, bottom=y, color=(16,128,128))
		else:
			return clip

###
def resize_clip(clip,w,h):
	# w = calculated interim target width  before addborders
	# h = calculated interim target height before addborders
	W = clip.width					# current clip width before resizing
	H = clip.height					# current clip height before resizing
	resize = None
	xyz = None
	if w>=W or h>=H:	# the clip needs to be increased in size in at least one dimension, or is the same
		resize = getattr(clip.resize, calc_ini["UPSIZE_KERNEL"])	# get the resize function object ?handle? with the nominated kernel
		xyz = "UPSIZE_KERNEL"
	else:			# the clip needs to be reduced in size in at least one dimension
		resize = getattr(clip.resize, calc_ini["DOWNSIZE_KERNEL"])	# get the resize function object ?handle? with the nominated kernel
		xyz = "DOWNSIZE_KERNEL"
	c = clip
	if c.format.color_family==vs.RGB:
		#rgb to YUV, perhaps only for png images, figure out what matrix out is needed ... use the HD one REC.709
		print_DEBUG(f'resize_clip: incoming clip properties before RGB resize: c.format.name="{c.format.name}" c.format.color_family="{c.format.color_family}" c.format.sample_type="{c.format.sample_type}" c.format.bits_per_sample="{c.format.bits_per_sample}" c.format.bytes_per_sample="{c.format.bytes_per_sample}" c.format.num_planes="{c.format.num_planes}" c.format.subsampling_w="{c.format.subsampling_w}" c.format.subsampling_h="{c.format.subsampling_h}"')
		with d.get_frame(0) as f:
			print_DEBUG(f'resize_clip: incoming frame properties before RGB resize: w={c.width} h={c.height} fps={c.fps} {objPrettyPrint.pformat(c)} {objPrettyPrint.pformat(f.props)}')
		print_DEBUG(f'resize_clip: TARGET resize properties: width={w}, height={h}, format={calc_ini["WORKING_PIXEL_FORMAT"]}, calc_ini["TARGET_COLOR_RANGE_I_ZIMG"]={calc_ini["TARGET_COLOR_RANGE_I_ZIMG"]}), primaries={calc_ini["TARGET_COLOR_PRIMARIES_I"]}, transfer={calc_ini["TARGET_COLOR_TRANSFER_I"]},  matrix={calc_ini["TARGET_COLORSPACE_MATRIX_I"]}')
		# https://www.vapoursynth.com/doc/functions/video/resize.html https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini["WORKING_PIXEL_FORMAT"], matrix=calc_ini["TARGET_COLORSPACE_MATRIX_I"], transfer=calc_ini["TARGET_COLOR_TRANSFER_I"], primaries=calc_ini["TARGET_COLOR_PRIMARIES_I"], range=calc_ini["TARGET_COLOR_RANGE_I_ZIMG"])
		c = core.std.AssumeFPS(clip=c, fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
		print_DEBUG(f'resize_clip: incoming clip properties after RGB resize: c.format.name="{c.format.name}" c.format.color_family="{c.format.color_family}" c.format.sample_type="{c.format.sample_type}" c.format.bits_per_sample="{c.format.bits_per_sample}" c.format.bytes_per_sample="{c.format.bytes_per_sample}" c.format.num_planes="{c.format.num_planes}" c.format.subsampling_w="{c.format.subsampling_w}" c.format.subsampling_h="{c.format.subsampling_h}"')
		with c.get_frame(0) as f:
			print_DEBUG(f'resize_clip: outgoing frame properties after RGB resize: w={c.width} h={c.height} fps={c.fps} {c} {objPrettyPrint.pformat(f.props)}')
	elif c.format.color_family==vs.YUV:
		print_DEBUG(f'resize_clip: incoming clip properties before YUV resize: c.format.name="{c.format.name}" c.format.color_family="{c.format.color_family}" c.format.sample_type="{c.format.sample_type}" c.format.bits_per_sample="{c.format.bits_per_sample}" c.format.bytes_per_sample="{c.format.bytes_per_sample}" c.format.num_planes="{c.format.num_planes}" c.format.subsampling_w="{c.format.subsampling_w}" c.format.subsampling_h="{c.format.subsampling_h}"')
		with c.get_frame(0) as f:
			print_DEBUG(f'resize_clip: incoming frame properties before YUV resize: w={c.width} h={c.height} fps={c.fps} {objPrettyPrint.pformat(c)} {objPrettyPrint.pformat(f.props)}')
		print_DEBUG(f'resize_clip: TARGET resize properties: width={w}, height={h}, format={calc_ini["WORKING_PIXEL_FORMAT"]}, calc_ini["TARGET_COLOR_RANGE_I_ZIMG"]={calc_ini["TARGET_COLOR_RANGE_I_ZIMG"]}), primaries={calc_ini["TARGET_COLOR_PRIMARIES_I"]}, transfer={calc_ini["TARGET_COLOR_TRANSFER_I"]},  matrix={calc_ini["TARGET_COLORSPACE_MATRIX_I"]}')
		# https://www.vapoursynth.com/doc/functions/video/resize.html https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini["WORKING_PIXEL_FORMAT"], matrix=calc_ini["TARGET_COLORSPACE_MATRIX_I"], transfer=calc_ini["TARGET_COLOR_TRANSFER_I"], primaries=calc_ini["TARGET_COLOR_PRIMARIES_I"], range=calc_ini["TARGET_COLOR_RANGE_I_ZIMG"])	
		c = core.std.AssumeFPS(clip=c, fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
		# AH !!! the above line with matrix_s='709' can cause this error:
		# 		Resize error 3074: no path between colorspaces (2/2/2 => 1/1/1). May need to specify additional colorspace parameters.
		# It usually means the matrix/transfer/primaries are unknown 
		# *** and you have to specify the input colorspace parameters yourself. *** Note: 2 means “unspecified” according to the ITU-T recommendation.
		print_DEBUG(f'resize_clip: incoming clip properties after YUV resize: c.format.name="{c.format.name}" c.format.color_family="{c.format.color_family}" c.format.sample_type="{c.format.sample_type}" c.format.bits_per_sample="{c.format.bits_per_sample}" c.format.bytes_per_sample="{c.format.bytes_per_sample}" c.format.num_planes="{c.format.num_planes}" c.format.subsampling_w="{c.format.subsampling_w}" c.format.subsampling_h="{c.format.subsampling_h}"')
		with c.get_frame(0) as f:
			print_DEBUG(f'resize_clip: outgoing frame properties after YUV resize: w={c.width} h={c.height} fps={c.fps} {c} {objPrettyPrint.pformat(f.props)}')
	else:
		#resize.(vnode clip[, int width, int height, int format, enum matrix, enum transfer, enum primaries, enum range, 
		#			enum chromaloc, enum matrix_in, enum transfer_in, enum primaries_in, enum range_in, enum chromaloc_in, 
		#			float filter_param_a, float filter_param_b, string resample_filter_uv, float filter_param_a_uv, float filter_param_b_uv, 
		#			string dither_type="none", string cpu_type, float src_left, float src_top, float src_width, float src_height, float nominal_luminance])
		print_DEBUG(f'resize_clip: incoming clip properties before non-vs.RGB,non-vs.YUV resize: c.format.name="{c.format.name}" c.format.color_family="{c.format.color_family}" c.format.sample_type="{c.format.sample_type}" c.format.bits_per_sample="{c.format.bits_per_sample}" c.format.bytes_per_sample="{c.format.bytes_per_sample}" c.format.num_planes="{c.format.num_planes}" c.format.subsampling_w="{c.format.subsampling_w}" c.format.subsampling_h="{c.format.subsampling_h}"')
		with c.get_frame(0) as f:
			print_DEBUG(f'resize_clip: incoming frame properties before non-vs.RGB,non-vs.YUV resize: w={c.width} h={c.height} fps={c.fps} {objPrettyPrint.pformat(c)} {objPrettyPrint.pformat(f.props)}')
		print_DEBUG(f'resize_clip: TARGET resize properties: width={w}, height={h}, format={calc_ini["WORKING_PIXEL_FORMAT"]}, calc_ini["TARGET_COLOR_RANGE_I_ZIMG"]={calc_ini["TARGET_COLOR_RANGE_I_ZIMG"]}), primaries={calc_ini["TARGET_COLOR_PRIMARIES_I"]}, transfer={calc_ini["TARGET_COLOR_TRANSFER_I"]},  matrix={calc_ini["TARGET_COLORSPACE_MATRIX_I"]}')
		# https://www.vapoursynth.com/doc/functions/video/resize.html https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini["WORKING_PIXEL_FORMAT"], matrix=calc_ini["TARGET_COLORSPACE_MATRIX_I"], transfer=calc_ini["TARGET_COLOR_TRANSFER_I"], primaries=calc_ini["TARGET_COLOR_PRIMARIES_I"], range=calc_ini["TARGET_COLOR_RANGE_I_ZIMG"])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		c = core.std.AssumeFPS(clip=c, fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
		# AH !!! the avove line with matrix_s='709' can cause this error:
		# 		Resize error 3074: no path between colorspaces (2/2/2 => 1/1/1). May need to specify additional colorspace parameters.
		# It usually means the matrix/transfer/primaries are unknown 
		# *** and you have to specify the input colorspace parameters yourself. *** Note: 2 means “unspecified” according to the ITU-T recommendation.
		print_DEBUG(f'resize_clip: incoming clip properties after non-vs.RGB,non-vs.YUV resize: c.format.name="{c.format.name}" c.format.color_family="{c.format.color_family}" c.format.sample_type="{c.format.sample_type}" c.format.bits_per_sample="{c.format.bits_per_sample}" c.format.bytes_per_sample="{c.format.bytes_per_sample}" c.format.num_planes="{c.format.num_planes}" c.format.subsampling_w="{c.format.subsampling_w}" c.format.subsampling_h="{c.format.subsampling_h}"')
		with c.get_frame(0) as f:
			print_DEBUG(f'resize_clip: outgoing frame properties after non-vs.RGB,non-vs.YUV resize: w={c.width} h={c.height} fps={c.fps} {c} {objPrettyPrint.pformat(f.props)}')
	del resize
	del xyz
	return c

###
def get_clip_specs(clip=None, path=None, ext=None):
	# find and return specs about the clip
	global last_file_opened_with_ffms2
	global last_file_opened_with_imwri
	global last_file_opened_with_LWLibavSource
	global last_file_opened_with_LibavSMASHSource
	if clip is None:
		raise ValueError(f'ERROR: get_clip_specs: "clip" not passed as an argument to get_clip_specs')
	if path is None:
		##raise ValueError(f'ERROR: get_clip_specs: "path" not passed as an argument to get_clip_specs')
		# we can use get_clip_specs on any clip including blank_clip and forego rotation checks if we check for is None then
		pass
	if ext is None:
		raise ValueError(f'ERROR: get_clip_specs: "ext" not passed as an argument to get_clip_specs')
	print_DEBUG(f'get_clip_specs: clip=\n{clip}')
	## https://www.vapoursynth.com/doc/pythonreference.html
	# Create a local dict of Clip and Frame properties, ready for later validation/resetting if need be of _Matrix/_Transfer/_Primaries/_ColorRange
	clip_specs = {}
	clip_specs["width"] = clip.width
	clip_specs["height"] = clip.height
	clip_specs["num_frames"] = clip.num_frames
	clip_specs["fps"] = clip.fps
	clip_specs["format_name"] = clip.format.name
	clip_specs["color_family"] = clip.format.color_family.value		# .value
	clip_specs["sample_type"] = clip.format.sample_type.value		# .value	If the format is integer or floating point based.
	clip_specs["bits_per_sample"] = clip.format.bits_per_sample
	clip_specs["bytes_per_sample"] = clip.format.bytes_per_sample
	clip_specs["num_planes"] = clip.format.num_planes
	clip_specs["subsampling_w"] = clip.format.subsampling_w
	clip_specs["subsampling_h"] = clip.format.subsampling_h
	print_DEBUG(f'get_clip_specs: JUST BEFORE "with clip.get_frame(0) as f:" path="{path}" ext="{ext}" clip={clip} clip_specs={objPrettyPrint.pformat(clip_specs)}')
	with clip.get_frame(0) as f:
		clip_specs["_Matrix"] = f.props["_Matrix"] if "_Matrix" in f.props else None
		clip_specs["_Transfer"] = f.props["_Transfer"] if "_Transfer" in f.props else None
		clip_specs["_Primaries"] = f.props["_Primaries"] if "_Primaries" in f.props else None
		clip_specs["_ColorRange"] = f.props["_ColorRange"] if "_ColorRange" in f.props else None
		clip_specs["_ChromaLocation"] = f.props["_ChromaLocation"] if  "_ChromaLocation" in f.props else None
		clip_specs["_DurationDen"] = f.props["_DurationDen"] if "_DurationDen" in f.props else None
		clip_specs["_DurationNum"] = f.props["_DurationNum"] if "_DurationNum" in f.props else None
		clip_specs["_FieldBased"] = f.props["_FieldBased"] if "_FieldBased" in f.props else None
		clip_specs["_PictType"] = f.props["_PictType"] if "_PictType" in f.props else None
	# check for picture/video rotation specified perhaps in EXIF but not auto-processed here by the file openers
	if path is None:
		rotation_value = 0
		rotation_direction = calc_ini["Rotation_clockwise"]
	else:
		# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
		# so ... rotation_direction is returned as "anti-clockise" or "clockwise" using  calc_ini["Rotation_anti-clockwise"] and calc_ini["Rotation_clockwise"]
		if ext in calc_ini["VID_EEK_EXTENSIONS"]:
			rotation_value, rotation_direction = auto_rotation_value_MediaInfo(clip, path)	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678326
		else: # source is not a video type, i.e. an image
			rotation_value, rotation_direction  = auto_rotation_value_PIL(clip, path)	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678326
	clip_specs["auto_rotation_degrees"] = rotation_value
	clip_specs["auto_rotation_direction"] = rotation_direction
	clip_specs["opened_with_ffms2"] = last_file_opened_with_ffms2
	clip_specs["opened_with_imwri"] = last_file_opened_with_imwri
	clip_specs["opened_with_LWLibavSource"] = last_file_opened_with_LWLibavSource
	clip_specs["opened_with_LibavSMASHSource"] = last_file_opened_with_LibavSMASHSource
	# try to obtain mediainfo specs for the current file
	# which we can use in guessing frame properties when ffms2 fails to yield them
	# Of interest, sample example values of use in the returned dict:
	# 	'ColorSpace': 'YUV'
	#	'ChromaSubsampling': '4:2:0'
	#	'BitDepth': 8
	#	'ScanType': 'Progressive'
	#	'colour_description_present': 'Yes'
	#	'colour_range': 'Limited'
	#	'colour_primaries': 'BT.709'
	#	'transfer_characteristics': 'BT.709'
	#	'matrix_coefficients': 'BT.709'
	if path is None:
		mediainfo_specs = {}
	else:
		mediainfo_specs = get_mediainfo_specs(path)
	print_DEBUG(f'get_clip_specs: mediainfo specs=\n{objPrettyPrint.pformat(mediainfo_specs)}')
	#
	# OK we have retrieved whatever specs are availabe from the image/clip.
	# There may be gaps in those.
	# Sometimes, ffms2 delvers content with missing metadata tellng us what the source frame properties are.
	# Perhaps mediainfo can find out for us.
	# Experience show usually not though, but it can't hurt to try
	# **********
	# Guess the Specs Pass #1 before we resort to total guesses.
	# **********
	# initialise whether we made guesses, and put in draft settings
	clip_specs["guessed_Matrix"] = False
	clip_specs["proposed_Matrix"] = clip_specs["_Matrix"]
	clip_specs["guessed_Primaries"] = False
	clip_specs["proposed_Primaries"] = clip_specs["_Primaries"]
	clip_specs["guessed_Transfer"] = False
	clip_specs["proposed_Transfer"] = clip_specs["_Transfer"]
	clip_specs["guessed_ColorRange"] = False
	clip_specs["proposed_ColorRange"] = clip_specs["_ColorRange"]

	# **********
	# Define translation tables from mediainfo (a bit of these are calculated based on the current clip, so do not create these globally)
	# Define translation tables from mediainfo return values to "vs" constants used to inform other choices
	# **********
	mi_standard_list = { 'Component', 'NTSC', 'PAL', None,}
	print_DEBUG(f'get_clip_specs: translation_table mi_standard_list=\n{objPrettyPrint.pformat(mi_standard_list)}')
	# values of video stream colour_primaries seen returned by  mediainfo used to convert mediainfo to "vs" ColorPrimaries
	mi_color_primaries_dict = {			'BT.2020' : 				vs.ColorPrimaries.PRIMARIES_BT2020,
										'BT.601 NTSC' :				vs.ColorPrimaries.PRIMARIES_ST170_M,		# ? newer than ColorPrimaries.PRIMARIES_BT470_M 
										'BT.601 PAL' :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
										'BT.709' :					vs.ColorPrimaries.PRIMARIES_BT709,
										#None :						None,
										# not seen, check them anyway
										'BT.470_BG' :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
										'BT.470 BG' :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
										'BT.470 PAL' :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
										'BT.470_PAL' :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
										'BT.470_M' :				vs.ColorPrimaries.PRIMARIES_ST170_M,
										'BT.470 M' :				vs.ColorPrimaries.PRIMARIES_ST170_M,
										'BT.470 NTSC' :				vs.ColorPrimaries.PRIMARIES_ST170_M,
										}
	print_DEBUG(f'get_clip_specs: translation_table mi_color_primaries_dict=\n{objPrettyPrint.pformat(mi_color_primaries_dict)}')
	# values of video stream transfer_characteristics seen returned by  mediainfo used to convert mediainfo to "vs" TransferCharacteristics
	mi_transfer_characteristics_dict = {'BT.470 System B/G' :		vs.TransferCharacteristics.TRANSFER_BT470_BG,
										'BT.601' :					vs.TransferCharacteristics.TRANSFER_BT601,
										'BT.709' :					vs.TransferCharacteristics.TRANSFER_BT709 ,
										#None :						None,
										# not seen, check them anyway
										'BT.470 System M' :			vs.TransferCharacteristics.TRANSFER_BT470_M,
										'BT.BT2020 10' :			vs.TransferCharacteristics.TRANSFER_BT2020_10,
										'BT.BT2020 12' :			vs.TransferCharacteristics.TRANSFER_BT2020_12,
										'ST.2084' :					vs.TransferCharacteristics.TRANSFER_ST2084,
										}
	print_DEBUG(f'get_clip_specs: translation_table mi_transfer_characteristics_dict=\n{objPrettyPrint.pformat(mi_transfer_characteristics_dict)}')
	# values of video stream matrix_coefficients seen returned by  mediainfo used to convert mediainfo to "vs" MatrixCoefficients
	mc_bt601 = vs.MatrixCoefficients.MATRIX_BT470_BG
	if 'Standard' in mediainfo_specs and mediainfo_specs['Standard'] is not None:
		if 'NTSC'.lower() in mediainfo_specs['Standard'].lower():
			mc_bt601 = vs.MatrixCoefficients.MATRIX_ST170_M
	if 'colour_primaries' in mediainfo_specs  and mediainfo_specs['colour_primaries'] is not None:
		if 'NTSC'.lower() in  mediainfo_specs['colour_primaries'].lower():	# if the substring string is in the string
			mc_bt601 = vs.MatrixCoefficients.MATRIX_ST170_M
		if  mediainfo_specs['colour_primaries'].lower() in list(map(str.lower,[ 'BT.470 M', 'BT.470 M', 'BT.470_M', 'BT.601 NTSC', 'BT.470 NTSC' ])):
			mc_bt601 = vs.MatrixCoefficients.MATRIX_ST170_M
	mi_matrix_coefficients_dict = {		'BT.470 System B/G' :		vs.MatrixCoefficients.MATRIX_BT470_BG,
										'BT.601' : 					mc_bt601,									# assume PAL unless colour_primaries/Standard say NTSC then vs.MatrixCoefficients.MATRIX_ST170_M 
										'BT.709' :					vs.MatrixCoefficients.MATRIX_BT709,
										'BT.2020 non-constant' :	vs.MatrixCoefficients.MATRIX_BT2020_NCL,
										'BT.2020 constant' :		vs.MatrixCoefficients.MATRIX_BT2020_CL,
										#None :						None,
										# not seen, check them anyway
										}
	print_DEBUG(f'get_clip_specs: translation_table mi_matrix_coefficients_dict=\n{objPrettyPrint.pformat(mi_matrix_coefficients_dict)}')
	# values of video stream colour_range seen returned by  mediainfo # used to convert mediainfo to "vs" ColorRange
	mi_colour_range_dict = {			'Full' :					vs.ColorRange.RANGE_FULL,
										'Limited' :					vs.ColorRange.RANGE_LIMITED,
										#None :						None,
										}
	print_DEBUG(f'get_clip_specs: translation_table mi_colour_range_dict={objPrettyPrint.pformat(mi_colour_range_dict)}')
	
	# **********
	# now start making the guessing in pass #1
	if True:
		if  clip_specs["_Matrix"] == vs.MatrixCoefficients.MATRIX_UNSPECIFIED or clip_specs["_Matrix"] is None:	# _Matrix is usually defined and the rest may not be. (ffms2 seems to usually yield MATRIX_BT470_BG ?)
			if 'matrix_coefficients' in mediainfo_specs:
				if mediainfo_specs['matrix_coefficients'] is not None:
					clip_specs["guessed_Matrix"] = True
					clip_specs["proposed_Matrix"] = mi_matrix_coefficients_dict[mediainfo_specs['matrix_coefficients']]	# translate to "vs." if possible
					print_DEBUG(f'get_clip_specs: Guess the Specs Pass #1 translated mediainfo matrix_coefficients "{mediainfo_specs["matrix_coefficients"]}" to "{clip_specs["proposed_Matrix"]}"')
		if  clip_specs["_Transfer"] == vs.TransferCharacteristics.TRANSFER_UNSPECIFIED or clip_specs["_Transfer"] is None:
			if 'transfer_characteristics' in mediainfo_specs:
				if mediainfo_specs['transfer_characteristics'] is not None:
					clip_specs["guessed_Transfer"] = False
					clip_specs["proposed_Transfer"] = mi_transfer_characteristics_dict[mediainfo_specs['transfer_characteristics']]	# translate to "vs." if possible
					print_DEBUG(f'get_clip_specs: Guess the Specs Pass #1 translated mediainfo transfer_characteristics "{mediainfo_specs["transfer_characteristics"]}" to "{clip_specs["proposed_Transfer"]}"')
		if  clip_specs["_Primaries"] == vs.ColorPrimaries.PRIMARIES_UNSPECIFIED or clip_specs["_Primaries"] is None:
			if 'colour_primaries' in mediainfo_specs:
				if mediainfo_specs['colour_primaries'] is not None:
					clip_specs["guessed_Primaries"] = True
					clip_specs["proposed_Primaries"] = mi_color_primaries_dict[mediainfo_specs['colour_primaries']]	# translate to "vs." if possible
					print_DEBUG(f'get_clip_specs: Guess the Specs Pass #1 translated mediainfo colour_primaries "{mediainfo_specs["colour_primaries"]}" to "{clip_specs["proposed_Primaries"]}"')
		if clip_specs["_ColorRange"] is None:
			if 'colour_range' in mediainfo_specs:
				if mediainfo_specs['colour_range'] is not None:
					clip_specs["guessed_ColorRange"] = True
					clip_specs["proposed_ColorRange"] = mi_colour_range_dict[mediainfo_specs['colour_range']]	# translate to "vs." if possible
					print_DEBUG(f'get_clip_specs: Guess the Specs Pass #1 translated mediainfo colour_range "{mediainfo_specs["colour_range"]}" to "{clip_specs["proposed_ColorRange"]}"')

	# **********
	# Guess the Specs Pass #2 once we've had a god with medinfo values ..
	# Sometimes, ffms2 delvers content with missing metadata tellng us what the source frame properties are 
	# So ... now we really guess.
	# **********
	# if not already specified, guess a new _Matrix ... explainer: https://docs.rs/av-data/0.4.1/av_data/pixel/index.html https://docs.rs/av-data/0.4.1/av_data/pixel/enum.MatrixCoefficients.html
	if  clip_specs["_Matrix"] == vs.MatrixCoefficients.MATRIX_UNSPECIFIED or clip_specs["_Matrix"] is None:	# _Matrix is usually defined and the rest may not be. (ffms2 usually yields MATRIX_BT470_BG)
		print_DEBUG(f'get_clip_specs: MatrixCoefficients.MATRIX_UNSPECIFIED: incoming clip_specs=\n{objPrettyPrint.pformat(clip_specs)}')
		clip_specs["guessed_Matrix"] = True
		if ext in calc_ini["PIC_EXTENSIONS"]:	#PIC # assume opened by ffms2 (ffms2 usually yields MATRIX_BT470_BG for images)
			print_DEBUG(f'get_clip_specs: PIC: MatrixCoefficients.MATRIX_UNSPECIFIED in PIC, choosing a default')
			if last_file_opened_with_ffms2:
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT470_BG
				print_DEBUG(f'get_clip_specs: PIC: MatrixCoefficients.MATRIX_UNSPECIFIED in PIC, opened by ffms2, replacement _Matrix={clip_specs["proposed_Matrix"]}')
			else:
				print_DEBUG(f'get_clip_specs: PIC: MatrixCoefficients.MATRIX_UNSPECIFIED in PIC, opened by non-ffms2')
				#### This is a poor guess, last resort, if there is no other way to deduce matrix.
				# NOTE: ffms2 usually yields MATRIX_BT470_BG for IMAGES regardless of what width/height they may be.
				if  clip_specs["width"] <= 720 and clip_specs["height"] <= 480:				# Likely NTSC SD
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_ST170_M
				elif clip_specs["width"]  <= 720 and clip_specs["height"] <= 576:				# Likely PAL SD
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT470_BG
				elif clip_specs["width"]  <= 1280 and clip_specs["height"] <= 720:				# Likely PAL HD
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT709
				elif clip_specs["width"]  <= 1920 and clip_specs["height"] <= 1088:				# Likely PAL HD
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT709
				elif clip_specs["width"]  <= 3840 and clip_specs["height"] <= 2160:				# Likely UHD
					# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
					# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
					# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
					# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
					# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
					# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
					# because the benefits are considered modest and entail some additional complexity
					#clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_CL					#     Constant Luminance
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_NCL				# Non-Constant Luminance
				elif clip_specs["width"]  <= 7680 and clip_specs["height"] <= 4320:				# Likely 8K
					# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
					# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
					# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
					# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
					# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
					# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
					# because the benefits are considered modest and entail some additional complexity
					#clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_CL					#     Constant Luminance
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_NCL 				# Non-Constant Luminance
				else:
					raise ValueError(f'ERROR: get_clip_specs: PIC: unable to guess default _Matrix in PIC to replace MatrixCoefficients.MATRIX_UNSPECIFIED')
				print_DEBUG(f'get_clip_specs: PIC: MatrixCoefficients.MATRIX_UNSPECIFIED ({vs.MatrixCoefficients.MATRIX_UNSPECIFIED}) in PIC, opened by non-ffms2, replacement _Matrix={clip_specs["proposed_Matrix"]}')
		elif ext in calc_ini["VID_EEK_EXTENSIONS"]:	#VID 
			print_DEBUG(f'get_clip_specs: VID: MatrixCoefficients.MATRIX_UNSPECIFIED in VID')
			#### This is a poor guess, last resort, if there is no other way to deduce matrix.
			# NOTE: ffms2 usually yields MATRIX_BT470_BG for IMAGES regardless of what width/height they may be.
			if  clip_specs["width"] <= 720 and clip_specs["height"] <= 480:	# Likely NTSC SD
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_ST170_M
			elif clip_specs["width"]  <= 720 and clip_specs["height"] <= 576:				# Likely PAL SD
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT470_BG
			elif clip_specs["width"]  <= 1280 and clip_specs["height"] <= 720:				# Likely PAL HD
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT709						# HD
			elif clip_specs["width"]  <= 1920 and clip_specs["height"] <= 1088:				# Likely PAL HD
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT709						# HD
			elif clip_specs["width"]  <= 3840 and clip_specs["height"] <= 2160:				# Likely UHD
				# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
				# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
				# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
				# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
				# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
				# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
				# because the benefits are considered modest and entail some additional complexity
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_CL					#     Constant Luminance
				#clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_NCL				# Non-Constant Luminance
			elif clip_specs["width"]  <= 7680 and clip_specs["height"] <= 4320:				# Likely 8K
				# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
				# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
				# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
				# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
				# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
				# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
				# because the benefits are considered modest and entail some additional complexity
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_CL					#     Constant Luminance
				#clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_NCL 				# Non-Constant Luminance
			else:
				raise ValueError(f'ERROR: get_clip_specs: VID: unable to guess default _Matrix in PIC to replace MatrixCoefficients.MATRIX_UNSPECIFIED')
			print_DEBUG(f'get_clip_specs: VID: MatrixCoefficients.MATRIX_UNSPECIFIED ({vs.MatrixCoefficients.MATRIX_UNSPECIFIED}) in VID, replacement _Matrix={clip_specs["proposed_Matrix"]}')
		else:
			raise ValueError(f'ERROR: get_clip_specs: VID: ext "{ext}" not recognised in VID to replace MatrixCoefficients.MATRIX_UNSPECIFIED')
	# **********
	# if not already specified, guess new _Primaries. explainer: https://docs.rs/av-data/0.4.1/av_data/pixel/index.html https://docs.rs/av-data/0.4.1/av_data/pixel/enum.ColorPrimaries.html
	if  clip_specs["_Primaries"] == vs.ColorPrimaries.PRIMARIES_UNSPECIFIED or clip_specs["_Primaries"] is None:
		print_DEBUG(f'get_clip_specs: ColorPrimaries.PRIMARIES_UNSPECIFIED: incoming clip_specs=\n{objPrettyPrint.pformat(clip_specs)}')
		clip_specs["guessed_Primaries"] = True
		if clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_ST170_M:
			clip_specs["proposed_Primaries"] = vs.ColorPrimaries.PRIMARIES_ST170_M
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT470_BG:
			clip_specs["proposed_Primaries"] = vs.ColorPrimaries.PRIMARIES_BT470_BG
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT709:
			clip_specs["proposed_Primaries"] = vs.ColorPrimaries.PRIMARIES_BT709
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT2020_CL or clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT2020_NCL:
			clip_specs["proposed_Primaries"] = vs.ColorPrimaries.PRIMARIES_BT2020
		else:
			raise ValueError(f'ERROR: get_clip_specs: unable to guess default _Primaries to replace ColorPrimaries.PRIMARIES_UNSPECIFIED')
		print_DEBUG(f'get_clip_specs: ColorPrimaries.PRIMARIES_UNSPECIFIED ({vs.ColorPrimaries.PRIMARIES_UNSPECIFIED}), replacement _Primaries={clip_specs["proposed_Primaries"]}')
	# **********
	# if not already specified, guess new _Transfer. explainer: https://docs.rs/av-data/0.4.1/av_data/pixel/index.html https://docs.rs/av-data/0.4.1/av_data/pixel/enum.TransferCharacteristic.html
	if  clip_specs["_Transfer"] == vs.TransferCharacteristics.TRANSFER_UNSPECIFIED or clip_specs["_Transfer"] is None:
		print_DEBUG(f'get_clip_specs: ColorPrimaries.PRIMARIES_UNSPECIFIED: incoming clip_specs=\n{objPrettyPrint.pformat(clip_specs)}')
		clip_specs["guessed_Transfer"] = True
		if clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_ST170_M:
			clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT601
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT470_BG:
			clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT470_BG
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT709:
			clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT709
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT2020_CL or clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT2020_NCL:
			if clip_specs["bits_per_sample"] == 10:
				# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
				# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
				# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
				# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
				# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
				# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
				# because the benefits are considered modest and entail some additional complexity
				clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT2020_10
			elif clip_specs["bits_per_sample"] == 12:
				# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
				# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
				# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
				# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
				# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
				# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
				# because the benefits are considered modest and entail some additional complexity
				clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT2020_12
			else:
				raise ValueError(f'ERROR: get_clip_specs: unable to guess {clip_specs["bits_per_sample"]}-bit default _Transfer to replace TransferCharacteristics.TRANSFER_UNSPECIFIED')
		else:
			raise ValueError(f'ERROR: get_clip_specs: unable to guess default _Transfer to replace TransferCharacteristics.TRANSFER_UNSPECIFIED')
		print_DEBUG(f'get_clip_specs: TransferCharacteristics.TRANSFER_UNSPECIFIED ({vs.TransferCharacteristics.TRANSFER_UNSPECIFIED}), replacement _Transfer={clip_specs["proposed_Transfer"]}')
	# **********
	# if not already specified, guess new _ColorRange. explainer: https://docs.rs/av-data/0.4.1/av_data/pixel/index.html https://docs.rs/av-data/0.4.1/av_data/pixel/enum.YUVRange.html
	# NOTE THESE IN REGARD TO VS "bug" in RANGE values not agreeing with the spec:
	#	https://github.com/vapoursynth/vapoursynth/issues/940
	#	https://github.com/vapoursynth/vapoursynth/issues/857
	# https://github.com/vapoursynth/vapoursynth/issues/940#issuecomment-1465041338
	# When calling rezisers etc, ONLY use these values:
	#	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
	#	ZIMG_RANGE_FULL     = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
	# but when obtaining from frame properties and comparing etc, use the vs values from
	# frame properties even though the vapoursynth values are incorrect (opposite to the spec)
	# BUT BUT BUT here we are working solely with vapoursynth settings, not resizers, so stick with using vapoursynth constants and not zimg ones
	if clip_specs["_ColorRange"] is None:
		clip_specs["guessed_ColorRange"] = True
		clip_specs["proposed_ColorRange"] = vs.ColorRange.RANGE_FULL
	# **********
	# guess at a possible incoming colour source
	if   clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT470_BG:
		clip_specs["possible_colour_source"] = "PAL".upper()
	elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_ST170_M:
		clip_specs["possible_colour_source"] = "NTSC".upper()
	elif clip_specs["proposed_Transfer"] == vs.TransferCharacteristics.TRANSFER_BT470_BG:
		clip_specs["possible_colour_source"] = "PAL".upper()
	elif clip_specs["proposed_Transfer"] in [vs.TransferCharacteristics.TRANSFER_BT470_M, vs.TransferCharacteristics.TRANSFER_ST240_M]:
		clip_specs["possible_colour_source"] = "NTSC".upper()
	elif clip_specs["proposed_Primaries"] == vs.ColorPrimaries.PRIMARIES_BT470_BG:
		clip_specs["possible_colour_source"] = "PAL".upper()
	elif clip_specs["proposed_Primaries"] in [vs.ColorPrimaries.PRIMARIES_ST170_M, vs.ColorPrimaries.PRIMARIES_BT470_M, vs.ColorPrimaries.PRIMARIES_ST170_M, vs.ColorPrimaries.PRIMARIES_ST240_M]:
		clip_specs["possible_colour_source"] = "PAL".upper()
	# allow for incoming errors in fps, use ranges instead of values
	elif (clip_specs["fps"] >=23.5 and clip_specs["fps"] <= 24.49) or (clip_specs["fps"] >=29 and clip_specs["fps"] <= 31):
		clip_specs["possible_colour_source"] = "NTSC".upper()		# possibly NTSC although 30fps could still be PAL in phone cameras :(
	elif (clip_specs["fps"] >=24.5 and clip_specs["fps"] <= 25.5):
		clip_specs["possible_colour_source"] = "PAL".upper()
	else:	# deault to PAL since, well, I'm in a PAL country
		clip_specs["possible_colour_source"] = "PAL".upper()
	#
	print_DEBUG(f'get_clip_specs: AFTER GUESSING, clip_specs=\n{objPrettyPrint.pformat(clip_specs)}')
	del mi_standard_list
	del mi_color_primaries_dict
	del mi_transfer_characteristics_dict
	del mi_matrix_coefficients_dict
	del mi_colour_range_dict
	del mediainfo_specs
	return clip_specs

###
def get_random_ffindex_path(path):
	# there is a significant to 100% chance of home picture/video filenames in directory trees being non-unique
	# apparently uuid4 has a good chance of returning a unique string
	f = ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"][0] + r'\ '.strip() + os.path.basename(path) + r'_' + str(uuid.uuid4()) + r'.ffindex'
	print_DEBUG(f'get_random_ffindex_path: random ffindex cache path="{f}"')
	return f

###
def get_clip(path):
	# open a clip and examine it and transform it
	global last_file_opened_with_ffms2
	global last_file_opened_with_imwri
	global last_file_opened_with_LWLibavSource
	global last_file_opened_with_LibavSMASHSource
	#
	last_file_opened_with_ffms2 = False
	last_file_opened_with_imwri = False
	last_file_opened_with_LWLibavSource = False
	last_file_opened_with_LibavSMASHSource = False
	if path.suffix.lower()   in calc_ini["EEK_EXTENSIONS"]:
		try:
			clip = core.lsmas.LWLibavSource(str(path))
			last_file_opened_with_LWLibavSource = True
			print_DEBUG(f'get_clip: opened lsmas Video {path.name} info:\n{clip}')
		except Exception as e:
			print_NORMAL(f'WARNING: error opening file via "lsmas": "{path.name}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}')
			clip = None
	elif path.suffix.lower() in calc_ini["VID_EXTENSIONS"]:
		try:
			clip = core.ffms2.Source(str(path), cachefile=get_random_ffindex_path(path))
			last_file_opened_with_ffms2 = True
			print_DEBUG(f'get_clip: opened ffms2 Video {path.name} info:\n{clip}')
			#clip = core.lsmas.LibavSMASHSource(str(path))
			#last_file_opened_with_LibavSMASHSource = True
			#print_DEBUG(f'get_clip: ffms2 Video {path.name} info:\n{clip}')
		except Exception as e:
			print_NORMAL(f'WARNING: error opening file via "ffms2": "{path.name}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}')
			clip = None
	elif path.suffix.lower() in calc_ini["PIC_EXTENSIONS"]:
		try:
			clip = core.ffms2.Source(str(path), cachefile=get_random_ffindex_path(path))
			last_file_opened_with_ffms2 = True
			print_DEBUG(f'get_clip: opened ffms2 Picture "{path.name}" info:\n{clip}')
			#print_DEBUG(f'get_clip: ffms2 PIC {path.name} info:\n{clip}')
			## NOTE: imwri returns no frame properties ! eg "_Matrix" ! and thus IS NO GOOD AT ALL FOR US
			##clip = core.imwri.Read(str(path)) # ImageMagick Writer-Reader, if installed into vapoursynth directory
			##last_file_opened_with_imwri = True
			##print_DEBUG(f'get_clip: imwri Video info:\n{clip}')
		except Exception as e:
			print_NORMAL(f'WARNING: error opening file via "ffms2": "{path.name}" ; ignoring this picture. The error was:\n{e}\n{type(e)}\n{str(e)}')
			clip = None
	else: # UNKNOWN TYPE
		try:
			clip = core.ffms2.Source(str(path), cachefile=get_random_ffindex_path(path))
			last_file_opened_with_ffms2 = True
			print_DEBUG(f'get_clip: opened unknown type of file with ffms2 "{path.name}" info:\n{clip}')
		except Exception as e:
			print_NORMAL(f'WARNING: error opening UNKNOWN type of file via "ffms2": "{path.name}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}')
			clip = None
	# If an ignored error, return immediately
	clip_specs = None
	if clip is None:
		return None
	clip_specs = get_clip_specs(clip, path, ext=path.suffix.lower())
	#++++++++++++++++++++
	# SET missing frame properties with guessed values
	if clip_specs["guessed_Matrix"]:
		print_DEBUG(f'get_clip: SetFrameProps _Matrix from existing "{clip_specs["_Matrix"]}" to guessed "{clip_specs["proposed_Matrix"]}"')
		clip = core.std.SetFrameProps(clip, _Matrix=clip_specs["proposed_Matrix"])
	if clip_specs["guessed_Primaries"]:
		print_DEBUG(f'get_clip: SetFrameProps _Primaries from existing "{clip_specs["_Primaries"]}" to guessed "{clip_specs["proposed_Primaries"]}"')
		clip = core.std.SetFrameProps(clip, _Primaries=clip_specs["proposed_Primaries"])
	if clip_specs["guessed_Transfer"]:
		print_DEBUG(f'get_clip: SetFrameProps _Transfer from existing "{clip_specs["_Transfer"]}" to guessed "{clip_specs["proposed_Transfer"]}"')
		clip = core.std.SetFrameProps(clip, _Transfer=clip_specs["proposed_Transfer"])
	# NOTE THESE IN REGARD TO VS "bug" in RANGE values not agreeing with the spec:
	#	https://github.com/vapoursynth/vapoursynth/issues/940
	#	https://github.com/vapoursynth/vapoursynth/issues/857
	# https://github.com/vapoursynth/vapoursynth/issues/940#issuecomment-1465041338
	# When calling rezisers etc, ONLY use these values:
	#	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
	#	ZIMG_RANGE_FULL     = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
	# but when obtaining from frame properties and comparing etc, use the vs values from
	# frame properties even though the vapoursynth values are incorrect (opposite to the spec)
	# BUT BUT BUT here we are working solely with vapoursynth settings, not resizers, so stick with using vapoursynth constants and not zimg ones
	if clip_specs["guessed_ColorRange"]:
		print_DEBUG(f'get_clip: SetFrameProps _ColorRange from existing "{clip_specs["_ColorRange"]}" to guessed "{clip_specs["proposed_ColorRange"]}"')
		clip = core.std.SetFrameProps(clip, _ColorRange=clip_specs["proposed_ColorRange"])
	#++++++++++++++++++++
	# # A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
	# Apply an auto-rotate auto_rotation if specified in the source file
	##if path.suffix.lower() in calc_ini["PIC_EXTENSIONS"]:
	#print_DEBUG(f'type(clip_specs["auto_rotation_degrees"])={type(clip_specs["auto_rotation_degrees"])}  clip_specs["auto_rotation_degrees"]={clip_specs["auto_rotation_degrees"]}')
	if clip_specs["auto_rotation_degrees"] == 0:
		#print_DEBUG(f'get_clip: zero auto-rotation of clip {path}')
		pass
	elif clip_specs["auto_rotation_degrees"] == 90 or clip_specs["auto_rotation_degrees"] == -270:
		print_DEBUG(f'get_clip: auto-Rotating {clip_specs["auto_rotation_direction"]} by {clip_specs["auto_rotation_degrees"]} degrees {path}')
		if clip_specs["auto_rotation_direction"] == calc_ini["Rotation_anti-clockwise"]:
			clip = clip.std.Transpose().std.FlipVertical()		# ANTICLOCKWISE ROTATION 90 DEGREES
		elif clip_specs["auto_rotation_direction"] == calc_ini["Rotation_clockwise"]:
			clip = clip.std.Transpose().std.FlipHorizontal()	# CLOCKWISE ROTATION 90 DEGREES
		else:
			raise ValueError(f'ERROR: get_clip: auto_rotation_degrees "{clip_specs["auto_rotation_degrees"]}" unrecognised direction={clip_specs["auto_rotation_direction"]} unable to be processed for "{path}" : only 0/90/180/270 are valid')
	elif clip_specs["auto_rotation_degrees"] == 180:
		print_DEBUG(f'get_clip: auto-Rotating {clip_specs["auto_rotation_direction"]} by {clip_specs["auto_rotation_degrees"]} degrees {path}')
		if clip_specs["auto_rotation_direction"] == calc_ini["Rotation_anti-clockwise"]:
			clip = clip.std.Turn180()
		elif clip_specs["auto_rotation_direction"] == calc_ini["Rotation_clockwise"]:
			clip = clip.std.Turn180()
		else:
			raise ValueError(f'ERROR: get_clip: auto_rotation_degrees "{clip_specs["auto_rotation_degrees"]}" unrecognised direction={clip_specs["auto_rotation_direction"]} unable to be processed for "{path}" : only 0/90/180/270 are valid')
	elif clip_specs["auto_rotation_degrees"] == 270 or clip_specs["auto_rotation_degrees"] == -90:
		print_DEBUG(f'get_clip: auto-Rotating {clip_specs["auto_rotation_direction"]} by {clip_specs["auto_rotation_degrees"]} degrees {path}')
		if clip_specs["auto_rotation_direction"] == calc_ini["Rotation_anti-clockwise"]:
			clip = clip.std.Transpose().std.FlipHorizontal()	# ANTICLOCKWISE ROTATION 270 degrees
		elif clip_specs["auto_rotation_direction"] == calc_ini["Rotation_clockwise"]:
			clip = clip.std.Transpose().std.FlipVertical()		# CLOCKWISE ROTATION 270 degrees
		else:
			raise ValueError(f'ERROR: get_clip: auto_rotation_degrees "{clip_specs["auto_rotation_degrees"]}" unrecognised direction={clip_specs["auto_rotation_direction"]} unable to be processed for "{path}" : only 0/90/180/270 are valid')
	else:
		raise ValueError(f'ERROR: get_clip: auto_rotation_degrees "{clip_specs["auto_rotation_degrees"]}" direction={clip_specs["auto_rotation_direction"]} unable to be processed for "{path}" : only 0/90/180/270 are valid')
	#++++++++++++++++++++
	# make video-specific or picture-specific changes
	if path.suffix.lower() in calc_ini["VID_EEK_EXTENSIONS"]:	#if any sort of video, probably an old hand-held camera or phone, sometimes variable fps ...
		print_DEBUG(f'get_clip: opened Video: {path.name}\nVideo info:\n{clip}')
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
		print_DEBUG(f'get_clip: {source_width}x{source_height} source_fpsnum:{source_fpsnum} source_fpsden:{source_fpsden} source_fps:{source_fps} source_duration_frames:{source_duration_frames} source_duration_secs:{source_duration_secs}')
		# change framerate ? too hard for a small simple video sample, just "assume" target fps and ignore consequences of speed-up or slow-down or VFR
		clip = clip.std.AssumeFPS(fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
		# if duration greater than out review maximum, clip it
		if source_duration_frames > (calc_ini["DURATION_MAX_VIDEO_FRAMES"]-1):
			clip = core.std.Trim(clip, first=0, last=(calc_ini["DURATION_MAX_VIDEO_FRAMES"]-1))
		if len(clip) < calc_ini["DURATION_PIC_FRAMES"]:
			how_many_frames_to_pad = calc_ini["DURATION_PIC_FRAMES"] - len(clip)
			if how_many_frames_to_pad > 0:
				frame_to_pad_with = clip[-1:]
				print_DEBUG(f'frame_to_pad_with len={len(frame_to_pad_with)} width={frame_to_pad_with.width} height={frame_to_pad_with.height} ... clip len={len(clip)} width={clip.width} height={clip.height} \n frame_to_pad_with={frame_to_pad_with} \n clip={clip}')
				clip = clip + (clip[-1:] * how_many_frames_to_pad)	# right pad with the final frame of the newly opened video clip
				print_DEBUG(f'Padded video clip "{path}" of {len(clip)} frames by {how_many_frames_to_pad} frames to be a total of {calc_ini["DURATION_PIC_FRAMES"]} long.')
			else:
				raise ValueError(f'ERROR: how_many_frames_to_pad<=0 BUT Padding video clip "{path}" of {len(clip)} frames by {how_many_frames_to_pad} frames to be a total of {calc_ini["DURATION_PIC_FRAMES"]} long.')
		# TEMPORARILY COMMENT OUT DG SHARPEN OF SMALL CLIPS
		# denoise ANY "small" dimension video clips, older videos likely to be noisy
		#if source_width < calc_ini["TARGET_WIDTH"] or source_height < calc_ini["TARGET_HEIGHT"]:	 
		#	print_DEBUG(f'applying DGDenoise to small {source_width}x{source_height} video {path.name}')
		#	# clip must be YUV420P16 for DGDenoise etc
		#	clip = clip.resize.Point(format=calc_ini["DG_PIXEL_FORMAT"])		# convert to DG_PIXEL_FORMAT via resizer which does no resizing
		#	#clip = core.avs.DGDenoise(clip, strength=0.06, cstrength=0.06)
		#	clip = core.avs.DGDenoise(clip, strength=0.15, cstrength=0.15)
		#	clip = clip.resize.Point(format=calc_ini["WORKING_PIXEL_FORMAT"])	# convert to calc_ini["WORKING_PIXEL_FORMAT"] via resizer which does no resizing
	else: # source is not a video type, i.e. it must be an image (picture)
		# ensure duration of a clip of an image is the proper number of frames
		if len(clip) < calc_ini["DURATION_PIC_FRAMES"]:
			clip = clip[0]*calc_ini["DURATION_PIC_FRAMES"]
	# either add borders to maintain aspect ratio (boxing), or just stretch to fit (yuk)
	if calc_ini["BOX"]:
		print_DEBUG(f'get_clip: boxing the clip, also doing format conversion and resizing')
		clip = boxing(clip, calc_ini["TARGET_WIDTH"], calc_ini["TARGET_HEIGHT"])									# new clip format from resize ... replace into clip_specs
	else:
		print_DEBUG(f'get_clip: NOT boxing the clip, also doing format conversion and resizing')
		clip = resize_clip(clip, calc_ini["TARGET_WIDTH"], calc_ini["TARGET_HEIGHT"])	# new clip format is consistent with boxing as it uses the same resizer

	#****************************************************************************************************************************************
	# both BOX/non-BOX resizes above convert "format" to calc_ini["WORKING_PIXEL_FORMAT"] (i.e. YUV444) and change to target color spaces  etc etc
	# at this point, clip_specs is stale
	#****************************************************************************************************************************************

	#++++++++++++++++++++
	# Add a subtitle being the trailing x parts of the path
	if calc_ini["SUBTITLE_DEPTH"] > 0:	# Add a subtitle being up to the trailing calc_ini["SUBTITLE_MAX_DEPTH"] parts of the path
		pwp = PureWindowsPath(path)
		num_parts = len(pwp.parts)
		text_subpath_for_subtitles = ""
		max_depth_this_time = min(num_parts-1, calc_ini["SUBTITLE_MAX_DEPTH"], calc_ini["SUBTITLE_DEPTH"]) # maybe (num_parts-1) should be ) ?
		if max_depth_this_time > 0:
			for i in range((num_parts - max_depth_this_time), (num_parts)):
				text_subpath_for_subtitles = text_subpath_for_subtitles + "/" + pwp.parts[i]
				print_DEBUG(f'get_clip: Subtitling loop: num_parts={num_parts} i={i} pwp.parts[{i}]= {pwp.parts[i]} text_subpath_for_subtitles="{text_subpath_for_subtitles}"')
			subtitle_style = f'sans-serif,{str(calc_ini["SUBTITLE_FONTSIZE"]).strip()},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0.9,0.5,3,2,2,2,1'
			clip = core.assrender.Subtitle(clip, text_subpath_for_subtitles, style=subtitle_style, scale=calc_ini["SUBTITLE_FONTSCALE"], colorspace=calc_ini["TARGET_COLORSPACE"])
			print_DEBUG(f'get_clip: Subtitling performed. calc_ini["SUBTITLE_DEPTH"]={calc_ini["SUBTITLE_DEPTH"]} pwp={pwp} num_parts={num_parts} max_depth_this_time={max_depth_this_time} text_subpath_for_subtitles="{text_subpath_for_subtitles}"')
		else:
			print_DEBUG(f'get_clip: No subtitling performed since max_depth_this_time <= 0. calc_ini["SUBTITLE_DEPTH"]={calc_ini["SUBTITLE_DEPTH"]} pwp={pwp} num_parts={num_parts} max_depth_this_time={max_depth_this_time}')
		# To tinker with .ass subs, see https://snapcraft.io/install/aegisub-procles/ubuntu
		# Also note from an aegisub created .ass file
		#	Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
		#	Style: h3333,Arial,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0.9,0.5,3,2,2,2,1
		# whereas default .assrender.Subtitle style="sans-serif,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,7,10,10,10,1"
		# https://github.com/AmusementClub/assrender
		# assrender.Subtitle(clip clip, string[] text, [string style="sans-serif,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,7,10,10,10,1", int[] start, int[] end, string vfr, int hinting=0, float scale=1.0, float line_spacing=1.0, float dar, float sar, bool set_default_storage_size=True, int top=0, int bottom=0, int left=0, int right=0, string charset, int debuglevel, string fontdir="", string srt_font="sans-serif", string colorspace])
		#	colorspace Rec2020, BT.2020 Rec709, BT.709, Rec601, BT.601, PC.709, PC.601, TV.fcc, PC.fcc, TV.240m, PC.240m
		#	When no hint found in ASS script and colorspace parameter is empty then the default is BT.601
	else:
		print_DEBUG(f'get_clip: No subtitling performed. calc_ini["SUBTITLE_DEPTH"]={calc_ini["SUBTITLE_DEPTH"]}')
	
	print_DEBUG(f'get_clip: returning working clip properties: clip.format.name="{clip.format.name}" clip.format.color_family="{clip.format.color_family}" clip.format.sample_type="{clip.format.sample_type}" clip.format.bits_per_sample="{clip.format.bits_per_sample}" clip.format.bytes_per_sample="{clip.format.bytes_per_sample}" clip.format.num_planes="{clip.format.num_planes}" clip.format.subsampling_w="{clip.format.subsampling_w}" clip.format.subsampling_h="{clip.format.subsampling_h}"')
	with clip.get_frame(0) as f:
		print_DEBUG(f'get_clip: returning working frame properties: w={clip.width} h={clip.height} fps={clip.fps} {clip} {objPrettyPrint.pformat(f.props)}')
	del clip_specs
	return clip

###
def get_path(path_generator):
	# get next path of desired extensions from generator, ignoring extensions we have not specified
	while 1:	# loop until we do a "return", hitting past the end of the iterator returns None
		try:
			path = next(path_generator)
			print_DEBUG(f'get_path: get success, path.name=' + path.name)
		except StopIteration:
			return None
		if path.suffix.lower() in calc_ini["EXTENSIONS"]:	# only return files which are in known extensions
			print_DEBUG(f'get_path: in calc_ini["EXTENSIONS"] success, path.name=' + path.name)
			return path
		  
###
def crossfade(a, b, crossfade_duration_frames):
	# THIS FUNCTION IS NO LONGER USED
	# gets crosfade part from end of clip a and start of clip b
	# bug: in the context of the caller, it duplicates bits of clips and looks very strange
	def fade_image(n, a, b):
		return core.std.Merge(a, b, weight=n/crossfade_duration_frames)
	if a.format.id != b.format.id or a.height != b.height or a.width != b.width:
		raise ValueError(f'ERROR: crossfade: Both clips must have the same dimensions and format.')
	# https://www.freecodecamp.org/news/how-to-substring-a-string-in-python/
	# string[start:end]	: all characters from start to (end - 1) : base 0
	# string[start:]	: all characters from "start" to the end of the string : base 0
	# string[0:]		: all characters (which is 0 to the end of the string) : base 0
	# string[1:]		: character 1 to the end of the string : base 0
	# string[:5]		: characters 0 to 4 inclusive : base 0
	# string[0:5]		: characters 0 to 4 inclusive : base 0
	# string[2:6]		: characters 2 to 5 inclusive : base 0
	# string[-1:]		: rightmost 1 character of the string
	# string[-5:]		: rightmost 5 characters of a string
	# string[:-1]		: all characters excluding the the rightmost character : base 0
	# string[:-5]		: all characters excluding the the rightmost 5 characters : base 0
	# string[1:-4]		: all characters except the leftmost character and last 4 characters : base 0
	# THE SAME APPLIES TO FRAMES
	#
	a_clipped = a[-crossfade_duration_frames:]	# rightmost "crossfade_duration_frames" frames of a
	b_clipped = b[:crossfade_duration_frames]	# leftmost  "crossfade_duration_frames" frames of b
	crossfade_clip = core.std.FrameEval(a_clipped, partial(fade_image, a=a_clipped, b=b_clipped))
	return crossfade_clip

###
def crossfade_merge(a=None, b=None, crossfade_duration_frames:int=4, crossfade_type:str=None, crossfade_direction:str=None):
	# (sort of) APPEND clip_b to the end of clip_a
	# using a crossfade transition to merge them, returning a merged clip HOWEVER
	# the TOTAL LENGTH of the returned clip will be (original_length_a + original_length_b - (2 * crossfade_duration_frames))
	# since "crossfade_duration_frames" is used from each clips to make the transition merger
	#
	# https://www.freecodecamp.org/news/how-to-substring-a-string-in-python/
	# string[start:end]	: all characters from start to (end - 1) : base 0
	# string[start:]	: all characters from "start" to the end of the string : base 0
	# string[0:]		: all characters (which is 0 to the end of the string) : base 0
	# string[1:]		: character 1 to the end of the string : base 0
	# string[:5]		: characters 0 to 4 inclusive : base 0
	# string[0:5]		: characters 0 to 4 inclusive : base 0
	# string[2:6]		: characters 2 to 5 inclusive : base 0
	# string[-1:]		: rightmost 1 character of the string
	# string[-5:]		: rightmost 5 characters of a string
	# string[:-1]		: all characters excluding the the rightmost character : base 0
	# string[:-5]		: all characters excluding the the rightmost 5 characters : base 0
	# string[1:-4]		: all characters except the leftmost character and last 4 characters : base 0
	# THE SAME APPLIES TO FRAMES
	#
	# vs-transitions DOCUMENTATION:
	#		https://vapoursynth-transitions.readthedocs.io/en/latest/api.html
	#
	# vs-transitions Enums and Constants:
	#		https://vapoursynth-transitions.readthedocs.io/en/latest/api.html
	#
	global crossfade_type_list
	global crossfade_type_list_no_black_fades
	global crossfade_direction_list
	global Count_of_files
	
	print_DEBUG(f'crossfade_merge: ENTERED from call: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}"\na={a}\nb={b}')
	print_DEBUG(f'crossfade_merge: ENTERED from call: a={a} a={a.width}x{a.height}')
	print_DEBUG(f'crossfade_merge: ENTERED from call: b={b} b={b.width}x{b.height}')
	
	if a is None:
		raise ValueError(f'ERROR: crossfade_merge: crossfade_type "{crossfade_type}" Clip "a" must be a clip. \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height}')
	if crossfade_type is None:
		crossfade_type = "random".lower()
		print_NORMAL(f'WARNING: crossfade_merge: unspecified crossfade_type "{crossfade_type}", using "random" instead.')
	else:
		crossfade_type = crossfade_type.lower()
		if crossfade_type not in crossfade_type_list:
			print_NORMAL(f'WARNING: crossfade_merge: unrecognised crossfade_type "{crossfade_type}", using "random" instead.')
			crossfade_type = "random".lower()
	if crossfade_type in list(map(str.lower,[ 'fade_to_black', 'fade_from_black', ])):	# these only consume clip a, and so clip b can be none
		pass	# these 2 crossfade_types do not need nor want a clip b
	else:
		if a.format.id != b.format.id or a.height != b.height or a.width != b.width:
			raise ValueError(f'ERROR: crossfade_merge: crossfade_type "{crossfade_type}" Both clips must have the same dimensions and format. \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height}')
	#print_DEBUG(f'crossfade_merge: about to enter "random" choice(): crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height}')
	i = 0
	if crossfade_type == 'random'.lower():
		while crossfade_type in list(map(str.lower,[ 'random', 'linear_boundary', ])):	# in the 'banned' list for random. perhaps peel too
			i = i + i
			if i > 10:
				crossfade_type = 'curtain_reveal'.lower()
				break
			crossfade_type = random.choice(crossfade_type_list_no_black_fades)
		# take care of suitable directions if 'random'
		if 'curtain'.lower() in crossfade_type:
			crossfade_direction = random.choice([vs_transitions.Direction.HORIZONTAL.value, vs_transitions.Direction.VERTICAL.value])
		else:
			crossfade_direction = random.choice([vs_transitions.Direction.LEFT.value, vs_transitions.Direction.RIGHT.value, vs_transitions.Direction.UP.value, vs_transitions.Direction.DOWN.value])
	#print_DEBUG(f'crossfade_merge: after "random" choice(): crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height}')
	# Check for a valid direction, if required
	#for v in vs_transitions.Direction:		``			
	#	print_DEBUG(f'crossfade_merge: vs_transitions.Direction ENUM: {str(v)} = {v.value}')
	if crossfade_type not in list(map(str.lower,[ 'none', 'fade', 'fade_to_black', 'fade_from_black', 'pixellate', ])):	# i.e. it actually requires a valid direction
		if crossfade_direction not in crossfade_direction_list:	# ensure the direction is valid
			raise ValueError(f'ERROR: crossfade_merge: crossfade_type "{crossfade_type}" required crossfade_direction "crossfade_direction" is not one of {crossfade_direction_list}.') 
	print_DEBUG(f'crossfade_merge: about to ACT via "match": crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height}')
	if 'curtain'.lower() in crossfade_type:
		d = [vs_transitions.Direction.HORIZONTAL.value, vs_transitions.Direction.VERTICAL.value]
		if crossfade_direction not in d:
			o = crossfade_direction
			crossfade_direction = random.choice(d)
			print_NORMAL(f'WARNING: crossfade_merge: crossfade_type="{crossfade_type}" invalid crossfade_direction="{o}" so random direction="{crossfade_direction}" chosen')
	else:
		d = [vs_transitions.Direction.LEFT.value, vs_transitions.Direction.RIGHT.value, vs_transitions.Direction.UP.value, vs_transitions.Direction.DOWN.value]
		if crossfade_direction not in d:
			o = crossfade_direction
			crossfade_direction = random.choice(d)
			print_NORMAL(f'WARNING: crossfade_merge: crossfade_type="{crossfade_type}" invalid crossfade_direction="{o}" so random direction="{crossfade_direction}" chosen')
	#
	# https://www.freecodecamp.org/news/how-to-substring-a-string-in-python/
	# string[start:end]	: all characters from start to (end - 1) : base 0
	# string[start:]	: all characters from "start" to the end of the string : base 0
	# string[0:]		: all characters (which is 0 to the end of the string) : base 0
	# string[1:]		: character 1 to the end of the string : base 0
	# string[:5]		: characters 0 to 4 inclusive : base 0
	# string[0:5]		: characters 0 to 4 inclusive : base 0
	# string[2:6]		: characters 2 to 5 inclusive : base 0
	# string[-1:]		: rightmost 1 character of the string
	# string[-5:]		: rightmost 5 characters of a string
	# string[:-1]		: all characters excluding the the rightmost character : base 0
	# string[:-5]		: all characters excluding the the rightmost 5 characters : base 0
	# string[1:-4]		: all characters except the leftmost character and last 4 characters : base 0
	# THE SAME APPLIES TO FRAMES
	a_leftmost_without_crossfade_frames  = a[                            : -crossfade_duration_frames ]		# all frames excluding the rightmost (crossfade_duration_frames) frames : base 0
	a_crossfading_frames                 = a[ -crossfade_duration_frames : ]								# rightmost (crossfade_duration_frames) frames inclusive
	b_rightmost_without_crossfade_frames = b[  crossfade_duration_frames : ]								# middle frame (crossfade_duration_frames) to the end of the frames inclusive : base 0
	b_crossfading_frames                 = b[                            : crossfade_duration_frames ]		# leftmost "crossfade_duration_frames" frames of b ... 
	len_a = len(a)
	len_a_leftmost_without_crossfade_frames = len(a_leftmost_without_crossfade_frames)
	len_a_crossfading_frames = len(a_crossfading_frames)
	len_b = len(b)
	len_b_rightmost_without_crossfade_frames = len(b_rightmost_without_crossfade_frames)
	len_b_crossfading_frames = len(b_crossfading_frames)
	if (len_a_leftmost_without_crossfade_frames + len_a_crossfading_frames) != len_a:
		raise ValueError(f'ERROR: crossfade_merge: calculation issue: len(clip_a)={len_a} != ( len(a_leftmost_without_crossfade_frames)={len_a_leftmost_without_crossfade_frames} +  len(a_crossfading_frames)={len_a_crossfading_frames} ({len_a_leftmost_without_crossfade_frames + len_a_crossfading_frames}))')
	if (len_b_rightmost_without_crossfade_frames + len_b_crossfading_frames) != len_b:
		raise ValueError(f'ERROR: crossfade_merge: calculation issue: len(clip_b)={len_b} != ( len(b_rightmost_without_crossfade_frames)={len_b_rightmost_without_crossfade_frames} +  len(b_crossfading_frames)={len_b_crossfading_frames} ) ({len_b_rightmost_without_crossfade_frames + len_b_crossfading_frames})')
	#
	crossfaded_clips = None
	# ok, there is intentionally NOT a case 'linear_boundary':
	try:
		match crossfade_type:
			case 'none':
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "none"')
				#crossfaded_clips = a_crossfading_frames + b_crossfading_frames	# original non-faded parts of clips, joined : this clip will be longer than the other crossfaded clips below since the other crossfades chew into the original clip display time and this one doesn't
				crossfaded_clips = vs_transitions.add_together(a_crossfading_frames, b_crossfading_frames)
				pass
			case 'fade': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "fade"')
				crossfaded_clips = vs_transitions.fade(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames)
				pass
			case 'fade_to_black':
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "fade_to_black"')
				crossfaded_clips = vs_transitions.fade_to_black(a, frames=crossfade_duration_frames)
				pass
			case 'fade_from_black':
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "fade_from_black"')
				crossfaded_clips = vs_transitions.fade_from_black(a, frames=crossfade_duration_frames)
				pass
			case 'pixellate':
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "pixellate"')
				if crossfade_duration_frames < 4:
					crossfade_duration_frames = 4
				crossfaded_clips = vs_transitions.pixellate(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, lowest_target_w=2, lowest_target_h=2)
				pass
			case 'wipe':
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "wipe"')
				crossfaded_clips = vs_transitions.wipe(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction)
				pass
			case 'push': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "push"')
				crossfaded_clips = vs_transitions.push(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction)
				pass
			case 'slide_expand':
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "slide_expand"')
				crossfaded_clips = vs_transitions.slide_expand(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction)
				pass
			case 'squeeze_slide': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "squeeze_slide"')
				crossfaded_clips = vs_transitions.squeeze_slide(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction)
				pass
			case 'squeeze_expand': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "squeeze_expand"')
				crossfaded_clips = vs_transitions.squeeze_expand(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction)
				pass
			case 'cover': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "cover"')
				crossfaded_clips = vs_transitions.cover(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction)
				pass
			case 'reveal': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "reveal"')
				crossfaded_clips = vs_transitions.reveal(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction)
				pass
			case 'curtain_cover': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_axis="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "curtain_cover"')
				crossfaded_clips = vs_transitions.curtain_cover(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, axis=crossfade_direction)		# vs_transitions.Direction.HORIZONTAL
				pass
			case 'curtain_reveal': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_axis="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "curtain_reveal"')
				crossfaded_clips = vs_transitions.curtain_reveal(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, axis=crossfade_direction)	# vs_transitions.Direction.HORIZONTAL
				pass
			case 'peel': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "pass"')
				crossfaded_clips = vs_transitions.peel(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction)
				pass
			case 'cube_rotate': 
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for "cube_rotate"')
				crossfaded_clips = vs_transitions.cube_rotate(a_crossfading_frames, b_crossfading_frames, frames=crossfade_duration_frames, direction=crossfade_direction, exaggeration=100)
				pass
			case _:	# the "_" means a final "else".	should be an error ... just concatenate the clips like 'none'
				print_DEBUG(f'crossfade_merge: calling: crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height} calling for case else "none"')
				#crossfaded_clips = a_crossfading_frames + a_crossfading_frames
				crossfaded_clips = vs_transitions.add_together(a_crossfading_frames, b_crossfading_frames)
				pass
	except:
		print_NORMAL(f'ERROR: crossfade_merge: exception returned from vs_transitions: File_number={Count_of_files} crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}" \na={a} a={a.width}x{a.height}\nb={b} b={b.width}x{b.height}')
		raise

	if crossfaded_clips is None or len(crossfaded_clips) == 0:
		raise ValueError(f'ERROR: crossfade_merge: empty cross-faded clips detected. crossfaded_clips={crossfaded_clips}')

	return_clip = a_leftmost_without_crossfade_frames + crossfaded_clips + b_rightmost_without_crossfade_frames
	del a_leftmost_without_crossfade_frames
	del a_crossfading_frames
	del b_rightmost_without_crossfade_frames
	del b_crossfading_frames
	del crossfaded_clips
	print_DEBUG(f'crossfade_merge: RETURNING from called with crossfade_type="{crossfade_type}" crossfade_duration_frames={crossfade_duration_frames} crossfade_direction="{crossfade_direction}"')
	print_DEBUG(f'crossfade_merge: RETURNING from call a={a} a={a.width}x{a.height}')
	print_DEBUG(f'crossfade_merge: RETURNING from call b={b} b={b.width}x{b.height}')
	print_DEBUG(f'crossfade_merge: RETURNING from call return_clip={return_clip} {return_clip.width}x{return_clip.height}')
	return return_clip

###
def print_exif_data(exif_data):
	# for images
	for tag_id in exif_data:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_data.get(tag_id)
		if isinstance(content, bytes):
			content = r'byte content'	#content.decode()
		print_DEBUG(f'{tag:25}: {content}')
	print_DEBUG(f'exif_data:\n{objPrettyPrint.pformat(exif_data)}\n')
	return
		
###
def print_exif_data2(exif_data):
	# for images
	for tag_id in exif_data:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_data.get(tag_id)
		if isinstance(content, bytes):
			content = r'byte content'	#content.decode()
		print_DEBUG(f'{tag:25}: {content}')
	print_DEBUG(f'exif_data2:\n{objPrettyPrint.pformat(exif_data)}\n')
	return

###
def auto_rotation_value_PIL(clip, path):
	# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
	# from PIL import Image, ExifTags, UnidentifiedImageError   # pip install Pillow, or equivalent
	# PIL Pillow module loads an image, checks if EXIF data, checks for 'Orientation'
	# The Python Pillow library is a fork of an older library called PIL. 
	# Older PIL stands for Python Imaging Library, and it's the original library that enabled Python to deal with images. 
	# PIL was discontinued in 2011 (that author died) and only supports Python 2.23 ... so use Pillow instead.
	# https://python-pillow.org/
	rotation_degrees = 0
	try:
		image = Image.open(str(path))
	except UnidentifiedImageError:
		print_DEBUG(f'auto_rotation_value_PIL: except UnidentifiedImageError immediate return now')
		try:
			image.close()
		except:
			pass
		return rotation_degrees, calc_ini["Rotation_anti-clockwise"]
	except PermissionError:
		print_DEBUG(f'auto_rotation_value_PIL: except PermissionError Permission denied to load: {path} immediate return now')
		try:
			image.close()
		except:
			pass
		return rotation_degrees, calc_ini["Rotation_anti-clockwise"]
	except Exception as e:
		print_DEBUG(f'auto_rotation_value_PIL: except Exception {e} {type(e)} {str(e)} - immediate return now')
		try:
			image.close()
		except:
			pass
		return rotation_degrees, calc_ini["Rotation_anti-clockwise"]
	print_DEBUG(f'auto_rotation_value_PIL: try on Image.open succeeded')
	rotation_value = 0
	try:		
		for key in ExifTags.TAGS.keys():
			if ExifTags.TAGS[key] == 'Orientation':
				break
		exif = dict(image.getexif().items())
		if ExifTags.TAGS[key] == 'Orientation':
			value = exif[key]
		else:
			value = 0
	except (AttributeError, KeyError, IndexError):
		print_DEBUG(f'auto_rotation_value_PIL: except AttributeError during for key in ExifTags.TAGS.keys(), immediate return now')
		try:
			image.close()
		except:
			pass
		return rotation_degrees, calc_ini["Rotation_anti-clockwise"]
	else:
		if   value == 0:
			rotation_degrees = 0
			#print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 0 degrees {path}')
		elif   value == 3:
			rotation_degrees = 180
			#print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 180 degrees {path}')
		elif value == 8:
			rotation_degrees = 90
			#print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by  90 degrees {path}')
		elif value == 6:
			rotation_degrees = 270
			#print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 270 degrees {path}')
	try:
		image.close()
	except:
		pass
	print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by {rotation_degrees} degrees {path}')
	return rotation_degrees, calc_ini["Rotation_anti-clockwise"]

###
def auto_rotation_value_MediaInfo(clip, path):
	# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
	rotation_degrees = 0
	param = 'Rotation'
	value = mediainfo_value(Stream.Video, 0, param, path)
	if param == 'Rotation':
		if value is None:
			rotation_degrees = 0
		else:
			rotation_degrees = int(float(value)) # for some reason Rotation value type mediainfo carries as a string,  like: '180.00'
	print_DEBUG(f'auto_rotation_value_MediaInfo: MediaInfo says auto-Rotating CLOCKWISE by {rotation_degrees} degrees {path}')
	return rotation_degrees, calc_ini["Rotation_clockwise"]

###
def perform_rotation_PIL(clip, path, save_rotated_image=False):
	# THIS FUNCTION IS NO LONGER USED
	# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
	# from PIL import Image, ExifTags, UnidentifiedImageError   # pip install Pillow, or equivalent
	# PIL Pillow module loads an image, checks if EXIF data, checks for 'Orientation'
	# The Python Pillow library is a fork of an older library called PIL. 
	# Older PIL stands for Python Imaging Library, and it's the original library that enabled Python to deal with images. 
	# PIL was discontinued in 2011 (that author died) and only supports Python 2.23 ... so use Pillow instead.
	# https://python-pillow.org/
	print_DEBUG(f'perform_rotation_PIL entered - this is bad')
	raise ValueError(f'ERROR: perform_rotation_PIL sould never have been called')
	try:
		image = Image.open(str(path))
	except UnidentifiedImageError:
		print_DEBUG(f'perform_rotation_PIL: except UnidentifiedImageError immediate return now')
		try:
			image.close()
		except:
			pass
		return clip
	except PermissionError:
		print_DEBUG(f'perform_rotation_PIL: except PermissionError Permission denied to load: {path} {e} {type(e)} {str(e)} - immediate return now')
		try:
			image.close()
		except:
			pass
		return clip
	except Exception as e:
		print_DEBUG(f'perform_rotation_PIL: except Exception {e} {type(e)} {str(e)} - immediate return now')
		try:
			image.close()
		except:
			pass
		return clip
	print_DEBUG(f'perform_rotation_PIL try on Image.open succeeded')
	try:		
		for key in ExifTags.TAGS.keys():
			if ExifTags.TAGS[key] == 'Orientation':
				break
		exif = dict(image.getexif().items())
		value = exif[key]
	except (AttributeError, KeyError, IndexError):
		print_DEBUG(f'perform_rotation_PIL except AttributeError during for key in ExifTags.TAGS.keys(), immediate return now')
		try:
			image.close()
		except:
			pass
		return clip
	else:
		if   value == 3:
			print_DEBUG(f'PIL says auto-Rotating anti-clockwise by 180 degrees {path}')
			clip = clip.std.Turn180()							# 180 DEGREE CLOCKWISE AND ANTI-CLOCLWISE ARE IDENTICAL
		elif value == 8:
			print_DEBUG(f'PIL says auto-Rotating by anti-clockwise  90 degrees {path}')
			clip = clip.std.Transpose().std.FlipVertical()		# THIS IS ANTICLOCKWISE
		elif value == 6:
			print_DEBUG(f'PIL says auto-Rotating anti-clockwise by 270 degrees {path}')
			clip = clip.std.Transpose().std.FlipHorizontal()	# THIS IS ANTICLOCKWISE
		else:
			print_DEBUG(f'PIL says auto-Rotating IGNORED value={value} {path}')
		if save_rotated_image and value in [3,8,6]:
			#rotation degrees are in counterclockwise direction!
			rotate = {3:Image.ROTATE_180, 6:Image.ROTATE_270, 8:Image.ROTATE_90}
			image = image.transpose(rotate[value])
			path2 = path.parent / f'{path.stem}_rotated{path.suffix}'
			##image.save(str(path2))	# comment this out ... no writing new images, please
			print_DEBUG(f'Rotated image {path} was NOT saved as requested into {path2}')
	if IS_DEBUG or IS_DEBUG_SYSTEM_OVERRIDE:
		exif = image.getexif()
		print_exif_data(exif)
		print_DEBUG(f'')
		print_exif_data(exif.get_ifd(0x8769))
		print_DEBUG(f'')
		print_exif_data2(image.getexif())
		print_DEBUG(f'')
		print_exif_data2(image._getexif())
		print_DEBUG(f'')
	try:
		image.close()
	except:
		pass
	return clip

###
def perform_rotation_MediaInfo(clip, path, save_rotated_image=False):
	# THIS FUNCTION IS NO LONGER USED
	# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
	print_DEBUG(f'perform_rotation_MediaInfo entered - this is bad')
	raise ValueError(f'ERROR: perform_rotation_MediaInfo should never have been called')
	param = 'Rotation'
	value = mediainfo_value(Stream.Video, 0, param, path)
	if param == 'Rotation':
		if value is None:
			value = 0
		else:
			value = int(float(value)) # for some reason Rotation value type mediainfo carries as a string,  like: '180.00'
	#print_DEBUG(f'perform_rotation_MediaInfo: auto-Rotating by value={value} for {path}')
	if   value == 180 or value == -180:
		print_DEBUG(f'MediaInfo says auto-Rotating clockwise by 180 degrees {path}')	# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
		clip = clip.std.Turn180()							# 180 DEGREE CLOCKWISE AND ANTI-CLOCLWISE ARE IDENTICAL
	elif value == 90 or value == -270:
		# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
		print_DEBUG(f'MediaInfo says auto-Rotating clockwise by 90 degrees {path}')
		#clip = clip.std.Transpose().std.FlipVertical()		# THIS IS ANTICLOCKWISE
		clip = clip.std.Transpose().std.FlipHorizontal()	# THIS IS CLOCKWISE
	elif value == 270 or value == -90:
		# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
		print_DEBUG(f'MediaInfo says auto-Rotating clockwise by 270 degrees {path}')
		#clip = clip.std.Transpose().std.FlipHorizontal()	# THIS IS ANTICLOCKWISE
		clip = clip.std.Transpose().std.FlipVertical()		# THIS IS CLOCKWISE
	else:
		print_DEBUG(f'MediaInfo says auto-Rotating clockwise IGNORED value={value} {path}')
	return clip


###################################################################################################################################################
###################################################################################################################################################
###################################################################################################################################################

### NEVER hide .vpy behind this: "if __name__=='__main__':"
### BECAUSE IT DOES NOT GETS RUN BY VSPIPE NOR FFMPEG

ini_file_specifying_parameters = fully_qualified_directory_no_trailing_backslash(DEFAULT_INI_FILE_SPECIFYING_PARAMETERS)
ini_section_name = 'slideshow'
print_DEBUG(f'pretified global DEFAULT_DIRECTORY_LIST={objPrettyPrint.pformat(DEFAULT_DIRECTORY_LIST)}')
print_DEBUG(f'pretified global DEFAULT_TEMP_DIRECTORY_LIST={objPrettyPrint.pformat(DEFAULT_TEMP_DIRECTORY_LIST)}')
print_DEBUG(f'ini_file_specifying_parameters="{ini_file_specifying_parameters}"')

# A note about fixed output colour characteristics (the y4m YUV4MPEG2 container doesn;t mention them.
# https://forum.videohelp.com/newreply.php?do=postreply&t=408230#post2684387
# So we always output BT.709 and related characteristics per what we specify in default_ini_values

default_ini_values =	{ ini_section_name : {
							'; CRITICAL NOTES re "directory_list" and "temp_directory"' : '.',
							';   1. paths MUST ALWAYS contain DOUBLE backslashes in every instance - a single backslash causes problems and the result, if any, will be extremely uncertain' : '.',
							';   2. paths must NEVER end with a backslash; backslashes are "escaping" notifiers - if a path ends in a backslash, always put a space character after it at the end of string' : '.',
							'; remember : always use double-backslashes in all paths' : '.',
							'; remember : never end a path with a backslash as the last character (you would rue it)' : '.',
							';' : '.',
							'; "DIRECTORY_LIST" is defined as a list of paths (double-backslashed); beware: .\\\\ by itself means current default path' : '.',
							'DIRECTORY_LIST' :					str(DEFAULT_DIRECTORY_LIST),						# must convert LIST to a STR or it all fails
							'; "TEMP_DIRECTORY_LIST" is defined as a list of paths (for coding convenience) however only the first path in the list will be used' : '.',
							'TEMP_DIRECTORY_LIST' :				str(DEFAULT_TEMP_DIRECTORY_LIST),
							'; "RECURSIVE" is True or False; if True, it also walks the sub-directory tree(s) looking for images/videos' : '.',
							'RECURSIVE' :						True,
							'; "SUBTITLE_DEPTH" an integer; it subtitles with the path/filename of the image/video from the right up to the nominated depth; 0 turns it off' : '.',
							'SUBTITLE_DEPTH' :					3,													# adds a subtitle in the bottom right corner containing the last specified number of  parts of the path to the image/video
							'; "SUBTITLE_FONTSIZE" an integer; the fontsize used for subtitling (18 is good)' : '.',
							'SUBTITLE_FONTSIZE' :				18,
							'; "SUBTITLE_FONTSCALE" a real number; scale applied to the fontsize (1.0 to 3.0 is good)' : '.',
							'SUBTITLE_FONTSCALE' :				1.0,
							'; "DURATION_PIC_SEC" a real number; the number of seconds a pic is displayed in trhe slideshow' : '.',
							'DURATION_PIC_SEC' :				4.0,												### MAXIMUM duration of display of an image, in seconds
							'; "DURATION_CROSSFADE_SECS" a real number; the number of seconds for a crossfade between each image/video' : '.',
							'DURATION_CROSSFADE_SECS':			0.5,													# 0.5 sec is best. # could be 0.2
							'; "CROSSFADE_TYPE" a string; the type of crossfade if DURATION_CROSSFADE_SECS > 0' : '.',
							f'; "CROSSFADE_TYPE" must be one of {crossfade_type_list}' : '.',
							'CROSSFADE_TYPE':					'random',
							'; "CROSSFADE_DIRECTION" a string; the direction of crossfade type if DURATION_CROSSFADE_SECS > 0' : '.',
							f'; "CROSSFADE_DIRECTION" must be one of {crossfade_direction_list}' : '.',
							f'; CROSSFADE_DIRECTION" could be be one of "{vs_transitions.Direction.LEFT.value}" "{vs_transitions.Direction.RIGHT.value}" "{vs_transitions.Direction.UP.value}" "{vs_transitions.Direction.DOWN.value}" if crossfade type not "curtain_cover" or "curtain_reveal"' : '.',
							f'; CROSSFADE_DIRECTION" could be be "{vs_transitions.Direction.HORIZONTAL.value}" or "{vs_transitions.Direction.VERTICAL.value}" if crossfade type is "curtain_cover" or "curtain_reveal"' : '.',
							'CROSSFADE_DIRECTION':				vs_transitions.Direction.LEFT.value,
							'; "DURATION_MAX_VIDEO_SEC" a real number; the maximum number of seconds a video runs before it is clipped off' : '.',
							'DURATION_MAX_VIDEO_SEC' :			15.0,												# Maximum duration of a video clip in seconds (incoming video will get clipped at this point)
							#'; "DENOISE_STRENGTH" a real number; the strength of (global) denoising; best set to 0 to turn it off' : '.',
							#'DENOISE_STRENGTH' :				0.15,												# values less than .3 are "OK"
							'; "SILENT_MODE" is True or False; if True, no status messages are produced to stderr' : '.',
							'SILENT_MODE' :						False,												# overrides DEBUG_MODE
							'; "DEBUG_MODE" is True or False; if True, you will rue the day - an unbelievable volume of debug messages as used during development/debugging' : '.',
							'DEBUG_MODE' :						False,
							'; Does not matter what you specify for TARGET_COLOR* stuff here, we always used fixed values ahs shown below' : '',
							'; "TARGET_COLORSPACE" a string; set for HD; required to render subtitles, it is fixed at this value; this item MUST MATCH TARGET_COLORSPACE_MATRIX_I etc' : '.',
							'TARGET_COLORSPACE' : 				r'BT.709',											# for subtitling. # colorspace Rec2020, BT.2020 Rec709, BT.709, Rec601, BT.601, PC.709, PC.601, TV.fcc, PC.fcc, TV.240m, PC.240m; When no hint found in ASS script and colorspace parameter is empty then the default is BT.601
							# ALSO ... A note about fixed output colour characteristics (the y4m YUV4MPEG2 container doesn't mention them.
							# https://forum.videohelp.com/newreply.php?do=postreply&t=408230#post2684387
							# So we always output BT.709 and related characteristics per what we specify here in default_ini_values
							'; "TARGET_COLORSPACE_MATRIX_I" an integer; set for HD; this is the value that counts; it is fixed at this value; turn on DEBUG_MODE to see lists of these values' : '.',
							'TARGET_COLORSPACE_MATRIX_I' :		int(vs.MatrixCoefficients.MATRIX_BT709.value),
							'; "TARGET_COLOR_TRANSFER_I" an integer; set for HD; this is the value that counts; it is fixed at this value; used by Vapoursynth; turn on DEBUG_MODE to see lists of these values' : '.',
							'TARGET_COLOR_TRANSFER_I' :			int(vs.TransferCharacteristics.TRANSFER_BT709.value),
							'; "TARGET_COLOR_PRIMARIES_I" an integer; set for HD; this is the value that counts; it is fixed at this value; turn on DEBUG_MODE to see lists of these values' : '.',
							'TARGET_COLOR_PRIMARIES_I' :		int(vs.ColorPrimaries.PRIMARIES_BT709.value),
							# NOTE THESE IN REGARD TO VS "bug" in RANGE values not agreeing with the spec:
							#	https://github.com/vapoursynth/vapoursynth/issues/940
							#	https://github.com/vapoursynth/vapoursynth/issues/857
							# https://github.com/vapoursynth/vapoursynth/issues/940#issuecomment-1465041338
							# When calling rezisers etc, ONLY use these values:
							#	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
							#	ZIMG_RANGE_FULL     = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
							# but when obtaining from frame properties and comparing etc, use the vs values from
							# frame properties even though the vapoursynth values are incorrect (opposite to the spec)
							# BUT BUT BUT here we are working solely with vapoursynth settings, not resizers, so stick with using vapoursynth constants and not zimg ones
							'; "TARGET_COLOR_RANGE_I" an integer; set for full-range, not limited-range; this is the (Vapoursynth) value that counts; it is fixed at this value; used by Vapoursynth; turn on DEBUG_MODE to see lists of these values' : '.',
							'; "TARGET_COLOR_RANGE_I note: this Vapoursynth value is opposite to that needed by ZIMG and by resizers which require the ZIMG (the propeer) value; internal transations vs->zimg are done' : '.',
							'TARGET_COLOR_RANGE_I' :			int(vs.ColorRange.RANGE_FULL.value),
							'; "TARGET_WIDTH" an integer; set for HD; do not change unless a dire emergency' : '.',
							'TARGET_WIDTH' :					1920,
							'; "TARGET_HEIGHT" an integer; set for HD; do not change unless a dire emergency' : '.',
							'TARGET_HEIGHT' :					1080,
							'; "TARGET_FPSNUM" an integer; set for PAL' : '.',
							'TARGET_FPSNUM' :					25,													# for fps numerator		... PAL world bias
							'; "TARGET_FPSDEN" an integer; set for PAL' : '.',
							'TARGET_FPSDEN' :					1,													# for fps denominator	... PAL world bias
							'; "UPSIZE_KERNEL" a string; do not change unless a dire emergency; you need the EXACT string name of the resizer' : '.',
							'UPSIZE_KERNEL' :					r'Lanczos',
							'; "DOWNSIZE_KERNEL" a string; do not change unless a dire emergency; you need the EXACT string name of the resizer' : '.',
							'DOWNSIZE_KERNEL' :					r'Spline36',
							'; "BOX" is True or False; if True, images and videos are resized vertically/horizontally to maintain aspect ratio and padded; False streches and squeezes ' : '.',
							'BOX' :								True,											# True would initiate letterboxing or pillarboxing. False fills to TARGET_WIDTH,TARGET_HEIGHT
							}
						}
ini_values = default_ini_values
print_DEBUG(f'RAW default_ini_values=\n{objPrettyPrint.pformat(default_ini_values)}')
#for k, v in default_ini_values[ini_section_name].items():
#	print_DEBUG(f'USING A FOR LOOP, default_ini_values {objPrettyPrint.pformat(k)}"] = "{objPrettyPrint.pformat(v)}"')
#
config = None
config = configparser.ConfigParser(default_ini_values[ini_section_name], allow_no_value=True)
reset_to_ini_defaults = False
if os.path.isfile(ini_file_specifying_parameters):
	print_DEBUG(f'.ini file "{ini_file_specifying_parameters}" exists ... about to try reading the file ...')
	# we used to have a try/except arpound this but it is easier and more informative for the user to just let it crash with a handy diagnostic message
	input_file = open(ini_file_specifying_parameters,'r')	# why is this failing on open ?
	config.read_file(input_file)
	input_file.close()
	print_DEBUG(f'in try: opened and closed .ini file "{ini_file_specifying_parameters}".')
	if config.has_section(ini_section_name):
		if config.has_option(ini_section_name, "SILENT_MODE"):
			print_DEBUG(f'config.getboolean(ini_section_name, "SILENT_MODE") detected EARLY in .ini, value={config.getboolean(ini_section_name, "SILENT_MODE")}')
			IS_SILENT = config.getboolean(ini_section_name, "SILENT_MODE")	# if enabled, turn on DEBUG immediately
		if config.has_option(ini_section_name, "DEBUG_MODE"):
			print_DEBUG(f'config.getboolean(ini_section_name, "DEBUG_MODE") detected EARLY in .ini, value={config.getboolean(ini_section_name, "DEBUG_MODE")}')
			IS_DEBUG = config.getboolean(ini_section_name, "DEBUG_MODE")	# if enabled, turn on DEBUG immediately
		print_DEBUG(f'"{ini_section_name}" is in config, config={objPrettyPrint.pformat(config[ini_section_name].items())}')
		for k,v in config[ini_section_name].items():
			print_DEBUG(f'\tRAW, READ FROM .ini WITH DEFAULTS: config["{ini_section_name}"]["{objPrettyPrint.pformat(k)}"] = {objPrettyPrint.pformat(v)}')
		reset_to_ini_defaults = False
	else:
		print_NORMAL(f'WARNING: Missing section "{ini_section_name}" in .ini file "{ini_file_specifying_parameters}". Using defaults.')
		reset_to_ini_defaults = True
else:
	print_NORMAL(f'WARNING: Missing .ini file "{ini_file_specifying_parameters}". Using defaults.')
	reset_to_ini_defaults = True
#
if reset_to_ini_defaults:
	print_DEBUG(f'Reverting to default settngs:\n{default_ini_values}')
	# revert to default values
	config = configparser.ConfigParser(allow_no_value=True)	# don't apply defaults here, do't want them written to the .ini file
	config.read_dict(default_ini_values)
	# re-write the .ini file with newly defaulted values
	o_f = open(ini_file_specifying_parameters,'w')
	config.write(o_f)
	o_f.close()
	# re-read the parameters from the newly re-created .inni file, this tim applying defaults to the read operation
	config = configparser.ConfigParser(default_ini_values[ini_section_name], allow_no_value=False)
	i_f = open(ini_file_specifying_parameters,'r')	# no try/except, let it fail this time
	config.read_file(i_f)
	i_f.close()
else:
	print_DEBUG(f'Using settings from .ini file "{ini_file_specifying_parameters}"')
if config.has_option(ini_section_name, "SILENT_MODE"):
	print_DEBUG(f'config.getboolean(ini_section_name, "SILENT_MODE") detected value={config.getboolean(ini_section_name, "SILENT_MODE")}')
	IS_SILENT = config.getboolean(ini_section_name, "SILENT_MODE")	# if enabled, turn on/off SILENT_MODE immediately
if config.has_option(ini_section_name, "DEBUG_MODE"):
	print_DEBUG(f'config.getboolean(ini_section_name, "DEBUG_MODE") detected value={config.getboolean(ini_section_name, "DEBUG_MODE")}')
	IS_DEBUG = config.getboolean(ini_section_name, "DEBUG_MODE")	# if enabled, turn on/off DEBUG_MODE immediately
#
print_DEBUG(f'Final setting of SILENT_MODE={config.getboolean(ini_section_name, "SILENT_MODE")}')
print_DEBUG(f'Final setting of DEBUG_MODE={config.getboolean(ini_section_name, "DEBUG_MODE")}')
#
# grab the .ini settings that the user has specified, or the defaults we have set, or combined both
if config.has_section(ini_section_name):
	print_DEBUG(f'RAW config .ini read as config.get(ini_section_name, "DIRECTORY_LIST")={config.get(ini_section_name, "DIRECTORY_LIST")}')
	ini_values[ini_section_name]["DIRECTORY_LIST"]				= ast.literal_eval(config.get(ini_section_name, 'DIRECTORY_LIST'))		# convert str back into a list
	print_DEBUG(f'RAW config .ini read as ini_values[ini_section_name]["DIRECTORY_LIST"]={ini_values[ini_section_name]["DIRECTORY_LIST"]}')
	ddl_fully_qualified = []									# make DIRECTORY_LIST entries all fully qualified and escaped where required
	for ddl in ini_values[ini_section_name]["DIRECTORY_LIST"]:
		ddl_fully_qualified.append(fully_qualified_directory_no_trailing_backslash(ddl))
	ini_values[ini_section_name]["DIRECTORY_LIST"]				= ddl_fully_qualified
	print_DEBUG(f'RAW config .ini read as config.get(ini_section_name, "TEMP_DIRECTORY_LIST")={config.get(ini_section_name, "TEMP_DIRECTORY_LIST")}')
	ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"]			= ast.literal_eval(config.get(ini_section_name, 'TEMP_DIRECTORY_LIST'))		# convert str back into a list
	print_DEBUG(f'RAW config .ini read as ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"]={ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"]}')
	td_fully_qualified = []
	for td in ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"]:	# should only be 1 in the list. if more then we convert them all but only use the first
		td_fully_qualified.append(fully_qualified_directory_no_trailing_backslash(td))
	ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"]			= td_fully_qualified
	ini_values[ini_section_name]["RECURSIVE"]					= config.getboolean(ini_section_name, 'RECURSIVE')
	ini_values[ini_section_name]["SUBTITLE_DEPTH"]				= int(config.getint(ini_section_name, 'SUBTITLE_DEPTH'))
	ini_values[ini_section_name]["SUBTITLE_FONTSIZE"]			= int(config.getint(ini_section_name, 'SUBTITLE_FONTSIZE'))
	ini_values[ini_section_name]["SUBTITLE_FONTSCALE"]			= float(config.getfloat(ini_section_name, 'SUBTITLE_FONTSCALE'))
	ini_values[ini_section_name]["DURATION_PIC_SEC"]			= float(config.getfloat(ini_section_name, 'DURATION_PIC_SEC'))
	ini_values[ini_section_name]["DURATION_CROSSFADE_SECS"]		= float(config.getfloat(ini_section_name, 'DURATION_CROSSFADE_SECS'))
	ini_values[ini_section_name]["CROSSFADE_TYPE"]				= config.get(ini_section_name, 'CROSSFADE_TYPE')
	ini_values[ini_section_name]["CROSSFADE_DIRECTION"]			= config.get(ini_section_name, 'CROSSFADE_DIRECTION')
	ini_values[ini_section_name]["DURATION_MAX_VIDEO_SEC"]		= float(config.getfloat(ini_section_name, 'DURATION_MAX_VIDEO_SEC'))
	#ini_values[ini_section_name]["DENOISE_STRENGTH"]			= float(config.getfloat(ini_section_name, 'DENOISE_STRENGTH'))
	ini_values[ini_section_name]["SILENT_MODE"]					= config.getboolean(ini_section_name, 'SILENT_MODE')
	ini_values[ini_section_name]["DEBUG_MODE"]					= config.getboolean(ini_section_name, 'DEBUG_MODE')
	# A note about fixed output colour characteristics (the y4m YUV4MPEG2 container doesn't mention them.
	# https://forum.videohelp.com/newreply.php?do=postreply&t=408230#post2684387
	# So we always output BT.709 and related characteristics per what we specify in default_ini_values
	# Hence we comment out TARGET_COLOR* ini-read stuff so as to only use our default settings and take the defaults from default_ini_values
	#ini_values[ini_section_name]["TARGET_COLORSPACE"] 			= config.get(ini_section_name, 'TARGET_COLORSPACE')	# for subtitliing
	#ini_values[ini_section_name]["TARGET_COLORSPACE_MATRIX_I"]	= int(config.getint(ini_section_name, 'TARGET_COLORSPACE_MATRIX_I'))
	#ini_values[ini_section_name]["TARGET_COLOR_TRANSFER_I"]		= int(config.getint(ini_section_name, 'TARGET_COLOR_TRANSFER_I'))
	#ini_values[ini_section_name]["TARGET_COLOR_PRIMARIES_I"]	= int(config.getint(ini_section_name, 'TARGET_COLOR_PRIMARIES_I'))
	#ini_values[ini_section_name]["TARGET_COLOR_RANGE_I"]		= int(config.get(ini_section_name, 'TARGET_COLOR_RANGE_I'))
	ini_values[ini_section_name]["TARGET_WIDTH"]				= int(config.getint(ini_section_name, 'TARGET_WIDTH'))
	ini_values[ini_section_name]["TARGET_HEIGHT"]				= int(config.getint(ini_section_name, 'TARGET_HEIGHT'))
	ini_values[ini_section_name]["TARGET_FPSNUM"]				= int(config.getint(ini_section_name, 'TARGET_FPSNUM'))
	ini_values[ini_section_name]["TARGET_FPSDEN"]				= int(config.getint(ini_section_name, 'TARGET_FPSDEN'))
	ini_values[ini_section_name]["UPSIZE_KERNEL"]				= config.get(ini_section_name, 'UPSIZE_KERNEL')
	ini_values[ini_section_name]["DOWNSIZE_KERNEL"]				= config.get(ini_section_name, 'DOWNSIZE_KERNEL')
	ini_values[ini_section_name]["BOX"]							= config.getboolean(ini_section_name, 'BOX')
	print_DEBUG(f'Read in from the .ini these values (defaults are applied from the .ini file):\n{ini_values[ini_section_name]}')
else:
	raise ValueError(f'ERROR: .ini file unable to be read or recreated properly')
# add clarifying information to and re-save the updated set of .ini values over the top of the existing .ini file
with open(ini_file_specifying_parameters, 'w') as configfile:
	# add the new set of .ini value to be saved
	update_config =  configparser.ConfigParser(allow_no_value=True)
	##update_config[ini_section_name] = default_ini_values[ini_section_name] # ?????????????????? found and fixed a bug presumably
	update_config[ini_section_name] = ini_values[ini_section_name]
	# add example values to make it easier for a human reader of the .ini file
	tmp_name = 'Enum_vs.MatrixCoefficients'
	tmp_dict = { tmp_name : {}}
	for v in vs.MatrixCoefficients:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.TransferCharacteristics'
	tmp_dict = { tmp_name : {}}
	for v in vs.TransferCharacteristics:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.ColorPrimaries'
	tmp_dict = { tmp_name : {}}
	for v in vs.ColorPrimaries:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.ColorRange'
	tmp_dict = { tmp_name : {}}
	for v in vs.ColorRange:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_ZIMG.ColorRange'
	tmp_dict = { tmp_name : {"ZIMG.RANGE_LIMITED" : ZIMG_RANGE_LIMITED, "ZIMG.RANGE_FULL" : ZIMG_RANGE_FULL}}
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.PresetFormat'
	tmp_dict = { tmp_name : {}}
	for v in vs.PresetFormat:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.ColorFamily'
	tmp_dict = { tmp_name : {}}
	for v in vs.ColorFamily:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.ChromaLocation'
	tmp_dict = { tmp_name : {}}
	for v in vs.ChromaLocation:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.FieldBased'
	tmp_dict = { tmp_name : {}}
	for v in vs.FieldBased:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	# update the .ini file
	print_DEBUG(f'Saving updated .ini file: ini_values=\n{objPrettyPrint.pformat(ini_values)}')
	update_config.write(configfile)
print_NORMAL(f'Saved updated .ini "{ini_file_specifying_parameters}"')
# calculate some values and create a new updated calculated values dict
calc_ini = ini_values[ini_section_name]
calc_ini["PIC_EXTENSIONS"]					= [".png", ".jpg", ".jpeg", ".gif"]								# always lower case
calc_ini["VID_EXTENSIONS"]					= [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov"]	# always lower case
calc_ini["EEK_EXTENSIONS"]					= [".m2ts"]														# always lower case
calc_ini["VID_EEK_EXTENSIONS"]				= calc_ini["VID_EXTENSIONS"] + calc_ini["EEK_EXTENSIONS"]
calc_ini["EXTENSIONS"]						= calc_ini["PIC_EXTENSIONS"] + calc_ini["VID_EXTENSIONS"] + calc_ini["EEK_EXTENSIONS"]
calc_ini["WORKING_PIXEL_FORMAT"]			= int(vs.YUV444P8.value)				# pixel format of the working clips (mainly required by vs_transitions)
calc_ini["TARGET_PIXEL_FORMAT"]				= int(vs.YUV420P8.value)				# pixel format of the target video
calc_ini["DG_PIXEL_FORMAT"]					= int(vs.YUV420P16.value)				# pixel format of the video for use by DG tools
calc_ini["TARGET_FPS"]						= round(calc_ini["TARGET_FPSNUM"] / calc_ini["TARGET_FPSDEN"], 3)
calc_ini["DURATION_PIC_FRAMES"]				= int(math.ceil(calc_ini["DURATION_PIC_SEC"] * calc_ini["TARGET_FPS"]))
calc_ini["DURATION_BLANK_CLIP_FRAMES"]		= calc_ini["DURATION_PIC_FRAMES"]	# make equal to the display time for an image; DURATION_CROSSFADE_FRAMES will be less than this
calc_ini["DURATION_CROSSFADE_FRAMES"]		= int(math.ceil(calc_ini["DURATION_CROSSFADE_SECS"] * calc_ini["TARGET_FPS"]))
calc_ini["DURATION_MAX_VIDEO_FRAMES"]		= int(math.ceil(calc_ini["DURATION_MAX_VIDEO_SEC"] * calc_ini["TARGET_FPS"]))
calc_ini["DOT_FFINDEX"]						= ".ffindex".lower()		# for removing temporary *.ffindex files at the end
calc_ini["MODX"]							= int(2)	   # mods for letterboxing calculations, example, for 411 YUV as an extreme
calc_ini["MODY"]							= int(2)	   # mods would have to be MODX=4, MODY=1 as minimum
calc_ini["SUBTITLE_MAX_DEPTH"]				= int(10)
calc_ini["Rotation_anti-clockwise"]			= "anti-clockwise".lower()
calc_ini["Rotation_clockwise"]				= "clockwise".lower()
# https://github.com/vapoursynth/vapoursynth/issues/940#issuecomment-1465041338
# When calling rezisers etc, ONLY use these values:
#	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
#	ZIMG_RANGE_FULL     = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
# but when obtaining from frame properties and comparing etc, use the vs values from
# frame properties even though the vapoursynth values are incorrect (opposite to the spec)
# https://www.vapoursynth.com/doc/api/vapoursynth.h.html#enum-vspresetformat
if calc_ini["TARGET_COLOR_RANGE_I"] == int(vs.ColorRange.RANGE_LIMITED.value):
	calc_ini["TARGET_COLOR_RANGE_I_ZIMG"] = ZIMG_RANGE_LIMITED					# use the ZIMG RANGE constants as they are correct and vapoursynth ones are not (opposite to the spec)
elif calc_ini["TARGET_COLOR_RANGE_I"] == int(vs.ColorRange.RANGE_FULL.value):
	calc_ini["TARGET_COLOR_RANGE_I_ZIMG"] = ZIMG_RANGE_FULL						# use the ZIMG RANGE constants as they are correct and vapoursynth ones are not (opposite to the spec)
else:
	raise ValueError(f'ERROR: calc_ini["TARGET_COLOR_RANGE_I"]={calc_ini["TARGET_COLOR_RANGE_I"]} is an invalid value')
#++++++++++++++++++++
# Consistency checks
min_actual_display_time = 0.5	# seconds
if (2 * ini_values[ini_section_name]["DURATION_CROSSFADE_SECS"]) + min_actual_display_time > ini_values[ini_section_name]["DURATION_PIC_SEC"]:
	raise ValueError(f'ERROR: DURATION_PIC_SEC must be >= (2 * DURATION_CROSSFADE_SECS) + min_actual_display_time \n\ DURATION_CROSSFADE_SECS={ini_values[ini_section_name]["DURATION_CROSSFADE_SECS"]} DURATION_PIC_SEC={ini_values[ini_section_name]["DURATION_PIC_SEC"]} min_actual_display_time={min_actual_display_time}')
if (2 * ini_values[ini_section_name]["DURATION_CROSSFADE_SECS"]) + min_actual_display_time > ini_values[ini_section_name]["DURATION_MAX_VIDEO_SEC"]:
	raise ValueError(f'ERROR: DURATION_MAX_VIDEO_SEC must be >= (2 * DURATION_CROSSFADE_SECS) + min_actual_display_time \n\ DURATION_CROSSFADE_SECS={ini_values[ini_section_name]["DURATION_CROSSFADE_SECS"]} DURATION_MAX_VIDEO_SEC={ini_values[ini_section_name]["DURATION_MAX_VIDEO_SEC"]} min_actual_display_time={min_actual_display_time}')
#++++++++++++++++++++
print_DEBUG(f'----------------------------------------------------------------------------------------------------------------------------')
for v in vs.PresetFormat:	# eg vs.YUV420P8
	print_DEBUG(f'vs.PresetFormat ENUM: {str(v)} = {v.value}')
for v in vs.MatrixCoefficients:
	print_DEBUG(f'vs.MatrixCoefficients ENUM: {str(v)} = {v.value}')
for v in vs.TransferCharacteristics:
	print_DEBUG(f'vs.TransferCharacteristics ENUM: {str(v)} = {v.value}')
for v in vs.ColorPrimaries:
	print_DEBUG(f'vs.ColorPrimaries ENUM: {str(v)} = {v.value}')
for v in vs.ColorRange:
	print_DEBUG(f'vs.ColorRange ENUM: {str(v)} = {v.value}')
for v in vs.ColorFamily:
	print_DEBUG(f'vs.ColorFamily ENUM: {str(v)} = {v.value}')
for v in vs.ChromaLocation:
	print_DEBUG(f'vs.ChromaLocation ENUM: {str(v)} = {v.value}')
for v in vs.FieldBased:
	print_DEBUG(f'vs.FieldBased ENUM: {str(v)} = {v.value}')
print_DEBUG(f'----------------------------------------------------------------------------------------------------------------------------')
print_DEBUG(f'default_ini_values=\n{objPrettyPrint.pformat(default_ini_values)}')
print_DEBUG(f'----------------------------------------------------------------------------------------------------------------------------')
print_DEBUG(f'ini_values=\n{objPrettyPrint.pformat(ini_values)}')
print_DEBUG(f'----------------------------------------------------------------------------------------------------------------------------')
print_DEBUG(f'calc_ini=\n{objPrettyPrint.pformat(calc_ini)}')
print_DEBUG(f'----------------------------------------------------------------------------------------------------------------------------')
#++++++++++++++++++++
if not os.path.isdir(ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"][0]):
	try: 
		os.mkdir(ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"][0]) 
		print_NORMAL(f'Created new directory: "{ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"][0]}"')
	except OSError as error: 
		#print_DEBUG(error) 
		pass
#++++++++++++++++++++
print_DEBUG(f'Creating blank_clip with the desired  target properties')
blank_clip = core.std.BlankClip(format=calc_ini["WORKING_PIXEL_FORMAT"], width=calc_ini["TARGET_WIDTH"], height=calc_ini["TARGET_HEIGHT"], fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"], length=calc_ini["DURATION_BLANK_CLIP_FRAMES"], color=(16,128,128))	 # notice no colorspace,"range" etc can be specified
blank_clip = core.std.AssumeFPS(clip=blank_clip, fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
last_file_opened_with_ffms2 = True	# JUST A DUMMY FOR get_clip_specs
last_file_opened_with_imwri = False
last_file_opened_with_LWLibavSource = False
last_file_opened_with_LibavSMASHSource = False
blank_clip_specs = get_clip_specs(blank_clip, path=None, ext=".mp4")
# now guess and set any missing specs in blank_clip
if blank_clip_specs["guessed_Matrix"]:
	print_DEBUG(f'blank_clip: SetFrameProps _Matrix from existing "{blank_clip_specs["_Matrix"]}" to guessed "{blank_clip_specs["proposed_Matrix"]}"')
	blank_clip = core.std.SetFrameProps(blank_clip, _Matrix=blank_clip_specs["proposed_Matrix"])
if blank_clip_specs["guessed_Primaries"]:
	print_DEBUG(f'blank_clip: SetFrameProps _Primaries from existing "{blank_clip_specs["_Primaries"]}" to guessed "{blank_clip_specs["proposed_Primaries"]}"')
	blank_clip = core.std.SetFrameProps(blank_clip, _Primaries=blank_clip_specs["proposed_Primaries"])
if blank_clip_specs["guessed_Transfer"]:
	print_DEBUG(f'blank_clip: SetFrameProps _Transfer from existing "{blank_clip_specs["_Transfer"]}" to guessed "{blank_clip_specs["proposed_Transfer"]}"')
	blank_clip = core.std.SetFrameProps(blank_clip, _Transfer=blank_clip_specs["proposed_Transfer"])
# NOTE THESE IN REGARD TO VS "bug" in RANGE values not agreeing with the spec:
#	https://github.com/vapoursynth/vapoursynth/issues/940
#	https://github.com/vapoursynth/vapoursynth/issues/857
# https://github.com/vapoursynth/vapoursynth/issues/940#issuecomment-1465041338
# When calling rezisers etc, ONLY use these values:
#	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
#	ZIMG_RANGE_FULL     = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
# but when obtaining from frame properties and comparing etc, use the vs values from
# frame properties even though the vapoursynth values are incorrect (opposite to the spec)
# BUT BUT BUT here we are working solely with vapoursynth settings, not resizers, so stick with using vapoursynth constants and not zimg ones
#if blank_clip_specs["guessed_ColorRange"]:
#	print_DEBUG(f'blank_clip: SetFrameProps _ColorRange from existing "{blank_clip_specs["_ColorRange"]}" to guessed "{blank_clip_specs["proposed_ColorRange"]}"')
#	blank_clip = core.std.SetFrameProps(blank_clip, _ColorRange=blank_clip_specs["proposed_ColorRange"])
# Ensure the colour range of the blank_clip is what we require, by using a resizer to set the properties
with blank_clip.get_frame(0) as f:
	print_DEBUG(f'blank_clip: incoming frame properties before resize: w={blank_clip.width} h={blank_clip.height} fps={blank_clip.fps} {objPrettyPrint.pformat(blank_clip)} {objPrettyPrint.pformat(f.props)}')
print_DEBUG(f'blank_clip: TARGET resize properties: width={blank_clip.width}, height={blank_clip.height}, format={calc_ini["WORKING_PIXEL_FORMAT"]}, calc_ini["TARGET_COLOR_RANGE_I_ZIMG"]={calc_ini["TARGET_COLOR_RANGE_I_ZIMG"]}), primaries={calc_ini["TARGET_COLOR_PRIMARIES_I"]}, transfer={calc_ini["TARGET_COLOR_TRANSFER_I"]},  matrix={calc_ini["TARGET_COLORSPACE_MATRIX_I"]}')
blank_clip_resize = getattr(blank_clip.resize, calc_ini["UPSIZE_KERNEL"])	# get the resize function object ?handle? with the nominated kernel
#
blank_clip = blank_clip_resize(width=calc_ini["TARGET_WIDTH"], height=calc_ini["TARGET_HEIGHT"], format=calc_ini["WORKING_PIXEL_FORMAT"], matrix=calc_ini["TARGET_COLORSPACE_MATRIX_I"], transfer=calc_ini["TARGET_COLOR_TRANSFER_I"], primaries=calc_ini["TARGET_COLOR_PRIMARIES_I"], range=calc_ini["TARGET_COLOR_RANGE_I_ZIMG"])
blank_clip = core.std.AssumeFPS(clip=blank_clip, fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
with blank_clip.get_frame(0) as f:
	print_DEBUG(f'blank_clip: outgoing frame properties after resize: w={blank_clip.width} h={blank_clip.height} fps={blank_clip.fps} {objPrettyPrint.pformat(blank_clip)} {objPrettyPrint.pformat(f.props)}')
#
last_file_opened_with_ffms2 = False
print_DEBUG(f'Created blank_clip with the desired  target properties')

#++++++++++++++++++++
crossfade_blank_clip = blank_clip[0]*calc_ini["DURATION_BLANK_CLIP_FRAMES"]
prior_clip_for_crossfade = crossfade_blank_clip
#if calc_ini["DURATION_CROSSFADE_FRAMES"] > 0:
#	#if len(blank_clip) < calc_ini["DURATION_CROSSFADE_FRAMES"] :
#	#	crossfade_blank_clip = blank_clip[0]*calc_ini["DURATION_CROSSFADE_FRAMES"]
#	#else 
#	#	crossfade_blank_clip = blank_clip
#	crossfade_blank_clip = blank_clip[0]*calc_ini["DURATION_CROSSFADE_FRAMES"]
#	prior_clip_for_crossfade = crossfade_blank_clip
#	print_DEBUG(f'calc_ini["DURATION_CROSSFADE_FRAMES"] ({calc_ini["DURATION_CROSSFADE_FRAMES"]}) > 0 ... crossfade_blank_clip={crossfade_blank_clip}')
#else:
#	prior_clip_for_crossfade = blank_clip
#	print_DEBUG(f'calc_ini["DURATION_CROSSFADE_FRAMES"] ({calc_ini["DURATION_CROSSFADE_FRAMES"]}) <= 0 ... no crossfade_blank_clipcreated')
#
#++++++++++++++++++++
if calc_ini["RECURSIVE"]:
	glob_var="**/*.*"			# recursive
	ff_glob_var="**/*.ffindex"	# for .ffindex file deletion recursive
else:
	glob_var="*.*"				# non-recursive
	ff_glob_var="*.ffindex"		# for .ffindex file deletion non-recursive
# glob : with DIRECTORY not having a trailing slash !!!
num_unreachable_objects = gc.collect()	# With no arguments, run a full garbage collection. # The number of unreachable objects found is returned
print_DEBUG(f'*** GARBAGE_COLLECTION: post blank_clip creation and pre-Directory-loop, number of unreachable objects found={num_unreachable_objects}')
Count_of_files = 0
clips = prior_clip_for_crossfade	# initialize the accumulated clips with a starting small blank clip


for Directory in calc_ini["DIRECTORY_LIST"]:
	current_Directory = fully_qualified_directory_no_trailing_backslash(Directory)
	ct = calc_ini["CROSSFADE_TYPE"] if calc_ini["DURATION_CROSSFADE_FRAMES"]>0 else None
	cd = calc_ini["CROSSFADE_DIRECTION"] if calc_ini["DURATION_CROSSFADE_FRAMES"]>0 else None
	print_NORMAL(f'Start processing image/video files in "{current_Directory}" crossfade="{ct}/{cd}" RECURSIVE={calc_ini["RECURSIVE"]} DEBUG_MODE={calc_ini["DEBUG_MODE"]} SILENT_MODE={calc_ini["SILENT_MODE"]}  glob_var="{glob_var}" \n      with Extensions={objPrettyPrint.pformat(calc_ini["EXTENSIONS"])}')
	# NOTE: current_Directory MUST NOT have a trailing backslash ... remove during ini setup
	paths = Path(current_Directory).glob(glob_var) # generator of all paths in a directory, files starting with . won't be matched by default
	path = get_path(paths)	#pre-fetch first path
	if path is None:
		raise ValueError(f'ERROR: File Extensions:\n{calc_ini["EXTENSIONS"]}\nnot found in "{current_Directory}"')
	#------
	while not (path is None):	# first clip already pre-retrieved ready for this while loop
		print_DEBUG(f'********************************************************************************************************************************************************************************************************************************************************')
		Count_of_files = Count_of_files + 1
		print_NORMAL(f'processing {Count_of_files} {str(path)}')
		this_clip = get_clip(path)
		if this_clip is not None:	# ignore clips which had an issue with being opened
			if calc_ini["DURATION_CROSSFADE_FRAMES"] > 0:		# and calc_ini["CROSSFADE_TYPE"].lower() != "none".lower():
				print_DEBUG(f'Performing crossfade_merge in while loop')
				#### There is a mysterious bug in vs_transitions, if you use a random function to randomly call different transitions
				#### Occasionally, you will receive errors like::
				#### 	Error: Failed to retrieve frame 88 with error: StackVertical: clip format and width must match
				#### 	Error: Failed to retrieve frame 2096 with error: FrameEval: Function didn't return a clip
				#### 	Error: Failed to retrieve frame 1347 with error: FrameEval: Function didn't return a clip
				#### PERHAPS ?? this seems to be caused by the vs_transition module's functions "interfering" with each other
				clips = crossfade_merge(a=clips, b=this_clip, crossfade_duration_frames=calc_ini["DURATION_CROSSFADE_FRAMES"], crossfade_type=calc_ini["CROSSFADE_TYPE"], crossfade_direction=calc_ini["CROSSFADE_DIRECTION"]) 
		path = get_path(paths)		# get next path to process in this while loop
		num_unreachable_objects = gc.collect()	# With no arguments, run a full garbage collection. # The number of unreachable objects found is returned
		print_DEBUG(f'*** GARBAGE_COLLECTION: in-Directory-loop end of processing a single file, number of unreachable objects found={num_unreachable_objects}')
		print_DEBUG(f'********************************************************************************************************************************************************************************************************************************************************')
	#------
	# perhaps a finishing crossfade to black ?
	if calc_ini["DURATION_CROSSFADE_FRAMES"] > 0 and calc_ini["CROSSFADE_TYPE"].lower() != "none".lower():	
		print_DEBUG(f'Performing final crossfade_merge after while loop')
		clips = crossfade_merge(a=clips, b=prior_clip_for_crossfade, crossfade_duration_frames=calc_ini["DURATION_CROSSFADE_FRAMES"], crossfade_type=calc_ini["CROSSFADE_TYPE"], crossfade_direction=calc_ini["CROSSFADE_DIRECTION"]) 
	else:
		print_DEBUG(f'Performing NO final crossfade_merge after while loop')
		clips = clips + prior_clip_for_crossfade	# add a small blank clip tothe end
clips = clips.std.AssumeFPS(fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
del this_clip
#++++++++++++++++++++

#++++++++++++++++++++
print_NORMAL(f'Finished processing {Count_of_files} image/video files in "{current_Directory}" num_frames={len(clips)} crossfade="{ct}/{cd}" RECURSIVE={calc_ini["RECURSIVE"]} DEBUG_MODE={calc_ini["DEBUG_MODE"]} SILENT_MODE={calc_ini["SILENT_MODE"]}  glob_var="{glob_var}" \n      with Extensions={objPrettyPrint.pformat(calc_ini["EXTENSIONS"])}')
#++++++++++++++++++++

#++++++++++++++++++++
# Convert from ["WORKING_PIXEL_FORMAT"] vs.YUV444P8 to  ["WORKING_PIXEL_FORMAT"] vs.YUV420P8 for output
clips = clips.resize.Point(format=calc_ini["TARGET_PIXEL_FORMAT"])
#++++++++++++++++++++

#++++++++++++++++++++
# Cleanup any temporary .ffindex files created by ffms2
print_NORMAL(f'Start removing temporary *.ffindex files from directory "{current_Directory}" with recursive="{calc_ini["RECURSIVE"]}" ...')
#--- IF THE .FFINDEX ARE CREATED ALONGSIDE THE VIDEO FILES
#ff_glob_var="**/*.ffindex"		# for .ffindex file deletion recursive
##ff_glob_var="*.ffindex"		# for .ffindex file deletion non-recursive
#Count_of_files_removed = 0
#for Directory in calc_ini["DIRECTORY_LIST"]:
#	current_Directory = fully_qualified_directory_no_trailing_backslash(Directory)
#	print_NORMAL(f'Start removing temporary *.ffindex files from directory "{current_Directory}" with recursive="{calc_ini["RECURSIVE"]}" ...')
#	pp = current_Directory + "/" + ff_glob_var
#	ffindex_files = glob.glob(pp, recursive=calc_ini["RECURSIVE"])
#	for ff in ffindex_files:
#		if ff.lower()[-len(calc_ini["DOT_FFINDEX"]):] == calc_ini["DOT_FFINDEX"]:	# double check the file really does have ext .ffindex
#			try:
#				Count_of_files_removed = Count_of_files_removed + 1
#				print_DEBUG(f'removing {Count_of_files_removed} {ff}')
#				os.remove(ff)
#				#if (Count_of_files_removed % (10))==0:
#				#	print_NORMAL(f'{Count_of_files_removed},', end='')	# https://www.geeksforgeeks.org/gfact-50-python-end-parameter-in-print/
#				#	if (Count_of_files_removed % (10*10*3))==0:
#				#		print_NORMAL(f'')
#			except OSError as ee:
#				print_NORMAL(f'ERROR:  error during removal of ffindex file: {ff} :{ee} : {ee.strerror}')
#				raise ValueError(f'ERROR: error during removal of ffindex file: {ff} :{ee} : {ee.strerror}')
#--- IF THE .FFINDEX ARE CREATED in the temporary folder
ff_glob_var="**/*.ffindex"		# for .ffindex file deletion recursive
#ff_glob_var="*.ffindex"		# for .ffindex file deletion non-recursive
pp = ini_values[ini_section_name]["TEMP_DIRECTORY_LIST"][0] + "/" + ff_glob_var
ffindex_files = glob.glob(pp, recursive=calc_ini["RECURSIVE"])
num_unreachable_objects = gc.collect()	# With no arguments, run a full garbage collection. # The number of unreachable objects found is returned
print_DEBUG(f'*** GARBAGE_COLLECTION: post-Directory-loop and pre-Delete-ffindex-files-loop, number of unreachable objects found={num_unreachable_objects}')
Count_of_files_removed = 0
for ff in ffindex_files:
	if ff.lower()[-len(calc_ini["DOT_FFINDEX"]):] == calc_ini["DOT_FFINDEX"]:	# double check the file really does have ext .ffindex
		try:
			Count_of_files_removed = Count_of_files_removed + 1
			print_DEBUG(f'removing {Count_of_files_removed} {ff}')
			os.remove(ff)
			#if (Count_of_files_removed % (10))==0:
			#	print_NORMAL(f'{Count_of_files_removed},', end='')	# https://www.geeksforgeeks.org/gfact-50-python-end-parameter-in-print/
			#	if (Count_of_files_removed % (10*10*3))==0:
			#		print_NORMAL(f'')
		except OSError as ee:
			print_NORMAL(f'ERROR:  error during removal of ffindex file: {ff} :{ee} : {ee.strerror}')
			raise ValueError(f'ERROR: error during removal of ffindex file: {ff} :{ee} : {ee.strerror}')
print_NORMAL(f'Finished removing {Count_of_files_removed} temporary .ffindex files with recursive="{calc_ini["RECURSIVE"]}"')
num_unreachable_objects = gc.collect()	# With no arguments, run a full garbage collection. # The number of unreachable objects found is returned
print_DEBUG(f'*** GARBAGE_COLLECTION: post-Delete-ffindex-files-loop, number of unreachable objects found={num_unreachable_objects}')
clips.set_output()

#++++++++++++++++++++
# hmm, audio ? maybe later using source filter "bas" ?
print_NORMAL(f'Done.')
output_clip_specs = get_clip_specs(clips, path=None, ext=".mp4")
print_DEBUG(f'OUTPUT VIDEO: clip and frame properties: w={clips.width} h={clips.height} specs=\n{objPrettyPrint.pformat(output_clip_specs)}')

#++++++++++++++++++++
### FOR DUBUG ONLY
#if IS_DEBUG or IS_DEBUG_SYSTEM_OVERRIDE:
if IS_DEBUG or IS_DEBUG_SYSTEM_OVERRIDE:
	vpy_log = []
	print_DEBUG('Post set_output: Consistency Check: loading all frames ...')
	num_frames = len(clips)
	baddies = 0
	for n in range(num_frames):
		try:
			clips.get_frame(n)
		except Exception as e:
			baddies = baddies + 1
			vpy_log.append(f'Post set_output: Consistency Check: FAILED to get_frame at frame {n} (base 0) of {num_frames-1} (base 0): {e}')
	if len(vpy_log) > 0:
		for n in range(len(vpy_log)):
			print_NORMAL(vpy_log[n])
		raise ValueError(f'Post set_output: Consistency Check: FAILED to get_frame {baddies} of {num_frames} frames')
	else:
		print_DEBUG(f'Post set_output: Consistency Check: passed, {num_frames} frames successfully retrieved')
