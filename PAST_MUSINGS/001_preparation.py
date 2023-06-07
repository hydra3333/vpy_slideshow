import vapoursynth as vs
#from vapoursynth import core
core = vs.core
#core.num_threads = 1

import sys
import os
import re
import argparse
import subprocess

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
from pymediainfo import MediaInfo

CDLL(r'MediaInfo.dll')				# note the hard-coded folder	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption		# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
#from MediaInfoDLL3 import *											# per https://github.com/MediaArea/MediaInfoLib/blob/master/Source/Example/HowToUse_Dll3.py

#core.std.LoadPlugin(r'DGDecodeNV.dll')
#core.avs.LoadPlugin(r'DGDecodeNV.dll')

global TERMINAL_WIDTH					# for use by PrettyPrinter
TERMINAL_WIDTH = 250
global objPrettyPrint
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc

# Path to the FFmpeg executable
FFMPEG_PATH = r'C:\\SOFTWARE\\ffmpeg\\ffmpeg.exe'

def normalize_path(path):
	#if DEBUG: print(f"DEBUG: normalize_path:  incoming path='{path}'",flush=True)
	# Replace single backslashes with double backslashes
	path = path.rstrip(os.linesep).strip('\r').strip('\n').strip()
	r1 = r'\\'
	r2 = r1 + r1
	r4 = r2 + r2
	path = path.replace(r1, r4)
	# Add double backslashes before any single backslashes
	for i in range(0,20):
		path = path.replace(r2, r1)
	#if DEBUG: print(f"DEBUG: normalize_path: outgoing path='{path}'",flush=True)
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
def get_random_ffindex_path(path):
	# there is a significant to 100% chance of home picture/video filenames in directory trees being non-unique
	# apparently uuid4 has a good chance of returning a unique string
	f = fully_qualified_filename(TEMP_DIRECTORY  + r'\ '.strip() + os.path.basename(path) + r'_' + str(uuid.uuid4()) + r'.ffindex')
	return f

###
def check_clip_from__path(path, ext):		# opens VID_EEK_EXTENSIONS only ... Source filter depends on extension
	if not ext in VID_EEK_EXTENSIONS:
		raise ValueError(f'get_clip_from_path: expected {path} to have extension in {VID_EEK_EXTENSIONS} ... aborting')
	if ext in VID_EXTENSIONS:
		try:
			ffcachefile = get_random_ffindex_path(path)
			clip = core.ffms2.Source(str(path), cachefile=ffcachefile)
			del clip
			os.remove(ffcachefile)
			return True
		except Exception as e:
			print(f'WARNING: error opening file via "ffms2": "{str(path)}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}')
			return False
	elif  ext in EEK_EXTENSIONS:
		try:
			clip = core.lsmas.LWLibavSource(str(path))
			del clip
			return True
		except Exception as e:
			print(f'WARNING: error opening file via "lsmas": "{path.name}" ; ignoring this video clip. The error was:\n{e}\n{type(e)}\n{str(e)}')
			return False
	else:
		raise ValueError(f'get_clip_from_path: expected {path} to have extension in {VID_EEK_EXTENSIONS} ... aborting')
	return False

###
def check_clip_from_pic(path, ext):
	if ext in PIC_EXTENSIONS:
		try:
			ffcachefile = get_random_ffindex_path(path)
			clip = core.ffms2.Source(str(path), cachefile=ffcachefile)
			del clip
			os.remove(ffcachefile)
			return True
		except Exception as e:
			print(f'WARNING: error opening file via "ffms2": "{path.name}" ; ignoring this picture. The error was:\n{e}\n{type(e)}\n{str(e)}')
			return False
	else:
		raise ValueError(f': expected {path} to have extension in {PIC_EXTENSIONS} ... aborting')
	return False

def check_file_validity_by_opening(path):
	if path is None:
		raise ValueError(f'ERROR: check_file_validity_by_opening: "path" not passed as an argument to check_file_validity_by_opening')
		sys.exit(1)
	ext = path.suffix.lower()
	if ext in VID_EXTENSIONS:
		is_valid = check_clip_from__path(path, ext)									# open depends on ext, the rest is the same
	elif ext in EEK_EXTENSIONS:
		is_valid = check_clip_from__path(path, ext)									# open depends on ext, the rest is the same
	elif ext in PIC_EXTENSIONS:
		is_valid = check_clip_from_pic(path, ext)
	else:
		raise ValueError(f'check_file_validity_by_opening: "{path}" - UNRECOGNISED file extension "{ext}", aborting ...')
		sys.exit()
	return is_valid

###
def get_path(path_generator):
	# get next path of desired extensions from generator, ignoring extensions we have not specified
	# loop around only returning a path with a known extension
	while 1:	# loop until we do a "return", hitting past the end of the iterator returns None
		try:
			path = next(path_generator)
			#if DEBUG: print(f'get_path: get success, path.name=' + path.name)
		except StopIteration:
			return None
		if path.suffix.lower() in EXTENSIONS:	# only return files which are in known extensions
			#if DEBUG: print(f'get_path: in EXTENSIONS success, path.name=' + path.name)
			return path

# ---------------

global DEBUG
DEBUG = True

RECURSIVE = True
MAX_FILES_PER_CHUNK = 150
TOLERANCE_FINAL_CHUNK = int(MAX_FILES_PER_CHUNK * 0.20)	# 20%

PIC_EXTENSIONS		= [".png", ".jpg", ".jpeg", ".gif"]								# always lower case
VID_EXTENSIONS		= [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov"]	# always lower case
EEK_EXTENSIONS		= [".m2ts"]														# always lower case
VID_EEK_EXTENSIONS	= VID_EXTENSIONS + EEK_EXTENSIONS
EXTENSIONS			= PIC_EXTENSIONS + VID_EXTENSIONS + EEK_EXTENSIONS

# ---------------

TEMP_DIRECTORY = fully_qualified_directory_no_trailing_backslash(r'.\\temp')

DIRECTORY_LIST =	[	fully_qualified_directory_no_trailing_backslash(r'D:\\ssTEST\\TEST_VIDS_IMAGES\\000-tasmania-renamed\\01'),
						fully_qualified_directory_no_trailing_backslash(r'D:\\ssTEST\\TEST_VIDS_IMAGES\\2TEST_rotations'),
					]

CHUNKS_JSON_FILE = fully_qualified_filename(r'.\\chunks.json')

if RECURSIVE:
	glob_var="**/*.*"			# recursive
	ff_glob_var="**/*.ffindex"	# for .ffindex file deletion recursive
else:
	glob_var="*.*"				# non-recursive
	ff_glob_var="*.ffindex"		# for .ffindex file deletion non-recursive
count_of_files = 0
chunk_id = -1	# base 0 chunk id, remember
chunks = {}
file_list_in_chunk = []
for Directory in DIRECTORY_LIST:
	current_Directory = fully_qualified_directory_no_trailing_backslash(Directory)
	paths = Path(current_Directory).glob(glob_var) # generator of all paths in a directory, files starting with . won't be matched by default
	path = get_path(paths)	#pre-fetch first path
	if path is None:
		raise ValueError(f'ERROR: File Extensions:\n{EXTENSIONS}\nnot found in "{current_Directory}"')
	while not (path is None):	# first clip already pre-retrieved ready for this while loop
		if path.suffix.lower() in EXTENSIONS:
			print(f"Checking file {count_of_files}. '{path}' for validity ...",flush=True)
			is_valid = check_file_validity_by_opening(path)
			if not is_valid:	# ignore clips which had an issue with being opened and return None
				print(f'Unable to process {count_of_files} {str(path)} ... ignoring it',flush=True)
			else:
				if (count_of_files % MAX_FILES_PER_CHUNK) == 0:
					# start a new chunk
					chunk_id = chunk_id + 1
					chunks[str(chunk_id)] = {"num_files": 0, "file_list" : [] }
					#chunks[str(chunk_id)]["num_files"] = 0
					#chunks[str(chunk_id)]["file_list"] = []
				# add file to chunk
				fully_qualified_path_string = fully_qualified_filename(path)
				chunks[str(chunk_id)]["file_list"].append(fully_qualified_path_string)
				chunks[str(chunk_id)]["num_files"] = chunks[str(chunk_id)]["num_files"] + 1
				count_of_files = count_of_files + 1
		path = get_path(paths)
	#end while
#end for
# If the final chunk is < 20% of MAX_FILES_PER_CHUNK then merge it into the previous chunk
chunk_count = len(chunks)
if chunk_count > 1:
	# if within tolerance, merge the final chunk into the previous chunk
	if chunks[str(chunk_id)]["num_files"] <= TOLERANCE_FINAL_CHUNK:
		print(f'DEBUG: Merging final chunk (chunk_id={chunk_id}, num_files={chunks[str(chunk_id)]["num_files"]}) into previous chunk (chunk_id={chunk_id - 1}, num_files={chunks[chunk_id - 1]["num_files"]})')
		chunks[str(chunk_id - 1)]["file_list"] = chunks[str(chunk_id - 1)]["file_list"] + chunks[str(chunk_id)]["file_list"]
		chunks[str(chunk_id - 1)]["num_files"] = chunks[str(chunk_id - 1)]["num_files"] + chunks[str(chunk_id)]["num_files"]
		# remove the last chunk since we just merged it into the chunk prior
		del chunks[str(chunk_id)]
chunk_count = len(chunks)

# OK lets print the chunks tree
print(f"Chunks tree contains {count_of_files} files:\n{objPrettyPrint.pformat(chunks)}",flush=True)

# and save the chunks tree
with open(CHUNKS_JSON_FILE, 'w') as fp:
	json.dump(chunks, fp)

# and check the chunks tree
#print(f"")
#print(f"Chunks tree contains {count_of_files} files:\n{objPrettyPrint.pformat(chunks)}",flush=True)
#print(f"Chunks tree saved to json file '{CHUNKS_JSON_FILE}'",flush=True)
print(f"Check re-read and parsing Chunks json file '{CHUNKS_JSON_FILE}'",flush=True)
with open(CHUNKS_JSON_FILE, 'r') as fp:
	chunks = json.load(fp)
chunk_count = len(chunks)
print(f'Retrieved Number of chunks = {chunk_count} with keys (0 to {chunk_count-1})',flush=True)
#print(f'chunks from json :\n{objPrettyPrint.pformat(chunks)}',flush=True)
for i in range(0,chunk_count):	# i.e. 0 to (chunk_count-1)
	#print(f'About to check-print data for chunks[{i}] : chunks[{i}]["num_files"] and chunks[{i}]["file_list"]:',flush=True)
	#print(f'chunks[{i}]["num_files"] = {chunks[str(i)]["num_files"]}',flush=True)
	#print(f'chunks[{i}]["file_list"] = \n{objPrettyPrint.pformat(chunks[str(i)]["file_list"])}',flush=True)
	num_files = chunks[str(i)]["num_files"]
	file_list = chunks[str(i)]["file_list"]
	for j in range(0,num_files):
		file1 = file_list[j]
		file2 = chunks[str(i)]["file_list"][j]
print(f"")
print(f"Finished checking and chunking files for processing. {count_of_files} files in {chunk_count} chunks.",flush=True)