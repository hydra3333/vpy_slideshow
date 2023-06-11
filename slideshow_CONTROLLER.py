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

import gc	# for inbuilt garbage collection
# THE NEXT STATEMENT IS ONLY FOR DEBUGGING AND WILL CAUSE EXTRANEOUS OUTPUT TO STDERR
#gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS)	# for debugging, additional garbage collection settings, writes to stderr https://docs.python.org/3/library/gc.html to help detect leaky memory issues
num_unreachable_objects = gc.collect()	# collect straight away

from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.ExifTags import TAGS

import pydub
from pydub import AudioSegment

CDLL(r'MediaInfo.dll')				# note the hard-coded folder	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption		# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
#from MediaInfoDLL3 import *											# per https://github.com/MediaArea/MediaInfoLib/blob/master/Source/Example/HowToUse_Dll3.py

# Ensure we can import modules from ".\" by adding the current default folder to the python path.
# (tried using just PYTHONPATH environment variable but it was unreliable)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
global FFMPEG_PATH

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

###

# ---------------
def find_all_chunks():
	# only use globals: SETTINGS_DICT, DEBUG

	def get_random_ffindex_path(path):
		# use the filename component of the incoming path and create a random fully qualified path into the temp folder
		# there is a significant to 100% chance of home picture/video filenames in directory trees being non-unique
		# apparently uuid4 has a good chance of returning a unique string
		f = fully_qualified_filename(os.path.join(SETTINGS_DICT['TEMP_FOLDER'], os.path.basename(path) + r'_' + str(uuid.uuid4()) + r'.ffindex'))
		return f

	def fac_get_path(path_generator):
		# get next path of desired extensions from generator, ignoring extensions we have not specified
		# loop around only returning a path with a known extension
		while 1:	# loop until we do a "return", hitting past the end of the iterator returns None
			try:
				path = next(path_generator)
				if DEBUG:	print(f'fac_get_path: get success, path.name=' + path.name,flush=True)
			except StopIteration:
				return None
			if path.suffix.lower() in SETTINGS_DICT['EXTENSIONS']:	# only return files which are in known extensions
				if DEBUG:	print(f'DEBUG: find_all_chunks: fac_get_path: in EXTENSIONS success, path.name=' + path.name,flush=True)
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
				print(f'WARNING: fac_check_clip_from__path: error opening file via "ffms2": "{str(path)}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
				return False
		elif  ext in SETTINGS_DICT['EEK_EXTENSIONS']:
			try:
				clip = core.lsmas.LWLibavSource(str(path))
				del clip
				return True
			except Exception as e:
				print(f'WARNING: fac_check_clip_from__path: error opening file via "lsmas": "{path.name}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
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
				print(f'WARNING: fac_check_clip_from_pic: error opening file via "ffms2": "{path.name}" ; ignoring this picture. The error was:\n{e}\n{type(e)}\n{str(e)}',flush=True)
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

	print(f"Commencing assigning files into chunks for processing usng:",flush=True)
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
				print(f"Checking file {count_of_files}. '{path}' for validity ...",flush=True)
				is_valid = fac_check_file_validity_by_opening(path)
				if not is_valid:	# ignore clips which had an issue with being opened and return None
					print(f'Unable to process {count_of_files} {str(path)} ... ignoring it',flush=True)
				else:
					# if required, start a new chunk
					if (count_of_files % SETTINGS_DICT['MAX_FILES_PER_CHUNK']) == 0:
						chunk_id = chunk_id + 1
						chunks[str(chunk_id)] = {	
													'chunk_id': chunk_id,
													'chunk_fixed_json_filename' :				fully_qualified_filename(SETTINGS_DICT['CURRENT_CHUNK_FILENAME'])		# always the same fixed filename
													#'snippet_fixed_json_filename' :				fully_qualified_filename(SETTINGS_DICT['CURRENT_SNIPPETS_FILENAME'])	# always the same fixed filename
													'proposed_ffv1_mkv_filename' :				fully_qualified_filename(SETTINGS_DICT['CHUNK_ENCODED_FFV1_FILENAME_BASE'] + str(chunk_id).zfill(5) + r'.mkv'),	# filename related to chunk_id
													'num_files': 								0,	# initialized but filled in by this loop, number of files in this chunk's file_list
													'num_frames_in_chunk' :						0,	# initialize to 0, filled in by encoder
													'start_frame_num_in_chunk':					0,	# initialize to 0, filled in by encoder
													'end_frame_num_in_chunk':					0,	# initialize to 0, filled in by encoder
													'start_frame_num_of_chunk_in_final_video':	0,	# initialize to 0, # calculated AFTER encoder finished completely
													'end_frame_num_of_chunk_in_final_video': 	0,	# initialize to 0, # calculated AFTER encoder finished completely
													'file_list':	 							[],	# each item is a fully qualified filename of a source file for this chunk
													'snippet_list': 							[], # an empty dict to be be filled in by encoder, it looks like this:
													# snippet_list:	[								# each snippet list item is a dict which looks like the below:
													#					{	
													#						start_frame_of_snippet_in_chunk: 0,					# filled in by encoder
													#						end_frame_of_snippet_in_chunk: XXX, 				# filled in by encoder
													#						start_frame_of_snippet_in_final_video: AAA,  		# AFTER all encoding completed, calculated and filled in by controller
													#						end_frame_of_snippet_in_final_video: XXX, 			# AFTER all encoding completed, calculated and filled in by controller
													#						snippet_num_frames: YYY,							# filled in by encoder
													#						snippet_source_video_filename: '\a\b\c\ZZZ1.3GP'	# filled in by encoder
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
			print(f'Merging final chunk (chunk_id={chunk_id}, num_files={chunks[str(chunk_id)]["num_files"]}) into previous chunk (chunk_id={chunk_id - 1}, num_files={chunks[str(chunk_id - 1)]["num_files"]+chunks[str(chunk_id)]["num_files"]})',flush=True)
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

	print(f"Finished assigning files into chunks for processing: {count_of_files} files into {chunk_count} chunks.",flush=True)

	return chunk_count, count_of_files, chunks

##################################################

if __name__ == "__main__":
	DEBUG = True
	
	##########################################################################################################################################
	##########################################################################################################################################
	# GATHER SETTINGS

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
	FFMPEG_PATH = SETTINGS_DICT['FFMPEG_PATH']

	if DEBUG:
		print(f"DEBUG: slideshow_CONTROLLER: DEBUG={DEBUG}",flush=True)
		print(f"DEBUG: slideshow_CONTROLLER: USER_SPECIFIED_SETTINGS_DICT=\n{objPrettyPrint.pformat(USER_SPECIFIED_SETTINGS_DICT)}",flush=True)
		print(f"DEBUG: slideshow_CONTROLLER: SETTINGS_DICT=\n{objPrettyPrint.pformat(SETTINGS_DICT)}",flush=True)
		print(f"DEBUG: slideshow_CONTROLLER: OLD_INI_DICT=\n{objPrettyPrint.pformat(OLD_INI_DICT)}",flush=True)
		print(f"DEBUG: slideshow_CONTROLLER: OLD_CALC_INI_DICT=\n{objPrettyPrint.pformat(OLD_CALC_INI_DICT)}",flush=True)

	##########################################################################################################################################
	##########################################################################################################################################
	# FIND PIC/IMAGES
	
	# Locate all openable files and put them into chunks in a dict, including { proposed filename for the encoded chunk, first/last frames, number of frames in chunk } 

	ALL_CHUNKS_COUNT, ALL_CHUNKS_COUNT_OF_FILES, ALL_CHUNKS = find_all_chunks()	# it uses settings in SETTINGS_DICT to do its thing
	
	if DEBUG:	print(f"DEBUG: retrieved ALL_CHUNKS tree: chunks: {ALL_CHUNKS_COUNT} files: {ALL_CHUNKS_COUNT_OF_FILES} dict:\n{objPrettyPrint.pformat(ALL_CHUNKS)}",flush=True)

	# create .JSON file containing the ALL_CHUNKS  dict. Note the start/stop frames etc are yet to be updated by the encoder
	try:
		fac = SETTINGS_DICT['CHUNKS_FILENAME_FOR_ALL_CHUNKS_DICT']
		with open(fac, 'w') as fp:
			json.dump(ALL_CHUNKS, fp, indent=4)
	except Exception as e:
		print(f"ERROR: error returned from json.dump ALL_CHUNKS to JSON file: '{fac}'\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)	
	
	##########################################################################################################################################
	##########################################################################################################################################
	# INTERIM ENCODING OF CHUNKS INTO INTERIM FFV1 VIDEO FILES, 
	# SAVING FRAME NUMBERS AND NUM VIDEO FRAMES INFO SNIPPET DICT, 
	# CREATING SNIPPET JSON, IMPORTING JSON AND ADDING TO ALL_SNIPPETS DICT:

	if DEBUG:	print(f"DEBUG: Starting encoder loop for each of ALL_CHUNKS tree. chunks: {ALL_CHUNKS_COUNT} files: {ALL_CHUNKS_COUNT_OF_FILES}",flush=True)
	
	for individual_chunk_id in range(0,ALL_CHUNKS_COUNT)	# 0 to (ALL_CHUNKS_COUNT - 1)
		# we cannot just import the legacy encoder and call it with parameters, it is a vpy consumed by ffmpeg and that does not accept parameters
		# so we need to create`a fixed-filenamed input file for it to consume (a chu`nk)
		#						and a fixed filename for it to create (snippets for that chunk)

		individual_chunk_dict = ALL_CHUNKS[str(individual_chunk_id)]

		chunk_json_filename = fully_qualified_filename(individual_chunk_dict['chunk_fixed_json_filename'])					# always the same fixed filename
		#### the CHUNK JASON FILE IS UPDATED AND RE-WRITTEN AND RE-READ, not a separate SNIPPETS FILE 
		#snippets_json_filename = fully_qualified_filename(individual_chunk_dict['snippet_fixed_json_filename'])				# always the same fixed filename
		proposed_ffv1_mkv_filename = fully_qualified_filename(individual_chunk_dict['proposed_ffv1_mkv_filename'])	# fixed filename plus a seqnential 5-digit-zero-padded ending based on chunk_id + r'.mkv'
		
		# remove any pre-existing files to be consumed and produced by the encoder
		if os.path.exists(chunk_json_filename):
			os.remove(chunk_json_filename)
		#if os.path.exists(snippets_json_filename):
		#	os.remove(snippets_json_filename)
		if os.path.exists(proposed_ffv1_mkv_filename):
			os.remove(proposed_ffv1_mkv_filename)
		
		# create the fixed-filename chunk file consumed by the encoder; it contains the fixed-filename of the snippet file to produce
		if DEBUG:	print(f"DEBUG: in encoder loop: attempting to create chunk_json_filename={chunk_json_filename} for encoder to consume.",flush=True)
		try:
			with open(chunk_json_filename, 'w') as fp:
				json.dump(individual_chunk_dict, fp, indent=4)
		except Exception as e:
			print(f"ERROR: dumping current chunk to JSON file: '{chunk_json_filename}' for encoder, chunk_id={individual_chunk_id}, individual_chunk_dict=\nobjPrettyPrint.pformat(individual_chunk_dict)\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		print(f"Created fixed-filename chunk file for encoder to consume: {chunk_json_filename} listing {num_files} files.",flush=True)

		# ????????????????????????????????????
		# ????????????????????????????????????
		# ????????????????????????????????????
		if DEBUG:	print(f"DEBUG: encoder loop: calling the encoder, VSPIPE piped to FFMPEG ... with controller using non-blocking reads of stdout and stderr (per chatgpt).",flush=True)
		# HERE: call the encoder ... vspipe piped to ffmpeg ... with controller using non-blocking reads of stdout and stderr (per chatgpt)
		if DEBUG:	print(f"DEBUG: encoder loop: returned from the encoder, VSPIPE piped to FFMPEG ... with controller using non-blocking reads of stdout and stderr (per chatgpt).",flush=True)
		# ????????????????????????????????????
		# ????????????????????????????????????
		# ????????????????????????????????????

		# Now the encoder has encoded a chunk and produced an updated chunk file and an ffv1 encoded video .mkv 
		# ... import updated chunk file (which will include a new snippet_list) check the chunk, and update the ALL_CHUNKS dict with updated chunk data
		# The format of the snippet_list produced by the encoder into the updated chunk JSON file is defined above.
		
		if not os.path.exists(chunk_json_filename):
			OOPS AN ERROR SOMEWHERE, encoder-updated current chunk to JSON file file not found {chunk_json_filename} not found !
		if not os.path.exists(proposed_ffv1_mkv_filename):
			OOPS AN ERROR SOMEWHERE, encoder-produced .mkv video file not found {snippets_jsoproposed_ffv1_mkv_filenamen_filename} not found !
		if DEBUG:	print(f"DEBUG: in encoder loop: attempting to load snippets_json_filename={snippets_json_filename} produced by the encoder.",flush=True)
		try:
			with open(chunk_json_filename, 'r') as fp:
				updated_individual_chunk_dict = json.load(fp)
		except Exception as e:
			print(f"ERROR: loading updated current chunk from JSON file: '{chunk_json_filename}' from encoder, chunk_id={individual_chunk_id}, related to individual_chunk_dict=\nobjPrettyPrint.pformat(individual_chunk_dict)\n{str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)	
		print(f"Loaded updated current chunk from JSON file: '{chunk_json_filename}'",flush=True)
		if (updated_individual_chunk_dict['chunk_id'] !=  individual_chunk_dict['chunk_id']) or (updated_individual_chunk_dict['chunk_id'] != str(individual_chunk_id)):
			OOPS AN ERROR SOMEWHERE ! the chunk_id returned from the encoder {updated_individual_chunk_dict['chunk_id']} in updated_individual_chunk_dict does not match both expected individual_chunk_dict {individual_chunk_dict['chunk_id'])} or loop individual_chunk_id ({individual_chunk_id})
			sys.exit(1)

		# poke the chunk updated by the encoder back into ALL_CHUNKS ... it should contain snippet data now.
		ALL_CHUNKS[str(individual_chunk_id)] = updated_individual_chunk_dict
	#end for

	if DEBUG:	print(f"After updating encoder added snippets into each chunk , and controller UPDATING chunk info into ALL_CHUNKS, the new ALL_CHUNKS tree is:\n{objPrettyPrint.pformat(ALL_CHUNKS)}",flush=True)

	##########################################################################################################################################
	##########################################################################################################################################
	# FINISHED INTERIM ENCODING
	# re-parse the ALL_CHUNKS tree dict to re-calculate global frame numbers on a per-chunk basis and within that on a per-snippet-within-chunk basis
	# using the newly added  ...  before processing any audio using snippets, 
	# so we can refer to absolute final-video frame numbers rather than chunk-internal frame numbers

	if DEBUG:	print(f"DEBUG: Startingre-parse the ALL_CHUNKS tree dict to re-calculate global frame numbers chunks: {ALL_CHUNKS_COUNT}.",flush=True)

	# To be calculated and updated in each chunk at the chunk level:
	#		ALL_CHUNKS[str(individual_chunk_id)]['start_frame_num_of_chunk_in_final_video']
	#		ALL_CHUNKS[str(individual_chunk_id)]['end_frame_num_of_chunk_in_final_video']
	#
	# To be calculated and updated in every 'snippet_list' item within a chunk (this is a list, so loop to process each snippet via its list index): 
	#		ALL_CHUNKS[str(individual_chunk_id)]['snippet_list'][index_number_in_for_loop']['start_frame_of_snippet_in_final_video']
	#		ALL_CHUNKS[str(individual_chunk_id)]['snippet_list'][index_number_in_for_loop']['end_frame_of_snippet_in_final_video']






	# keep track of the frame numbers of a video where all of the slideshow videos will be concatenated in sequence
	seq_previous_ending_frame_num = -1	# initialize so the start frame number for the first clip with be (-1 + 1) = 0 .. base 0
	global_video_first_frame_num = 0
	global_video_last_frame_num = 0
	
	if DEBUG: print(f"DEBUG: seq_previous_ending_frame_num init to {seq_previous_ending_frame_num}",flush=True)

	for individual_chunk_id in range(0,ALL_CHUNKS_COUNT)	# 0 to (ALL_CHUNKS_COUNT - 1)
		seq_start_frame_num = seq_previous_ending_frame_num + 1		# base 0, this is now the start_frame_num_of_chunk_in_final_video

		# for this chunk, re-calculate chunk info and poke it back into ALL_CHUNKS
		start_frame_num_of_chunk_in_final_video = calculated NOW 
		end_frame_num_of_chunk_in_final_video = calculated NOW 
		ALL_CHUNKS[str(individual_chunk_id)]['start_frame_num_of_chunk_in_final_video'] = start_frame_num_of_chunk_in_final_video
		ALL_CHUNKS[str(individual_chunk_id)]['end_frame_num_of_chunk_in_final_video'] =  end_frame_num_of_chunk_in_final_video NOW 

		# for the snippets in this chunk, re-calculate chunk info and then poke it back into ALL_CHUNKS
		snippet_dict = ALL_CHUNKS[str(individual_chunk_id)]["snippet_dict"]	# try to retrieve the snippet for a chunk, forces python error if not found
	#end for





	##########################################################################################################################################
	##########################################################################################################################################
	# BACKGROUND AUDIO

	#AFTER ENCODING we can re-import the saved .json file and change the following 
	#- audio editing process to add up all the frame counts and use that (total frame count) in the audio processing
	#- just do audio processing then transcoding/muxing in one step


	##########################################################################################################################################
	##########################################################################################################################################
	# USE SNIPPET INFO BACKGROUND AUDIO:

	##########################################################################################################################################
	##########################################################################################################################################
	# TRANSCODE BACKGROUND AUDIO:
