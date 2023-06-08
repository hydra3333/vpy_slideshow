import vapoursynth as vs
from vapoursynth import core
core = vs.core
import sys
import os
import re
from functools import partial
import pathlib
from pathlib import Path, PureWindowsPath
import datetime
from datetime import datetime, date, time, timezone
from fractions import Fraction
from collections import defaultdict, OrderedDict
from enum import Enum
from enum import auto
import itertools
import math
import yaml
import json
import pprint
import uuid
import logging
#
global DEBUG
DEBUG = False
TERMINAL_WIDTH_3333 = 250
objPrettyPrint_3333 = pprint.PrettyPrinter(width=TERMINAL_WIDTH_3333, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc

def normalize_path_3333(path):
	#if DEBUG: print(f"DEBUG: normalize_path_3333:  incoming path='{path}'",flush=True)
	# Replace single backslashes with double backslashes
	path = path.rstrip(os.linesep).strip('\r').strip('\n').strip()
	r1 = r'\\'
	r2 = r1 + r1
	r4 = r2 + r2
	path = path.replace(r1, r4)
	# Add double backslashes before any single backslashes
	for i in range(0,20):
		path = path.replace(r2, r1)
	if DEBUG: print(f"DEBUG: normalize_path_3333: outgoing path='{path}'",flush=True)
	return path

def fully_qualified_directory_no_trailing_backslash_3333(directory_name):
	# make into a fully qualified directory string stripped and without a trailing backslash
	# also remove extraneous backslashes which get added by things like abspath
	new_directory_name = os.path.abspath(directory_name).rstrip(os.linesep).strip('\r').strip('\n').strip()
	if directory_name[-1:] == (r'\ '.strip()):		# r prefix means the string is treated as a raw string so all escape codes will be ignored. EXCEPT IF THE \ IS THE LAST CHARACTER IN THE STRING !
		new_directory_name = directory_name[:-1]	# remove any trailing backslash
	new_directory_name = normalize_path_3333(new_directory_name)
	return new_directory_name

def fully_qualified_filename_3333(file_name):
	# Make into a fully qualified filename string using double backslashes
	# to later print/write with double backslashes use eg
	#	converted_string = fully_qualified_filename_3333('D:\\a\\b\\\\c\\\\\\d\\e\\f\\filename.txt')
	#	print(repr(converted_string),flush=True)
	# yields 'D:\\a\\b\\c\\d\\e\\f\\filename.txt'
	new_file_name = os.path.abspath(file_name).rstrip(os.linesep).strip('\r').strip('\n').strip()
	if new_file_name.endswith('\\'):
		new_file_name = new_file_name[:-1]  # Remove trailing backslash
	new_file_name = normalize_path_3333(new_file_name)
	return new_file_name

#
def load_settings(filename=".\\settings_3333.json"):
	# Settings_filename is always "fixed" in the same place as the script is run from, 
	# A filename parameter is provided for convenience and testing, however the default is ".\\settings_3333.json"
	# A dict is returned with all of the settings in it, missing values are defaulted, yield calculated ones as well.

	# This is ALWAYS a fixed filename in the current default folder !!!
	SLIDESHOW_SETTINGS_FILE						= os.path.join(r'.', 'SLIDESHOW_SETTINGS.JSON')

	ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS	= [ r'.' ]
	ROOT_FOLDER_FOR_OUTPUTS						= r'.'
	TEMP_FOLDER									= os.path.join(r'.', 'TEMP')
	PIC_EXTENSIONS								= [ r'.png', r'.jpg', r'.jpeg', r'.gif' ]
	VID_EXTENSIONS								= [ r'.mp4', r'.mpeg4', r'.mpg', r'.mpeg', r'.avi', r'.mjpeg', r'.3gp', r'.mov' ]
	EEK_EXTENSIONS								= [ r'.m2ts' ]
	VID_EEK_EXTENSIONS							= VID_EXTENSIONS + EEK_EXTENSIONS
	EXTENSIONS									= PIC_EXTENSIONS + VID_EXTENSIONS + EEK_EXTENSIONS
	CHUNKS_OUTPUT_FILE_ALL_CHUNKS				= os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'001_preparation.all_chunks.json')
	CHUNKS_OUTPUT_FILES_COMMON_NAME				= os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'001_preparation.chunk_')
	CHUNKS_OUTPUT_FILES_COMMON_NAME_GLOB		= os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'001_preparation.chunk_*.json')
	PER_CHUNK_LIST_OF_SNIPPET_FILES				= os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'001_preparation.PER_CHUNK_LIST_OF_SNIPPET_FILES.json')
	BACKGROUND_AUDIO_INPUT_FILE					= os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'pre_editing_background_audio_input.m4a')
	FINAL_OUTPUT_MP4_FILE						= os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'vpy_slideshow.FINAL_MUXED_SLIDESHOW.mp4')
	MAX_VIDEO_FILES_PER_CHUNK					= int(150)
	TOLERANCE_PERCENT_FINAL_CHUNK				= int(20)
	RECURSIVE									= True
	DEBUG										= False
	FFMPEG_PATH									= os.path.join(r'.', r'ffmpeg.exe')

	SUBTITLE_DEPTH								= float(0)
	SUBTITLE_FONTSIZE							= float(18)
	SUBTITLE_FONTSCALE							= float(1.0)
	DURATION_PIC_SEC							= float(3.0)
	DURATION_CROSSFADE_SECS						= float(0.5)
	CROSSFADE_TYPE								= r'random'
	CROSSFADE_DIRECTION							= r'left'
	DURATION_MAX_VIDEO_SEC						= float(7200.0)
	DENOISE_SMALL_SIZE_VIDEOS					= True

	TARGET_WIDTH								= int(1920)	# ; "target_width" an integer; set for hd; do not change unless a dire emergency = .
	TARGET_HEIGHT								= int(1080)	# ; "target_height" an integer; set for hd; do not change unless a dire emergency = .
	TARGET_FPSNUM								= int(25)	# ; "target_fpsnum" an integer; set for pal = .
	TARGET_FPSDEN								= int(1)	# ; "target_fpsden" an integer; set for pal = .
	TARGET_COLORSPACE							= r'BT.709'	# ; "target_colorspace" a string; set for hd; required to render subtitles, it is fixed at this value; this item must match target_colorspace_matrix_i etc = .
	TARGET_COLORSPACE_MATRIX_I					= int(1)	# ; "target_colorspace_matrix_i" an integer; set for hd; this is the value that counts; it is fixed at this value; turn on debug_mode to see lists of these values = .
	TARGET_COLOR_TRANSFER_I						= int(1)	# ; "target_color_transfer_i" an integer; set for hd; this is the value that counts; it is fixed at this value; used by vapoursynth; turn on debug_mode to see lists of these values = .
	TARGET_COLOR_PRIMARIES_I					= int(1)	# ; "target_color_primaries_i" an integer; set for hd; this is the value that counts; it is fixed at this value; turn on debug_mode to see lists of these values = .
	TARGET_COLOR_RANGE_I						= int(0)	# ; "target_color_range_i" an integer; set for full-range, not limited-range; this is the (vapoursynth) value that counts; it is fixed at this value; used by vapoursynth; turn on debug_mode to see lists of these values = .
															# ; "target_color_range_i note: this vapoursynth value is opposite to that needed by zimg and by resizers which require the zimg (the propeer) value; internal transations vs->zimg are done = .
	UPSIZE_KERNEL								= r'Lanczos'	# ; "upsize_kernel" a string; do not change unless a dire emergency; you need the exact string name of the resizer = .
	DOWNSIZE_KERNEL								= r'Spline36'	#; "downsize_kernel" a string; do not change unless a dire emergency; you need the exact string name of the resizer = .
	BOX											= True		# ; "box" is true or false; if true, images and videos are resized vertically/horizontally to maintain aspect ratio and padded; false streches and squeezes  = .

	OUTPUT_MKV_FILENAME_PATH_LIST				= os.path.join(ROOT_FOLDER_FOR_OUTPUTS, r'dummy.mkv')	# no longer used. retained for compatibility. was written into last line of every snippets file as part of: [start frame number (0), last frame number, 'filename of encoded video snippets belong to' ]

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
	VS_INTERLACED = { 'Progressive' : 0, 'BFF' : 1, 'TFF' : 2 }		# vs documnetation says frame property _FieldBased is one of 0=frame based (progressive), 1=bottom field first, 2=top field first.

	TARGET_FPS									= None		# CALCULATED LATER : # = round(self.calc_ini["TARGET_FPSNUM"] / self.calc_ini["TARGET_FPSDEN"], 3)
	DURATION_PIC_FRAMES							= None		# CALCULATED LATER : 	# = int(math.ceil(self.calc_ini["DURATION_PIC_SEC"] * self.calc_ini["TARGET_FPS"]))
	DURATION_CROSSFADE_FRAMES					= None		# CALCULATED LATER : 	# = int(math.ceil(self.calc_ini["DURATION_CROSSFADE_SECS"] * self.calc_ini["TARGET_FPS"]))
	DURATION_BLANK_CLIP_FRAMES					= None		# CALCULATED LATER : 	# = self.calc_ini["DURATION_CROSSFADE_FRAMES"] + 1	# make equal to the display time for an image; DURATION_CROSSFADE_FRAMES will be less than this
	DURATION_MAX_VIDEO_FRAMES					= None		# CALCULATED LATER : 	# = int(math.ceil(self.calc_ini["DURATION_MAX_VIDEO_SEC"] * self.calc_ini["TARGET_FPS"]))
	TARGET_VFR_FPSNUM							= None		# CALCULATED LATER : 	# = self.calc_ini["TARGET_FPSNUM"] * 2
	TARGET_VFR_FPSDEN							= None		# CALCULATED LATER : 	# = self.calc_ini["TARGET_FPSDEN"]
	TARGET_VFR_FPS								= None		# CALCULATED LATER : 	# = self.calc_ini["TARGET_VFR_FPSNUM"] / self.calc_ini["TARGET_VFR_FPSDEN"]	
	TARGET_COLOR_RANGE_I_ZIMG					= None		# CALCULATED LATER : 	# = if something, calculate

	default_settings_dict = {
		'SLIDESHOW_SETTINGS_FILE':					SLIDESHOW_SETTINGS_FILE,
		
		'ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS': ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS,	# this is the ONLY file/folder thing in the NEW version that is actually already a LIST
		'TEMP_FOLDER':								TEMP_FOLDER,
		'PIC_EXTENSIONS' :							PIC_EXTENSIONS,
		'VID_EXTENSIONS' :							VID_EXTENSIONS,
		'EEK_EXTENSIONS' :							EEK_EXTENSIONS,
		'EXTENSIONS' :								EXTENSIONS,
		'ROOT_FOLDER_FOR_OUTPUTS': 					ROOT_FOLDER_FOR_OUTPUTS,
		'CHUNKS_OUTPUT_FILE_ALL_CHUNKS': 			CHUNKS_OUTPUT_FILE_ALL_CHUNKS,
		'CHUNKS_OUTPUT_FILES_COMMON_NAME':			CHUNKS_OUTPUT_FILES_COMMON_NAME,
		'CHUNKS_OUTPUT_FILES_COMMON_NAME_GLOB': 	CHUNKS_OUTPUT_FILES_COMMON_NAME_GLOB,
		'PER_CHUNK_LIST_OF_SNIPPET_FILES':			PER_CHUNK_LIST_OF_SNIPPET_FILES,
		'BACKGROUND_AUDIO_INPUT_FILE': 				BACKGROUND_AUDIO_INPUT_FILE,
		'FINAL_OUTPUT_MP4_FILE':					FINAL_OUTPUT_MP4_FILE,
		'MAX_VIDEO_FILES_PER_CHUNK':				MAX_VIDEO_FILES_PER_CHUNK,
		'TOLERANCE_PERCENT_FINAL_CHUNK':			TOLERANCE_PERCENT_FINAL_CHUNK,
		'RECURSIVE':								RECURSIVE,
		'DEBUG':									DEBUG,
		'FFMPEG_PATH':								FFMPEG_PATH,
		
		'SUBTITLE_DEPTH':							SUBTITLE_DEPTH,
		'SUBTITLE_FONTSIZE':						SUBTITLE_FONTSIZE,
		'SUBTITLE_FONTSCALE':						SUBTITLE_FONTSCALE,
		'DURATION_PIC_SEC':						DURATION_PIC_SEC,
		'DURATION_CROSSFADE_SECS':					DURATION_CROSSFADE_SECS,
		'CROSSFADE_TYPE':							CROSSFADE_TYPE,
		'CROSSFADE_DIRECTION':						CROSSFADE_DIRECTION,
		'DURATION_MAX_VIDEO_SEC':					DURATION_MAX_VIDEO_SEC,
		'DENOISE_SMALL_SIZE_VIDEOS':				DENOISE_SMALL_SIZE_VIDEOS,

		'TARGET_WIDTH':								TARGET_WIDTH,
		'TARGET_HEIGHT':							TARGET_HEIGHT,
		'TARGET_FPSNUM':							TARGET_FPSNUM,
		'TARGET_FPSDEN':							TARGET_FPSDEN,

		'TARGET_COLORSPACE':						TARGET_COLORSPACE,
		'TARGET_COLORSPACE_MATRIX_I':				TARGET_COLORSPACE_MATRIX_I,
		'TARGET_COLOR_TRANSFER_I':					TARGET_COLOR_TRANSFER_I,
		'TARGET_COLOR_PRIMARIES_I':					TARGET_COLOR_PRIMARIES_I,
		'TARGET_COLOR_RANGE_I':						TARGET_COLOR_RANGE_I,
		'UPSIZE_KERNEL':							UPSIZE_KERNEL,
		'DOWNSIZE_KERNEL':							DOWNSIZE_KERNEL,
		'BOX':										BOX,

		'OUTPUT_MKV_FILENAME_PATH_LIST':			OUTPUT_MKV_FILENAME_PATH_LIST,

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

	# load the json settings with try/except, abort if file not found (part of json.load)
	# do not rewrite then on the basis it loses any comments in the source file
	user_specified_settings_dict = {}
	try:
		with open(fully_qualified_filename_3333(SLIDESHOW_SETTINGS_FILE), 'r') as fp:
			user_specified_settings_dict = json.load(fp)
	except Exception as e:
		print(f"load_settings: ERROR: loading user specified Settings from JSON file: '{SLIDESHOW_SETTINGS_FILE}'\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)	

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
		ddl_fully_qualified.append(fully_qualified_directory_no_trailing_backslash_3333(ddl))
	final_settings_dict['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS'] = ddl_fully_qualified
	#
	final_settings_dict['SLIDESHOW_SETTINGS_FILE'] = fully_qualified_filename_3333(final_settings_dict['SLIDESHOW_SETTINGS_FILE'])
	final_settings_dict['ROOT_FOLDER_FOR_OUTPUTS'] = fully_qualified_directory_no_trailing_backslash_3333(final_settings_dict['ROOT_FOLDER_FOR_OUTPUTS'])
	final_settings_dict['TEMP_FOLDER'] = fully_qualified_directory_no_trailing_backslash_3333(final_settings_dict['TEMP_FOLDER'])
	final_settings_dict['CHUNKS_OUTPUT_FILE_ALL_CHUNKS'] = fully_qualified_filename_3333(final_settings_dict['CHUNKS_OUTPUT_FILE_ALL_CHUNKS'])
	final_settings_dict['CHUNKS_OUTPUT_FILES_COMMON_NAME'] = fully_qualified_filename_3333(final_settings_dict['CHUNKS_OUTPUT_FILES_COMMON_NAME'])
	final_settings_dict['CHUNKS_OUTPUT_FILES_COMMON_NAME_GLOB'] = fully_qualified_filename_3333(final_settings_dict['CHUNKS_OUTPUT_FILES_COMMON_NAME_GLOB'])
	final_settings_dict['PER_CHUNK_LIST_OF_SNIPPET_FILES'] = fully_qualified_filename_3333(final_settings_dict['PER_CHUNK_LIST_OF_SNIPPET_FILES'])
	final_settings_dict['BACKGROUND_AUDIO_INPUT_FILE'] = fully_qualified_filename_3333(final_settings_dict['BACKGROUND_AUDIO_INPUT_FILE'])
	final_settings_dict['FINAL_OUTPUT_MP4_FILE'] = fully_qualified_filename_3333(final_settings_dict['FINAL_OUTPUT_MP4_FILE'])

	# check the files which should exist do exist
	def check_file_exists_3333(file, text):
		if not os.path.exists(file):
			print(f"load_settings: ERROR: the specified {text} File '{file}' does not exist",flush=True,file=sys.stderr)
			sys.exit(1)
		return
	check_file_exists_3333(final_settings_dict['FFMPEG_PATH'], r'FFMPEG_PATH')
	check_file_exists_3333(final_settings_dict['BACKGROUND_AUDIO_INPUT_FILE'], r'BACKGROUND_AUDIO_INPUT_FILE')
	# check the folders which should exist do exist
	# 1. check the folders in this LIST
	def check_folder_exists_3333(folder, text):
		if not os.path.isdir(folder):
			print(f"load_settings: ERROR: the specified {text} folder does not exist: '{folder}' does not exist",flush=True,file=sys.stderr)
			sys.exit(1)
		return
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
	old_calc_ini_dict =	{	'directory_list' :					final_settings_dict['ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS'],	# This is already a list []
							'temp_directory_list' :				[ final_settings_dict['TEMP_FOLDER'] ],
							'snippets_filename_path_list' :		[ final_settings_dict['PER_CHUNK_LIST_OF_SNIPPET_FILES'] ],			# SUPERSEDED
							'output_mkv_filename_path_list' :	[ final_settings_dict['OUTPUT_MKV_FILENAME_PATH_LIST'] ],			# SUPERSEDED
							'recursive' :						final_settings_dict['RECURSIVE'],
							'subtitle_depth' :					final_settings_dict['SUBTITLE_DEPTH'],
							'subtitle_fontsize' :				final_settings_dict['SUBTITLE_FONTSIZE'],
							'subtitle_fontscale' :				final_settings_dict['SUBTITLE_FONTSCALE'],
							'duration_pic_sec' :				final_settings_dict['DURATION_PIC_SEC'],
							'duration_crossfade_secs' :			final_settings_dict['DURATION_CROSSFADE_SECS'],
							'crossfade_type' :					final_settings_dict['CROSSFADE_TYPE'],
							'crossfade_direction' :				final_settings_dict['CROSSFADE_DIRECTION'],
							'duration_max_video_sec' :			final_settings_dict['DURATION_MAX_VIDEO_SEC'],
							'denoise_small_size_videos' :		final_settings_dict['DENOISE_SMALL_SIZE_VIDEOS'],
							'debug_mode' :						final_settings_dict['DEBUG'],
							'target_colorspace' :				final_settings_dict['TARGET_COLORSPACE'],
							'target_colorspace_matrix_i' :		final_settings_dict['TARGET_COLORSPACE_MATRIX_I'],
							'target_color_transfer_i' :			final_settings_dict['TARGET_COLOR_TRANSFER_I'],
							'target_color_primaries_i' :		final_settings_dict['TARGET_COLOR_PRIMARIES_I'],
							'target_color_range_i' :			final_settings_dict['TARGET_COLOR_RANGE_I'],
							'target_width' :					final_settings_dict['TARGET_WIDTH'],
							'target_height' :					final_settings_dict['TARGET_HEIGHT'],
							'target_fpsnum' :					final_settings_dict['TARGET_FPSNUM'],
							'target_fpsden' :					final_settings_dict['TARGET_FPSDEN'],
							'upsize_kernel' :					final_settings_dict['UPSIZE_KERNEL'],
							'downsize_kernel' :					final_settings_dict['DOWNSIZE_KERNEL'],
							'box' :								final_settings_dict['BOX'],
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
							'Rotation_anti_clockwise':			final_settings_dict['Rotation_anti_clockwise'],
							'Rotation_clockwise':				final_settings_dict['Rotation_clockwise'],
							'TARGET_VFR_FPSNUM':				final_settings_dict['TARGET_VFR_FPSNUM'],
							'TARGET_VFR_FPSDEN':				final_settings_dict['TARGET_VFR_FPSDEN'],
							'TARGET_VFR_FPS':					final_settings_dict['TARGET_VFR_FPS'],
							'TARGET_VFR_FPSNUM':				final_settings_dict['TARGET_VFR_FPSNUM'],
							'TARGET_VFR_FPSDEN':				final_settings_dict['TARGET_VFR_FPSDEN'],
							'TARGET_VFR_FPS':					final_settings_dict['TARGET_VFR_FPS'],
							'precision_tolerance':				final_settings_dict['PRECISION_TOLERANCE'],				# the only one that is a lowercase ley
							'TARGET_COLOR_RANGE_I_ZIMG':		final_settings_dict['TARGET_COLOR_RANGE_I_ZIMG'],
						}

	# MAP that back into something compatible with OLD _ini_values[self._ini_section_name]["SETTING_NAME"]
	old_ini_dict = { final_settings_dict['_INI_SECTION_NAME']: old_calc_ini_dict }

	if DEBUG:
		try:
			f_debug = SLIDESHOW_SETTINGS_FILE + r'.DEBUG.user_settings.JSON'
			with open(f_debug, 'w') as fp:
				json.dump(user_specified_settings_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		#
		try:
			f_debug = SLIDESHOW_SETTINGS_FILE + r'.DEBUG.default_settings.JSON'
			with open(f_debug, 'w') as fp:
				json.dump(default_settings_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		#
		try:
			f_debug = SLIDESHOW_SETTINGS_FILE + r'.DEBUG.final_settings.JSON'
			with open(f_debug, 'w') as fp:
				json.dump(final_settings_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		#
		try:
			f_debug = SLIDESHOW_SETTINGS_FILE + r'.DEBUG.old_ini_dict.JSON'
			with open(f_debug, 'w') as fp:
				json.dump(old_ini_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		#
		try:
			f_debug = SLIDESHOW_SETTINGS_FILE + r'.DEBUG.old_calc_ini_dict.JSON'
			with open(f_debug, 'w') as fp:
				json.dump(old_calc_ini_dict, fp, indent=4)
		except Exception as e:
			print(f"DEBUG: load_settings: ERROR: error dumping JSON file: '{f_debug}'\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	

	return settings_dict, old_ini_dict, old_calc_ini_dict

