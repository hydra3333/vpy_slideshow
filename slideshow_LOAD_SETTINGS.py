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

#from PIL import Image, ExifTags, UnidentifiedImageError
#from PIL.ExifTags import TAGS

#import pydub
#from pydub import AudioSegment

# Ensure we can import modules from ".\" by adding the current default folder to the python path.
# (tried using just PYTHONPATH environment variable but it was unreliable)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

#CDLL(r'MediaInfo.dll')				# note the hard-coded folder	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
#from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption		# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
##from MediaInfoDLL3 import *											# per https://github.com/MediaArea/MediaInfoLib/blob/master/Source/Example/HowToUse_Dll3.py

global DEBUG
DEBUG = False

global TERMINAL_WIDTH					# for use by PrettyPrinter
TERMINAL_WIDTH = 250
global objPrettyPrint
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc

### ********** end of common header ********** 
#global MI
#MI = MediaInfo()

#core.std.LoadPlugin(r'DGDecodeNV.dll')
#core.avs.LoadPlugin(r'DGDecodeNV.dll')

# Based on ChatGPT, we are no longer using settings.json, we will use SLIDESHOW_SETTINGS.py
# This will allow us to use descriptive comments in SLIDESHOW_SETTINGS.py which a user must edit.
# If the user mucks up python syntax, we rely on the module crashing on import.

# What we are doing instead is to re-import SLIDESHOW_SETTINGS.py every time load_settings() is called.
# Like this
#    import importlib
#    importlib.reload(mymodule)  # Reload the module

# check the files which should exist do exist
def check_file_exists_3333(file, text):
	if not os.path.exists(file):
		print(f"load_settings: ERROR: the specified {text} File '{file}' does not exist",flush=True,file=sys.stderr)
		sys.exit(1)
	return

def check_folder_exists_3333(folder, text):
	if not os.path.isdir(folder):
		print(f"load_settings: ERROR: the specified {text} folder does not exist: '{folder}' does not exist",flush=True,file=sys.stderr)
		sys.exit(1)
	return

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
	if DEBUG:	print(f"DEBUG: normalize_path: outgoing path='{path}'",flush=True)
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

def create_py_file_from_specially_formatted_list(dot_py_filename, specially_formatted_list):
	# a dict may contain strings defined like r''
	# parse a specially formatted LIST [key, value, annotation_text]
	# and create a .py file containing settings = { key: value, # annotation_text ... }
	def make_r_prefix(value):
		if isinstance(value, str):
			if  '\\' in repr(value):
				return 'r' + repr(value).replace('\\\\', '\\')
			else:
				return repr(value)
		#elif isinstance(value, int):
		#	return str(value)
		#elif isinstance(value, float):
		#	return repr(value)
		#elif isinstance(value, bool):
		#	return str(value)
		elif isinstance(value, list):
			return '[' + ', '.join(make_r_prefix(item) for item in value) + ']'
		elif isinstance(value, dict):
			return '{' + ', '.join(f'{make_r_prefix(k)}: {make_r_prefix(v)}' for k, v in value.items()) + '}'
		elif isinstance(value, tuple):
			return '(' + ', '.join(make_r_prefix(item) for item in value) + ')'
		else:
			return repr(value)
	with open(dot_py_filename, "w") as file:
		file.write("settings = {\n")
		for item in specially_formatted_list:
			key, value, annotation_text = item
			file.write(f'\t{make_r_prefix(key)}:\t{make_r_prefix(value)},\t\t# {annotation_text}\n')
		file.write("}\n")
	return

def load_settings():	
	# This will always force reload of 'setup.py' from the current default folder
	# Settings_filename is always "fixed" in the same place as the script is run from, 
	# A dict is returned with all of the settings in it.
	# Missing values are defaulted here, yielding calculated ones as well.
	global DEBUG
	
	if DEBUG:	print(f'DEBUG: at top of load_settings DEBUG={DEBUG}',flush=True)

	# This is ALWAYS a fixed filename in the current default folder !!!
	SLIDESHOW_SETTINGS_MODULE_NAME				= 'SLIDESHOW_SETTINGS'.lower()	# SLIDESHOW_SETTINGS.py
	SLIDESHOW_SETTINGS_MODULE_FILENAME			= fully_qualified_filename(os.path.join(r'.', SLIDESHOW_SETTINGS_MODULE_NAME + '.py'))

	ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS	= [ fully_qualified_directory_no_trailing_backslash(r'.') ]
	ROOT_FOLDER_FOR_OUTPUTS						= fully_qualified_directory_no_trailing_backslash(r'.')
	TEMP_FOLDER									= fully_qualified_directory_no_trailing_backslash(r'.\\TEMP')
	PIC_EXTENSIONS								= [ r'.png', r'.jpg', r'.jpeg', r'.gif' ]
	VID_EXTENSIONS								= [ r'.mp4', r'.mpeg4', r'.mpg', r'.mpeg', r'.avi', r'.mjpeg', r'.3gp', r'.mov' ]
	EEK_EXTENSIONS								= [ r'.m2ts' ]
	VID_EEK_EXTENSIONS							= VID_EXTENSIONS + EEK_EXTENSIONS
	EXTENSIONS									= PIC_EXTENSIONS + VID_EXTENSIONS + EEK_EXTENSIONS

	# we need a json file to contain a dict of all chunks
	CHUNKS_FILENAME_FOR_ALL_CHUNKS_DICT			= os.path.join(TEMP_FOLDER, r'chunks_file_for_all_chunks_dict.json')		# only for debug
	SNIPPETS_FILENAME_FOR_ALL_SNIPPETS_DICT		= os.path.join(TEMP_FOLDER, r'snippets_file_for_all_snippets_dict.json')	# only for debug
	CHUNK_ENCODED_FFV1_FILENAME_BASE			= os.path.join(TEMP_FOLDER, r'encoded_chunk_ffv1_')	# the interim encoded video created by the encoding process, to be associated with a snippet dict, full names dynamically created eg "interim_ffv1_0001.mkv"
	
	# Now we need a set of inter-step comms files
	# 1. PREPARATION: 
	# the CONTROLLER calls load_settings.load_settings() and can call a function to do the chunking into a dict and keep it in memory and write a debug copy to CHUNKS_FILENAME_FOR_ALL_CHUNKS_DICT

	# 2. ENCODER : process_video also creating a snippets file ... change the format of the snippets file to exclude the last line with a filename and change the code
	CURRENT_CHUNK_FILENAME						= os.path.join(TEMP_FOLDER, r'current_chunk_file.json') 	# used by the ENCODER to load a file whose .json content gives the ENCODER (a dict of the current chunk, and a filename to be encoded into)
	CURRENT_SNIPPETS_FILENAME					= os.path.join(TEMP_FOLDER, r'current_snippets_file.json') 	# used by the ENCODER to write file whose .json content will be a dict of snippets for this chunk, and a filename/[start/end]-frames of the encoded file)
																											# the file will contain the start/end frame numbers and the fully qualified SOURCE filename for each snippet, and a filename/[start/end-frames] for the encoded file (used in calcs later)
																											# after encoding this chunk is completed, the CONTROLLER loads a dict from this json file, being snippet data for this chunk, and loads into a global dict for tracking
	
	# 3. re-encode all encoded ffv1 chunks into a concatenated AVC .mp4
	# the CONTROLLER keeps track of a list of files created by the encoder with base filenames CHUNK_ENCODED_FFV1_FILENAME_BASE ... encoded_chunk_ffv1_00001.mkv
	# the CONTROLLER re-encodes all these (to avoid timestmp issues) into one large final video without audio
	### INTERIM_VIDEO_MP4_NO_AUDIO_FILENAME			= os.path.join(TEMP_FOLDER, r'slideshow.INTERIM_VIDEO_MP4_NO_AUDIO_FILENAME.mp4')
	#??? INTERIM_VIDEO_MP4_NO_AUDIO_FILENAME not used ?


	# 4. the CONTROLLER does snippet processsing based on snippets written by the encoder per chunk and re-read and placed into a large dict on the fly by the CONTROLLER... 
	#	 use the global snippets dict updated by the fly by the encoding CONTROLLER process
	#	 global frame numbers are now re-calculated after encoding all chunks by processing snippet dicts in sequence and recalculating the global [frame-start/frame-end] pairs for each snippet
	#	 then process snippets into the audio, re-encoding into .aac which can be muxed later.
	#	this process touches the 
	BACKGROUND_AUDIO_INPUT_FILENAME				= fully_qualified_filename(os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'background_audio_pre_snippet_editing.m4a'))
	BACKGROUND_AUDIO_WITH_OVERLAID_SNIPPETS_FILENAME = os.path.join(TEMP_FOLDER, r'background_audio_with_overlaid_snippets.mp4')	# pydyub hates .m4a, so use .mp4

	# 5. the CONTROLLER does Final muxing of the interim video .mp4 and the interim background_audio_post_snippet_editing
	FINAL_MP4_WITH_AUDIO_FILENAME				= fully_qualified_filename(os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'slideshow.FINAL_MP4_WITH_AUDIO_FILENAME.mp4'))

	MAX_FILES_PER_CHUNK							= int(150)
	TOLERANCE_PERCENT_FINAL_CHUNK				= int(20)
	RECURSIVE									= True
	DEBUG										= False if DEBUG==False else True
	FFMPEG_PATH									= fully_qualified_filename(os.path.join(r'.\Vapoursynth_x64', r'ffmpeg.exe'))
	FFPROBE_PATH								= fully_qualified_filename(os.path.join(r'.\Vapoursynth_x64', r'ffprobe.exe'))
	VSPIPE_PATH									= fully_qualified_filename(os.path.join(r'.\Vapoursynth_x64', r'vspipe.exe'))
	
	slideshow_CONTROLLER_path					= fully_qualified_filename(os.path.join(r'.\slideshow_CONTROLLER.py'))
	slideshow_LOAD_SETTINGS_path				= fully_qualified_filename(os.path.join(r'.\slideshow_LOAD_SETTINGS.py'))
	slideshow_ENCODER_legacy_path				= fully_qualified_filename(os.path.join(r'.\slideshow_ENCODER_legacy.vpy'))

	SUBTITLE_DEPTH								= int(0)
	SUBTITLE_FONTSIZE							= int(18)
	SUBTITLE_FONTSCALE							= float(1.0)
	DURATION_PIC_SEC							= float(3.0)
	DURATION_CROSSFADE_SECS						= float(0.5)
	CROSSFADE_TYPE								= r'random'
	CROSSFADE_DIRECTION							= r'left'
	DURATION_MAX_VIDEO_SEC						= float(7200.0)
	DENOISE_SMALL_SIZE_VIDEOS					= True

	TARGET_WIDTH								= int(1920)		# ; "target_width" an integer; set for hd; do not change unless a dire emergency = .
	TARGET_HEIGHT								= int(1080)		# ; "target_height" an integer; set for hd; do not change unless a dire emergency = .
	TARGET_FPSNUM								= int(25)		# ; "target_fpsnum" an integer; set for pal = .
	TARGET_FPSDEN								= int(1)		# ; "target_fpsden" an integer; set for pal = .
	TARGET_BACKGROUND_AUDIO_FREQUENCY			= int(48000) 
	TARGET_BACKGROUND_AUDIO_CHANNELS			= int(2) 
	TARGET_BACKGROUND_AUDIO_BYTEDEPTH			= int(2)		# 2 ; bytes not bits, 2 byte = 16 bit to match pcm_s16le
	TARGET_BACKGROUND_AUDIO_CODEC				= r'libfdk_aac'
	TARGET_BACKGROUND_AUDIO_BITRATE				= r'256k'
	TARGET_AUDIO_NORMALIZE_HEADROOM_DB			= int(-2)		# normalize audio to -xxDB ; pydub calls it headroom

	TEMPORARY_BACKGROUND_AUDIO_CODEC			= r'pcm_s16le'	# ; for 16 bit .wav
	TEMPORARY_AUDIO_FILENAME					= os.path.join(TEMP_FOLDER, r'temporary_audio_file_for_standardization_then_input_to_pydub.wav')	# file is overwritten and deleted as needed

	TARGET_COLORSPACE							= r'BT.709'	# ; "target_colorspace" a string; set for hd; required to render subtitles, it is fixed at this value; this item must match target_colorspace_matrix_i etc = .
	TARGET_COLORSPACE_MATRIX_I					= int(1)	# ; "target_colorspace_matrix_i" an integer; set for hd; this is the value that counts; it is fixed at this value; turn on debug_mode to see lists of these values = .
	TARGET_COLOR_TRANSFER_I						= int(1)	# ; "target_color_transfer_i" an integer; set for hd; this is the value that counts; it is fixed at this value; used by vapoursynth; turn on debug_mode to see lists of these values = .
	TARGET_COLOR_PRIMARIES_I					= int(1)	# ; "target_color_primaries_i" an integer; set for hd; this is the value that counts; it is fixed at this value; turn on debug_mode to see lists of these values = .
	TARGET_COLOR_RANGE_I						= int(0)	# ; "target_color_range_i" an integer; set for full-range, not limited-range; this is the (vapoursynth) value that counts; it is fixed at this value; used by vapoursynth; turn on debug_mode to see lists of these values = .
															# ; "target_color_range_i note: this vapoursynth value is opposite to that needed by zimg and by resizers which require the zimg (the propeer) value; internal transations vs->zimg are done = .
	UPSIZE_KERNEL								= r'Lanczos'	# ; "upsize_kernel" a string; do not change unless a dire emergency; you need the exact string name of the resizer = .
	DOWNSIZE_KERNEL								= r'Spline36'	#; "downsize_kernel" a string; do not change unless a dire emergency; you need the exact string name of the resizer = .
	BOX											= True		# ; "box" is true or false; if true, images and videos are resized vertically/horizontally to maintain aspect ratio and padded; false streches and squeezes  = .

	# compatibility
	_INI_SECTION_NAME							= r'slideshow'	# use in OLD ...  self._default_ini_values = { self._ini_section_name : { ini_value, ini_value, ini_vsalue ...} ... use like: self._ini_values[self._ini_section_name]["TARGET_WIDTH"]
																# then self.calc_ini = self._ini_values[self._ini_section_name] which pops all the settings into calc_ini and used like: self.calc_ini["PIC_EXTENSIONS"]
																# self.calc_ini us a superset of self._ini_values[self._ini_section_name] ... i.e. just {ini_value, ini_value, ...}

	WORKING_PIXEL_FORMAT						= vs.YUV444P8	# int(vs.YUV444P8.value)				# pixel format of the working clips (mainly required by vs_transitions)
	TARGET_PIXEL_FORMAT							= vs.YUV420P8	# int(vs.YUV420P8.value)				# pixel format of the target video
	DG_PIXEL_FORMAT								= vs.YUV420P16	# int(vs.YUV420P16.value)				# pixel format of the video for use by DG tools

	DOT_FFINDEX									= r'.ffindex'.lower()		# for removing temporary *.ffindex files at the end
	MODX										= int(2)	   # mods for letterboxing calculations, example, for 411 YUV as an extreme
	MODY										= int(2)	   # mods would have to be MODX=4, MODY=1 as minimum
	SUBTITLE_MAX_DEPTH							= int(10)
	ROTATION_ANTI_CLOCKWISE						= r'anti-clockwise'.lower()
	ROTATION_CLOCKWISE							= r'clockwise'.lower()
	PRECISION_TOLERANCE							= float(0.0002)	# used in float comarisons eg fps calculations and comparisons so do not have to use "==" which would almost never work

	MIN_ACTUAL_DISPLAY_TIME						= float(0.5)	# seconds

	SNIPPET_AUDIO_FADE_IN_DURATION_MS			= int(500)		# milliseconds of fade for overlaying snippet audio onto background audio
	SNIPPET_AUDIO_FADE_OUT_DURATION_MS			= int(500)		# milliseconds of fade for overlaying snippet audio onto background audio

	# EXTERNAL CONSTANTS ...
	# https://github.com/vapoursynth/vapoursynth/issues/940#issuecomment-1465041338
	# When calling rezisers etc, ONLY use these values:
	#	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
	#	ZIMG_RANGE_FULL	 = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
	# but when obtaining from frame properties and comparing etc, use the vs values from
	# frame properties even though the vapoursynth values are incorrect (opposite to the spec)
	ZIMG_RANGE_LIMITED  = 0		# /**< Studio (TV) legal range, 16-235 in 8 bits. */
	ZIMG_RANGE_FULL	 = 1		# /**< Full (PC) dynamic range, 0-255 in 8 bits. */
	# https://www.vapoursynth.com/doc/apireference.html?highlight=_FieldBased
	VS_INTERLACED = { 'Progressive' : 0, 'BFF' : 1, 'TFF' : 2 }		# vs documentation says frame property _FieldBased is one of 0=frame based (progressive), 1=bottom field first, 2=top field first.

	TARGET_FPS									= None		# CALCULATED LATER :	# = round(self.calc_ini["TARGET_FPSNUM"] / self.calc_ini["TARGET_FPSDEN"], 3)
	DURATION_PIC_FRAMES							= None		# CALCULATED LATER : 	# = int(math.ceil(self.calc_ini["DURATION_PIC_SEC"] * self.calc_ini["TARGET_FPS"]))
	DURATION_CROSSFADE_FRAMES					= None		# CALCULATED LATER : 	# = int(math.ceil(self.calc_ini["DURATION_CROSSFADE_SECS"] * self.calc_ini["TARGET_FPS"]))
	DURATION_BLANK_CLIP_FRAMES					= None		# CALCULATED LATER : 	# = self.calc_ini["DURATION_CROSSFADE_FRAMES"] + 1	# make equal to the display time for an image; DURATION_CROSSFADE_FRAMES will be less than this
	DURATION_MAX_VIDEO_FRAMES					= None		# CALCULATED LATER : 	# = int(math.ceil(self.calc_ini["DURATION_MAX_VIDEO_SEC"] * self.calc_ini["TARGET_FPS"]))
	TARGET_VFR_FPSNUM							= None		# CALCULATED LATER : 	# = self.calc_ini["TARGET_FPSNUM"] * 2
	TARGET_VFR_FPSDEN							= None		# CALCULATED LATER : 	# = self.calc_ini["TARGET_FPSDEN"]
	TARGET_VFR_FPS								= None		# CALCULATED LATER : 	# = self.calc_ini["TARGET_VFR_FPSNUM"] / self.calc_ini["TARGET_VFR_FPSDEN"]	
	TARGET_COLOR_RANGE_I_ZIMG					= None		# CALCULATED LATER : 	# = if something, calculate

	default_settings_dict = {
		'SLIDESHOW_SETTINGS_MODULE_NAME':			SLIDESHOW_SETTINGS_MODULE_NAME,
		'SLIDESHOW_SETTINGS_MODULE_FILENAME':		SLIDESHOW_SETTINGS_MODULE_FILENAME,
		
		'ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS': ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS,	# this is the ONLY file/folder thing in the NEW version that is actually already a LIST
		'ROOT_FOLDER_FOR_OUTPUTS': 					ROOT_FOLDER_FOR_OUTPUTS,
		'TEMP_FOLDER':								TEMP_FOLDER,
		'PIC_EXTENSIONS' :							PIC_EXTENSIONS,
		'VID_EXTENSIONS' :							VID_EXTENSIONS,
		'EEK_EXTENSIONS' :							EEK_EXTENSIONS,
		'VID_EEK_EXTENSIONS':						VID_EEK_EXTENSIONS,
		'EXTENSIONS' :								EXTENSIONS,

		'CHUNKS_FILENAME_FOR_ALL_CHUNKS_DICT': 		CHUNKS_FILENAME_FOR_ALL_CHUNKS_DICT,		# only for debug
		'SNIPPETS_FILENAME_FOR_ALL_SNIPPETS_DICT':	SNIPPETS_FILENAME_FOR_ALL_SNIPPETS_DICT,	# only for debug
		'CHUNK_ENCODED_FFV1_FILENAME_BASE': 		CHUNK_ENCODED_FFV1_FILENAME_BASE,
		'CURRENT_CHUNK_FILENAME':					CURRENT_CHUNK_FILENAME,
		'CURRENT_SNIPPETS_FILENAME': 				CURRENT_SNIPPETS_FILENAME,
		'BACKGROUND_AUDIO_INPUT_FILENAME':			BACKGROUND_AUDIO_INPUT_FILENAME,
		'BACKGROUND_AUDIO_WITH_OVERLAID_SNIPPETS_FILENAME':	BACKGROUND_AUDIO_WITH_OVERLAID_SNIPPETS_FILENAME,
		'FINAL_MP4_WITH_AUDIO_FILENAME':			FINAL_MP4_WITH_AUDIO_FILENAME,

		'MAX_FILES_PER_CHUNK':						MAX_FILES_PER_CHUNK,
		'TOLERANCE_PERCENT_FINAL_CHUNK':			TOLERANCE_PERCENT_FINAL_CHUNK,
		'RECURSIVE':								RECURSIVE,
		'DEBUG':									DEBUG,
		'FFMPEG_PATH':								FFMPEG_PATH,
		'FFPROBE_PATH':								FFPROBE_PATH,
		'VSPIPE_PATH':								VSPIPE_PATH,
		'slideshow_CONTROLLER_path':				slideshow_CONTROLLER_path,
		'slideshow_LOAD_SETTINGS_path':				slideshow_LOAD_SETTINGS_path,
		'slideshow_ENCODER_legacy_path':			slideshow_ENCODER_legacy_path,
		
		'SUBTITLE_DEPTH':							SUBTITLE_DEPTH,
		'SUBTITLE_FONTSIZE':						SUBTITLE_FONTSIZE,
		'SUBTITLE_FONTSCALE':						SUBTITLE_FONTSCALE,
		'DURATION_PIC_SEC':							DURATION_PIC_SEC,
		'DURATION_CROSSFADE_SECS':					DURATION_CROSSFADE_SECS,
		'CROSSFADE_TYPE':							CROSSFADE_TYPE,
		'CROSSFADE_DIRECTION':						CROSSFADE_DIRECTION,
		'DURATION_MAX_VIDEO_SEC':					DURATION_MAX_VIDEO_SEC,
		'DENOISE_SMALL_SIZE_VIDEOS':				DENOISE_SMALL_SIZE_VIDEOS,

		'TARGET_WIDTH':								TARGET_WIDTH,
		'TARGET_HEIGHT':							TARGET_HEIGHT,
		'TARGET_FPSNUM':							TARGET_FPSNUM,
		'TARGET_FPSDEN':							TARGET_FPSDEN,
		'TARGET_BACKGROUND_AUDIO_FREQUENCY':		TARGET_BACKGROUND_AUDIO_FREQUENCY,
		'TARGET_BACKGROUND_AUDIO_CHANNELS':			TARGET_BACKGROUND_AUDIO_CHANNELS,
		'TARGET_BACKGROUND_AUDIO_BYTEDEPTH':		TARGET_BACKGROUND_AUDIO_BYTEDEPTH,
		'TARGET_BACKGROUND_AUDIO_CODEC':			TARGET_BACKGROUND_AUDIO_CODEC,
		'TARGET_BACKGROUND_AUDIO_BITRATE':			TARGET_BACKGROUND_AUDIO_BITRATE,
		'TARGET_AUDIO_NORMALIZE_HEADROOM_DB':		TARGET_AUDIO_NORMALIZE_HEADROOM_DB,

		'TEMPORARY_BACKGROUND_AUDIO_CODEC':			TEMPORARY_BACKGROUND_AUDIO_CODEC,
		'TEMPORARY_AUDIO_FILENAME':					TEMPORARY_AUDIO_FILENAME,

		'TARGET_COLORSPACE':						TARGET_COLORSPACE,
		'TARGET_COLORSPACE_MATRIX_I':				TARGET_COLORSPACE_MATRIX_I,
		'TARGET_COLOR_TRANSFER_I':					TARGET_COLOR_TRANSFER_I,
		'TARGET_COLOR_PRIMARIES_I':					TARGET_COLOR_PRIMARIES_I,
		'TARGET_COLOR_RANGE_I':						TARGET_COLOR_RANGE_I,
		'UPSIZE_KERNEL':							UPSIZE_KERNEL,
		'DOWNSIZE_KERNEL':							DOWNSIZE_KERNEL,
		'BOX':										BOX,

		'_INI_SECTION_NAME':						_INI_SECTION_NAME,

		'WORKING_PIXEL_FORMAT':						WORKING_PIXEL_FORMAT,
		'TARGET_PIXEL_FORMAT':						TARGET_PIXEL_FORMAT,
		'DG_PIXEL_FORMAT':							DG_PIXEL_FORMAT,
		'DOT_FFINDEX':								DOT_FFINDEX,
		'MODX':										MODX,
		'MODY':										MODY,
		'SUBTITLE_MAX_DEPTH':						SUBTITLE_MAX_DEPTH,	
		'ROTATION_ANTI_CLOCKWISE':					ROTATION_ANTI_CLOCKWISE,
		'ROTATION_CLOCKWISE':						ROTATION_CLOCKWISE,
		'PRECISION_TOLERANCE':						PRECISION_TOLERANCE,
		'MIN_ACTUAL_DISPLAY_TIME':					MIN_ACTUAL_DISPLAY_TIME,

		'SNIPPET_AUDIO_FADE_IN_DURATION_MS':		SNIPPET_AUDIO_FADE_IN_DURATION_MS,
		'SNIPPET_AUDIO_FADE_OUT_DURATION_MS':		SNIPPET_AUDIO_FADE_OUT_DURATION_MS,

		'ZIMG_RANGE_LIMITED':						ZIMG_RANGE_LIMITED,	# = 0		# /**< Studio (TV) legal range, 16-235 in 8 bits. */
		'ZIMG_RANGE_FULL':							ZIMG_RANGE_FULL,	# = 1		# /**< Full (PC) dynamic range, 0-255 in 8 bits. */
		'VS_INTERLACED':							VS_INTERLACED,		# = { 'Progressive' : 0, 'BFF' : 1, 'TFF' : 2 }		# vs documnetation says frame property _FieldBased is one of 0=frame based (progressive), 1=bottom field first, 2=top field first.

		# placeholders for calculated values - calculated after reading in the user-specified JSON
		'TARGET_FPS':								TARGET_FPS,					# CALCULATED LATER # = round(self.calc_ini["TARGET_FPSNUM"] / self.calc_ini["TARGET_FPSDEN"], 3)
		'DURATION_PIC_FRAMES':						DURATION_PIC_FRAMES,		# CALCULATED LATER # = int(math.ceil(self.calc_ini["DURATION_PIC_SEC"] * self.calc_ini["TARGET_FPS"]))
		'DURATION_CROSSFADE_FRAMES':				DURATION_CROSSFADE_FRAMES,	# CALCULATED LATER # = int(math.ceil(self.calc_ini["DURATION_CROSSFADE_SECS"] * self.calc_ini["TARGET_FPS"]))
		'DURATION_BLANK_CLIP_FRAMES':				DURATION_BLANK_CLIP_FRAMES,	# CALCULATED LATER # = self.calc_ini["DURATION_CROSSFADE_FRAMES"] + 1	# make equal to the display time for an image; DURATION_CROSSFADE_FRAMES will be less than this
		'DURATION_MAX_VIDEO_FRAMES':				DURATION_MAX_VIDEO_FRAMES,	# CALCULATED LATER # = int(math.ceil(self.calc_ini["DURATION_MAX_VIDEO_SEC"] * self.calc_ini["TARGET_FPS"]))
		'TARGET_VFR_FPSNUM':						TARGET_VFR_FPSNUM,			# CALCULATED LATER # = self.calc_ini["TARGET_FPSNUM"] * 2
		'TARGET_VFR_FPSDEN':						TARGET_VFR_FPSDEN,			# CALCULATED LATER # = self.calc_ini["TARGET_FPSDEN"]
		'TARGET_VFR_FPS':							TARGET_VFR_FPS,				# CALCULATED LATER # = self.calc_ini["TARGET_VFR_FPSNUM"] / self.calc_ini["TARGET_VFR_FPSDEN"]	
		'TARGET_COLOR_RANGE_I_ZIMG':				TARGET_COLOR_RANGE_I_ZIMG,	# CALCULATED LATER # = if something, calculated
	}

	if DEBUG:	print(f'DEBUG: created default_settings_dict=\n{objPrettyPrint.pformat(default_settings_dict)}',flush=True)

	#######################################################################################################################################
	#######################################################################################################################################
	
	if not os.path.exists(SLIDESHOW_SETTINGS_MODULE_FILENAME):
		specially_formatted_settings_list =	[
										[ 'ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS',	ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS,	r'a list, one or more folders to look in for slideshow pics/videos. the r in front of the string is CRITICAL' ],
										[ 'RECURSIVE',									RECURSIVE,									r'case sensitive: whether to recurse the source folder(s) looking for slideshow pics/videos' ],
										[ 'ROOT_FOLDER_FOR_OUTPUTS', 					ROOT_FOLDER_FOR_OUTPUTS,					r'folder in which outputs are to be placed' ],
										[ 'TEMP_FOLDER',								TEMP_FOLDER,								r'folder where temporary files go; USE A DISK WITH LOTS OF SPARE DISK SPACE - CIRCA 6 GB PER 100 PICS/VIDEOS' ],
										[ 'BACKGROUND_AUDIO_INPUT_FILENAME',			BACKGROUND_AUDIO_INPUT_FILENAME,			r'Use the word None to generate a silence background, or specify a .m4a audio file if you want a background track (it is not looped if too short)' ],
										[ 'FINAL_MP4_WITH_AUDIO_FILENAME',				FINAL_MP4_WITH_AUDIO_FILENAME,				r'the filename of the FINAL slideshow .mp4' ],
										[ 'SUBTITLE_DEPTH',								SUBTITLE_DEPTH,								r'how many folders deep to display in subtitles; use 0 for no subtitling' ],
										[ 'SUBTITLE_FONTSIZE',							SUBTITLE_FONTSIZE,							r'fontsize for subtitles, leave this alone unless confident' ],
										[ 'SUBTITLE_FONTSCALE',							SUBTITLE_FONTSCALE,							r'fontscale for subtitles, leave this alone unless confident' ],
										[ 'DURATION_PIC_SEC',							DURATION_PIC_SEC,							r'in seconds, duration each pic is shown in the slideshow' ],
										[ 'DURATION_CROSSFADE_SECS',					DURATION_CROSSFADE_SECS,					r'in seconds duration crossfade between pic, leave this alone unless confident' ],
										[ 'CROSSFADE_TYPE',								CROSSFADE_TYPE,								r'random is a good choice, leave this alone unless confident' ],
										[ 'CROSSFADE_DIRECTION',						CROSSFADE_DIRECTION,						r'Please leave this alone unless really confident' ],
										[ 'DURATION_MAX_VIDEO_SEC',						DURATION_MAX_VIDEO_SEC,						r'in seconds, maximum duration each video clip is shown in the slideshow' ],
										[ 'TARGET_AUDIO_NORMALIZE_HEADROOM_DB',			TARGET_AUDIO_NORMALIZE_HEADROOM_DB,			r'normalize audios to this maximum db' ],
										[ 'DEBUG',										DEBUG,										r'see and regret seeing, ginormous debug output' ],
										[ 'FFMPEG_PATH',								FFMPEG_PATH,								r'Please leave this alone unless really confident' ],
										[ 'FFPROBE_PATH',								FFPROBE_PATH,								r'Please leave this alone unless really confident' ],
										[ 'VSPIPE_PATH',								VSPIPE_PATH,								r'Please leave this alone unless really confident' ],
										[ 'slideshow_CONTROLLER_path',					slideshow_CONTROLLER_path,					r'Please leave this alone unless really confident' ],
										[ 'slideshow_LOAD_SETTINGS_path',				slideshow_LOAD_SETTINGS_path,				r'Please leave this alone unless really confident' ],
										[ 'slideshow_ENCODER_legacy_path',				slideshow_ENCODER_legacy_path,				r'Please leave this alone unless really confident' ],
									]	
		if DEBUG:	print(f'DEBUG: specially_formatted_settings_list=\n{objPrettyPrint.pformat(specially_formatted_settings_list)}',flush=True)
		print(f"load_settings: ERROR: File '{SLIDESHOW_SETTINGS_MODULE_FILENAME}' does not exist, creating it with template settings... you MUST edit it now ...",flush=True,file=sys.stderr)
		create_py_file_from_specially_formatted_list(SLIDESHOW_SETTINGS_MODULE_FILENAME, specially_formatted_settings_list)
		sys.exit(1)

	#######################################################################################################################################
	#######################################################################################################################################

	# read the user-edited settings from SLIDESHOW_SETTINGS_MODULE_NAME (SLIDESHOW_SETTINGS.py)
	if SLIDESHOW_SETTINGS_MODULE_NAME not in sys.modules:
		if DEBUG:	print(f'DEBUG: SLIDESHOW_SETTINGS_MODULE_NAME not in sys.modules',flush=True)
		# Import the module dynamically, if it is not done already
		try:
			if DEBUG:	print(f'DEBUG: importing SLIDESHOW_SETTINGS_MODULE_NAME={SLIDESHOW_SETTINGS_MODULE_NAME} dynamically',flush=True)
			#importlib.invalidate_caches()
			SETTINGS_MODULE = importlib.import_module(SLIDESHOW_SETTINGS_MODULE_NAME)
		except ImportError as e:
			# Handle the ImportError if the module cannot be imported
			print(f"load_settings: ERROR: ImportError, failed to dynamically import user specified Settings from import module: '{SLIDESHOW_SETTINGS_MODULE_NAME}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		except Exception as e:
			print(f"load_settings: ERROR: Exception, failed to dynamically import user specified Settings from import module: '{SLIDESHOW_SETTINGS_MODULE_NAME}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
	else:
		if DEBUG:	print(f'DEBUG: SLIDESHOW_SETTINGS_MODULE_NAME IS in sys.modules',flush=True)
		# Reload the module since it had been dynamically loaded already ... remember, global variables in thee module are not scrubbed by reloading
		try:
			if DEBUG:	print(f'DEBUG: reloading SETTINGS_MODULE={SETTINGS_MODULE} ',flush=True)
			#importlib.invalidate_caches()
			importlib.reload(SETTINGS_MODULE)
		except Exception as e:
			print(f"load_settings: ERROR: Exception, failed to RELOAD user specified Settings from import module: '{SLIDESHOW_SETTINGS_MODULE_NAME}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)
	
	#print(f'DEBUG: before import slideshow_settings.py static',flush=True)
	#import slideshow_settings
	#user_specified_settings_dict = slideshow_settings.settings
	#print(f'DEBUG: after import slideshow_settings.py static',flush=True)

	# retrieve the settigns from SLIDESHOW_SETTINGS_MODULE_NAME (SLIDESHOW_SETTINGS.py)
	if DEBUG:	print(f"DEBUG: Attempting to load user_specified_settings_dict = SETTINGS_MODULE.settings'",flush=True)
	try:
		user_specified_settings_dict = SETTINGS_MODULE.settings
	except Exception as e:
		print(f"load_settings: ERROR: Exception, failed to execute 'user_specified_settings_dict = SETTINGS_MODULE.settings'\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	print(f'Successfully loaded user_specified_settings_dict=\n{objPrettyPrint.pformat(user_specified_settings_dict)}',flush=True)

	#######################################################################################################################################
	#######################################################################################################################################

	# x = {**y, **z} creates a new dictionary. Similar to the dict.update method,
	# if both dictionaries has the same key with different values,
	# then the final output will contain the value of the second dictionary. 
	final_settings_dict = {**default_settings_dict, **user_specified_settings_dict}	
	# FOR NOW, NOT USING THIS METHOD:
	#		create a new dict in which user settings dict items overwrite the defaults dict
	#		final_settings_dict = default_settings_dict
	#		final_settings_dict.update(user_specified)	# updates a dictiony in-place

	if final_settings_dict['DEBUG']: DEBUG = True

	# format  proper paths for folders and files ...
	#
	# process a LIST ... make ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS list entries all fully qualified and escaped where required
	ddl_fully_qualified = []									
	for ddl in final_settings_dict['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS']:
		ddl_fully_qualified.append(fully_qualified_directory_no_trailing_backslash(ddl))
	final_settings_dict['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS'] = ddl_fully_qualified
	#
	final_settings_dict['SLIDESHOW_SETTINGS_MODULE_NAME'] = final_settings_dict['SLIDESHOW_SETTINGS_MODULE_NAME']
	final_settings_dict['SLIDESHOW_SETTINGS_MODULE_FILENAME'] = fully_qualified_filename(final_settings_dict['SLIDESHOW_SETTINGS_MODULE_FILENAME'])
	
	final_settings_dict['ROOT_FOLDER_FOR_OUTPUTS'] = fully_qualified_directory_no_trailing_backslash(final_settings_dict['ROOT_FOLDER_FOR_OUTPUTS'])
	final_settings_dict['TEMP_FOLDER'] = fully_qualified_directory_no_trailing_backslash(final_settings_dict['TEMP_FOLDER'])

	final_settings_dict['CHUNKS_FILENAME_FOR_ALL_CHUNKS_DICT'] = fully_qualified_filename(final_settings_dict['CHUNKS_FILENAME_FOR_ALL_CHUNKS_DICT'])
	final_settings_dict['SNIPPETS_FILENAME_FOR_ALL_SNIPPETS_DICT'] = fully_qualified_filename(final_settings_dict['SNIPPETS_FILENAME_FOR_ALL_SNIPPETS_DICT'])
	final_settings_dict['CHUNK_ENCODED_FFV1_FILENAME_BASE'] = fully_qualified_filename(final_settings_dict['CHUNK_ENCODED_FFV1_FILENAME_BASE'])
	final_settings_dict['CURRENT_CHUNK_FILENAME'] = fully_qualified_filename(final_settings_dict['CURRENT_CHUNK_FILENAME'])
	final_settings_dict['CURRENT_SNIPPETS_FILENAME'] = fully_qualified_filename(final_settings_dict['CURRENT_SNIPPETS_FILENAME'])

	final_settings_dict['BACKGROUND_AUDIO_INPUT_FILENAME'] = fully_qualified_filename(final_settings_dict['BACKGROUND_AUDIO_INPUT_FILENAME'])
	final_settings_dict['BACKGROUND_AUDIO_WITH_OVERLAID_SNIPPETS_FILENAME'] = fully_qualified_filename(final_settings_dict['BACKGROUND_AUDIO_WITH_OVERLAID_SNIPPETS_FILENAME'])
	final_settings_dict['FINAL_MP4_WITH_AUDIO_FILENAME'] = fully_qualified_filename(final_settings_dict['FINAL_MP4_WITH_AUDIO_FILENAME'])

	final_settings_dict['FFMPEG_PATH'] = fully_qualified_filename(final_settings_dict['FFMPEG_PATH'])
	final_settings_dict['FFPROBE_PATH'] = fully_qualified_filename(final_settings_dict['FFPROBE_PATH'])
	final_settings_dict['VSPIPE_PATH'] = fully_qualified_filename(final_settings_dict['VSPIPE_PATH'])

	final_settings_dict['slideshow_CONTROLLER_path'] = fully_qualified_filename(final_settings_dict['slideshow_CONTROLLER_path'])
	final_settings_dict['slideshow_LOAD_SETTINGS_path'] = fully_qualified_filename(final_settings_dict['slideshow_LOAD_SETTINGS_path'])
	final_settings_dict['slideshow_ENCODER_legacy_path'] = fully_qualified_filename(final_settings_dict['slideshow_ENCODER_legacy_path'])

	final_settings_dict['TEMPORARY_AUDIO_FILENAME'] = fully_qualified_filename(final_settings_dict['TEMPORARY_AUDIO_FILENAME'])	# file is overwritten and deleted as needed

	check_file_exists_3333(final_settings_dict['FFMPEG_PATH'], r'FFMPEG_PATH')
	check_file_exists_3333(final_settings_dict['FFPROBE_PATH'], r'FFPROBE_PATH')
	check_file_exists_3333(final_settings_dict['VSPIPE_PATH'], r'VSPIPE_PATH')
	check_file_exists_3333(final_settings_dict['slideshow_CONTROLLER_path'], r'slideshow_CONTROLLER_path')
	check_file_exists_3333(final_settings_dict['slideshow_LOAD_SETTINGS_path'], r'slideshow_LOAD_SETTINGS_path')
	check_file_exists_3333(final_settings_dict['slideshow_ENCODER_legacy_path'], r'slideshow_ENCODER_legacy_path')

	if final_settings_dict['BACKGROUND_AUDIO_INPUT_FILENAME'] is not None:	# allow None for a silence background to be generated
		check_file_exists_3333(final_settings_dict['BACKGROUND_AUDIO_INPUT_FILENAME'], r'BACKGROUND_AUDIO_INPUT_FILENAME')
	
	# check the folders which should exist do exist
	# 1. check the folders in this LIST
	for ddl in final_settings_dict['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS']:
		check_folder_exists_3333(ddl, r'ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS')
	# 2. now check the other folders
	check_folder_exists_3333(final_settings_dict['ROOT_FOLDER_FOR_OUTPUTS'], r'ROOT_FOLDER_FOR_OUTPUTS')

	# if the TEMP_FOLDER folder does not exist, try to create it
	if not os.path.isdir(final_settings_dict['TEMP_FOLDER']):
		try:
			os.makedirs(final_settings_dict['TEMP_FOLDER'])
		except Exception as e:
			print(f"load_settings: ERROR: creating TEMP_FOLDER '{final_settings_dict['TEMP_FOLDER']}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		print(f'load_settings: created TEMP_FOLDER "{final_settings_dict["TEMP_FOLDER"]}"',flush=True)

	# Check for out-of-spec values
	# for now, no validation checking of values ...

	# Consistency checks
	if (2 * final_settings_dict['DURATION_CROSSFADE_SECS'] ) + final_settings_dict['MIN_ACTUAL_DISPLAY_TIME'] > final_settings_dict['DURATION_PIC_SEC']:
		raise ValueError(f'load_settings: ERROR:  calculate_settings: ERROR: DURATION_PIC_SEC must be >= (2 * DURATION_CROSSFADE_SECS) + MIN_ACTUAL_DISPLAY_TIME \n\ DURATION_CROSSFADE_SECS={final_settings_dict["DURATION_CROSSFADE_SECS"] } DURATION_PIC_SEC={final_settings_dict["DURATION_PIC_SEC"]} MIN_ACTUAL_DISPLAY_TIME={final_settings_dict["MIN_ACTUAL_DISPLAY_TIME"]}')
	if (2 * final_settings_dict['DURATION_CROSSFADE_SECS'] ) + final_settings_dict['MIN_ACTUAL_DISPLAY_TIME'] > final_settings_dict['DURATION_MAX_VIDEO_SEC']:
		raise ValueError(f'load_settings: ERROR:  calculate_settings: ERROR: DURATION_MAX_VIDEO_SEC must be >= (2 * DURATION_CROSSFADE_SECS) + MIN_ACTUAL_DISPLAY_TIME \n\ DURATION_CROSSFADE_SECS={final_settings_dict["DURATION_CROSSFADE_SECS"] } DURATION_MAX_VIDEO_SEC={final_settings_dict["DURATION_MAX_VIDEO_SEC"]} MIN_ACTUAL_DISPLAY_TIME={final_settings_dict["MIN_ACTUAL_DISPLAY_TIME"]}')

	# Perform calculations based on updated inputs then updated the dict default_settings_dict
	final_settings_dict['TARGET_FPS']						= round(final_settings_dict['TARGET_FPSNUM'] / final_settings_dict['TARGET_FPSDEN'], 3)
	final_settings_dict['DURATION_PIC_FRAMES']				= int(math.ceil(final_settings_dict['DURATION_PIC_SEC'] * final_settings_dict['TARGET_FPS']))
	final_settings_dict['DURATION_CROSSFADE_FRAMES']		= int(math.ceil(final_settings_dict['DURATION_CROSSFADE_SECS'] * final_settings_dict['TARGET_FPS']))
	final_settings_dict['DURATION_BLANK_CLIP_FRAMES']		= final_settings_dict['DURATION_CROSSFADE_FRAMES'] + 1	# make equal to the display time for an image; DURATION_CROSSFADE_FRAMES will be less than this
	final_settings_dict['DURATION_MAX_VIDEO_FRAMES']		= int(math.ceil(final_settings_dict['DURATION_MAX_VIDEO_SEC'] * final_settings_dict['TARGET_FPS']))
	final_settings_dict['TARGET_VFR_FPSNUM']				= final_settings_dict['TARGET_FPSNUM'] * 2
	final_settings_dict['TARGET_VFR_FPSDEN']				= final_settings_dict['TARGET_FPSDEN']
	final_settings_dict['TARGET_VFR_FPS']					= final_settings_dict['TARGET_VFR_FPSNUM'] / final_settings_dict['TARGET_VFR_FPSDEN']
	# https://github.com/vapoursynth/vapoursynth/issues/940#issuecomment-1465041338
	# When calling rezisers etc, ONLY use these values:
	#	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
	#	ZIMG_RANGE_FULL	 = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
	# but when obtaining from frame properties and comparing etc, use the vs values from
	# frame properties even though the vapoursynth values are incorrect (opposite to the spec)
	# https://www.vapoursynth.com/doc/api/vapoursynth.h.html#enum-vspresetformat
	if final_settings_dict['TARGET_COLOR_RANGE_I'] == int(vs.ColorRange.RANGE_LIMITED.value):
		final_settings_dict['TARGET_COLOR_RANGE_I_ZIMG'] = ZIMG_RANGE_LIMITED					# use the ZIMG RANGE constants as they are correct and vapoursynth ones are not (opposite to the spec)
	elif final_settings_dict['TARGET_COLOR_RANGE_I'] == int(vs.ColorRange.RANGE_FULL.value):
		final_settings_dict['TARGET_COLOR_RANGE_I_ZIMG'] = ZIMG_RANGE_FULL						# use the ZIMG RANGE constants as they are correct and vapoursynth ones are not (opposite to the spec)
	else:
		raise ValueError(f'load_settings: ERROR: "TARGET_COLOR_RANGE_I"={TARGET_COLOR_RANGE_I} is an invalid value')

	# insert calcuated values into default_settings_dict
	#default_settings_dict['TARGET_FPS']						= final_settings_dict['TARGET_FPS']
	#default_settings_dict['DURATION_PIC_FRAMES']			= final_settings_dict['DURATION_PIC_FRAMES']
	#default_settings_dict['DURATION_CROSSFADE_FRAMES']		= final_settings_dict['DURATION_CROSSFADE_FRAMES']
	#default_settings_dict['DURATION_BLANK_CLIP_FRAMES']		= final_settings_dict['DURATION_BLANK_CLIP_FRAMES']
	#default_settings_dict['DURATION_MAX_VIDEO_FRAMES']		= final_settings_dict['DURATION_MAX_VIDEO_FRAMES']
	#default_settings_dict['TARGET_VFR_FPSNUM']				= final_settings_dict['TARGET_VFR_FPSNUM']
	#default_settings_dict['TARGET_VFR_FPSDEN']				= final_settings_dict['TARGET_VFR_FPSDEN']
	#default_settings_dict['TARGET_VFR_FPS']					= final_settings_dict['TARGET_VFR_FPS']
	#default_settings_dict['TARGET_COLOR_RANGE_I_ZIMG']		= final_settings_dict['TARGET_COLOR_RANGE_I_ZIMG']

	# now  MAP these back into format/names compatible with the OLD calc_ini["SETTING_NAME"]
	# "case" of keys is important
	old_calc_ini_dict =	{	'DIRECTORY_LIST' :					final_settings_dict['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS'],	# This is already a list []
							'TEMP_DIRECTORY' :					final_settings_dict['TEMP_FOLDER'],
							'TEMP_DIRECTORY_LIST' :				[ final_settings_dict['TEMP_FOLDER'] ],
							'CURRENT_CHUNK_FILENAME' :			final_settings_dict['CURRENT_CHUNK_FILENAME'],		# ADDED	for encoder; no need, it should use final_settings_dict for this
							'CURRENT_SNIPPETS_FILENAME' :		final_settings_dict['CURRENT_SNIPPETS_FILENAME'],	# ADDED	for encoder; no need, it should use final_settings_dict for this
							'RECURSIVE' :						final_settings_dict['RECURSIVE'],
							'SUBTITLE_DEPTH' :					final_settings_dict['SUBTITLE_DEPTH'],
							'SUBTITLE_FONTSIZE' :				final_settings_dict['SUBTITLE_FONTSIZE'],
							'SUBTITLE_FONTSCALE' :				final_settings_dict['SUBTITLE_FONTSCALE'],
							'DURATION_PIC_SEC' :				final_settings_dict['DURATION_PIC_SEC'],
							'DURATION_CROSSFADE_SECS' :			final_settings_dict['DURATION_CROSSFADE_SECS'],
							'CROSSFADE_TYPE' :					final_settings_dict['CROSSFADE_TYPE'],
							'CROSSFADE_DIRECTION' :				final_settings_dict['CROSSFADE_DIRECTION'],
							'DURATION_MAX_VIDEO_SEC' :			final_settings_dict['DURATION_MAX_VIDEO_SEC'],
							'DENOISE_SMALL_SIZE_VIDEOS' :		final_settings_dict['DENOISE_SMALL_SIZE_VIDEOS'],
							'DEBUG_MODE' :						final_settings_dict['DEBUG'],
							'TARGET_COLORSPACE' :				final_settings_dict['TARGET_COLORSPACE'],
							'TARGET_COLORSPACE_MATRIX_I' :		final_settings_dict['TARGET_COLORSPACE_MATRIX_I'],
							'TARGET_COLOR_TRANSFER_I' :			final_settings_dict['TARGET_COLOR_TRANSFER_I'],
							'TARGET_COLOR_PRIMARIES_I' :		final_settings_dict['TARGET_COLOR_PRIMARIES_I'],
							'TARGET_COLOR_RANGE_I' :			final_settings_dict['TARGET_COLOR_RANGE_I'],
							'TARGET_WIDTH' :					final_settings_dict['TARGET_WIDTH'],
							'TARGET_HEIGHT' :					final_settings_dict['TARGET_HEIGHT'],
							'TARGET_FPSNUM' :					final_settings_dict['TARGET_FPSNUM'],
							'TARGET_FPSDEN' :					final_settings_dict['TARGET_FPSDEN'],
							'UPSIZE_KERNEL' :					final_settings_dict['UPSIZE_KERNEL'],
							'DOWNSIZE_KERNEL' :					final_settings_dict['DOWNSIZE_KERNEL'],
							'BOX' :								final_settings_dict['BOX'],
							'PIC_EXTENSIONS':					final_settings_dict['PIC_EXTENSIONS'],
							'VID_EXTENSIONS':					final_settings_dict['VID_EXTENSIONS'],
							'EEK_EXTENSIONS':					final_settings_dict['EEK_EXTENSIONS'],
							'VID_EEK_EXTENSIONS':				final_settings_dict['VID_EEK_EXTENSIONS'],
							'EXTENSIONS':						final_settings_dict['EXTENSIONS'],
							'WORKING_PIXEL_FORMAT':				final_settings_dict['WORKING_PIXEL_FORMAT'],
							'TARGET_PIXEL_FORMAT':				final_settings_dict['TARGET_PIXEL_FORMAT'],
							'DG_PIXEL_FORMAT':					final_settings_dict['DG_PIXEL_FORMAT'],
							'TARGET_FPS':						final_settings_dict['TARGET_FPS'],
							'DURATION_PIC_FRAMES':				final_settings_dict['DURATION_PIC_FRAMES'],
							'DURATION_CROSSFADE_FRAMES':		final_settings_dict['DURATION_CROSSFADE_FRAMES'],
							'DURATION_BLANK_CLIP_FRAMES':		final_settings_dict['DURATION_BLANK_CLIP_FRAMES'],
							'DURATION_MAX_VIDEO_FRAMES':		final_settings_dict['DURATION_MAX_VIDEO_FRAMES'],
							'MODX':								final_settings_dict['MODX'],
							'MODY':								final_settings_dict['MODY'],
							'SUBTITLE_MAX_DEPTH':				final_settings_dict['SUBTITLE_MAX_DEPTH'],
							'Rotation_anti_clockwise':			final_settings_dict['ROTATION_ANTI_CLOCKWISE'],
							'Rotation_clockwise':				final_settings_dict['ROTATION_CLOCKWISE'],
							'TARGET_VFR_FPSNUM':				final_settings_dict['TARGET_VFR_FPSNUM'],
							'TARGET_VFR_FPSDEN':				final_settings_dict['TARGET_VFR_FPSDEN'],
							'TARGET_VFR_FPS':					final_settings_dict['TARGET_VFR_FPS'],
							'TARGET_VFR_FPSNUM':				final_settings_dict['TARGET_VFR_FPSNUM'],
							'TARGET_VFR_FPSDEN':				final_settings_dict['TARGET_VFR_FPSDEN'],
							'TARGET_VFR_FPS':					final_settings_dict['TARGET_VFR_FPS'],
							'precision_tolerance':				final_settings_dict['PRECISION_TOLERANCE'],				# the only one that is a lowercase ley
							'TARGET_COLOR_RANGE_I_ZIMG':		final_settings_dict['TARGET_COLOR_RANGE_I_ZIMG'],
						}

	# MAP that back into something compatible with OLD '_ini_values[self._ini_section_name]["SETTING_NAME"]'
	old_ini_dict = { final_settings_dict['_INI_SECTION_NAME']: old_calc_ini_dict }

	# now save debug versions of those dicts
	if DEBUG:
		try:
			f_debug = fully_qualified_filename(os.path.join(TEMP_FOLDER, SLIDESHOW_SETTINGS_MODULE_NAME + r'.DEBUG.user_settings.JSON'))
			with open(f_debug, 'w') as fp:
				json.dump(user_specified_settings_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		#
		try:
			f_debug = fully_qualified_filename(os.path.join(TEMP_FOLDER, SLIDESHOW_SETTINGS_MODULE_NAME + r'.DEBUG.default_settings.JSON'))
			with open(f_debug, 'w') as fp:
				json.dump(default_settings_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		#
		try:
			f_debug = fully_qualified_filename(os.path.join(TEMP_FOLDER, SLIDESHOW_SETTINGS_MODULE_NAME + r'.DEBUG.final_settings.JSON'))
			with open(f_debug, 'w') as fp:
				json.dump(final_settings_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		#
		try:
			f_debug = fully_qualified_filename(os.path.join(TEMP_FOLDER, SLIDESHOW_SETTINGS_MODULE_NAME + r'.DEBUG.old_ini_dict.JSON'))
			with open(f_debug, 'w') as fp:
				json.dump(old_ini_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		#
		try:
			f_debug = fully_qualified_filename(os.path.join(TEMP_FOLDER, SLIDESHOW_SETTINGS_MODULE_NAME + r'.DEBUG.old_calc_ini_dict.JSON'))
			with open(f_debug, 'w') as fp:
				json.dump(old_calc_ini_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	

	return final_settings_dict, old_ini_dict, old_calc_ini_dict, user_specified_settings_dict

