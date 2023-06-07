import vapoursynth as vs
from vapoursynth import core
#core = vs.core
#core.num_threads = 1

import sys
import os
import re
import argparse
import subprocess

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
from collections import defaultdict, OrderedDict
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
global MI
MI = MediaInfo()

#core.std.LoadPlugin(r'DGDecodeNV.dll')
#core.avs.LoadPlugin(r'DGDecodeNV.dll')

global TERMINAL_WIDTH					# for use by PrettyPrinter
TERMINAL_WIDTH = 250
global objPrettyPrint
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc

# Path to the FFmpeg executable
FFMPEG_PATH = 'C:\\SOFTWARE\\ffmpeg\\ffmpeg.exe'

#
def normalize_path(path):
	#if DEBUG: print(f"DEBUG: normalize_path:  incoming path='{path}'",flush=True)
	# Replace single backslashes with double backslashes
	r1 = r'\\'
	r2 = r1 + r1
	r4 = r2 + r2
	path = path.replace(r1, r4)
	# Add double backslashes before any single backslashes
	for i in range(0,20):
		path = path.replace(r2, r1)
	if DEBUG: print(f"DEBUG: normalize_path: outgoing path='{path}'",flush=True)
	return path

#
def gather_snippets_data(snippets_input_file_list):
	# before looping through snippets files
	# (1)	init the list to contain all the snippet data
	#		each list entry will be a tuple ( original_start_frame_number, recalculated_global_start_frame_number, number_of_frames_to_replace, '\\path\\to\\snippet\\snippet_filename.mp4' )
	seq_snippets_list = []
	# (2)	init a list containing the list of individial slideshows (one snippet file per individial slideshow) which were later concatenated in sequence to create a global slideshow .mp4
	seq_slideshow = []

	# this list of snippet files which is IN SEQUENCE so be careful with it
	snippets_input_file_list = normalize_path(snippets_input_file_list)
	try:
		if DEBUG: print(f"DEBUG: gather_snippets_data: Opening snippets_input_file_list '{snippets_input_file_list}'",flush=True,file=sys.stderr)
		with open(snippets_input_file_list, 'r') as file:
			snippets_input_file_list_lines = file.readlines()
	except IOError as e:
		print(f"Error: Failed to open or read Input file of snippets file list '{snippets_input_file_list}': {str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)

	# keep track of the frame numbers of a video where all of the slideshow videos have been concatenated in sequence
	seq_previous_ending_frame_num = -1	# initialize so the start frame number for the first clip with be (-1 + 1) = 0 .. base 0
	if DEBUG: print(f"DEBUG: gather_snippets_data: seq_previous_ending_frame_num init to {seq_previous_ending_frame_num}",flush=True)

	for iii, snippets_file_list_line in enumerate(snippets_input_file_list_lines):
		snippets_input_file = normalize_path(snippets_file_list_line.rstrip(os.linesep).strip('\r').strip('\n').strip())	# assume this is in the right format usable by python, i.e. like 'd:\\folder\\abc.txt'
		if DEBUG: print(f"DEBUG: ",flush=True)
		if DEBUG: print(f"DEBUG: gather_snippets_data: snippets_input_file {iii} contains '{snippets_input_file}'",flush=True)
		
		# a snippet file, one extra line is written as last line:
		#		start_frame_number_in_slideshow (0), end_frame_number_in_slideshow (being num_frames_in_slideshow - 1), 'filename of this slideshow in quotes'
		#		0, 2999, 'd:\slideshow_file.mp4'
		try:
			if DEBUG: print(f"DEBUG: gather_snippets_data: Opening snippets_input_file '{snippets_input_file}'",flush=True,file=sys.stderr)
			with open(snippets_input_file, 'r') as file:
				lines = file.readlines()
		except IOError as e:
			print(f"Error: Failed to open or read Input file of snippets '{snippets_input_file}': {str(e)}",flush=True,file=sys.stderr)
			sys.exit(1)
		total_snippets = len(lines) - 1
		print(f"Total audio snippets: {total_snippets} in '{snippets_input_file}'",flush=True)

		# keep track of the frame numbers for a video where all of the slideshow videos have been concatenated in sequence
		seq_start_frame_num = seq_previous_ending_frame_num + 1		# base 0

		# line format: 1234 125 'D:\folder1\folder2\audio_snippet_001.m4a'
		for i, L in enumerate(lines[:-1]):		# Process all lines except the last line
			line = L.rstrip(os.linesep).strip('\r').strip('\n').strip()
			if DEBUG: print(f"DEBUG: gather_snippets_data: snippets_input_file line {i} contains '{line}'",flush=True)
			line_parts = re.findall(r"^(\d+)\s+(\d+)\s+'([^']+)'$", line)		# https://stackoverflow.com/questions/76394785/python3-regex-pattern-to-separate-items-on-a-line
			start_frame_for_replacement = int(line_parts[0][0])
			snippet_num_frames_to_replace = int(line_parts[0][1])
			snippet_path = normalize_path(line_parts[0][2])
			if DEBUG: print(f"DEBUG: gather_snippets_data: snippets_input_file line {i} contains start_frame_for_replacement={start_frame_for_replacement} snippet_num_frames_to_replace={snippet_num_frames_to_replace} snippet_path={snippet_path}",flush=True)

			seq_start_frame_for_replacement = seq_start_frame_num + start_frame_for_replacement		# base 0; first will be 0 + frame num eg 0 + 0
			seq_end_frame_for_replacement = seq_start_frame_for_replacement + snippet_num_frames_to_replace - 1
				
			seq_snippet_dict = {	"snippet_original_start_frame_for_replacement" : start_frame_for_replacement, 
									"snippet_original_num_frames_to_replace"	   : snippet_num_frames_to_replace, 
									"snippet_seq_start_frame_for_replacement"	  : seq_start_frame_for_replacement, 
									"snippet_seq_end_frame_for_replacement"		: seq_end_frame_for_replacement, 
									"snippet_path"								 : snippet_path, 
									"from_snippets_input_file"					 : snippets_input_file
									}
			seq_snippets_list.append(seq_snippet_dict)
				
			print(f"Gathered info for audio snippet {i + 1}/{total_snippets}",flush=True)
		#
		# Perform a different action with the last line of a snippet file
		# line format: 0 123456 'D:\folder1\folder2\audio_snippet_001.m4a' ... base 0; start_frame_number_in_slideshow, end_frame_number_in_slideshow, 'filename of this slideshow in quotes'
		last_line = lines[-1].rstrip(os.linesep).strip('\r').strip('\n').strip()
		line_parts = re.findall(r"^(\d+)\s+(\d+)\s+'([^']+)'$", last_line)		# https://stackoverflow.com/questions/76394785/python3-regex-pattern-to-separate-items-on-a-line
		start_frame_number_of_slideshow = int(line_parts[0][0])
		end_frame_number_of_slideshow = int(line_parts[0][1])
		slideshow_path = line_parts[0][2]
		if DEBUG: print(f"DEBUG: gather_snippets_data: snippets_input_file LAST LINE contains start_frame_number_of_slideshow={start_frame_number_of_slideshow} end_frame_number_of_slideshow={end_frame_number_of_slideshow} slideshow_path={slideshow_path}",flush=True)
		
		# reclaculate the seq_start_frame_num ready for the next snippet file.
		# let's see an example;
		#	slideshow 1: 0 to 299 ... which is 300 frames, making a running total of 300 frames and the ending frame should be 299
		#		seq_previous_ending_frame_num was "-1" pre initialization
		#		calculate new seq_previous_ending_frame_num = -1 + 299 + 1 = 299 which is correct
		#	slideshow 2: 0 to 199 ... which is 200 frames, making a running total of 500 frames and the ending frame should be 499
		#		seq_previous_ending_frame_num was 299 per the last calculation
		#		calculate new seq_previous_ending_frame_num = 299 + 199 + 1 = 499 which is correct
		#
		tmp = seq_previous_ending_frame_num + end_frame_number_of_slideshow + 1
		seq_slideshow_dict = {	"slideshow_original_start_frame_number" : start_frame_number_of_slideshow, 
								"slideshow_original_end_frame_number"   : end_frame_number_of_slideshow,
								"slideshow_seq_start_frame_number"	 	: seq_previous_ending_frame_num + 1, 
								"slideshow_seq_end_frame_number"		: tmp, 
								"slideshow_path"						: slideshow_path
								}
		seq_slideshow.append(seq_slideshow_dict)
		seq_previous_ending_frame_num = tmp
	#
	# OK by now we have 2 lists, each containing some dicts
	#
	if DEBUG: print(f"",flush=True)
	if DEBUG: print(f"DEBUG: slideshow data derived from snippet files:\n{objPrettyPrint.pformat(seq_slideshow)}",flush=True)
	if DEBUG: print(f"",flush=True)
	if DEBUG: print(f"DEBUG: snippet data derived from snippet files:\n{objPrettyPrint.pformat(seq_snippets_list)}",flush=True)
	if DEBUG: print(f"",flush=True)
	#
	return seq_slideshow, seq_snippets_list

# ------------------------------------------------------------------------------------
# https://mediaarea.net/download/binary/libmediainfo0/
# https://mediaarea.net/en/MediaInfo/Download/Windows
# download 64bit DLL without installer, unzip, find Media
# put MediaInfoDLL3.py in your directory (portable setup) or site-packages directory

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
				'reversal_clockwise_rotation_degrees': (360 - positive_rotation) % 360,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			}
# ------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------
# SUPERSEDED - does not return num_frames
def xxxx_get_video_info(video_path):
	try:
		print(f"get_video_info: retrieving info from MediaInfo.parse",flush=True)
		media_info = MediaInfo.parse(video_path, full=True)
		if media_info is None:
			del media_info
			return None, None, None
		else:
			#for track in media_info.tracks:
			#	if track.track_type == "Video":
			#		video_track = track
			#		break
			#for track in media_info.tracks:
			#	if track.track_type == "Audio":
			#		audio_track = track
			#		break
			video_track = media_info.video_tracks[0]
			audio_track = media_info.audio_tracks[0]
			return media_info, video_track, audio_track
	except FileNotFoundError:
		print(f"get_video_info: MediaInfo: File not found: '{video_path}'",flush=True,file=sys.stderr)
		sys.exit(1)
	except IndexError:
		print(f"get_video_info: MediaInfo: No video track found in file: '{video_path}'",flush=True,file=sys.stderr)
		sys.exit(1)
	except ValueError:
		print(f"get_video_info: MediaInfo: Invalid video information in file: '{video_path}'",flush=True,file=sys.stderr)
		sys.exit(1)
	except OSError as e:
		print(f"get_video_info: MediaInfo: OSError error getting information from file: '{video_path}'\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"get_video_info: MediaInfo: Unexpected error getting information from file: '{video_path}'\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
# SUPERSEDED
# ------------------------------------------------------------------------------------

# Generate silent audio using FFmpeg
def generate_silent_padding(duration, silent_audio_path):
	if DEBUG: print(f"generate_silent_padding: generate silent padding: silent_audio_path='{silent_audio_path}'",flush=True,file=sys.stderr)
	ffmpeg_cmd = [
		FFMPEG_PATH,
		'-hide_banner',
		'-v', 'warning',
		'-nostats',
		'-threads', '2',
		'-f', 'lavfi',
		'-i', 'anullsrc',
		'-t', str(duration),
		'-c:a', 'aac',
		'-b:a', '256k',
		'-ar', '48000',
		'-y',
		silent_audio_path
	]
	try:
		if DEBUG: print(f"generate_silent_padding: ffmpeg_cmd='{ffmpeg_cmd}'",flush=True)
		subprocess.run(ffmpeg_cmd, check=True)
	except subprocess.CalledProcessError as e:
		print(f"generate_silent_padding: Error: subprocess.CalledProcessError Failed to transcode audio:\n{ffmpeg_cmd}\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"generate_silent_padding: Unexpected error: \n{ffmpeg_cmd}\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)

# Transcode audio to AAC using FFmpeg
def transcode_audio_to_aac(audio_file, output_file):
	if DEBUG: print(f"transcode_audio_to_aac: generate silent padding: audio_file='{audio_file}' output_file='{output_file}'",flush=True)
	ffmpeg_cmd = [
		FFMPEG_PATH,
		'-hide_banner',
		'-v', 'warning',
		'-nostats',
		'-threads', '2',
		'-i', audio_file,
		'-c:a', 'libfdk_aac',
		'-b:a', '256k',
		'-ar', '48000',
		'-y',
		output_file
	]
	try:
		if DEBUG: print(f"transcode_audio_to_aac: ffmpeg_cmd='{ffmpeg_cmd}'",flush=True)
		subprocess.run(ffmpeg_cmd, check=True)
	except subprocess.CalledProcessError as e:
		print(f"transcode_audio_to_aac: Error: subprocess.CalledProcessError Failed to transcode audio:\n{ffmpeg_cmd}\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"transcode_audio_to_aac: Unexpected error: \n{ffmpeg_cmd}\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
#
def mux_video_audio(video_file, audio_file, output_file):
	if DEBUG: print(f"mux_video_audio: video_file='{video_file}', audio_file='{audio_file}' output_file='{output_file}'",flush=True)
	mux_cmd = [
		FFMPEG_PATH,
		'-i', video_file,
		'-i', audio_file,
		'-map', '0:v',
		'-map', '1:a',
		'-c:v', 'copy',
		'-c:a', 'copy',
		'-movflags', '+faststart',
		'-y',
		output_file
	]
	try:
		if DEBUG: print(f"mux_video_audio: ffmpeg_cmd='{ffmpeg_cmd}'",flush=True)
		subprocess.run(mux_cmd, check=True)
	except subprocess.CalledProcessError as e:
		print(f"mux_video_audio: Error: subprocess.CalledProcessError Failed to mux video and audio:\n{mux_cmd}\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"mux_video_audio: Unexpected error: \n{mux_cmd}\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	# Check if Destination file exists
	if not os.path.exists(output_file):
		print(f"Error: Failed to mux video/audio files into: '{output_file}'.",flush=True,file=sys.stderr)
		sys.exit(1)

#
def replace_audio_with_snippets_from_file(input_video_path, video_fps, video_frame_count, video_duration_ms, seq_snippets_list, output_video_path, background_audio_path, fade_out_duration_ms, fade_in_duration_ms):
	# Load the background audio
	# LOOK AT THIS AND MAKE MORE ROBUST LIKE THE OTHER FUNCTION IN THE OTHER CODE 
	# ... if it was None then create silence audio for the expected duration (same length as video_duration_ms
	# ... else check file exists and load etc
	if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file.",flush=True)
	try:
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: 'from_file' to background_audio '{background_audio_path}'",flush=True)
		background_audio = AudioSegment.from_file(background_audio_path)
	except FileNotFoundError:
		print(f"replace_audio_with_snippets_from_file: background_audio File not found from AudioSegment.from_file('{background_audio_path}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except TypeError:
		print(f"replace_audio_with_snippets_from_file: background_audio Type mismatch or unsupported operation from AudioSegment.from_file('{background_audio_path}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except ValueError:
		print(f"replace_audio_with_snippets_from_file: background_audio Invalid or unsupported value from AudioSegment.from_file('{background_audio_path}')",flush=True,file=sys.stderr)
		sys.exit(1)
	except IOError:
		print(f"replace_audio_with_snippets_from_file: background_audio I/O error occurred '{background_audio_path}'",flush=True,file=sys.stderr)
		sys.exit(1)
	except OSError as e:
		print(f"replace_audio_with_snippets_from_file: background_audio Unexpected OSError from AudioSegment.from_file('{background_audio_path}')\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"replace_audio_with_snippets_from_file: background_audio Unexpected error from AudioSegment.from_file('{background_audio_path}')\n{str(e)}",flush=True,file=sys.stderr)
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
	edited_background_audio_path_tmp = r".\\temporary_edited_background_audio.mkv"
	try:
		if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: 'export' background_audio to file '{edited_background_audio_path_tmp}' with format='matroska', codec='libfdk_aac', bitrate='256k', parameters=['-ar', '48000', '-ac', '2']",flush=True)
		background_audio.export(edited_background_audio_path_tmp, format="matroska", codec="libfdk_aac", bitrate="256k", parameters=["-ar", "48000", "-ac", "2"])
	except FileNotFoundError:
		print(f"replace_audio_with_snippets_from_file: File not found from background_audio.export('{edited_background_audio_path_tmp}',...)",flush=True,file=sys.stderr)
		sys.exit(1)
	except TypeError:
		print(f"replace_audio_with_snippets_from_file: Type mismatch or unsupported operation from background_audio.export('{edited_background_audio_path_tmp}',...)",flush=True,file=sys.stderr)
		sys.exit(1)
	except ValueError:
		print(f"replace_audio_with_snippets_from_file: Invalid or unsupported value from background_audio.export('{edited_background_audio_path_tmp}',...)",flush=True,file=sys.stderr)
		sys.exit(1)
	except IOError:
		print(f"replace_audio_with_snippets_from_file: I/O error occurred from background_audio.export('{edited_background_audio_path_tmp}',...)",flush=True,file=sys.stderr)
		sys.exit(1)
	except OSError as e:
		print(f"replace_audio_with_snippets_from_file: Unexpected OSError from background_audio.export('{edited_background_audio_path_tmp}',...)\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f"replace_audio_with_snippets_from_file: Unexpected error from background_audio.export('{edited_background_audio_path_tmp}',...)\n{str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)
	del background_audio	# release a bunch of memory
	
	# Mux together the original video with the edited background audio
	if DEBUG: print(f"DEBUG: replace_audio_with_snippets_from_file: callng muxer '{input_video_path}'+'{edited_background_audio_path_tmp}'='{output_video_path}' ",flush=True)
	mux_video_audio(input_video_path, edited_background_audio_path_tmp, output_video_path)

	# Clean up temporary file(s)
	try:
		os.remove(edited_background_audio_path_tmp)
	except Exception as e:
		print(f"Error: Failed to clean up temporary file(s) '{edited_background_audio_path_tmp}' : {str(e)}",flush=True,file=sys.stderr)
		sys.exit(1)

	return output_video_path

#
if __name__ == "__main__":
	global DEBUG
	DEBUG = False

	# Pydub provides a logger that outputs the subprocess calls to help you track down issues:
	if DEBUG:
		pydub_logger = logging.getLogger("pydub.converter")
		pydub_logger.setLevel(logging.DEBUG)	
		pydub_logger.addHandler(logging.StreamHandler())
		#logging.DEBUG		Detailed information, typically of interest only when diagnosing problems.
		#logging.INFO		Confirmation that things are working as expected.
		#logging.WARNING	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’).
		#logging.ERROR		Due to a more serious problem, the software has not been able to perform some function.
		#logging.CRITICAL	A serious error, indicating that the program itself may be unable to continue running.

	if len(sys.argv) < 4:
		print(f"Error: number of commandline arguments is < 4 ({len(sys.argv)})",flush=True,file=sys.stderr)
		print(f"Usage: python 'script.py' -i main_video_path.mp4 -s snippets_file_list.txt -b background_music.m4a -o destination_video_path.mp4 ",flush=True,file=sys.stderr)
		sys.exit(0)
	
	parser = argparse.ArgumentParser(description='Replace audio snippets in a video with silence and specified audio snippets.')
	parser.add_argument('-i', '--input_video_path', help='Main video/audio file path, a .mp4 file', required=True)
	parser.add_argument('-s', '--snippets_input_file_list', help='Snippets info file containing a list of snippet files', required=True)
	parser.add_argument('-o', '--output_video_path', help='Resulting Destinaton video/audio file path, a .mp4', required=True)
	parser.add_argument('-b', '--background_audio_path', help='Background audio file path', required=False)

	args = parser.parse_args()

	input_video_path = args.input_video_path					# mandatory
	input_video_path = normalize_path(input_video_path)

	snippets_input_file_list = args.snippets_input_file_list	# mandatory
	snippets_input_file_list = normalize_path(snippets_input_file_list)

	output_video_path = args.output_video_path					# mandatory
	output_video_path = normalize_path(output_video_path)

	background_audio_path = args.background_audio_path			# optional; if omitted no audio processing will use a "silence" clip
	if background_audio_path is not None:
		background_audio_path = normalize_path(background_audio_path)
		print(f"Background audio path was specified: {background_audio_path}",flush=True)
	else:
		print(f"Background audio path was not specified, silence will be use as background.",flush=True)

	# determine the video framerate, video duration (number of frames) from the input_video_path
	media_info_dict = video_extract_metadata_via_MEDIAINFO(input_video_path)
	if media_info_dict is not None:
		if DEBUG: print(f"DEBUG: input_video_path: '{input_video_path}'\n {objPrettyPrint.pformat(media_info_dict)}",flush=True)
		video_fps = float(media_info_dict["FrameRate"])			# Frame Rate eg 25 or 27.976
		video_frame_count = int(media_info_dict["FrameCount"])		# number of frames
		video_duration_ms = int(media_info_dict["Duration"])		# Duration in milliseconds
		#frame_count = int(video_fps * (video_duration_ms / 1000))		# 
		del media_info_dict
		if DEBUG: print(f"DEBUG: Video file: {input_video_path}",flush=True)
		if DEBUG: print(f"DEBUG: Video Framerate: {video_fps}",flush=True)
		if DEBUG: print(f"DEBUG: Video Number of Frames: {video_frame_count}",flush=True)
		if DEBUG: print(f"DEBUG: Video Duration (ms): {video_duration_ms}",flush=True)
	else:
		print(f"Error: Failed to get metadata video_fps, video_duration_ms, video_frame_count from file '{input_video_path}'",flush=True,file=sys.stderr)
		sys.exit(1)

	# process file snippets_input_file_list to gather all snippet data into 2 LIST variables
	# 	seq_slideshow_list
	#		Each list entry contains a dict of attributes describing a slideshow that 
	#		has been consolidated into the main slideshow. i.e. one for each snippet input file.
	#		This list has no practical use here other than it is information for debugging
	#			{	"slideshow_original_start_frame_number" : start_frame_number_of_slideshow, 
	#				"slideshow_original_end_frame_number"   : end_frame_number_of_slideshow,
	#				"slideshow_seq_start_frame_number"	  	: seq_previous_ending_frame_num + 1, 
	#				"slideshow_seq_end_frame_number"		: tmp, 
	#				"slideshow_path"						: slideshow_path
	#			}
	#	seq_snippets_list
	# 		Each list entry contains a dict of attributes for snippets to be applied to the main background audio
	#			{	"snippet_original_start_frame_for_replacement"	: start_frame_for_replacement, 
	#				"snippet_original_num_frames_to_replace"	  	: snippet_num_frames_to_replace, 
	#				"snippet_seq_start_frame_for_replacement"	 	: seq_start_frame_for_replacement, 
	#				"snippet_seq_end_frame_for_replacement"			: seq_end_frame_for_replacement, 
	#				"snippet_path"								 	: snippet_path, 
	#				"from_snippets_input_file"					 	: snippets_input_file
	#			}
	seq_slideshow_list, seq_snippets_list = gather_snippets_data(snippets_input_file_list)

	print(f"Processing Main video/audio file                        : {input_video_path}",flush=True)
	print(f"Snippets info file containing a list of snippet files   : {snippets_input_file_list}",flush=True)
	print(f"Resulting file of muxed new video/audio                 : {output_video_path}",flush=True)
	print(f"Background ausio (or None for silence)                  : {background_audio_path}",flush=True)

	fade_in_duration_ms, fade_out_duration_ms = 500, 500
	
	destination_video_path = replace_audio_with_snippets_from_file(input_video_path, video_fps, video_frame_count, video_duration_ms, seq_snippets_list, output_video_path, background_audio_path, fade_out_duration_ms, fade_in_duration_ms)

	print(f"Finished! Resulting file of muxed video/audio: {destination_video_path}",flush=True)
