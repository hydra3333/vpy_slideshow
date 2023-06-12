import vapoursynth as vs
from vapoursynth import core
core = vs.core
#core.num_threads = 1
import sys
import os
import importlib
import re
import argparse
from functools import partial
import pathlib
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
import datetime
from datetime import datetime, date, time, timezone
from fractions import Fraction
from ctypes import *		# for mediainfo ... load via ctypes.CDLL(r'.\MediaInfo.dll')
from typing import Union	# for mediainfo
from typing import NamedTuple
from collections import defaultdict, OrderedDict
from enum import Enum
from enum import auto
#from strenum import StrEnum
#from strenum import LowercaseStrEnum
#from strenum import UppercaseStrEnum
import itertools
import math
import random
import glob
import configparser	# or in v3: configparser 
import yaml
import json
import pprint
import ast
import uuid
import logging

# for subprocess control eg using Popen
import time
from queue import Queue, Empty
from threading import Thread

import gc	# for inbuilt garbage collection
# THE NEXT STATEMENT IS ONLY FOR DEBUGGING AND WILL CAUSE EXTRANEOUS OUTPUT TO STDERR
#gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS)	# for debugging, additional garbage collection settings, writes to stderr https://docs.python.org/3/library/gc.html to help detect leaky memory issues
num_unreachable_objects = gc.collect()	# collect straight away

from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.ExifTags import TAGS

import pydub
from pydub import AudioSegment

# Ensure we can import modules from ".\" by adding the current default folder to the python path.
# (tried using just PYTHONPATH environment variable but it was unreliable)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

CDLL(r'MediaInfo.dll')				# note the hard-coded folder	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption		# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
#from MediaInfoDLL3 import *											# per https://github.com/MediaArea/MediaInfoLib/blob/master/Source/Example/HowToUse_Dll3.py

global DEBUG

global TERMINAL_WIDTH					# for use by PrettyPrinter
TERMINAL_WIDTH = 250
global objPrettyPrint
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc

### ********** end of common header ********** 

global SETTINGS_DICT
global OLD_INI_DICT
global OLD_CALC_INI_DICT
global USER_SPECIFIED_SETTINGS_DICT
global ALL_CHUNKS
global ALL_CHUNKS_COUNT
global ALL_CHUNKS_COUNT_OF_FILES

global FFMPEG_EXE
global FFPROBE_EXE
global VSPIPE_EXE

global MI
MI = MediaInfo()

#core.std.LoadPlugin(r'DGDecodeNV.dll')
#core.avs.LoadPlugin(r'DGDecodeNV.dll')

# Path to the FFmpeg executable

def normalize_path(path):
	#if DEBUG:	print(f"DEBUG: normalize_path:  incoming path='{path}'",flush=True)
	# Replace single backslashes with double backslashes
	path = path.rstrip(os.linesep).strip('\r').strip('\n').strip()
	r1 = r'\\'
	r2 = r1 + r1
	r4 = r2 + r2
	path = path.replace(r1, r4)
	# Add double backslashes before any single backslashes
	for i in range(0,20):
		path = path.replace(r2, r1)
	#if DEBUG:	print(f"DEBUG: normalize_path: outgoing path='{path}'",flush=True)
	return path

def fully_qualified_directory_no_trailing_backslash(directory_name):
	# make into a fully qualified directory string stripped and without a trailing backslash
	# also remove extraneous backslashes which get added by things like abspath
	new_directory_name = os.path.abspath(directory_name).rstrip(os.linesep).strip('\r').strip('\n').strip()
	if directory_name[-1:] == (r'\ '.strip()):		# r prefix means the string is treated as a raw string so all escape codes will be ignored. EXCEPT IF THE \ IS THE LAST CHARACTER IN THE STRING !
		new_directory_name = directory_name[:-1]	# remove any trailing backslash
	new_directory_name = normalize_path(new_directory_name)
	return new_directory_name

def fully_qualified_filename(file_name):
	# Make into a fully qualified filename string using double backslashes
	# to later print/write with double backslashes use eg
	#	converted_string = fully_qualified_filename('D:\\a\\b\\\\c\\\\\\d\\e\\f\\filename.txt')
	#	print(repr(converted_string))
	# yields 'D:\\a\\b\\c\\d\\e\\f\\filename.txt'
	new_file_name = os.path.abspath(file_name).rstrip(os.linesep).strip('\r').strip('\n').strip()
	if new_file_name.endswith('\\'):
		new_file_name = new_file_name[:-1]  # Remove trailing backslash
	new_file_name = normalize_path(new_file_name)
	return new_file_name

#********************************************************************************************************
#********************************************************************************************************
#--------------------------------------------------------------------------------------------------------

# OK, IN THIS BLOCK WE HAVE FUNCTIONS TO GET A LOT OF IMAGE AND VIDEO METADATA

#--------------------------------------------------------------------------------------------------------

# https://mediaarea.net/download/binary/libmediainfo0/
# https://mediaarea.net/en/MediaInfo/Download/Windows
# download 64bit DLL without installer, unzip, find Media
# put MediaInfoDLL3.py in your directory (portable setup) or site-packages directory

# use mediainfo functions below like this:
#
# 'Encoded_Date': '2013-09-01 03:46:29 UTC',#
#	video_metadata_dict = video_extract_metadata_via_MEDIAINFO(file_path)
#	Encoded_Date  = datetime.strptime(video_metadata_dict["Encoded_Date"], "%Y-%m-%d %H:%M:%S").strftime("%Y_%m_%d_%H_%M_%S_%f")
# or
#	MI.Open(file_path)
#	mi_dict = {}
#	for param in mi_video_params_1:
#		value = video_mediainfo_value_worker(Stream.Video, track=0, param=param, path=path)
#		video_mediainfo_value_worker
#		mi_dict[param] = value	# any of str, bool, int, float, etc
#	MI.Close()
#	print(f'\n====================mi_dict=\n{objPrettyPrint.pformat(mi_dict)}')

def video_mediainfo_value_worker(stream:int, track:int, param:str, path: Union[Path,str]) -> Union[int,float,str]:
	# Assume MI.Open(str(path)) has already occurred
	global MI	# use the global, since we re-use it across functions
	if not stream in range(0,8):
		raise ValueError(f'ERROR: video_mediainfo_value_worker: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
	if not isinstance(track, int) or track<0:
		raise ValueError(f'ERROR: video_mediainfo_value_worker: track must be a positive integer')
	if not isinstance(param, str):
		raise ValueError(f'ERROR: video_mediainfo_value_worker: param must be a string for particular stream, ion_Static("Info_Parameters")')
	if not isinstance(path, (Path, str)):
		raise ValueError(f'ERROR: video_mediainfo_value_worker: path must be Path or str class')    
	#MI.Open(str(path)) # CHANGED: open/close in calling routine, allowing this to be called mutiple times
	str_value = MI.Get(stream, track, param)
	info_option =  MI.Get(stream, track, param, InfoKind=Info.Options)
	#MI.Close() 		# CHANGED: open/close in calling routine, allowing this to be called mutiple times
	if not str_value:
		return None
	if info_option:
		#returning a proper value type, int, float or str for particular parameter
		type_ = info_option[InfoOption.TypeOfValue] #type_=info_option[3] #_type will be 'I', 'F', 'T', 'D' or 'B'
		try:	# sometimes mediainfo flags an INT or a FLOAT which cannou be ocnverted, so catch those
			val = {'I':int, 'F':float, 'T':str, 'D':str, 'B':str}[type_](str_value)
		except Exception as err:
			#print_NORMAL(f'CONVERSION EXCEPTION ON val =["I":int, "F":float, "T":str, "D":str, "B":str][type_](str_value) ... type_="{type_}" param="{param}" str_value="{str_value}" path={path}')
			#print_NORMAL(f"Unexpected Error {err=}, {type(err)=}")
			val = None
			#raise
			pass
		return val
	else:
		raise ValueError(f'ERROR: video_mediainfo_value_worker: wrong parameter: "{param}" for given stream: {stream}')
#
def video_mediainfo_value(stream:int, track:int, param:str, path: Union[Path,str]) -> Union[int,float,str]:
	# A wrapper for video_mediainfo_value_worker, which gets and returns a single parameter
	# it opens and closes MI, unlike video_mediainfo_value_worker
	# This function permits video_mediainfo_value_worker to be recycled elsewhere to be called mutiple times per one single MI.open
	global MI	# use the global, since we re-use it across functions
	if not stream in range(0,8):
		raise ValueError(f'ERROR: video_mediainfo_value: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
	if not isinstance(track, int) or track<0:
		raise ValueError(f'ERROR: video_mediainfo_value: track must be a positive integer')
	if not isinstance(param, str):
		raise ValueError(f'ERROR: video_mediainfo_value: param must be a string for particular stream, ion_Static("Info_Parameters")')
	if not isinstance(path, (Path, str)):
		raise ValueError(f'ERROR: video_mediainfo_value: path must be Path or str class')   
	MI.Open(str(path))
	val = video_mediainfo_value_worker(stream, track, param, path)
	MI.Close()
	return val
#
def video_extract_metadata_via_MEDIAINFO(file_path):
	global MI
	if DEBUG: print(f"DEBUG: video_extract_metadata_via_MEDIAINFO: entered with file_path='{file_path}'.",flush=True)
	# ALWAYS include Width, Height, Rotation, Encoded_Date
	mi_video_params_1 = [
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
		'Rotation',                                      # : Rotation as a real number eg 180.00
		'FrameRate',                                     # : Frames per second
		'FrameRate_Num',                                 # : Frames per second, numerator
		'FrameRate_Den',                                 # : Frames per second, denominator
		'FrameCount',                                    # : Number of frames
		#
		'Recorded_Date',								 # : Time/date/year that the recording began ... this can be None so use Encoded_Date instead
		'Encoded_Date',									 # : Time/date/year that the encoding of this content was completed
		#
		'FrameRate_Mode',								 # : Frame rate mode (CFR, VFR)
		'FrameRate_Minimum',							 # : Minimum Frames per second
		'FrameRate_Nominal',							 # : Nominal Frames per second
		'FrameRate_Maximum',							 # : Maximum Frames per second
		'FrameRate_Real',								 # : Real (capture) frames per second
		'ScanType',
		'ScanOrder',
		'ScanOrder_Stored',
		'ScanOrder_StoredDisplayedInverted',
		#
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
	mi_dict = {}
	try:
		MI.Open(str(file_path))
	except Exception as e:
		#print(f"video_extract_metadata_via_MEDIAINFO: MediaInfo: Unexpected error getting information from file: '{file_path}'\n{str(e)}",flush=True,file=sys.stderr)
		return mi_dict
	for param in mi_video_params_1:
		#value = mediainfo_value(Stream.Video, track=0, param=param, path=file_path)	# version: single-value retrieval and lots of open/close
		value = video_mediainfo_value_worker(Stream.Video, track=0, param=param, path=file_path)
		video_mediainfo_value_worker
		mi_dict[param] = value	# any of str, bool, int, float, etc
	MI.Close()
	if DEBUG: print(f"Extracted MediaInfo metadata for file_path='{file_path}'\n{objPrettyPrint.pformat(mi_dict)}",flush=True)
	
	# Example dates from mediainfo:	'Recorded_Date': None, 'Encoded_Date': '2016-10-22 02:46:59 UTC'
	try:
		date_recorded = datetime.strptime(mi_dict["Recorded_Date"], "%Y-%m-%d %H:%M:%S UTC")
	except:
		date_recorded = datetime.strptime(datetime.fromtimestamp(pathlib.Path(file_path).stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S") # chatgpt and https://pynative.com/python-file-creation-modification-datetime/
		#print(f"DEBUG video_extract_metadata_via_MEDIAINFO: FILE DATEMODIFIED USED FOR date_recorded='{date_recorded}'",flush=True)
	try:
		date_encoded = datetime.strptime(mi_dict["Encoded_Date"], "%Y-%m-%d %H:%M:%S UTC")
	except:
		date_encoded = datetime.strptime(datetime.fromtimestamp(pathlib.Path(file_path).stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S") # chatgpt and https://pynative.com/python-file-creation-modification-datetime/
		#print(f"DEBUG video_extract_metadata_via_MEDIAINFO: FILE DATEMODIFIED USED FOR date_encoded='{date_recorded}'",flush=True)
	rotation_flipping_dict = video_calculate_rotation_flipping(int(float(mi_dict["Rotation"])))
	rotation_positive_degrees = rotation_flipping_dict["clockwise_rotation_degrees"]
	width_before_rotation = int(float(mi_dict["Width"]))
	height_before_rotation = int(float(mi_dict["Height"]))
	tolerance_degrees = 0.9
	if abs(rotation_positive_degrees % 90) <= tolerance_degrees:
		if abs(rotation_positive_degrees % 180) <= tolerance_degrees:
			# Handle 180-degree rotation (no change in width/height which are integers)
			width_after_rotation = width_before_rotation
			height_after_rotation = height_before_rotation
		else:
			# Handle 90-degree rotation (width/height which are integers)
			width_after_rotation = height_before_rotation
			height_after_rotation = width_before_rotation
	else:
		# Convert the rotation degrees to radians
		rotation_radians = math.radians(rotation_positive_degrees)
		# Calculate the new width and height after rotation (width/height which are integers)
		width_after_rotation = int(math.ceil(abs(width_before_rotation * math.cos(rotation_radians)) + abs(height_before_rotation * math.sin(rotation_radians))))
		height_after_rotation = int(math.ceil(abs(width_before_rotation * math.sin(rotation_radians)) + abs(height_before_rotation * math.cos(rotation_radians))))
	mi_dict["calc_data"] = {
			"Date_Recorded": date_recorded,						# sometimes this is None
			"Date_Encoded": date_encoded,						# use this one
			"Rotation_Flipping": rotation_flipping_dict,
			"width_before_rotation": width_before_rotation,
			"height_before_rotation": height_before_rotation,
			"width_after_rotation": width_after_rotation,
			"height_after_rotation": height_after_rotation
	}
	#print(f'\n====================mi_dict=\n{objPrettyPrint.pformat(mi_dict)}',flush=True)
	return mi_dict

def video_calculate_rotation_flipping(rotation_degrees):
	# return a dict containing rotation related information, similar to that in image_calculate_rotation_flipping
	# ffprobe and mediainfo yield clockwise rotation as degrees, there appears to be no flipping involved
	# assume the incoming rotation value has been converted from string-float to int by: int(float(video_metadata_dict["Rotation"]))
	# sometimes negative rotation degree values have been seen in the wild, so convert them to positive clockwise rotations.
	# I have only ever seen video rotations in increments of 90 degrees, however allow for others
	#
	positive_rotation = (360 + rotation_degrees) % 360	# calculates the positive rotation value in degrees based on a given rotation in degrees.
	return {
				'orientation_value': rotation_degrees,
				'clockwise_rotation_degrees': positive_rotation,
				'vertical_flips': 0,
				'horizontal_flips': 0,
				'reversal_absolute_clockwise_rotation_degrees': (360 - positive_rotation) % 360,
				'reversal_clockwise_rotation_degrees': (360 - positive_rotation) % 360,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			}

#********************************************************************************************************

# use ffprobe class like this:
#
#	obj_ffprobe = ffprobe(file_path)
#	print(f'{objPrettyPrint.pformat(obj_ffprobe.dict)}')	# to print everything. take care to notice stream indexing to correctly find your video stream metadata
#	encoded_date = obj_ffprobe.format_dict.get("Encoded_Date")	# 'Encoded_Date': '2013-09-01 03:46:29 UTC'
#	duration = obj_ffprobe.format_dict.get("duration")
#	rotation = obj_ffprobe.first_video.get("rotation")
#	r_frame_rate = obj_ffprobe.first_video.get("r_frame_rate")

class ffprobe:
	# This is a beaut class.
	# It uses ffprobe to query a media file and fetch into a dict as much metadata as it can find
	# Given the complexities of ffprobe streams and stream IDs (which are unique across video/audio/data streams),
	# this class makes it easier to find by also storing values for first_video and first_audio.
	# The native ffprobe tag names go straight into the dict so they always align with ffprobe querying
	# Usage:
	#	obj_ffprobe = ffprobe(file_path)
	#	print(f'{objPrettyPrint.pformat(obj_ffprobe.dict)}')	# to print everything. take care to notice stream indexing to correctly find your video stream metadata
	#	duration = obj_ffprobe.format_dict.get("duration")
	#	rotation = obj_ffprobe.first_video.get("rotation")
	#	r_frame_rate = obj_ffprobe.first_video.get("r_frame_rate")
	# 
	import os
	import sys
	import subprocess
	from pathlib import Path
	from typing import NamedTuple
	import json
	#
	global FFPROBE_EXE	# assume is set by main process before this class is called
	#
	def __init__(self, file_path):
		# Assume ffprobe.exe is in the current folder and/or path
		self.dict = {}
		self.format_dict = {}
		self.streams_list = []
		self.return_code = 0
		self.error_code = 0
		self.error = ''
		self.num_streams = 0
		self.num_video_streams = 0
		self.num_audio_streams = 0
		self.indices_video = None
		self.first_video_stream_pair = None
		self.first_video_stream_index = None
		self.first_video_list_index = None
		self.indices_audio = None
		self.first_audio_stream_pair = None
		self.first_audio_stream_index = None
		self.first_audio_list_index = None
		self.first_video = {}
		self.first_audio = {}
		command_array =	[FFPROBE_EXE, "-hide_banner", "-v", "quiet", "-print_format", "json", "-show_programs", "-show_format", "-show_streams", "-show_private_data", file_path]
		#
		e = 0
		try:
			result = subprocess.run(command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
		except Exception as e:
			print(f"CONTROLLER: ffprobe.exe failed to run on '{file_path}', with error: '{result.stderr}'", file=sys.stderr, flush=True)
			self.return_code = result.returncode
			self.error_code = e
			self.error = result.stderr
			return
		#
		self.return_code = result.returncode
		self.error_code = e
		self.error = result.stderr
		try:
			self.dict = json.loads(result.stdout)
		except:
			print(f'CONTROLLER: ffprobe: ERROR: {file_path} loading ffprobe "json" data. json=\n{objPrettyPrint.pformat(self.streams_list)}', file=sys.stderr, flush=True)
			self.dict = {}
			pass
		self.format_dict = self.dict.get("format")
		if self.format_dict is None:
			print(f'CONTROLLER: ffprobe: ERROR: {file_path} contains no ffprobe "format" data. json=\n{objPrettyPrint.pformat(self.streams_list)}', file=sys.stderr, flush=True)
			self.format_dict = {}
			pass
		self.streams_list = self.dict.get("streams")
		if self.streams_list is None:
			print(f'CONTROLLER: ffprobe: ERROR: {file_path} contains no ffprobe "streams" data. json=\n{objPrettyPrint.pformat(self.streams_list)}', file=sys.stderr, flush=True)
			self.streams_list = []
			pass
		else:
			# determine the first video stream indexes
			self.indices_video  = [ {"list_index" : i, "stream_index" : _streams["index"] } for i, _streams in enumerate(self.streams_list) if _streams["codec_type"].lower() == "video".lower()]
			self.num_video_streams = len(self.indices_video)
			if self.num_video_streams > 0:
				self.first_video_stream_pair = min(self.indices_video, key=lambda x: x["stream_index"])
				self.first_video_list_index = self.first_video_stream_pair["list_index"]
				self.first_video_stream_index = self.first_video_stream_pair["stream_index"]
				self.streams_list[self.first_video_list_index]["color_matrix"] = self.streams_list[self.first_video_list_index].get("color_space")	# NOT LIKE MEDIAINFO !!! color_matrix is in ff field "color_space" (instances of it show bt2020nc which is a matrix name).
				self.first_video = self.streams_list[self.first_video_list_index]
				self.first_video["displaymatrix"] = None
				self.first_video["rotation"] = 0
				sdl = self.first_video.get("side_data_list")
				#	'side_data_list':	[
				#		{	'side_data_type': 'Display Matrix',
				#			'displaymatrix':	'00000000:            0       65536           0'
				#								'00000001:       -65536           0           0'
				#								'00000002:     31457280           0  1073741824',
				#			'rotation': -90
				#		}
				#						]
				if sdl is not None:
					for v in sdl:	# iterate the side data list if it exists; v is an item from the list which "should" be a dict for display matrix
						try:
							dm = v.get("displaymatrix")
							rot = v.get("rotation")
						except:
							dm = None
						if dm is not None:
							self.first_video["displaymatrix"] = dm.replace('\n',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ').strip()
						if rot is not None:
							self.first_video["rotation"] = rot		# rot is the video rotation integer, which may be negative
			# determine the first audio stream indexes
			self.indices_audio = [ {"list_index" : i, "stream_index" : _streams["index"] } for i, _streams in enumerate(self.streams_list) if _streams["codec_type"].lower() == "audio".lower()]
			self.num_audio_streams = len(self.indices_audio)
			if self.num_audio_streams > 0:
				self.first_audio_stream_pair = min(self.indices_audio, key=lambda x: x["stream_index"])
				self.first_audio_list_index = self.first_audio_stream_pair["list_index"]
				self.first_audio_stream_index = self.first_audio_stream_pair["stream_index"]
				self.first_audio = self.streams_list[self.first_audio_list_index]
		self.num_streams = self.num_video_streams + self.num_audio_streams
		# return with the dict and codes filled in
		del command_array, e, result
		return

#********************************************************************************************************

def image_get_metadata_via_PIL(image_path):
	with Image.open(image_path) as image:
		exif_data = image._getexif()
		if exif_data is None:
			date_recorded = datetime.strptime(datetime.fromtimestamp(pathlib.Path(image_path).stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")	# chatgpt and https://pynative.com/python-file-creation-modification-datetime/
			#print(f"DEBUG image_get_metadata_via_PIL: no exif_data, FILE DATEMODIFIED WILL BE USED FOR date_recorded='{date_recorded}'")
			return {
				"Date_Recorded": date_recorded,
				"Rotation_Flipping": {	'exif_orientation_value': 1,
										'exif_clockwise_rotation_degrees': 0,
										'exif_vertical_flips': 0,
										'exif_horizontal_flips': 0,
										'reversal_absolute_clockwise_rotation_degrees': 0,
										'reversal_clockwise_rotation_degrees': 0,
										'reversal_vertical_flips': 0,
										'reversal_horizontal_flips': 0
									},
				"width_before_rotation": image.width,
				"height_before_rotation": image.height,
				"width_after_rotation": image.width,
				"height_after_rotation": image.height
			}
		# fetch and calculate the exif data
		date_recorded = image_get_date_recorded_from_exif(image_path, exif_data)
		rotation_flipping_dict = image_calculate_rotation_flipping(exif_data)
		width_before_rotation = image.width
		height_before_rotation = image.height
		# Calculate width and Height_after_rotation (if rotation is applied)
		if rotation_flipping_dict["exif_clockwise_rotation_degrees"] == 90 or rotation_flipping_dict["exif_clockwise_rotation_degrees"] == 270:
			width_after_rotation = height_before_rotation
			height_after_rotation = width_before_rotation
		else:
			width_after_rotation = width_before_rotation
			height_after_rotation = height_before_rotation

		return {
			"Date_Recorded": date_recorded,
			"Rotation_Flipping": rotation_flipping_dict,
			"width_before_rotation": width_before_rotation,
			"height_before_rotation": height_before_rotation,
			"width_after_rotation": width_after_rotation,
			"height_after_rotation": height_after_rotation
		}

def image_get_date_recorded_from_exif(image_path, exif_data):
	date_tag = 36867  # Exif tag for DateTimeOriginal
	date_recorded = None
	if date_tag in exif_data:
		date_recorded = exif_data[date_tag]
		try:
			date_recorded = datetime.strptime(date_recorded, "%Y:%m:%d %H:%M:%S")	#.strftime("%Y_%m_%d_%H_%M_%S_%f")
		except:
			date_recorded = None
	if date_recorded == None:	# attempt to get the file date-modified
		# chatgpt and https://pynative.com/python-file-creation-modification-datetime/
		date_recorded = datetime.strptime(datetime.fromtimestamp(pathlib.Path(image_path).stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S") # chatgpt and https://pynative.com/python-file-creation-modification-datetime/
		#print(f"DEBUG image_get_date_recorded_from_exif: FILE DATEMODIFIED USED FOR date_recorded='{date_recorded}'")
	#print(f"DEBUG image_get_date_recorded_from_exif: date_recorded='{date_recorded}'")
	return date_recorded

def image_calculate_rotation_flipping(exif_data):
	# https://sirv.com/help/articles/rotate-photos-to-be-upright/
	#	Exif Orientation values 1,3,6,8 have no flipping, 2,4,5,7 involve flipping as well as rotations.
	#	Orientation Value: 1
	#		Rotation Angle: 0 degrees (no rotation)
	#	Orientation Value: 2
	#		Rotation Angle: 0 degrees (no rotation) + Horizontal flip
	#	Orientation Value: 3
	#		Rotation Angle: 180 degrees clockwise rotation
	#	Orientation Value: 4
	#		Rotation Angle: 180 degrees clockwise rotation + Horizontal flip
	#	Orientation Value: 5
	#		Rotation Angle: 90 degrees clockwise rotation + Horizontal flip
	#	Orientation Value: 6
	#		Rotation Angle: 270 degrees clockwise rotation
	#	Orientation Value: 7
	#		Rotation Angle: 270 degrees clockwise rotation + Horizontal flip
	#	Orientation Value: 8
	#		Rotation Angle: 90 degrees clockwise rotation	
	#
	#	Therefore, the optimal REVERSAL rotation and flip values for each orientation are as follows:
	#	Orientation Value: 1
	#		Optimal Rotation: No rotation
	#		Optimal Flip: No flip
	#		ABSOLUTE REVERSAL ROTATION:  No rotation
	#	Orientation Value: 2
	#		Optimal Rotation: 0 degrees clockwise rotation
	#		Optimal Flip: Horizontal flip  ** MUST FLP
	#		ABSOLUTE REVERSAL ROTATION:  0
	#	Orientation Value: 3
	#		Optimal Rotation: 180 degrees clockwise rotation
	#		Optimal Flip: No flip
	#		ABSOLUTE REVERSAL ROTATION: 180 degrees clockwise rotation
	#	Orientation Value: 4
	#		Optimal Rotation: 0 degrees clockwise rotation
	#		Optimal Flip: Vertical flip	 ** MUST FLP
	#		ABSOLUTE REVERSAL ROTATION: 0
	#	Orientation Value: 5
	#		Optimal Rotation: 90 degrees clockwise rotation
	#		Optimal Flip: Horizontal flip  ** MUST FLIP
	#		ABSOLUTE REVERSAL ROTATION: 0
	#	Orientation Value: 6
	#		Optimal Rotation: 90 degrees clockwise rotation
	#		Optimal Flip: No flip
	#		ABSOLUTE REVERSAL ROTATION: 90 degrees clockwise rotation
	#	Orientation Value: 7
	#		Optimal Rotation: 90 degrees clockwise rotation
	#		Optimal Flip: Vertical flip  ** MUST FLP
	#		ABSOLUTE REVERSAL ROTATION: 0
	#	Orientation Value: 8
	#		Optimal Rotation: 270 degrees clockwise rotation
	#		Optimal Flip: No flip
	#		ABSOLUTE REVERSAL ROTATION: 270 degrees clockwise rotation
	#
	exif_orientation_value = 1
	if hasattr(exif_data, '__getitem__'):
		exif_orientation_value = exif_data.get(0x0112)
		if exif_orientation_value == 1:		# Rotation Angle: 0 degrees (no rotation). Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 0,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_absolute_clockwise_rotation_degrees': 0,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			}
		elif exif_orientation_value == 2:	# Rotation Angle: 0 degrees (no rotation) + Horizontal flip. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 0,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 1,
				'reversal_absolute_clockwise_rotation_degrees': 0,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 1
			}
		elif exif_orientation_value == 3:	# Rotation Angle: 180 degrees clockwise rotation. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 180,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_absolute_clockwise_rotation_degrees': 180,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 1,
				'reversal_horizontal_flips': 1
			}
		elif exif_orientation_value == 4:	# Rotation Angle: 180 degrees clockwise rotation + Horizontal flip. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 180,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 1,
				'reversal_absolute_clockwise_rotation_degrees': 0,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 1,
				'reversal_horizontal_flips': 0
			}
		elif exif_orientation_value == 5:	# Rotation Angle: 90 degrees clockwise rotation + Horizontal flip. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 90,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 1,
				'reversal_absolute_clockwise_rotation_degrees': 0,
				'reversal_clockwise_rotation_degrees': 90,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 1
			}
		elif exif_orientation_value == 6:	# Rotation Angle: 270 degrees clockwise rotation. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 270,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_absolute_clockwise_rotation_degrees': 90,
				'reversal_clockwise_rotation_degrees': 90,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			}
		elif exif_orientation_value == 7:	# Rotation Angle: 270 degrees clockwise rotation + Horizontal flip. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 270,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 1,
				'reversal_absolute_clockwise_rotation_degrees': 0,
				'reversal_clockwise_rotation_degrees': 90,
				'reversal_vertical_flips': 1,
				'reversal_horizontal_flips': 0
			}
		elif exif_orientation_value == 8:	# Rotation Angle: 90 degrees clockwise rotation. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 90,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_absolute_clockwise_rotation_degrees': 270,
				'reversal_clockwise_rotation_degrees': 270,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			}
		else: # unknown exif value, assume no rotation and no flipping. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 0,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_absolute_clockwise_rotation_degrees': 0,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			} 
	return {  # no exif data, assume no rotation and no flipping. Exif Orientation values 1,3,6,8 have no flipping, 2.4.5.7 involve flipping as well as rotations.
		'exif_orientation_value': 1,
		'exif_clockwise_rotation_degrees': 0,
		'exif_vertical_flips': 0,
		'exif_horizontal_flips': 0,
		'reversal_absolute_clockwise_rotation_degrees': 0,
		'reversal_clockwise_rotation_degrees': 0,
		'reversal_vertical_flips': 0,
		'reversal_horizontal_flips': 0
	}

#--------------------------------------------------------------------------------------------------------
#********************************************************************************************************
#********************************************************************************************************

###
def get_random_ffindex_path(path):
	# use the filename component of the incoming path and create a random fully qualified path into the temp folder
	# there is a significant to 100% chance of home picture/video filenames in directory trees being non-unique
	# apparently uuid4 has a good chance of returning a unique string
	f = fully_qualified_filename(os.path.join(SETTINGS_DICT['TEMP_FOLDER'], os.path.basename(path) + r'_' + str(uuid.uuid4()) + r'.ffindex'))
	return f

###
def find_all_chunks():
	# only use globals: SETTINGS_DICT, DEBUG

	def fac_get_path(path_generator):
		# get next path of desired extensions from generator, ignoring extensions we have not specified
		# loop around only returning a path with a known extension
		while 1:	# loop until we do a "return", hitting past the end of the iterator returns None
			try:
				path = next(path_generator)
				#if DEBUG:	print(f'fac_get_path: get success, path.name=' + path.name,flush=True)
			except StopIteration:
				return None
			if path.suffix.lower() in SETTINGS_DICT['EXTENSIONS']:	# only return files which are in known extensions
				#if DEBUG:	print(f'DEBUG: find_all_chunks: fac_get_path: in EXTENSIONS success, path.name=' + path.name,flush=True)
				return path

	def fac_check_clip_from__path(path, ext):		# opens VID_EEK_EXTENSIONS only ... Source filter depends on extension
		if not ext in SETTINGS_DICT['VID_EEK_EXTENSIONS']:
			raise ValueError(f'get_clip_from_path: expected {path} to have extension in {SETTINGS_DICT["VID_EEK_EXTENSIONS"]} ... aborting')
		if ext in SETTINGS_DICT['VID_EXTENSIONS']:
			try:
				ffcachefile = get_random_ffindex_path(path)
				clip = core.ffms2.Source(str(path), cachefile=ffcachefile)
				del clip
				os.remove(ffcachefile)
				return True
			except Exception as e:
				print(f'CONTROLLER: WARNING: fac_check_clip_from__path: error opening file via "ffms2": "{str(path)}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
				return False
		elif  ext in SETTINGS_DICT['EEK_EXTENSIONS']:
			try:
				clip = core.lsmas.LWLibavSource(str(path))
				del clip
				return True
			except Exception as e:
				print(f'CONTROLLER: WARNING: fac_check_clip_from__path: error opening file via "lsmas": "{path.name}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
				return False
		else:
			raise ValueError(f'ERROR: fac_check_clip_from__path: get_clip_from_path: expected {path} to have extension in {SETTINGS_DICT["VID_EEK_EXTENSIONS"]} ... aborting')
		return False

	def fac_check_clip_from_pic(path, ext):
		if ext in SETTINGS_DICT['PIC_EXTENSIONS']:
			try:
				ffcachefile = get_random_ffindex_path(path)
				clip = core.ffms2.Source(str(path), cachefile=ffcachefile)
				del clip
				os.remove(ffcachefile)
				return True
			except Exception as e:
				print(f'CONTROLLER: WARNING: fac_check_clip_from_pic: error opening file via "ffms2": "{path.name}" ; ignoring this picture. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
				return False
		else:
			raise ValueError(f'ERROR: fac_check_clip_from_pic: : expected {path} to have extension in {SETTINGS_DICT["PIC_EXTENSIONS"]} ... aborting')
		return False

	def fac_check_file_validity_by_opening(path):
		if path is None:
			raise ValueError(f'ERROR: fac_check_file_validity_by_opening: "path" not passed as an argument to fac_check_file_validity_by_opening')
			sys.exit(1)
		ext = path.suffix.lower()
		if ext in SETTINGS_DICT['VID_EXTENSIONS']:
			is_valid = fac_check_clip_from__path(path, ext)									# open depends on ext, the rest is the same
		elif ext in SETTINGS_DICT['EEK_EXTENSIONS']:
			is_valid = fac_check_clip_from__path(path, ext)									# open depends on ext, the rest is the same
		elif ext in SETTINGS_DICT['PIC_EXTENSIONS']:
			is_valid = fac_check_clip_from_pic(path, ext)
		else:
			raise ValueError(f'ERROR: fac_check_file_validity_by_opening: "{path}" - UNRECOGNISED file extension "{ext}", aborting ...')
			sys.exit()
		return is_valid

	#
	TOLERANCE_FINAL_CHUNK = max(1, int(SETTINGS_DICT['MAX_FILES_PER_CHUNK'] * (float(SETTINGS_DICT['TOLERANCE_PERCENT_FINAL_CHUNK'])/100.0)))

	print(f"CONTROLLER: Commencing assigning files into chunks for processing usng:",flush=True)
	print(f"{objPrettyPrint.pformat(SETTINGS_DICT['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS'])}",flush=True)
	print(f"{objPrettyPrint.pformat(SETTINGS_DICT['EXTENSIONS'])}",flush=True)
	print(f"RECURSIVE={SETTINGS_DICT['RECURSIVE']}",flush=True)
	if DEBUG:
		print(	f"DEBUG: find_all_chunks: " +
				f"MAX_FILES_PER_CHUNK={SETTINGS_DICT['MAX_FILES_PER_CHUNK']}, " +
				f"TOLERANCE_PERCENT_FINAL_CHUNK={SETTINGS_DICT['TOLERANCE_PERCENT_FINAL_CHUNK']}, " +
				f"TOLERANCE_FINAL_CHUNK={TOLERANCE_FINAL_CHUNK}",flush=True)

	if SETTINGS_DICT['RECURSIVE']:
		glob_var="**/*.*"			# recursive
		ff_glob_var="**/*.ffindex"	# for .ffindex file deletion recursive
	else:
		glob_var="*.*"				# non-recursive
		ff_glob_var="*.ffindex"		# for .ffindex file deletion non-recursive

	count_of_files = 0
	chunk_id = -1	# base 0 chunk id, remember
	chunks = {}
	file_list_in_chunk = []
	for Directory in SETTINGS_DICT['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS']:
		current_Directory = Directory
		paths = Path(current_Directory).glob(glob_var) # generator of all paths in a directory, files starting with . won't be matched by default
		path = fac_get_path(paths)	#pre-fetch first path
		if path is None:
			raise ValueError(f"ERROR: find_all_chunks: File Extensions:\n{SETTINGS_DICT['EXTENSIONS']}\nnot found in '{current_Directory}'")
		while not (path is None):	# first clip already pre-retrieved ready for this while loop
			if path.suffix.lower() in SETTINGS_DICT['EXTENSIONS']:
				print(f"CONTROLLER: Checking file {count_of_files}. '{path}' for validity ...",flush=True)
				is_valid = fac_check_file_validity_by_opening(path)
				if not is_valid:	# ignore clips which had an issue with being opened and return None
					print(f'CONTROLLER: Unable to process {count_of_files} {str(path)} ... ignoring it',flush=True)
				else:
					# if required, start a new chunk
					if (count_of_files % SETTINGS_DICT['MAX_FILES_PER_CHUNK']) == 0:
						chunk_id = chunk_id + 1
						chunks[str(chunk_id)] = {	
													'chunk_id': chunk_id,
													'chunk_fixed_json_filename' :				fully_qualified_filename(SETTINGS_DICT['CURRENT_CHUNK_FILENAME']),		# always the same fixed filename
													'proposed_ffv1_mkv_filename' :				fully_qualified_filename(SETTINGS_DICT['CHUNK_ENCODED_FFV1_FILENAME_BASE'] + str(chunk_id).zfill(5) + r'.mkv'),	# filename related to chunk_id, with 5 digit zero padded sequential number
													'num_frames_in_chunk' :						0,	# initialize to 0, filled in by encoder
													'start_frame_num_in_chunk':					0,	# initialize to 0, filled in by encoder
													'end_frame_num_in_chunk':					0,	# initialize to 0, filled in by encoder
													'start_frame_num_of_chunk_in_final_video':	0,	# initialize to 0, # calculated AFTER encoder finished completely
													'end_frame_num_of_chunk_in_final_video': 	0,	# initialize to 0, # calculated AFTER encoder finished completely
													'num_files': 								0,	# initialized but filled in by this loop, number of files in file_list
													'file_list':	 							[],	# each item is a fully qualified filename of a source file for this chunk
													'num_snippets': 							0,	# # initialize to 0, number of files in file_list, filled in by encoder
													'snippet_list': 							[], # an empty dict to be be filled in by encoder, it looks like this:
													# snippet_list:	[								# each snippet list item is a dict which looks like the below:
													#					{	
													#						'start_frame_of_snippet_in_chunk': 0,				# filled in by encoder
													#						'end_frame_of_snippet_in_chunk': XXX, 				# filled in by encoder
													#						'start_frame_of_snippet_in_final_video': AAA,  		# AFTER all encoding completed, calculated and filled in by controller
													#						'end_frame_of_snippet_in_final_video': XXX, 		# AFTER all encoding completed, calculated and filled in by controller
													#						'snippet_num_frames': YYY,							# filled in by encoder
													#						'snippet_source_video_filename': '\a\b\c\ZZZ1.3GP'	# filled in by encoder
													#					},
													#				]
												}
					# add currently examined file to chunk
					fully_qualified_path_string = fully_qualified_filename(path)
					chunks[str(chunk_id)]['file_list'].append(fully_qualified_path_string)
					chunks[str(chunk_id)]['num_files'] = chunks[str(chunk_id)]['num_files'] + 1
					count_of_files = count_of_files + 1
			path = fac_get_path(paths)
		#end while
	#end for
	# If the final chunk is < 20% of SETTINGS_DICT['MAX_FILES_PER_CHUNK'] then merge it into the previous chunk
	chunk_count = len(chunks)
	if chunk_count > 1:
		# if within tolerance, merge the final chunk into the previous chunk
		if chunks[str(chunk_id)]['num_files'] <= TOLERANCE_FINAL_CHUNK:
			print(f'CONTROLLER: Merging final chunk (chunk_id={chunk_id}, num_files={chunks[str(chunk_id)]["num_files"]}) into previous chunk (chunk_id={chunk_id - 1}, num_files={chunks[str(chunk_id - 1)]["num_files"]+chunks[str(chunk_id)]["num_files"]})',flush=True)
			chunks[str(chunk_id - 1)]["file_list"] = chunks[str(chunk_id - 1)]["file_list"] + chunks[str(chunk_id)]["file_list"]
			chunks[str(chunk_id - 1)]["num_files"] = chunks[str(chunk_id - 1)]["num_files"] + chunks[str(chunk_id)]["num_files"]
			# remove the last chunk since we just merged it into the chunk prior
			del chunks[str(chunk_id)]
	chunk_count = len(chunks)

	# OK lets print the chunks tree
	if DEBUG:	print(f"DEBUG: find_all_chunks: Chunks tree contains {count_of_files} files:\n{objPrettyPrint.pformat(chunks)}",flush=True)

	# CHECK the chunks tree
	if DEBUG:	print(f"DEBUG: find_all_chunks: Chunks tree contains {count_of_files} files:\n{objPrettyPrint.pformat(chunks)}",flush=True)
	for i in range(0,chunk_count):	# i.e. 0 to (chunk_count-1)
		print(f'DEBUG: find_all_chunks: About to check-print data for chunks[{i}] : chunks[{i}]["num_files"] and chunks[{i}]["file_list"]:',flush=True)
		print(f'DEBUG:find_all_chunks: chunks[{i}]["num_files"] = {chunks[str(i)]["num_files"]}',flush=True)
		print(f'DEBUG:find_all_chunks:  chunks[{i}]["file_list"] = \n{objPrettyPrint.pformat(chunks[str(i)]["file_list"])}',flush=True)
		num_files = chunks[str(i)]["num_files"]
		file_list = chunks[str(i)]["file_list"]
		for j in range(0,num_files):
			# retrieve a file 2 different ways
			file1 = file_list[j]
			file2 = chunks[str(i)]["file_list"][j]

	print(f"CONTROLLER: Finished assigning files into chunks for processing: {count_of_files} files into {chunk_count} chunks.",flush=True)

	return chunk_count, count_of_files, chunks

###
def encode_using_vsipe_ffmpeg(individual_chunk_id):
	# encode an individual chunk using vspipe and ffmpeg
	# 
	# using ChatGPT suggested method for non-blocking reads of subprocess stderr, stdout
	global SETTINGS_DICT
	global ALL_CHUNKS
	global ALL_CHUNKS_COUNT
	global ALL_CHUNKS_COUNT_OF_FILES
	
	global FFMPEG_EXE
	global VSPIPE_EXE
	
	def enqueue_output(out, queue):
		# for subprocess thread output queueing
		for line in iter(out.readline, b''):
			queue.put(line)
		out.close()

	#
	individual_chunk_dict = ALL_CHUNKS[str(individual_chunk_id)]
	proposed_ffv1_mkv_filename = fully_qualified_filename(individual_chunk_dict['proposed_ffv1_mkv_filename'])

	#????????????? perhaps relocate the other logic to HERE here ...

	# Define the commandlines for the subprocesses subprocesses
	
	vspipe_commandline = [VSPIPE_EXE, '--progress', '--filter-time', '--container', 'y4m', '.\slideshow_ENCODER.vpy', '-']

	ffmpeg_commandline = [	ffmpeg_exe,
							'-hide_banner', 
							'-loglevel', 'info', 
							'-nostats', 
							'-colorspace', 'bt709', 
							'-color_primaries', 'bt709', 
							'-color_trc', 
							'bt709', 
							'-color_range', 'pc',
							'-f', 'yuv4mpegpipe', 
							'-i', 'pipe:',
							'-probesize', '200M', 
							'-analyzeduration', '200M',
							'-sws_flags', 'lanczos+accurate_rnd+full_chroma_int+full_chroma_inp',
							'-filter_complex', 'format=yuv420p,setdar=16/9',
							'-c:v', 'ffv1', '-level', '3', '-coder', '1', '-context', '1', '-slicecrc', '1',
							'-an',
							'-y', proposed_ffv1_mkv_filename
							]
	try:	
		# Run the commands in subprocesses
		process1 = subprocess.Popen(vspipe_commandline, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		process2 = subprocess.Popen(ffmpeg_commandline, stdin=process1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		# Create queues to store the output and error streams
		stderr_queue1 = Queue()
		stdout_queue2 = Queue()
		stderr_queue2 = Queue()

		# Launch separate threads to read the output and error streams
		stderr_thread1 = Thread(target=enqueue_output, args=(process1.stderr, stderr_queue1))
		stdout_thread2 = Thread(target=enqueue_output, args=(process2.stdout, stdout_queue2))
		stderr_thread2 = Thread(target=enqueue_output, args=(process2.stderr, stderr_queue2))
		stderr_thread1.daemon = True
		stdout_thread2.daemon = True
		stderr_thread2.daemon = True
		stderr_thread1.start()
		stdout_thread2.start()
		stderr_thread2.start()

		# Read output and error streams
		while True:
			try:
				stderr_line1 = stderr_queue1.get_nowait().decode('utf-8').strip()
				if stderr_line1:
					print(f"vspipe: {stderr_line1}")
				pass
			except Empty:
				pass
			try:
				stdout_line2 = stdout_queue2.get_nowait().decode('utf-8').strip()
				if stdout_line2:
					print(f"ffmpeg: {stdout_line2}")
				pass
			except Empty:
				pass
			try:
				stderr_line2 = stderr_queue2.get_nowait().decode('utf-8').strip()
				if stderr_line2:
					print(f"ffmpeg: {stderr_line2}")
				pass
			except Empty:
				pass
			if 	(not stderr_thread1.is_alive()) and (not stdout_thread2.is_alive()) and (not stderr_thread2.is_alive()) and (stderr_queue1.empty()) and (stdout_queue2.empty()) and (stderr_queue2.empty()):
				break
			# Introduce a 50ms delay to reduce CPU load
			time.sleep(0.05)  # Sleep for 50 milliseconds so as to not thrash the cpu
		#end while

		# Retrieve the remaining output and error streams
		output, error2 = process2.communicate()
		error1 = process1.stderr.read()

		# Decode any ffmpeg final output from bytes to string and print it
		print(f"ffmpeg: {output.decode('utf-8').strip()}")

		# Print any final error messages
		if error1:
				print(f"vspipe: {error1.decode('utf-8').strip()}")
		if error2:
				print(f"ffmpeg: {error2.decode('utf-8').strip()}")
	except KeyboardInterrupt:
		# Retrieve the process IDs
		pid1 = process1.pid
		pid2 = process2.pid
		# Perform cleanup or other actions
		# before terminating the program
		process1.terminate()
		process2.terminate()
		process1.wait()
		process2.wait()
		# Delay before terminating forcefully with taskkill
		time.sleep(2)  # Add a delay of a couple of seconds
		# Terminate subprocesses forcefully using taskkill if they arem
		os.system(f'taskkill /F /PID {process1.pid}')
		os.system(f'taskkill /F /PID {process2.pid}')
		# Raise the exception again
		raise
	return

##################################################

if __name__ == "__main__":
	DEBUG = False
	
	##########################################################################################################################################
	##########################################################################################################################################
	# GATHER SETTINGS
	print(f"{100*'-'}",flush=True)
	print(f'CONTROLLER: STARTING GATHER SETTINGS')

	import slideshow_LOAD_SETTINGS	# from same folder .\
	SETTINGS_DICT, OLD_INI_DICT, OLD_CALC_INI_DICT, USER_SPECIFIED_SETTINGS_DICT = slideshow_LOAD_SETTINGS.load_settings()
	# SETTINGS_DICT					contains user settings with defaults appled plus "closed" settings added
	# OLD_INI_DICT					an old dict compatible with the "chunk encoder" which has an older code base (with changes to understand modern chunk and snippet)
	# OLD_CALC_INI_DICT 			per "OLD_INI_DICT" but with extra fields added
	# USER_SPECIFIED_SETTINGS_DICT	the settings which were specified by the user

	# find/assign a few  global variables
	if SETTINGS_DICT['DEBUG']:
		DEBUG = True
	else:
		DEBUG = False

	# Assign paths to useful programs into global variables
	FFMPEG_EXE = SETTINGS_DICT['FFMPEG_PATH']
	FFPROBE_EXE = SETTINGS_DICT['FFPROBE_PATH']
	VSPIPE_EXE = SETTINGS_DICT['VSPIPE_PATH']

	if DEBUG:
		print(f"DEBUG: slideshow_CONTROLLER: DEBUG={DEBUG}",flush=True)
		print(f"DEBUG: slideshow_CONTROLLER: USER_SPECIFIED_SETTINGS_DICT=\n{objPrettyPrint.pformat(USER_SPECIFIED_SETTINGS_DICT)}",flush=True)
		print(f"DEBUG: slideshow_CONTROLLER: SETTINGS_DICT=\n{objPrettyPrint.pformat(SETTINGS_DICT)}",flush=True)
		print(f"DEBUG: slideshow_CONTROLLER: OLD_INI_DICT=\n{objPrettyPrint.pformat(OLD_INI_DICT)}",flush=True)
		print(f"DEBUG: slideshow_CONTROLLER: OLD_CALC_INI_DICT=\n{objPrettyPrint.pformat(OLD_CALC_INI_DICT)}",flush=True)

	##########################################################################################################################################
	##########################################################################################################################################
	# FIND PIC/IMAGES

	print(f"{100*'-'}",flush=True)
	print(f'CONTROLLER: STARTING FIND/CHECK OF PIC AND IMAGES')
	
	# Locate all openable files and put them into chunks in a dict, including { proposed filename for the encoded chunk, first/last frames, number of frames in chunk } 

	ALL_CHUNKS_COUNT, ALL_CHUNKS_COUNT_OF_FILES, ALL_CHUNKS = find_all_chunks()	# it uses settings in SETTINGS_DICT to do its thing
	
	if DEBUG:	print(f"DEBUG: retrieved ALL_CHUNKS tree: chunks: {ALL_CHUNKS_COUNT} files: {ALL_CHUNKS_COUNT_OF_FILES} dict:\n{objPrettyPrint.pformat(ALL_CHUNKS)}",flush=True)

	# create .JSON file containing the ALL_CHUNKS  dict. Note the start/stop frames etc are yet to be updated by the encoder
	try:
		fac = SETTINGS_DICT['CHUNKS_FILENAME_FOR_ALL_CHUNKS_DICT']
		with open(fac, 'w') as fp:
			json.dump(ALL_CHUNKS, fp, indent=4)
	except Exception as e:
		print(f"CONTROLLER: ERROR: error returned from json.dump ALL_CHUNKS to JSON file: '{fac}'\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)	
	
	##########################################################################################################################################
	##########################################################################################################################################
	# INTERIM ENCODING OF CHUNKS INTO INTERIM FFV1 VIDEO FILES, 
	# SAVING FRAME NUMBERS AND NUM VIDEO FRAMES INFO SNIPPET DICT, 
	# CREATING SNIPPET JSON, IMPORTING JSON AND ADDING TO ALL_SNIPPETS DICT:

	print(f"{100*'-'}",flush=True)
	print(f'CONTROLLER: STARTING INTERIM ENCODING OF CHUNKS INTO INTERIM FFV1 VIDEO FILES')
		
	if DEBUG:	
		print(f"DEBUG: Starting encoder loop for each of ALL_CHUNKS tree. chunks: {ALL_CHUNKS_COUNT} files: {ALL_CHUNKS_COUNT_OF_FILES}",flush=True)
	
	for individual_chunk_id in range(0,ALL_CHUNKS_COUNT):	# 0 to (ALL_CHUNKS_COUNT - 1)
		# we cannot just import the legacy encoder and call it with parameters, it is a vpy consumed by ffmpeg and that does not accept parameters
		# so we need to create`a fixed-filenamed input file for it to consume (a chu`nk)
		#						and a fixed filename for it to create (snippets for that chunk)

		individual_chunk_dict = ALL_CHUNKS[str(individual_chunk_id)]

		chunk_json_filename = fully_qualified_filename(individual_chunk_dict['chunk_fixed_json_filename'])					# always the same fixed filename
		#### the CHUNK JASON FILE IS UPDATED AND RE-WRITTEN AND RE-READ, not a separate SNIPPETS FILE 
		proposed_ffv1_mkv_filename = fully_qualified_filename(individual_chunk_dict['proposed_ffv1_mkv_filename'])	# preset by find_all_chunks to: fixed filename plus a seqential 5-digit-zero-padded ending based on chunk_id + r'.mkv'
		
		# remove any pre-existing files to be consumed and produced by the encoder
		if os.path.exists(chunk_json_filename):
			os.remove(chunk_json_filename)
		if os.path.exists(proposed_ffv1_mkv_filename):
			os.remove(proposed_ffv1_mkv_filename)
		
		# create the fixed-filename chunk file consumed by the encoder; it contains the fixed-filename of the snippet file to produce
		if DEBUG:	print(f"DEBUG: in encoder loop: attempting to create chunk_json_filename='{chunk_json_filename}' for encoder to consume.",flush=True)
		try:
			with open(chunk_json_filename, 'w') as fp:
				json.dump(individual_chunk_dict, fp, indent=4)
		except Exception as e:
			print(f"CONTROLLER: ERROR: dumping current chunk to JSON file: '{chunk_json_filename}' for encoder, chunk_id={individual_chunk_id}, individual_chunk_dict=\n{objPrettyPrint.pformat(individual_chunk_dict)}\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		print(f"CONTROLLER: Created fixed-filename chunk file for encoder to consume: '{chunk_json_filename}' listing {ALL_CHUNKS[str(individual_chunk_id)]['num_files']} files, individual_chunk_dict=\n{objPrettyPrint.pformat(individual_chunk_dict)}",flush=True)

		if DEBUG:	print(f"DEBUG: encoder loop: calling the encoder, VSPIPE piped to FFMPEG ... with controller using non-blocking reads of stdout and stderr (per chatgpt).",flush=True)
		# These fields in a chunk dict need to be updated by the encoder:
		#	'num_frames_in_chunk'
 		#	'start_frame_num_in_chunk'
		#	'end_frame_num_in_chunk'
		#	'num_files': 								0,	# initialized but filled in by this loop, number of files in file_list
		#	'file_list':	 							[],	# each item is a fully qualified filename of a source file for this chunk
		#	'num_snippets': 							0,	# # initialize to 0, number of files in file_list, filled in by encoder
		#		'snippet_list'
		#			'start_frame_of_snippet_in_chunk': 0,				# filled in by encoder
		#			'end_frame_of_snippet_in_chunk': XXX, 				# filled in by encoder
		#			'snippet_num_frames': YYY,							# filled in by encoder
		#			'snippet_source_video_filename': '\a\b\c\ZZZ1.3GP'	# filled in by encoder
		
		
		
	
		
		# NOT YET ENCODE WITH FFMPEG, ONLY TEST WITH VSPIPE
		#encode_using_vsipe_ffmpeg(individual_chunk_id)

		# Run vspipe command by itself
		vspipe_commandline = [VSPIPE_EXE, '--progress', '--container', 'y4m', '.\slideshow_ENCODER_legacy.vpy', 'NUL']
		subprocess.run(vspipe_commandline, check=True)

		time.sleep(1)


	
		if DEBUG:	print(f"DEBUG: encoder loop: returned from the encoder, VSPIPE piped to FFMPEG ... with controller using non-blocking reads of stdout and stderr (per chatgpt).",flush=True)

		# Now the encoder has encoded a chunk and produced an updated chunk file and an ffv1 encoded video .mkv 
		# ... we must import updated chunk file (which will include a new snippet_list) check the chunk, and update the ALL_CHUNKS dict with updated chunk data
		# The format of the snippet_list produced by the encoder into the updated chunk JSON file is defined above.
		
		if not os.path.exists(chunk_json_filename):
			print(f"CONTROLLER: ERROR: controller: encoder-updated current chunk to JSON file file not found '{chunk_json_filename}' not found !",flush=True)
			sys.exit(1)
		
		
		# TEMPORARILY DISABLE THE CHECK FOR A VALID FFV1 FILE
		
		#if not os.path.exists(proposed_ffv1_mkv_filename):
		#	print(f"CONTROLLER: ERROR: controller: encoder-produced .mkv video file not found '{proposed_ffv1_mkv_filename}' not found !",flush=True)
		#	sys.exit(1)
		
		
		
		
		if DEBUG:	print(f"DEBUG: controller: in encoder loop: attempting to load chunk_json_filename={chunk_json_filename} produced by the encoder.",flush=True)
		try:
			with open(chunk_json_filename, 'r') as fp:
				updated_individual_chunk_dict = json.load(fp)
		except Exception as e:
			print(f"CONTROLLER: ERROR: controller: loading updated current chunk from JSON file: '{chunk_json_filename}' from encoder, chunk_id={individual_chunk_id}, related to individual_chunk_dict=\nobjPrettyPrint.pformat(individual_chunk_dict)\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		print(f"CONTROLLER: Loaded updated current chunk from JSON file: '{chunk_json_filename}'",flush=True)
		if (updated_individual_chunk_dict['chunk_id'] !=  individual_chunk_dict['chunk_id']) or (updated_individual_chunk_dict['chunk_id'] != individual_chunk_id):
			print(f"CONTROLLER: ERROR: controller: the chunk_id returned from the encoder={updated_individual_chunk_dict['chunk_id']} in updated_individual_chunk_dict does not match both expected individual_chunk_dict chunk_id={individual_chunk_dict['chunk_id']} or loop's individual_chunk_id={individual_chunk_id}",flush=True)
			sys.exit(1)
		# poke the chunk updated by the encoder back into ALL_CHUNKS ... it should contain snippet data now.
		ALL_CHUNKS[str(individual_chunk_id)] = updated_individual_chunk_dict
	#end for

	if DEBUG:
		print(f'CONTROLLER: Finished INTERIM ENCODING OF CHUNKS INTO INTERIM FFV1 VIDEO FILES')
		print(f"CONTROLLER: After updating encoder added snippets into each chunk and controller UPDATING chunk info into ALL_CHUNKS, the new ALL_CHUNKS tree is:\n{objPrettyPrint.pformat(ALL_CHUNKS)}",flush=True)

	##########################################################################################################################################
	##########################################################################################################################################
	# FINISHED INTERIM ENCODING
	# re-parse the ALL_CHUNKS tree dict to re-calculate global frame numbers on a per-chunk basis and within that on a per-snippet-within-chunk basis
	# using the newly added  ...  before processing any audio using snippets, 
	# so we can refer to absolute final-video frame numbers rather than chunk-internal frame numbers

	print(f"{100*'-'}",flush=True)
	print(f"CONTROLLER: STARTING RE-PARSE OF ALL_CHUNKS TREE DICT TO RE-CALCULATE AND SAVE GLOBAL FRAME NUMBERS. NUMVER OF CHUNKS TO PROCESS: {ALL_CHUNKS_COUNT}.",flush=True)

	# To be calculated and updated in each chunk at the chunk level:
	#		ALL_CHUNKS[str(individual_chunk_id)]['start_frame_num_of_chunk_in_final_video']
	#		ALL_CHUNKS[str(individual_chunk_id)]['end_frame_num_of_chunk_in_final_video']
	#
	# To be calculated and updated in every 'snippet_list' item within a chunk (this is a list, so loop to process each snippet via its list index): 
	#		ALL_CHUNKS[str(individual_chunk_id)]['snippet_list'][index_number_in_for_loop]['start_frame_of_snippet_in_final_video']
	#		ALL_CHUNKS[str(individual_chunk_id)]['snippet_list'][index_number_in_for_loop]['end_frame_of_snippet_in_final_video']

	# keep track of the frame numbers of a video where all of the slideshow videos will be concatenated in sequence
	seq_previous_ending_frame_num = -1	# initialize so the start frame number for the first clip with be (-1 + 1) = 0 .. base 0
	start_frame_num_of_chunk_in_final_video = 0
	end_frame_num_of_chunk_in_final_video = 0
	
	if DEBUG: print(f"{'#'*100}\nDEBUG: Start calculate start/end final_video based frame numbers for all chunks and their snippets, incoming ALL_CHUNKS tree is:\n{objPrettyPrint.pformat(ALL_CHUNKS)}\n{'#'*100}",flush=True)

	for individual_chunk_id in range(0,ALL_CHUNKS_COUNT):	# 0 to (ALL_CHUNKS_COUNT - 1)
		seq_start_frame_num = seq_previous_ending_frame_num + 1		# base 0, this is now the start_frame_num in the full final video

	# for this chunk, re-calculate chunk info and poke it back into ALL_CHUNKS
	#		eg (0..9)  goes to (0..9) when starting at frame 0 and having 10 frames     0,1,2,3,4,5,6,7,8,9 -> 0,1,2,3,4,5,6,7,8,9
	#		eg (0..19) goes to (0..19) when starting at frame 0 and having 20 frames    0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 -> 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19
	#		eg (0..1)  goes to (10..11) when starting at frame 10 and having 2 frames   10,11
	#		eg (0..3)  goes to (11..14) when starting at frame 11 and having 4 frames   0,1,2,3 -> 11,12,13,14
	#		eg (0..5)  goes to (50..55) when starting at frame 50 and having 6 frames   0,1,2,3,4,5 -> 50,51,52,53,54,55
		start_frame_num_of_chunk_in_final_video	= seq_start_frame_num + ALL_CHUNKS[str(individual_chunk_id)]['start_frame_num_in_chunk']
		end_frame_num_of_chunk_in_final_video	= seq_start_frame_num + ALL_CHUNKS[str(individual_chunk_id)]['end_frame_num_in_chunk']
		ALL_CHUNKS[str(individual_chunk_id)]['start_frame_num_of_chunk_in_final_video'] = start_frame_num_of_chunk_in_final_video
		ALL_CHUNKS[str(individual_chunk_id)]['end_frame_num_of_chunk_in_final_video'] =  end_frame_num_of_chunk_in_final_video

		for i in range(0, ALL_CHUNKS[str(individual_chunk_id)]['num_snippets']):
			# for this snippet in this chunk, re-calculate snippet info and then poke it back into ALL_CHUNKS
			start_frame_of_snippet_in_final_video = seq_start_frame_num + ALL_CHUNKS[str(individual_chunk_id)]['snippet_list'][i]['start_frame_of_snippet_in_chunk']
			end_frame_of_snippet_in_final_video = seq_start_frame_num + ALL_CHUNKS[str(individual_chunk_id)]['snippet_list'][i]['end_frame_of_snippet_in_chunk']
			ALL_CHUNKS[str(individual_chunk_id)]['snippet_list'][i]['start_frame_of_snippet_in_final_video'] = start_frame_of_snippet_in_final_video
			ALL_CHUNKS[str(individual_chunk_id)]['snippet_list'][i]['end_frame_of_snippet_in_final_video'] = end_frame_of_snippet_in_final_video
		#end for

		seq_previous_ending_frame_num = end_frame_num_of_chunk_in_final_video	# set seq_previous_ending_frame_num ready for use by the next chunk
	#end for
	
	# Save the end frame number of the final video based on the final chunk's end frame number
	end_frame_num_of_final_video = end_frame_num_of_chunk_in_final_video


	if DEBUG: print(f"{'*'*100}\nDEBUG: Finished calculate start/end final_video based frame numbers for all chunks and their snippets, outgoing ALL_CHUNKS tree is:\n{objPrettyPrint.pformat(ALL_CHUNKS)}\n{'*'*100}",flush=True)
	
	##########################################################################################################################################
	##########################################################################################################################################
	# USE SNIPPET INFO TO OVERLAY SNIPPET AUDIO INTO BACKGROUND AUDIO, AND TRANSCODE AUDIO to AAC in an MP4 (so pydub accepts it):
	print(f"{100*'-'}",flush=True)
	print(f'CONTROLLER: STARTING OVERLAY SNIPPETS AUDIOS ONTO BACKGROUND AUDIO, AND TRANSCODE AUDIO to AAC in an MP4')

	final_video_frame_count = end_frame_num_of_final_video + 1		# base 0
	final_video_fps = SETTINGS_DICT['TARGET_FPS']
	final_video_duration_ms = (float(final_video_frame_count) / video_fps) * 1000
	background_audio_input_filename = SETTINGS_DICT['BACKGROUND_AUDIO_INPUT_FILENAME']
	background_audio_with_snippets_filename = SETTINGS_DICT['BACKGROUND_AUDIO_WITH_SNIPPETS_FILENAME']
	final_mp4_with_audio_filename = SETTINGS_DICT['FINAL_MP4_WITH_AUDIO_FILENAME']
	# not used	INTERIM_VIDEO_MP4_NO_AUDIO_FILENAME = SETTINGS_DICT['INTERIM_VIDEO_MP4_NO_AUDIO_FILENAME'] ????????????????????????????????????????
	snippet_audio_fade_in_duration_ms = SETTINGS_DICT['snippet_audio_fade_in_duration_ms']
	snippet_audio_fade_out_duration_ms = SETTINGS_DICT['snippet_audio_fade_out_duration_ms']

	# Load the main background audio
	try:
		if DEBUG: print(f"DEBUG: CONTROLLER: replace_audio_with_snippets_from_file: 'from_file' to background_audio '{background_audio_input_filename}'",flush=True)
		background_audio = AudioSegment.from_file(background_audio_input_filename)
	except FileNotFoundError:
		print(f"CONTROLLER: replace_audio_with_snippets_from_file: background_audio File not found from AudioSegment.from_file('{background_audio_input_filename}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except TypeError:
		print(f"CONTROLLER: replace_audio_with_snippets_from_file: background_audio Type mismatch or unsupported operation from AudioSegment.from_file('{background_audio_input_filename}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except ValueError:
		print(f"CONTROLLER: replace_audio_with_snippets_from_file: background_audio Invalid or unsupported value from AudioSegment.from_file('{background_audio_input_filename}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except IOError:
		print(f"CONTROLLER: replace_audio_with_snippets_from_file: background_audio I/O error occurred '{background_audio_input_filename}'",flush=True,file=sys.stderr)
		sys.exit(1)
	except OSError as e:
		print(f"CONTROLLER: replace_audio_with_snippets_from_file: background_audio Unexpected OSError from AudioSegment.from_file('{background_audio_input_filename}')\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"CONTROLLER: replace_audio_with_snippets_from_file: background_audio Unexpected error from AudioSegment.from_file('{background_audio_input_filename}')\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)





	for individual_chunk_id in range(0,ALL_CHUNKS_COUNT):	# 0 to (ALL_CHUNKS_COUNT - 1)
		individual_chunk_dict = ALL_CHUNKS[str(individual_chunk_id)]
		num_files = individual_chunk_dict['num_files']
		num_snippets = individual_chunk_dict['num_snippets']
		if num_snippets > 0:
			num_snippets(f'CONTROLLER: Start processing chunk: {individual_chunk_id} list of {num_snippets} audio snippet files to be overlaid onto backgroiund audio.',flush=True)
			for i in range(0,num_snippets):	# base 0; 0..(num_files - 1)
				individual_snippet_dict = individual_chunk_dict['snippet_list'][i]
				# which looks like this:	{	
				#								'start_frame_of_snippet_in_chunk':			integer,
				#								'end_frame_of_snippet_in_chunk':			integer,
				#								'start_frame_of_snippet_in_final_video':	integer,	<- this is useful
				#								'end_frame_of_snippet_in_final_video':		integer,	<- this is useful
				#								'snippet_num_frames':						integer,	<- this is useful
				#								'snippet_source_video_filename':			filename,	<- this is useful
				#							}




		#end for

	#end for


	##########################################################################################################################################
	##########################################################################################################################################
	# CONCATENATE/TRANSCODE INTERIM FFV1 VIDEO FILES INTO ONE VIDEO MP4 AND AT SAME TIME MUX WITH BACKGROUND AUDIO.mp4
	print(f"{100*'-'}",flush=True)
	print(f'CONTROLLER: STARTING CONCATENATE/TRANSCODE INTERIM FFV1 VIDEO FILES INTO ONE VIDEO MP4 AND AT SAME TIME MUX WITH BACKGROUND AUDIO')
	
	
	##########################################################################################################################################
	##########################################################################################################################################
	# CLEANUP
	
	
	
	
	def replace_audio_with_snippets_from_file(input_video_path, video_fps, final_video_frame_count, video_duration_ms, seq_snippets_list, output_video_path, background_audio_input_filename, fade_out_duration_ms, fade_in_duration_ms):
	# Load the background audio
	# LOOK AT THIS AND MAKE MORE ROBUST LIKE THE OTHER FUNCTION IN THE OTHER CODE 
	# ... if it was None then create silence audio for the expected duration (same length as video_duration_ms
	# ... else check file exists and load etc
	if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file.",flush=True)
	try:
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: 'from_file' to background_audio '{background_audio_input_filename}'",flush=True)
		background_audio = AudioSegment.from_file(background_audio_input_filename)
	except FileNotFoundError:
		print(f"replace_audio_with_snippets_from_file: background_audio File not found from AudioSegment.from_file('{background_audio_input_filename}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except TypeError:
		print(f"replace_audio_with_snippets_from_file: background_audio Type mismatch or unsupported operation from AudioSegment.from_file('{background_audio_input_filename}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except ValueError:
		print(f"replace_audio_with_snippets_from_file: background_audio Invalid or unsupported value from AudioSegment.from_file('{background_audio_input_filename}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except IOError:
		print(f"replace_audio_with_snippets_from_file: background_audio I/O error occurred '{background_audio_input_filename}'",flush=True,file=sys.stderr)
		sys.exit(1)
	except OSError as e:
		print(f"replace_audio_with_snippets_from_file: background_audio Unexpected OSError from AudioSegment.from_file('{background_audio_input_filename}')\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"replace_audio_with_snippets_from_file: background_audio Unexpected error from AudioSegment.from_file('{background_audio_input_filename}')\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	
	# Trim or pad the background audio to match the duration of the video
	background_audio_len = len(background_audio)
	if background_audio_len < video_duration_ms:
		padding_duration = video_duration_ms - background_audio_len
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: background_audio_len {background_audio_len}ms, padding with silence to {background_audio_len+padding_duration}ms",flush=True)
		background_audio = background_audio + AudioSegment.silent(duration=padding_duration)
	else:
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: background_audio_len {background_audio_len}ms, trimming to {video_duration_ms}ms",flush=True)
		background_audio = background_audio[:video_duration_ms]

	# make the edits to the background audio
	# using the pre-parsed snippets list
	#	seq_snippets_list
	# 		Each list entry contains a dict of attributes for snippets to be applied to the main background audio
	#			{	"snippet_original_start_frame_for_replacement" 	: start_frame_for_replacement, 
	#				"snippet_original_num_frames_to_replace"	   	: snippet_num_frames_to_replace, 
	#				"snippet_seq_start_frame_for_replacement"	  	: seq_start_frame_for_replacement, 
	#				"snippet_seq_end_frame_for_replacement"			: seq_end_frame_for_replacement, 
	#				"snippet_path"								 	: snippet_path, 
	#				"from_snippets_input_file"					 	: snippets_input_file
	#			}
	total_snippets = len(seq_snippets_list)
	for i, snippet_data in enumerate(seq_snippets_list):
		start_frame = snippet_data["snippet_seq_start_frame_for_replacement"]
		end_frame = snippet_data["snippet_seq_end_frame_for_replacement"]
		snippet_path = snippet_data["snippet_path"]
		print(f"Processing snippet {i+1}/{total_snippets} from LIST, start_frame={start_frame} end_frame={end_frame} snippet_path='{snippet_path}'",flush=True)

		# Load the snippet audio
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: about to get audio from snippet via AudioSegment.from_file('{snippet_path}')",flush=True)
		try:
			snippet_audio = AudioSegment.from_file(snippet_path)
		except FileNotFoundError:
			print(f"replace_audio_with_snippets_from_file: snippet File not found from AudioSegment.from_file('{snippet_path}')",flush=True,file=sys.stderr)
			sys.exit(1)
		except TypeError:
			print(f"replace_audio_with_snippets_from_file: snippet Type mismatch or unsupported operation from AudioSegment.from_file('{snippet_path}')",flush=True,file=sys.stderr)
			sys.exit(1)
		except ValueError:
			print(f"replace_audio_with_snippets_from_file: snippet Invalid or unsupported value from AudioSegment.from_file('{snippet_path}')",flush=True,file=sys.stderr)
			sys.exit(1)
		except IOError:
			print(f"replace_audio_with_snippets_from_file: snippet I/O error occurred from AudioSegment.from_file('{snippet_path}')",flush=True,file=sys.stderr)
			sys.exit(1)
		except OSError as e:
			print(f"replace_audio_with_snippets_from_file: snippet Unexpected OSError from AudioSegment.from_file('{snippet_path}')\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)
		except Exception as e:
			print(f"replace_audio_with_snippets_from_file: snippet Unexpected error from AudioSegment.from_file('{snippet_path})'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)

		# Calculate the snippet audio duration based in what was specified for this edit in the seq_snippets_list
		snippet_duration_ms = ((end_frame - start_frame + 1) / video_fps) * 1000   # +1 to account for inclusive range
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: snippet {i+1}/{total_snippets} calculated snippet_duration_ms={snippet_duration_ms}",flush=True)

		# Extract the corresponding portion of the snippet audio based on the calculated duration
		# there should be enough audio unless the a very small clip had to padded during slideshow creation, which can happen
		# Trim or pad the snippet audio to match snippet_duration_ms
		snippet_audio_len = len(snippet_audio)
		if snippet_audio_len < snippet_duration_ms:
			padding_duration = snippet_duration_ms - snippet_audio_len
			snippet_audio = snippet_audio + AudioSegment.silent(duration=padding_duration)
			if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: snippet {i+1}/{total_snippets} audio snippet was {snippet_audio_len}ms, padded to {snippet_duration_ms}ms",flush=True)
		else:
			snippet_audio = snippet_audio[:snippet_duration_ms]
			if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: snippet {i+1}/{total_snippets} audio snippet was {snippet_audio_len}ms, trimmed to {snippet_duration_ms}ms",flush=True)

		# Calculate the pre and post fade times
		#	Fade out (to silent) the end of this AudioSegment
		#	Fade in (from silent) the beginning of this AudioSegment
		# fade_out_duration_ms passed as a parameter
		# fade_in_duration_ms passed as a parameter
		fade_out_start_time_ms = ((start_frame / video_fps) * 1000) - fade_out_duration_ms
		fade_out_end_time = fade_out_start_time_ms + fade_out_duration_ms
		fade_in_start_time_ms = ((end_frame / video_fps) * 1000)
		fade_in_end_time_ms = fade_in_start_time_ms + fade_in_duration_ms
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: snippet {i+1}/{total_snippets} calculated fade_out_start_time_ms={fade_out_start_time_ms} fade_out_end_time={fade_out_end_time}",flush=True)
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: snippet {i+1}/{total_snippets} calculated fade_in_start_time_ms={fade_in_start_time_ms} fade_in_end_time_ms={fade_in_end_time_ms}",flush=True)
		
		# Apply fade-in and fade-out effects to the background audio either side of the insertion point
		# https://github.com/jiaaro/pydub/blob/master/API.markdown
		if fade_out_start_time_ms >= 0:
			if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: snippet {i+1}/{total_snippets}, applying 'fade-out', 'fade_in', to background_audio",flush=True)
			background_audio = background_audio.fade(to_gain=-120.0,start=fade_out_start_time_ms,duration=fade_out_duration_ms).fade(from_gain=-120.0,start=fade_in_start_time_ms,duration=fade_in_duration_ms)
		else:
			if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: snippet {i+1}/{total_snippets}, NO fade-in, fade_out, applied to background_audio since fade_out_start_time_ms {fade_out_start_time_ms} < 0",flush=True)

		# Overlay the snippet audio onto the background audio at the specified position
		# Use gain_during_overlay even if fading is applied above
		# 		Change the original audio by this many dB while overlaying audio. 
		#		This can be used to make the original audio quieter while the overlaid audio plays.
		#		example: -6.0 default: 0 (no change in volume during overlay) 
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: snippet {i+1}/{total_snippets}, applying 'overlay' to background_audio",flush=True)
		background_audio = background_audio.overlay(snippet_audio, position=((start_frame / video_fps) * 1000), gain_during_overlay=-120.0, loop=False)
	del snippet_audio
	# end for ... FINISHED looping through the snippets LIST
	
	# Save the edited background audio using .export
	# https://stackoverflow.com/questions/62598172/m4a-mp4-audio-file-encoded-with-pydubffmpeg-doesnt-play-on-android
	edited_background_audio_input_filename_tmp = r".\\temporary_edited_background_audio.mkv"
	try:
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: 'export' background_audio to file '{edited_background_audio_input_filename_tmp}' with format='matroska', codec='libfdk_aac', bitrate='256k', parameters=['-ar', '48000', '-ac', '2']",flush=True)
		background_audio.export(edited_background_audio_input_filename_tmp, format="matroska", codec="libfdk_aac", bitrate="256k", parameters=["-ar", "48000", "-ac", "2"])
	except FileNotFoundError:
		print(f"replace_audio_with_snippets_from_file: File not found from background_audio.export('{edited_background_audio_input_filename_tmp}',...)",flush=True,file=sys.stderr)
		sys.exit(1)
	except TypeError:
		print(f"replace_audio_with_snippets_from_file: Type mismatch or unsupported operation from background_audio.export('{edited_background_audio_input_filename_tmp}',...)",flush=True,file=sys.stderr)
		sys.exit(1)
	except ValueError:
		print(f"replace_audio_with_snippets_from_file: Invalid or unsupported value from background_audio.export('{edited_background_audio_input_filename_tmp}',...)",flush=True,file=sys.stderr)
		sys.exit(1)
	except IOError:
		print(f"replace_audio_with_snippets_from_file: I/O error occurred from background_audio.export('{edited_background_audio_input_filename_tmp}',...)",flush=True,file=sys.stderr)
		sys.exit(1)
	except OSError as e:
		print(f"replace_audio_with_snippets_from_file: Unexpected OSError from background_audio.export('{edited_background_audio_input_filename_tmp}',...)\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"replace_audio_with_snippets_from_file: Unexpected error from background_audio.export('{edited_background_audio_input_filename_tmp}',...)\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	del background_audio	# release a bunch of memory
	
	# Mux together the original video with the edited background audio
	if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: callng muxer '{input_video_path}'+'{edited_background_audio_input_filename_tmp}'='{output_video_path}' ",flush=True)
	mux_video_audio(input_video_path, edited_background_audio_input_filename_tmp, output_video_path)

	# Clean up temporary file(s)
	try:
		os.remove(edited_background_audio_input_filename_tmp)
	except Exception as e:
		print(f"Error: Failed to clean up temporary file(s) '{edited_background_audio_input_filename_tmp}' : {str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)

	return output_video_path
