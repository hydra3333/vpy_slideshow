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
#from datetime import datetime, date, time, timezone
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
	#	print(repr(converted_string),flush=True)
	# yields 'D:\\a\\b\\c\\d\\e\\f\\filename.txt'
	new_file_name = os.path.abspath(file_name).rstrip(os.linesep).strip('\r').strip('\n').strip()
	if new_file_name.endswith('\\'):
		new_file_name = new_file_name[:-1]  # Remove trailing backslash
	new_file_name = normalize_path(new_file_name)
	return new_file_name

def reconstruct_full_directory_only(incoming, default):
	# default is assumed to be a directory, any text in it treated as that and not a filename
	if incoming:
		#outgoing = os.path.normpath(incoming + '\\' if not incoming.endswith('\\') else '')
		incoming_abspath = os.path.abspath(incoming) + '\\' if not incoming.endswith('\\') else ''
		outgoing = os.path.normpath(incoming_abspath)
	else:
		default_abs_path = os.path.abspath(default) + '\\' if not default.endswith('\\') else ''
		outgoing = os.path.normpath(default_abs_path)
	# CRIICAL NOTE:  file=sys.stderr MUST be used in slideshow_LOAD_SETTINGS and not in slideshow_CONTROLLER !!
	if DEBUG:	print(f"DEBUG: reconstruct_full_directory_only: incoming='{incoming}' default='{default}' outgoing='{outgoing}'",flush=True,file=sys.stderr)
	return outgoing

def reconstruct_full_directory_and_filename(incoming, default_path, default_filename):
	# default is assumed to be a filename, any text in it treated as that and not a directory unless ending in \ (repr='\\')
	default_directory = reconstruct_full_directory_only(default_path, default_path)
	#print(f"{20*'%'}  reconstruct_full_directory_and_filename: incoming='{incoming}' default_path='{default_path}' default_filename='{default_filename}' default_directory='{default_directory}' default_filename='{default_filename}'",flush=True,file=sys.stderr)
	default_filename, default_extension = os.path.splitext(default_filename)
	if incoming:
		incoming_directory, incoming_filename = os.path.split(incoming)
		if incoming_directory:
			incoming_directory = reconstruct_full_directory_only(incoming_directory, incoming_directory)
		incoming_filename, incoming_extension = os.path.splitext(incoming_filename)
		directory = incoming_directory or default_directory
		filename = incoming_filename or default_filename
		extension = incoming_extension or default_extension
		outgoing = os.path.normpath(os.path.join(directory, filename + extension))
	else:
		outgoing = os.path.normpath(default_abs_path)
	# CRIICAL NOTE:  file=sys.stderr MUST be used in slideshow_LOAD_SETTINGS and not in slideshow_CONTROLLER !!
	if DEBUG:	print(f"DEBUG: reconstruct_full_directory_and_filename: incoming='{incoming}' default_path='{default_path}' default_filename='{default_filename}' outgoing='{outgoing}'",flush=True,file=sys.stderr)
	return outgoing

def old__bad_reconstruct_full_directory_and_filename(incoming, default):
	# default is assumed to be a filename, any text in it treated as that and not a directory unless ending in \ (repr='\\')
	default_abs_path = os.path.abspath(default)
	default_directory, default_filename = os.path.split(default_abs_path)
	print(f"{20*'%'}  econstruct_full_directory_and_filename: incoming='{incoming}' default='{default}' default_abs_path='{default_abs_path}' default_directory='{default_directory}' default_filename='{default_filename}'",flush=True,file=sys.stderr)
	default_directory = os.path.abspath(default_directory) + '\\' if not default_directory.endswith('\\') else ''
	default_filename, default_extension = os.path.splitext(default_filename)
	if incoming:
		incoming_directory, incoming_filename = os.path.split(incoming)
		incoming_directory = os.path.abspath(incoming_directory) + '\\' if not incoming_directory.endswith('\\') else ''
		incoming_filename, incoming_extension = os.path.splitext(incoming_filename)
		directory = incoming_directory or default_directory
		filename = incoming_filename or default_filename
		extension = incoming_extension or default_extension
		outgoing = os.path.normpath(os.path.join(directory, filename + extension))
	else:
		outgoing = os.path.normpath(default_abs_path)
	# CRIICAL NOTE:  file=sys.stderr MUST be used in slideshow_LOAD_SETTINGS and not in slideshow_CONTROLLER !!
	if DEBUG:	print(f"DEBUG: old__bad_reconstruct_full_directory_and_filename: incoming='{incoming}' default='{default}' outgoing='{outgoing}'",flush=True,file=sys.stderr)
	return outgoing

def format_duration_ms_to_hh_mm_ss_hhh(milliseconds):
	duration = datetime.timedelta(milliseconds=milliseconds)
	hours = duration.seconds // 3600
	minutes = (duration.seconds // 60) % 60
	seconds = duration.seconds % 60
	milliseconds = duration.microseconds // 1000
	return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

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
#	print(f'\n====================mi_dict=\n{objPrettyPrint.pformat(mi_dict)}',flush=True)

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
#	print(f'{objPrettyPrint.pformat(obj_ffprobe.dict)}',flush=True)	# to print everything. take care to notice stream indexing to correctly find your video stream metadata
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
	#	print(f'{objPrettyPrint.pformat(obj_ffprobe.dict)}',flush=True)	# to print everything. take care to notice stream indexing to correctly find your video stream metadata
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
			#print(f"DEBUG image_get_metadata_via_PIL: no exif_data, FILE DATEMODIFIED WILL BE USED FOR date_recorded='{date_recorded}'",flush=True)
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
		#print(f"DEBUG image_get_date_recorded_from_exif: FILE DATEMODIFIED USED FOR date_recorded='{date_recorded}'",flush=True)
	#print(f"DEBUG image_get_date_recorded_from_exif: date_recorded='{date_recorded}'",flush=True)
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
def get_random_ffindex_filename(path):
	# use the filename component of the incoming path and create a random fully qualified path into the temp folder
	# there is a significant to 100% chance of home picture/video filenames in directory trees being non-unique
	# apparently uuid4 has a good chance of returning a unique string
	f = fully_qualified_filename(os.path.join(SETTINGS_DICT['TEMP_FOLDER'], os.path.basename(path) + r'_' + str(uuid.uuid4()) + r'.ffindex'))
	return f

###
def find_all_chunks():
	# only use globals: SETTINGS_DICT, DEBUG

	def fac_get_filename(files_generator):
		# get next filename of desired extensions from generator, ignoring extensions we have not specified
		# loop around only returning a filename with a known extension
		while 1:	# loop until we do a "return", hitting past the end of the iterator returns None
			try:
				filename = next(files_generator)
				#if DEBUG:	print(f'fac_get_filename: get success, filename.name=' + filename.name,flush=True)
			except StopIteration:
				return None
			if filename.suffix.lower() in SETTINGS_DICT['EXTENSIONS']:	# only return files which are in known extensions
				#if DEBUG:	print(f'DEBUG: find_all_chunks: fac_get_filename: in EXTENSIONS success, filename.name=' + filename.name,flush=True)
				return filename

	def fac_check_clip_from_filename(filename, ext):		# opens VID_EEK_EXTENSIONS only ... Source filter depends on extension
		if not ext in SETTINGS_DICT['VID_EEK_EXTENSIONS']:
			raise ValueError(f'get_clip_from_path: expected {filename} to have extension in {SETTINGS_DICT["VID_EEK_EXTENSIONS"]} ... aborting')
		if ext in SETTINGS_DICT['VID_EXTENSIONS']:
			try:
				ffcachefile = get_random_ffindex_filename(filename)
				clip = core.ffms2.Source(str(filename), cachefile=ffcachefile)
				del clip
				if os.path.exists(ffcachefile):
					os.remove(ffcachefile)
				return True
			except Exception as e:
				print(f'CONTROLLER: WARNING: fac_check_clip_from_filename: error opening file via "ffms2": "{str(filename)}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
				return False
		elif  ext in SETTINGS_DICT['EEK_EXTENSIONS']:
			try:
				clip = core.lsmas.LWLibavSource(str(filename))
				del clip
				return True
			except Exception as e:
				print(f'CONTROLLER: WARNING: fac_check_clip_from_filename: error opening file via "lsmas": "{filename.name}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
				return False
		else:
			raise ValueError(f'ERROR: fac_check_clip_from_filename: get_clip_from_path: expected {filename} to have extension in {SETTINGS_DICT["VID_EEK_EXTENSIONS"]} ... aborting')
		return False

	def fac_check_clip_from_pic(filename, ext):
		if ext in SETTINGS_DICT['PIC_EXTENSIONS']:
			ffcachefile = get_random_ffindex_filename(filename)
			try:
				clip = core.ffms2.Source(str(filename), cachefile=ffcachefile)
				del clip
				if os.path.exists(ffcachefile):
					os.remove(ffcachefile)
				return True
			except Exception as e:
				print(f'CONTROLLER: WARNING: fac_check_clip_from_pic: error opening file via "ffms2": "{filename.name}" ; ignoring this picture. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
				return False
		else:
			raise ValueError(f'ERROR: fac_check_clip_from_pic: : expected {filename} to have extension in {SETTINGS_DICT["PIC_EXTENSIONS"]} ... aborting')
		return False

	def fac_check_file_validity_by_opening(filename):
		if filename is None:
			raise ValueError(f'ERROR: fac_check_file_validity_by_opening: "filename" not passed as an argument to fac_check_file_validity_by_opening')
			sys.exit(1)
		ext = filename.suffix.lower()
		if ext in SETTINGS_DICT['VID_EXTENSIONS']:
			is_valid = fac_check_clip_from_filename(filename, ext)									# open depends on ext, the rest is the same
		elif ext in SETTINGS_DICT['EEK_EXTENSIONS']:
			is_valid = fac_check_clip_from_filename(filename, ext)									# open depends on ext, the rest is the same
		elif ext in SETTINGS_DICT['PIC_EXTENSIONS']:
			is_valid = fac_check_clip_from_pic(filename, ext)
		else:
			raise ValueError(f'ERROR: fac_check_file_validity_by_opening: "{filename}" - UNRECOGNISED file extension "{ext}", aborting ...')
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
	#for Directory in sorted(SETTINGS_DICT['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS']):	# Sort the list provided by the user prior to using it
	for Directory in SETTINGS_DICT['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS']:				# Use the order of folders as specified by the user in the LIST, unsorted
		current_Directory = Directory
		#files = sorted(Path(current_Directory).glob(glob_var)) 									# generator of all files in a directory, files starting with . won't be matched by default
		files = sorted( (entry for entry in Path(current_Directory).glob(glob_var) if (entry.is_file() and entry.suffix.lower() in SETTINGS_DICT['EXTENSIONS'])), key=lambda p: (p.parent, p.name) )  # consider files but exclude directories in the generator, sorting them
		for filename in files:		# filename type='<class 'pathlib.WindowsPath'>'
			if DEBUG:	print(f"DEBUG: find_all_chunks: found file '{filename}', re-checking if file is in '{SETTINGS_DICT['EXTENSIONS']}'",flush=True)
			if filename.suffix.lower() in SETTINGS_DICT['EXTENSIONS']:
				print(f"CONTROLLER: Checking file {count_of_files}. '{filename}' for validity with fac_check_file_validity_by_opening ...",flush=True)
				is_valid = fac_check_file_validity_by_opening(filename)
				if not is_valid:	# ignore clips which had an issue with being opened and return None
					print(f'CONTROLLER: Unable to process {count_of_files} {str(filename)} ... ignoring it',flush=True)
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
					fully_qualified_path_string = fully_qualified_filename(filename)
					chunks[str(chunk_id)]['file_list'].append(fully_qualified_path_string)
					chunks[str(chunk_id)]['num_files'] = chunks[str(chunk_id)]['num_files'] + 1
					count_of_files = count_of_files + 1
		#end for
	#end for
	if count_of_files <=0:
		raise ValueError(f"ERROR: find_all_chunks: File Extensions:\n{SETTINGS_DICT['EXTENSIONS']}\nnot found in '{SETTINGS_DICT['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS']}'")

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
		if DEBUG:
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
def audio_standardize_and_import_file(audio_filename, headroom_db, ignore_error_converting=False):
	# use global SETTINGS_DICT for the convert and import audio
	# https://pydub.com/
	# https://github.com/jiaaro/pydub/blob/master/API.markdown
	# NOTE	we MUST ensure the clips all have the SAME characteristics !!!!! or overlay etc will not work.
	#		using .from_file a file may be an arbitrary number of channels, which pydub cannot handle
	#			so we must first convert number of channels etc into a fixed file so we can use .from_file, eg
	#			ffmpeg -i "filename.mp4" -vn -ac 2 -ar 48000 -acodec pcm_s16le "some_audio_filename_in_temp_folder.wav"
	# rely on multi-used settings variables defined in main

	if os.path.exists(temporary_audio_filename):
		os.remove(temporary_audio_filename)

	loglevel = 'warning'
	if DEBUG:
		loglevel = 'info'
	ffmpeg_commandline = [	FFMPEG_EXE,
							'-hide_banner', 
							'-loglevel', loglevel, 
							'-nostats', 
							'-i', audio_filename,
							'-vn',
							'-af', f'ebur128=peak=true:target={headroom_db}:dualmono=true',	# this normalizes audio using industry standard ebur128; it takes a while
							'-acodec', temporary_background_audio_codec,
							'-ac', str(target_background_audio_channels),
							'-ar', str(target_background_audio_frequency),
							'-y', temporary_audio_filename
							]
	print(f"CONTROLLER: audio_standardize_and_import_file attempting to standardize audio using {ffmpeg_commandline}",flush=True)

	if ignore_error_converting:
		result = subprocess.run(ffmpeg_commandline, check=False)
		if result.returncode != 0:
			print(f"CONTROLLER: WARNING: audio_standardize_and_import_file: ignoring an audio file due to Unexpected error from subprocess.run\n{objPrettyPrint.pformat(ffmpeg_commandline)}",flush=True,file=sys.stderr)
			return None
	else:
		# this will crash if there's an error
		subprocess.run(ffmpeg_commandline, check=True)

	try:
		audio = AudioSegment.from_file(temporary_audio_filename)
		audio = audio.set_channels(target_background_audio_channels).set_sample_width(target_background_audio_bytedepth).set_frame_rate(target_background_audio_frequency)
		audio = audio.apply_gain(headroom_db - audio.max_dBFS)	# RE-normalize imported audio, not sure ffmpeg ebur128 does anything
	#except FileNotFoundError:
	#	print(f"CONTROLLER: audio_standardize_and_import_file: audio File not found from AudioSegment.from_file('{temporary_audio_filename}')",flush=True,file=sys.stderr)
	#	sys.exit(1)
	#except TypeError:
	#	print(f"CONTROLLER: audio_standardize_and_import_file: audio Type mismatch or unsupported operation from AudioSegment.from_file('{temporary_audio_filename}')",flush=True,file=sys.stderr)
	#	sys.exit(1)
	#except ValueError:
	#	print(f"CONTROLLER: audio_standardize_and_import_file: audio Invalid or unsupported value from AudioSegment.from_file('{temporary_audio_filename}')",flush=True,file=sys.stderr)
	#	sys.exit(1)
	#except IOError:
	#	print(f"CONTROLLER: audio_standardize_and_import_file: audio I/O error occurred from AudioSegment.from_file('{temporary_audio_filename}')",flush=True,file=sys.stderr)
	#	sys.exit(1)
	#except OSError as e:
	#	print(f"CONTROLLER: audio_standardize_and_import_file: audio Unexpected OSError from AudioSegment.from_file('{temporary_audio_filename}')\n{str(e)}",flush=True,file=sys.stderr)
	#	sys.exit(1)
	except Exception as e:
		print(f"CONTROLLER: audio_standardize_and_import_file: audio Unexpected error from AudioSegment.from_file('{temporary_audio_filename}')\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)

	if os.path.exists(temporary_audio_filename):
		os.remove(temporary_audio_filename)

	return audio

def audio_standardize_and_import_background_audios_from_folder(background_audio_folder, extensions=['.mp2', '.mp3', '.mp4', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.wma']):
	# loop through files in a specified  background_audio_folder in alphabetical order, 
	# standardize them (ffmpeg reads anything useful and converts it)
	# and import and append them to form a large background audio clip
	# rely on multi-used settings variables defined in main

	background_audio = AudioSegment.empty()
	background_audio = background_audio.set_channels(target_background_audio_channels)
	background_audio = background_audio.set_sample_width(target_background_audio_bytedepth)
	background_audio = background_audio.set_frame_rate(target_background_audio_frequency)

	background_audio_folder = os.path.abspath(background_audio_folder).rstrip(os.linesep).strip('\r').strip('\n').strip()
	#glob_var="**/*.*"			# recursive
	glob_var="*.*"				# non-recursive
	c = 0
	v = 0
	#files = sorted(os.listdir(background_audio_folder))
	files = sorted( (entry for entry in Path(background_audio_folder).glob(glob_var) if (entry.is_file() and entry.suffix.lower() in extensions)), key=lambda p: (p.parent, p.name) )  # consider files but exclude directories in the generator, sorting them
	for filename in files:
		c = c + 1
		if DEBUG:	print(f"DEBUG: audio_standardize_and_import_background_audios_from_folder: found file '{filename}', checking if file is in '{extensions}'",flush=True)
		filename = fully_qualified_filename(filename)
		# having found a suitable audio file in the background_audio_folder, standardize and import and append it
		audio_imported_from_file = audio_standardize_and_import_file(filename, target_audio_background_normalize_headroom_db, ignore_error_converting=True)
		if audio_imported_from_file is not None:
			v = v + 1
			background_audio = background_audio + audio_imported_from_file
	#end for
	print(f"CONTROLLER: audio_standardize_and_import_background_audios_from_folder: found {v} valid background audio files out of {c}, duration={format_duration_ms_to_hh_mm_ss_hhh(len(background_audio))}, in '{extensions}' in '{background_audio_folder}', ",flush=True)

	# return an empty audio of zero length if no background files were found
	return background_audio

def audio_create_standardized_silence(duration_ms):
	# use global SETTINGS_DICT for the convert and import audio
	# https://pydub.com/
	# https://github.com/jiaaro/pydub/blob/master/API.markdown
	# NOTE	we MUST ensure the clips all have the SAME characteristics !!!!! or overlay etc will not work.
	# rely on multi-used settings variables defined in main

	audio = AudioSegment.silent(duration=duration_ms)
	audio = audio.set_channels(target_background_audio_channels).set_sample_width(target_background_audio_bytedepth).set_frame_rate(target_background_audio_frequency)
	
	return audio

###
def encode_chunk_using_vsipe_ffmpeg(individual_chunk_id):
	# encode an individual chunk using vspipe and ffmpeg
	# 
	# using ChatGPT suggested method for non-blocking reads of subprocess stderr, stdout
	global SETTINGS_DICT
	global ALL_CHUNKS
	global ALL_CHUNKS_COUNT
	global ALL_CHUNKS_COUNT_OF_FILES
	
	global FFMPEG_EXE
	global VSPIPE_EXE

	slideshow_ENCODER_legacy_path = SETTINGS_DICT['slideshow_ENCODER_legacy_path']

	def enqueue_output(out, queue):
		# for subprocess thread output queueing
		for line in iter(out.readline, b''):
			queue.put(line)
		out.close()

	individual_chunk_dict = ALL_CHUNKS[str(individual_chunk_id)]
	
	chunk_json_filename = fully_qualified_filename(individual_chunk_dict['chunk_fixed_json_filename'])					# always the same fixed filename
	proposed_ffv1_mkv_filename = fully_qualified_filename(individual_chunk_dict['proposed_ffv1_mkv_filename'])	# preset by find_all_chunks to: fixed filename plus a seqential 5-digit-zero-padded ending based on chunk_id + r'.mkv'

	# remove any pre-existing files to be consumed and produced by the ENCODER
	if os.path.exists(chunk_json_filename):
		os.remove(chunk_json_filename)
	if os.path.exists(proposed_ffv1_mkv_filename):
		os.remove(proposed_ffv1_mkv_filename)

	# create the fixed-filename chunk file consumed by the encoder; it contains the fixed-filename of the snippet file to produce
	if DEBUG:	print(f"DEBUG: CONTROLLER: in encoder loop: attempting to create chunk_json_filename='{chunk_json_filename}' for encoder to consume.",flush=True)
	try:
		with open(chunk_json_filename, 'w') as fp:
			json.dump(individual_chunk_dict, fp, indent=4)
	except Exception as e:
		print(f"CONTROLLER: ERROR: dumping current chunk to JSON file: '{chunk_json_filename}' for encoder, chunk_id={individual_chunk_id}, individual_chunk_dict=\n{objPrettyPrint.pformat(individual_chunk_dict)}\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)	
	print(f"CONTROLLER: Created fixed-filename chunk file for encoder to consume: '{chunk_json_filename}' listing {ALL_CHUNKS[str(individual_chunk_id)]['num_files']} files, individual_chunk_dict=\n{objPrettyPrint.pformat(individual_chunk_dict)}",flush=True)

	# Define the commandlines for the subprocesses forming the ENCODER
	vspipe_commandline = [VSPIPE_EXE, '--progress', '--container', 'y4m', slideshow_ENCODER_legacy_path, '-']
	ffmpeg_commandline = [FFMPEG_EXE,
							'-hide_banner', 
							'-loglevel', 'info', 
							'-nostats', 
							'-colorspace', 'bt709', 
							'-color_primaries', 'bt709', 
							'-color_trc', 'bt709', 
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
	# this vspipe commandline is for DEBUGGING only
	# it produces the vspipe output but directs it to NUL and does not invoke ffmpeg
	# but it is still handy becuase it prodices updated snippet into into ALL_CHUNKS
	vspipe_commandline_NUL = [VSPIPE_EXE, '--progress', '--container', 'y4m',  slideshow_ENCODER_legacy_path, 'NUL']

	# run the vspipe -> ffmpeg with non-blocking reads of stderr and stdout

	piping_method = 3	# 3 works
	
	if piping_method == 1:	# this loses stdout from ffmpeg
		# stderr from process_ffmpeg works OK.  stdout from ffmpeg gets lost.
		print(f"CONTROLLER: Running the ENCODER via piping_method={piping_method}, simple Popens, losing ffmpeg stdout?, using commandlines:\n{vspipe_commandline}\n{objPrettyPrint.pformat(ffmpeg_commandline)}",flush=True)
		process_vspipe = subprocess.Popen( vspipe_commandline, stdout=subprocess.PIPE)
		process_ffmpeg = subprocess.Popen( ffmpeg_commandline, stdin=process_vspipe.stdout)
		process_ffmpeg.communicate()
	elif piping_method == 2:	# this method DOES NOT WORK because subprocess.run hates the pipe symbol
		# Execute the command using subprocess.run
		vspipe_pipe_ffmpeg_commandline = vspipe_commandline + [r' | '] + ffmpeg_commandline
		print(f"CONTROLLER: Running the ENCODER via piping_method={piping_method}, subprocess.run, with one commandline:\n{objPrettyPrint.pformat(vspipe_pipe_ffmpeg_commandline)}",flush=True)
		result = subprocess.run(vspipe_pipe_ffmpeg_commandline, shell=True)
		if result.returncode != 0:
			print(f"CONTROLLER: ERROR RUNNING ENCODER VSPIPE/FFMPEG via piping_method={piping_method} subprocess.run, Command execution failed with exit status: {result.returncode}",flush=True)
			sys.exit(1)
		else:
			print(f"CONTROLLER: Returned successfully from the ENCODER via piping_method={piping_method}, subprocess.run, with one commandline:\n{objPrettyPrint.pformat(vspipe_pipe_ffmpeg_commandline)}",flush=True)
	elif piping_method == 3:	# less control but you see everything
		# Execute the command using subprocess.run but using a string not a list
		def command_list_to_command_string(command_list):
			command_parts = []
			for part in command_list:
				#if part.startswith('-') or part.lower() == r'pipe:'.lower():  # Check if the part starts with a dash (indicating a switch)
				#	command_parts.append(part)  # Add the part as is (switch)
				#else:
				#	command_parts.append(f'"{part}"')  # Enclose the part in double quotes
				if part.startswith('format='.lower()) or (len(part) >= 2 and part[1] == r':'):
					command_parts.append(f'"{part}"')  # Enclose the part in double quotes
				else:
					command_parts.append(part)  # Add the part as is
			commandline = ' '.join(command_parts)
			return commandline
		vspipe_cmd = command_list_to_command_string(vspipe_commandline)
		ffmpeg_cmd = command_list_to_command_string(ffmpeg_commandline)
		vspipe_pipe_ffmpeg_commandline = vspipe_cmd + r' | ' + ffmpeg_cmd
		print(f"CONTROLLER: Running the ENCODER via piping_method={piping_method}, subprocess.run, with one commandline:\n{objPrettyPrint.pformat(vspipe_pipe_ffmpeg_commandline)}",flush=True)
		result = subprocess.run(vspipe_pipe_ffmpeg_commandline, shell=True)
		if result.returncode != 0:
			print(f"CONTROLLER: ERROR RUNNING ENCODER VSPIPE/FFMPEG via piping_method={piping_method} subprocess.run, Command execution failed with exit status: {result.returncode}",flush=True)
			sys.exit(1)
		else:
			print(f"CONTROLLER: Returned successfully from the ENCODER via piping_method={piping_method}, subprocess.run, with one commandline:\n{objPrettyPrint.pformat(vspipe_pipe_ffmpeg_commandline)}",flush=True)
	elif piping_method == 4:
		# Execute the command using os.system
		def command_list_to_command_string(command_list):
			command_parts = []
			for part in command_list:
				#if part.startswith('-') or part.lower() == r'pipe:'.lower():  # Check if the part starts with a dash (indicating a switch)
				#	command_parts.append(part)  # Add the part as is (switch)
				#else:
				#	command_parts.append(f'"{part}"')  # Enclose the part in double quotes
				if part.startswith('format='.lower()) or (len(part) >= 2 and part[1] == r':'):
					command_parts.append(f'"{part}"')  # Enclose the part in double quotes
				else:
					command_parts.append(part)  # Add the part as is
			commandline = ' '.join(command_parts)
			return commandline
		vspipe_cmd = command_list_to_command_string(vspipe_commandline)
		ffmpeg_cmd = command_list_to_command_string(ffmpeg_commandline)
		vspipe_pipe_ffmpeg_commandline = vspipe_cmd + r' | ' + ffmpeg_cmd
		print(f"CONTROLLER: Running the ENCODER via piping_method={piping_method}, subprocess.run, with one commandline:\n{objPrettyPrint.pformat(vspipe_pipe_ffmpeg_commandline)}",flush=True)
		exit_status = os.system(vspipe_pipe_ffmpeg_commandline)	# os.system fails to run this even though the string works in a dos box
		if exit_status != 0:
			print(f"CONTROLLER: ERROR RUNNING ENCODER VSPIPE/FFMPEG via piping_method={piping_method} os.system, Command execution failed with exit status: {exit_status}",flush=True)
			sys.exit(1)
		else:
			print(f"CONTROLLER: Returned successfully from the ENCODER via piping_method={piping_method}, os.system, with one commandline:\n{objPrettyPrint.pformat(vspipe_pipe_ffmpeg_commandline)}",flush=True)
	elif piping_method == 5:	# non-blocking reads, works fine as long as nothing goes wrong.
		print(f"CONTROLLER: Running the ENCODER via piping_method={piping_method}, non=blocking reads, using commandlines:\n{objPrettyPrint.pformat(vspipe_commandline)}\n{objPrettyPrint.pformat(ffmpeg_commandline)}",flush=True)
		try:	
			# Run the commands in subprocesses for the ENCODER
			process1 = subprocess.Popen(vspipe_commandline, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			process2 = subprocess.Popen(ffmpeg_commandline, stdin=process1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			# FOR TESTING:
			#pid1 = process1.pid
			#pid2 = process2.pid
			#time.sleep(3)  # Add a delay of a couple of seconds
			## Terminate subprocesses forcefully using taskkill if they aren't already terminated
			#os.system(f'taskkill /F /PID {process1.pid}')
			#os.system(f'taskkill /F /PID {process2.pid}')
			#sys.exit()
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
						print(f"vspipe: {stderr_line1}",flush=True,file=sys.stderr)
					pass
				except Empty:
					pass
				try:
					stdout_line2 = stdout_queue2.get_nowait().decode('utf-8').strip()
					if stdout_line2:
						print(f"ffmpeg: {stdout_line2}",flush=True)
					pass
				except Empty:
					pass
				try:
					stderr_line2 = stderr_queue2.get_nowait().decode('utf-8').strip()
					if stderr_line2:
						print(f"ffmpeg: {stderr_line2}",flush=True,file=sys.stderr)
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
			print(f"ffmpeg: {output.decode('utf-8').strip()}",flush=True)
			# Print any final error messages
			if error1:
					print(f"vspipe: {error1.decode('utf-8').strip()}",flush=True,file=sys.stderr)
			if error2:
					print(f"ffmpeg: {error2.decode('utf-8').strip()}",flush=True,file=sys.stderr)
			# Close the queues
			stderr_queue1.close()
			stdout_queue2.close()
			stderr_queue2.close()
			# Close the subprocesses
			process1.stdout.close()
			process1.stderr.close()
			process2.stdout.close()
			process2.stderr.close()
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
			# Terminate subprocesses forcefully using taskkill if they aren't already terminated
			os.system(f'taskkill /F /PID {process1.pid}')
			os.system(f'taskkill /F /PID {process2.pid}')
			# Raise the exception again
			raise
		except Exception as e:
			print(f'CONTROLLER: ERROR RUNNING SUBPROCESSES, :\n{e}\n{type(e)}\n{str(e)}',flush=True)
			raise e
	else:
		print(f"print(f'CONTROLLER: ERROR RUNNING VSPIPE/FFMPEG, invalid piping_method={piping_method}",flush=True)
		sys.exit(1)

	time.sleep(2.0)	# give it a chance (2 seconds, or 2000ms) to settle down
	print(f"CONTROLLER: Finished running the ENCODER.",flush=True)
	if not os.path.exists(chunk_json_filename):
		print(f"CONTROLLER: ERROR: CONTROLLER: encoder-updated current chunk to JSON file file not found '{chunk_json_filename}' not found !",flush=True)
		sys.exit(1)
	if not os.path.exists(proposed_ffv1_mkv_filename):
		print(f"CONTROLLER: ERROR: CONTROLLER: encoder-produced .mkv video file not found '{proposed_ffv1_mkv_filename}' not found !",flush=True)
		sys.exit(1)

	# Now the encoder has encoded a chunk and produced an updated chunk file and an ffv1 encoded video .mkv 
	# ... we must import updated chunk file (which will include a new snippet_list) check the chunk, and update the ALL_CHUNKS dict with updated chunk data
	# The format of the snippet_list produced by the encoder into the updated chunk JSON file is defined above.
	if DEBUG:	print(f"DEBUG: CONTROLLER: in encoder loop: attempting to load chunk_json_filename={chunk_json_filename} produced by the encoder.",flush=True)
	try:
		with open(chunk_json_filename, 'r') as fp:
			updated_individual_chunk_dict = json.load(fp)
	except Exception as e:
		print(f"CONTROLLER: ERROR: CONTROLLER: loading updated current chunk from JSON file: '{chunk_json_filename}' from encoder, chunk_id={individual_chunk_id}, related to individual_chunk_dict=\nobjPrettyPrint.pformat(individual_chunk_dict)\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)	
	print(f"CONTROLLER: Loaded updated current chunk from ENCODER-updated JSON file: '{chunk_json_filename}'",flush=True)
	if (updated_individual_chunk_dict['chunk_id'] !=  individual_chunk_dict['chunk_id']) or (updated_individual_chunk_dict['chunk_id'] != individual_chunk_id):
		print(f"CONTROLLER: ERROR: the chunk_id returned from the encoder={updated_individual_chunk_dict['chunk_id']} in updated_individual_chunk_dict does not match both expected individual_chunk_dict chunk_id={individual_chunk_dict['chunk_id']} or loop's individual_chunk_id={individual_chunk_id}",flush=True)
		sys.exit(1)
	# poke the chunk updated by the encoder back into global ALL_CHUNKS ... it should contain snippet data now.
	ALL_CHUNKS[str(individual_chunk_id)] = updated_individual_chunk_dict

	return

##################################################

if __name__ == "__main__":
	DEBUG = False

	##########################################################################################################################################
	##########################################################################################################################################
	# GATHER SETTINGS
	print(f"{100*'-'}",flush=True)
	print(f'CONTROLLER: STARTING GATHER SETTINGS',flush=True)

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
	# DEFINE MILTI-USED SETTINGS VARIABLES
	# rather than go to SETTINGS_DICT all the time ... since these are defined in main, functions should see them but cannot change them

	target_background_audio_frequency = SETTINGS_DICT['TARGET_BACKGROUND_AUDIO_FREQUENCY']			# hopefully 48000
	target_background_audio_channels = SETTINGS_DICT['TARGET_BACKGROUND_AUDIO_CHANNELS']			# hopefully 2
	target_background_audio_bytedepth = SETTINGS_DICT['TARGET_BACKGROUND_AUDIO_BYTEDEPTH']			# hopefully 2 ; bytes not bits, 2 byte = 16 bit to match pcm_s16le
	target_background_audio_codec = SETTINGS_DICT['TARGET_BACKGROUND_AUDIO_CODEC']					# hopefully 'libfdk_aac'
	target_background_audio_bitrate = SETTINGS_DICT['TARGET_BACKGROUND_AUDIO_BITRATE']				# hopefully '256k'
	temporary_background_audio_codec = SETTINGS_DICT['TEMPORARY_BACKGROUND_AUDIO_CODEC']			# hopefully pcm_s16le ; for 16 bit
	target_audio_background_normalize_headroom_db = SETTINGS_DICT['TARGET_AUDIO_BACKGROUND_NORMALIZE_HEADROOM_DB']		# normalize background audio to this maximum db
	target_audio_background_gain_during_overlay = SETTINGS_DICT['TARGET_AUDIO_BACKGROUND_GAIN_DURING_OVERLAY']			# how many DB to reduce backround audio during video clip audio overlay
	target_audio_snippet_normalize_headroom_db =  SETTINGS_DICT['TARGET_AUDIO_SNIPPET_NORMALIZE_HEADROOM_DB']			# normalize video clip audio to this maximum db
	temporary_audio_filename = SETTINGS_DICT['TEMPORARY_AUDIO_FILENAME']							# in temp folder

	##########################################################################################################################################
	##########################################################################################################################################
	# FIND PIC/IMAGES
	print(f"{100*'-'}",flush=True)
	print(f'CONTROLLER: STARTING FIND/CHECK OF PIC AND IMAGES',flush=True)
	
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
	print(f'CONTROLLER: STARTING INTERIM ENCODING OF CHUNKS INTO INTERIM FFV1 VIDEO FILES',flush=True)
	if DEBUG:	
		print(f"DEBUG: CONTROLLER: Starting encoder loop for each of ALL_CHUNKS tree. chunks: {ALL_CHUNKS_COUNT} files: {ALL_CHUNKS_COUNT_OF_FILES}",flush=True)
	
	for individual_chunk_id in range(0,ALL_CHUNKS_COUNT):	# 0 to (ALL_CHUNKS_COUNT - 1)
		# we cannot just import the legacy encoder and call it with parameters, it is a vpy consumed by ffmpeg and that does not accept parameters
		# so we need to create`a fixed-filenamed input file for it to consume (a chu`nk)
		#						and a fixed filename for it to create (snippets for that chunk)

		individual_chunk_dict = ALL_CHUNKS[str(individual_chunk_id)]

		chunk_json_filename = fully_qualified_filename(individual_chunk_dict['chunk_fixed_json_filename'])					# always the same fixed filename
		proposed_ffv1_mkv_filename = fully_qualified_filename(individual_chunk_dict['proposed_ffv1_mkv_filename'])	# preset by find_all_chunks to: fixed filename plus a seqential 5-digit-zero-padded ending based on chunk_id + r'.mkv'
		
		if DEBUG:	print(f"DEBUG: CONTROLLER: encoder loop: calling the encoder, VSPIPE piped to FFMPEG ... with controller using non-blocking reads of stdout and stderr (per chatgpt).",flush=True)
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

		#+++
		encode_chunk_using_vsipe_ffmpeg(individual_chunk_id)
		#+++
	
		if DEBUG:	print(f"DEBUG: encoder loop: returned from the encoder, VSPIPE piped to FFMPEG ... with controller using non-blocking reads of stdout and stderr (per chatgpt).",flush=True)
	#end for

	if DEBUG:
		print(f'CONTROLLER: Finished INTERIM ENCODING OF CHUNKS INTO INTERIM FFV1 VIDEO FILES',flush=True)
		print(f"CONTROLLER: After updating encoder added snippets into each chunk and controller UPDATING chunk info into ALL_CHUNKS, the new ALL_CHUNKS tree is:\n{objPrettyPrint.pformat(ALL_CHUNKS)}",flush=True)

	##########################################################################################################################################
	##########################################################################################################################################
	# FINISHED INTERIM ENCODING
	# re-parse the ALL_CHUNKS tree dict to re-calculate global frame numbers on a per-chunk basis and within that on a per-snippet-within-chunk basis
	# using the newly added  ...  before processing any audio using snippets, 
	# so we can refer to absolute final-video frame numbers rather than chunk-internal frame numbers

	print(f"{100*'-'}",flush=True)
	print(f"CONTROLLER: STARTING RE-PARSE OF ALL_CHUNKS TREE DICT TO RE-CALCULATE AND SAVE GLOBAL FRAME NUMBERS. NUMBER OF CHUNKS TO PROCESS: {ALL_CHUNKS_COUNT}.",flush=True)

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
	print(f'CONTROLLER: STARTING OVERLAY SNIPPETS AUDIOS ONTO BACKGROUND AUDIO, AND TRANSCODE AUDIO to AAC in an MP4',flush=True)

	final_video_frame_count = end_frame_num_of_final_video + 1		# base 0
	final_video_fps = SETTINGS_DICT['TARGET_FPS']
	final_video_duration_ms = int((float(final_video_frame_count) / float(final_video_fps)) * 1000.0)
	final_mp4_with_audio_filename = SETTINGS_DICT['FINAL_MP4_WITH_AUDIO_FILENAME']

	background_audio_with_overlaid_snippets_filename = SETTINGS_DICT['BACKGROUND_AUDIO_WITH_OVERLAID_SNIPPETS_FILENAME']
	background_audio_input_folder = SETTINGS_DICT['BACKGROUND_AUDIO_INPUT_FOLDER']

	# https://pydub.com/
	# https://github.com/jiaaro/pydub/blob/master/API.markdown
	# NOTE	we MUST ensure the clips all have the SAME characteristics !!!!! or overlay etc will not work.
	#		using .from_file a file may be an arbitrary number of channels, which pydub cannot handle
	#			so we must first convert number of channels etc into a fixed file so we can use .from_file, eg
	#			ffmpeg -i "filename.mp4" -vn -ac 2 -ar 48000 -acodec pcm_s16le "some_audio_filename_in_temp_folder.wav"
	# rely on multi-used settings variables defined in main
	
	# Import background audio files.
	background_audio = audio_standardize_and_import_background_audios_from_folder(background_audio_input_folder, extensions=['.mp2', '.mp3', '.mp4', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.wma'])
	
	# Generate a silence background if no valid background audio files found
	if len(background_audio) <=0:
		try:
			print(f"WARNING: CONTROLLER: generate silence as background_audio since len(background_audio) ({len(background_audio)}) <=0 ... probably no background audio files found",flush=True)
			background_audio = audio_create_standardized_silence(final_video_duration_ms)
		except Exception as e:
			print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: Unexpected error for background_audio from audio_create_standardized_silence({final_video_duration_ms})\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)

	# now RE-normalize the background_audio
	#background_audio = background_audio.apply_gain(target_audio_background_normalize_headroom_db - background_audio.max_dBFS)

	# Trim or pad-with-silence the background audio to match the duration final_video_frame_count .. in case concatenated background audio files is too short
	background_audio_len = len(background_audio)
	if background_audio_len < final_video_duration_ms:
		padding_duration = final_video_duration_ms - background_audio_len
		try:
			if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: background_audio_len {background_audio_len}ms, padding background_audio with silence to length {background_audio_len+padding_duration}ms",flush=True)
			padding_audio = audio_create_standardized_silence(padding_duration)
		except Exception as e:
			print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: padding_audio Unexpected error from AudioSegment.silent(duration={padding_duration})\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)
		if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: background_audio_len {background_audio_len}ms, padding with silence to {background_audio_len+padding_duration}ms",flush=True)
		background_audio = background_audio + padding_audio
		del padding_audio
	else:
		if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: background_audio_len {background_audio_len}ms, trimming to {final_video_duration_ms}ms",flush=True)
		background_audio = background_audio[:final_video_duration_ms]
	background_audio_len = len(background_audio)

	if DEBUG:
		debug_background_audio_input_filename = temporary_audio_filename + r'_DEBUG.BACKGROUND_AUDIO_TRIMMED' + '.mp4'
		debug_export_format = r'mp4'
		debug_export_parameters = ["-ar", str(target_background_audio_frequency), "-ac", str(target_background_audio_channels)]
		background_audio.export(debug_background_audio_input_filename, format=debug_export_format, codec=target_background_audio_codec, bitrate=str(target_background_audio_bitrate), parameters=debug_export_parameters)
		print(f"DEBUG: CONTROLLER: exported background_audio converted and trimmed audio to '{debug_background_audio_input_filename}'",flush=True)

	# loop through chunks, and snippets within chunks, overlaying sandardized audio onto background_audio as we go
	snippet_audio_fade_in_duration_ms = SETTINGS_DICT['SNIPPET_AUDIO_FADE_IN_DURATION_MS']
	snippet_audio_fade_out_duration_ms = SETTINGS_DICT['SNIPPET_AUDIO_FADE_OUT_DURATION_MS']
	running_snippet_count = 0
	snippet_processing_summary = []
	for individual_chunk_id in range(0,ALL_CHUNKS_COUNT):	# 0 to (ALL_CHUNKS_COUNT - 1)
		individual_chunk_dict = ALL_CHUNKS[str(individual_chunk_id)]
		num_files = individual_chunk_dict['num_files']
		num_snippets = individual_chunk_dict['num_snippets']
		if num_snippets > 0:
			print(f'CONTROLLER: Start processing chunk: {individual_chunk_id} list of {num_snippets} audio snippet files to be overlaid onto background audio.',flush=True)
			for i in range(0,num_snippets):	# base 0; 0..(num_files - 1)
				running_snippet_count = running_snippet_count + 1
				# grab an individual_snippet_dict which specified details of snippet audio to be overlaid onto background audio; we have pre-calculated "good" frame numbers to calculate ms from
				individual_snippet_dict = individual_chunk_dict['snippet_list'][i]
				# which looks like this:	{	
				#								'start_frame_of_snippet_in_chunk':			integer,
				#								'end_frame_of_snippet_in_chunk':			integer,
				#								'start_frame_of_snippet_in_final_video':	integer,	<- this is useful
				#								'end_frame_of_snippet_in_final_video':		integer,	<- this is useful
				#								'snippet_num_frames':						integer,	<- this is useful
				#								'snippet_source_video_filename':			filename,	<- this is useful
				#							}
				snippet_source_video_filename = individual_snippet_dict['snippet_source_video_filename'] 
				snippet_num_frames = individual_snippet_dict['snippet_num_frames']
				snippet_duration_ms = int((float(snippet_num_frames) / float(final_video_fps)) * 1000.0)	# this IS GOOD. The snippet may have been trimmed or padded for use in the final video, so do not use the audio duration from the original file
				start_frame_of_snippet_in_final_video = individual_snippet_dict['start_frame_of_snippet_in_final_video'] 
				end_frame_of_snippet_in_final_video = individual_snippet_dict['end_frame_of_snippet_in_final_video'] 

				# Load a snippet audio
				if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: about to get audio from snippet {running_snippet_count} via AudioSegment.from_file('{snippet_source_video_filename}')",flush=True)
				snippet_audio = audio_standardize_and_import_file(snippet_source_video_filename, target_audio_snippet_normalize_headroom_db)

				# Extract the corresponding portion of the snippet file audio based on the calculated snippet duration
				# There should be enough audio unless the a very small clip had to padded during slideshow creation
				# Trim or pad the snippet file audio to match the target snippet_duration_ms
				snippet_audio_len = len(snippet_audio)
				if snippet_audio_len < snippet_duration_ms:
					padding_duration = snippet_duration_ms - snippet_audio_len
					try:
						if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: snippet {running_snippet_count} snippet_audio_len {snippet_audio_len}ms, padding with silence to duration {snippet_audio_len+padding_duration}ms",flush=True)
						padding_audio = audio_create_standardized_silence(padding_duration)
					except Exception as e:
						print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: padding_audio Unexpected error from AudioSegment.silent(duration={padding_duration})\n{str(e)}",flush=True,file=sys.stderr)
						sys.exit(1)
					snippet_audio = snippet_audio + padding_audio
					del padding_audio
					if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: snippet {running_snippet_count} snippet_audio_len {snippet_audio_len}ms, was padded with silence to duration {snippet_audio_len+padding_duration}ms",flush=True)
				else:
					if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: snippet {running_snippet_count} snippet audio was {snippet_audio_len}ms, trimming to {snippet_duration_ms}ms",flush=True)
					snippet_audio = snippet_audio[:snippet_duration_ms]
				snippet_audio_len = len(snippet_audio)
				# now RE-normalize the snippet_audio
				#snippet_audio = snippet_audio.apply_gain(target_audio_snippet_normalize_headroom_db - snippet_audio.max_dBFS)

				if DEBUG:
					debug_background_audio_with_overlaid_snippets_filename = temporary_audio_filename + r'_DEBUG.converted.audio.from.snippet.' + str(running_snippet_count) + '.mp4'
					debug_export_format = r'mp4'
					debug_export_parameters = ["-ar", str(target_background_audio_frequency), "-ac", str(target_background_audio_channels)]
					snippet_audio.export(debug_background_audio_with_overlaid_snippets_filename, format=debug_export_format, codec=target_background_audio_codec, bitrate=str(target_background_audio_bitrate), parameters=debug_export_parameters)
					print(f"DEBUG: CONTROLLER: exported snippet {running_snippet_count} converted audio to '{debug_background_audio_with_overlaid_snippets_filename}'",flush=True)

				# Calculate the pre and post fade times for the snippet
				#	Fade out (to silent) the end of this AudioSegment
				#	Fade in (from silent) the beginning of this AudioSegment
				snippet_fade_out_start_time_ms = int((float(start_frame_of_snippet_in_final_video) / float(final_video_fps)) * 1000.0) - snippet_audio_fade_out_duration_ms
				snippet_fade_out_end_time = snippet_fade_out_start_time_ms + snippet_audio_fade_out_duration_ms
				snippet_fade_in_start_time_ms = int((float(end_frame_of_snippet_in_final_video) / float(final_video_fps)) * 1000.0)
				snippet_fade_in_end_time_ms = snippet_fade_in_start_time_ms + snippet_audio_fade_in_duration_ms
				if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: snippet {running_snippet_count} calculated snippet_fade_out_start_time_ms={snippet_fade_out_start_time_ms} fade_out_end_time={snippet_fade_out_end_time}",flush=True)
				if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: snippet {running_snippet_count} calculated snippet_fade_in_start_time_ms={snippet_fade_in_start_time_ms} snippet_fade_in_end_time_ms={snippet_fade_in_end_time_ms}",flush=True)

				# FADE does not seem to work properly, so ignore it ... 
				# Apply fade-in and fade-out effects to the background audio either side of the insertion point
				# https://github.com/jiaaro/pydub/blob/master/API.markdown
				#if snippet_fade_out_start_time_ms >= 0:
				#	if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: snippet {running_snippet_count}, applying 'fade-out', 'fade_in', to background_audio",flush=True)
				#	# careful not to try: "background_audio.fade_out().fade_in()" because I am unsure of the order (real vs theeoretical)
				#	background_audio = background_audio.fade(from_gain=0,to_gain=-18.0,start=snippet_fade_out_start_time_ms,duration=snippet_audio_fade_out_duration_ms)	#-120 is silent during fade
				#	background_audio = background_audio.fade(from_gain=-18.0,to_gain=0,start=snippet_fade_in_start_time_ms,duration=snippet_audio_fade_in_duration_ms)	#-120 is silent during fade
				#else:
				#	if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: snippet {running_snippet_count}, NO fade-in, NO fade_out, applied to background_audio since snippet_fade_out_start_time_ms {snippet_fade_out_start_time_ms} < 0",flush=True)

				# Overlay the snippet audio onto the background audio at the specified position
				# Use gain_during_overlay even if fading is applied above
				# 		Change the original audio by this many dB while overlaying audio. 
				#		This can be used to make the original audio quieter while the overlaid audio plays.
				#		example: -6.0 default: 0 (no change in volume during overlay) 
				start_position_of_snippet_in_final_video_ms = int((float(start_frame_of_snippet_in_final_video) / float(final_video_fps)) * 1000.0)
				end_position_of_snippet_in_final_video_ms = int((float(end_frame_of_snippet_in_final_video) / float(final_video_fps)) * 1000.0)
				if DEBUG:
					print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: snippet {running_snippet_count}, applying snippet using 'overlay' to background_audio",flush=True)
					print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: start_position_of_snippet_in_final_video_s={float(start_position_of_snippet_in_final_video_ms)/1000.0} end_position_of_snippet_in_final_video_s={float(end_position_of_snippet_in_final_video_ms)/1000.0} snippet_audio_len={float(snippet_audio_len)/1000.0}",flush=True)
				background_audio = background_audio.overlay(snippet_audio, loop=False, times=1, position=start_position_of_snippet_in_final_video_ms, gain_during_overlay=target_audio_background_gain_during_overlay)	# -120 is silent during overlay
				snippet_processing_summary.append(	[	{	'background_audio_len_ms':						background_audio_len,
															'snippet_seq_no':								running_snippet_count,
															'snippet_final_duration__ms':					snippet_audio_len,
															'snippet_fade_out_start_time_ms':				snippet_fade_out_start_time_ms,
															'snippet_audio_fade_out_duration_ms':			snippet_audio_fade_out_duration_ms,
															'snippet_fade_out_end_time_ms':					snippet_fade_out_end_time,
															'start_position_of_snippet_in_final_video_ms':	start_position_of_snippet_in_final_video_ms,
															'end_position_of_snippet_in_final_video_ms':	end_position_of_snippet_in_final_video_ms,
															'snippet_fade_in_start_time_ms':				snippet_fade_in_start_time_ms,
															'snippet_audio_fade_in_duration_ms':			snippet_audio_fade_in_duration_ms,
															'end_fadein_ms_in_background_ms':				snippet_fade_in_end_time_ms, 
															'snippet_filename':								snippet_source_video_filename
														}
													] )
		#end for
	#end for

	if DEBUG:
		print(f"{100*'-'}",flush=True)
		print(f"DEBUG: CONTROLLER: FINISHED SNIPPET PROCESSING. SUMMARY:\n{objPrettyPrint.pformat(snippet_processing_summary)}",flush=True)
		print(f"{100*'-'}",flush=True)

	# OK, by now we have a standardized background_audio in 'background_audio'
	# Export it to background_audio_with_overlaid_snippets_filename (pydub hates .m4a so use .mp4 instead)
	try:
		export_format = r'mp4'
		export_parameters = ["-ar", str(target_background_audio_frequency), "-ac", str(target_background_audio_channels)]
		if DEBUG: print(f"DEBUG: CONTROLLER: overlay_snippet_audio_onto_background_audio: 'export' background_audio to file '{background_audio_with_overlaid_snippets_filename}' with format='{export_format}', codec='(target_background_audio_codec)', bitrate='{target_background_audio_bitrate}', parameters={export_parameters}",flush=True)
		background_audio.export(background_audio_with_overlaid_snippets_filename, format=export_format, codec=target_background_audio_codec, bitrate=str(target_background_audio_bitrate), parameters=export_parameters)
	#except FileNotFoundError:
	#	print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: File not found from background_audio.export('{background_audio_with_overlaid_snippets_filename}',...)",flush=True,file=sys.stderr)
	#	sys.exit(1)
	#except TypeError:
	#	print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: Type mismatch or unsupported operation from background_audio.export('{background_audio_with_overlaid_snippets_filename}',...)",flush=True,file=sys.stderr)
	#	sys.exit(1)
	#except ValueError:
	#	print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: Invalid or unsupported value from background_audio.export('{background_audio_with_overlaid_snippets_filename}',...)",flush=True,file=sys.stderr)
	#	sys.exit(1)
	#except IOError:
	#	print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: I/O error occurred from background_audio.export('{background_audio_with_overlaid_snippets_filename}',...)",flush=True,file=sys.stderr)
	#	sys.exit(1)
	#except OSError as e:
	#	print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: Unexpected OSError from background_audio.export('{background_audio_with_overlaid_snippets_filename}',...)\n{str(e)}",flush=True,file=sys.stderr)
	#	sys.exit(1)
	except Exception as e:
		print(f"CONTROLLER: overlay_snippet_audio_onto_background_audio: Unexpected error from background_audio.export('{background_audio_with_overlaid_snippets_filename}',...)\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)

	del background_audio	# release a bunch of memory

	##########################################################################################################################################
	##########################################################################################################################################
	# CONCATENATE/TRANSCODE INTERIM FFV1 VIDEO FILES INTO ONE VIDEO MP4 AND AT SAME TIME MUX WITH BACKGROUND AUDIO.mp4
	print(f"{100*'-'}",flush=True)
	print(f'CONTROLLER: STARTING CONCATENATE/TRANSCODE INTERIM FFV1 VIDEO FILES INTO ONE VIDEO MP4 AND AT SAME TIME MUX WITH BACKGROUND AUDIO',flush=True)

	# create the video-concat input file for ffmpeg, listing all of the FFV1 files to be concatenated/transcoded
	temporary_ffmpeg_concat_list_filename = SETTINGS_DICT['TEMPORARY_FFMPEG_CONCAT_LIST_FILENAME']
	with open(temporary_ffmpeg_concat_list_filename, 'w') as fp:
		for individual_chunk_id in range(0,ALL_CHUNKS_COUNT):	# 0 to (ALL_CHUNKS_COUNT - 1)
			ffv1_filename =  ALL_CHUNKS[str(individual_chunk_id)]['proposed_ffv1_mkv_filename']
			fp.write(f"file '{ffv1_filename}'\n")
			fp.flush()
		#end for
	#end with
	
	# We now have 
	#	temporary_ffmpeg_concat_list_filename				the concat list of videos to be concatenated and transcoded
	#	background_audio_with_overlaid_snippets_filename	the background audio with video snippets audio overlayed onto it the final format we need
	# Lets transcode/mux them together.
	final_mp4_with_audio_filename = SETTINGS_DICT['FINAL_MP4_WITH_AUDIO_FILENAME']
	ffmpeg_commandline_libx264 = [
							FFMPEG_EXE,
							'-hide_banner', 
							'-loglevel', 'info', 
							'-stats', 
							'-i', background_audio_with_overlaid_snippets_filename,
							'-f', 'concat', '-safe', '0', '-i', temporary_ffmpeg_concat_list_filename,
							'-sws_flags', 'lanczos+accurate_rnd+full_chroma_int+full_chroma_inp',
							'-filter_complex', 'format=yuv420p,setdar=16/9',
							'-strict', 'experimental',
							'-c:a', 'copy',
							'-c:v', 'libx264',
							'-preset', 'veryslow',
							'-crf', '21', 
							'-refs', '3',  			# Set the number of reference frames to 3 (it used be 16 by default)
							#'-b:v', '5M', 			# 5M target bitrate instead of crf 22
							'-minrate:v', '1M', 
							'-maxrate:v', '12M', 
							'-bufsize', '12M',
							'-profile:v', 'high',
							'-level', '5.1',		# we are only 1080p so 5.1 is enough # H.264 Maximum supported bitrate: Level 5.1: 50 Mbps, Level 5.2: 62.5 Mbps
							'-movflags', '+faststart+write_colr',
							'-y', final_mp4_with_audio_filename,
							]
	ffmpeg_commandline_h264_nvenc = [		# h264_nvenc ... has parameters ONLY for use with an nvidia 2060plus or higher video encoding card
							FFMPEG_EXE,
							'-hide_banner', 
							'-loglevel', 'info', 
							'-stats', 
							'-i', background_audio_with_overlaid_snippets_filename,
							'-f', 'concat', '-safe', '0', '-i', temporary_ffmpeg_concat_list_filename,
							'-sws_flags', 'lanczos+accurate_rnd+full_chroma_int+full_chroma_inp',
							'-filter_complex', 'format=yuv420p,setdar=16/9',
							'-strict', 'experimental',
							'-c:a', 'copy',
							'-c:v', 'h264_nvenc', 
							'-pix_fmt', 'nv12', 
							'-preset', 'p7', 
							'-multipass', 
							'fullres', 
							'-forced-idr', '1', 
							'-g', '25', 
							'-coder:v', 'cabac', 
							'-spatial-aq', '1', 
							'-temporal-aq', '1', 
							'-dpb_size', '0', 
							'-bf:v', '3', 
							'-b_ref_mode:v', '0', 
							'-rc:v', 'vbr', 
							'-cq:v', '0', 
							'-b:v', '5M', 			# 5M target bitrate
							'-minrate:v', '1M', 
							'-maxrate:v', '12M', 
							'-bufsize', '12M',
							'-profile:v', 'high',
							'-level', '5.1',		# we are only 1080p so 5.1 is enough# H.264 Maximum supported bitrate: Level 5.1: 50 Mbps, Level 5.2: 62.5 Mbps
							'-movflags', '+faststart+write_colr',
							'-y', final_mp4_with_audio_filename,
							]

	ffmpeg_commandline = ffmpeg_commandline_libx264
	print(f"CONTROLLER: START FFMPEG CONATENATE/TRANSCODE INTERIM VIDEOS AND MUX AUDIO IN ONE GO. FFMPEG command:\n{objPrettyPrint.pformat(ffmpeg_commandline)}",flush=True)
	subprocess.run(ffmpeg_commandline, check=True)
	print(f'CONTROLLER: FINISHED CONCATENATE/TRANSCODE INTERIM FFV1 VIDEO FILES INTO ONE VIDEO MP4 AND AT SAME TIME MUX WITH BACKGROUND AUDIO\nFinal Slideshow={objPrettyPrint.pformat(final_mp4_with_audio_filename)}',flush=True)
	print(f"{100*'-'}",flush=True)
	
	##########################################################################################################################################
	##########################################################################################################################################
	# CLEANUP


	#find uplifting royalty free background music 
	#edit current one for first  and second first song

	#cleanup step is not yet done in controller
	#... either as we go ... or at the end or both

	#tassie -- individual people's not combined

