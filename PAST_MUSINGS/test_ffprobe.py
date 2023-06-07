#python3
# https://mediaarea.net/download/binary/libmediainfo0/
# https://mediaarea.net/download/binary/libmediainfo0/22.12/MediaInfo_DLL_22.12_Windows_x64_WithoutInstaller.zip
# https://mediaarea.net/en/MediaInfo/Download/Windows
#download 64bit DLL without installer, unzip, find MediaInfo.dll and MediaInfoDLL3.py
#put MediaInfoDLL3.py in your directory (portable setup) or site-packages directory
#MediaInfo.dll is loaded by ctypes with full path
#or put MediaInfo.dll in your directory (for portable setup) and load it: ctypes.CDLL('.\MediaInfo.dll')

#from pathlib import Path
#from ctypes import *
#from typing import Union
#import vapoursynth as vs
#from vapoursynth import core
#CDLL('.\MediaInfo.dll')   #'.\MediaInfo.dll' if in directory or include path
#from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption

import vapoursynth as vs
from vapoursynth import core
from datetime import datetime, date, time, timezone
from fractions import Fraction
from functools import partial
from pathlib import Path, PureWindowsPath
from ctypes import *		# for mediainfo ... load via ctypes.CDLL(r'.\MediaInfo.dll')
from typing import Union	# for mediainfo
from typing import NamedTuple
from collections import defaultdict, OrderedDict
import itertools
import math
import sys
import os
import subprocess
import glob
import configparser	# or in v3: configparser 
import yaml
import json
import pprint

from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.ExifTags import TAGS
#core.std.LoadPlugin(r'C:\SOFTWARE\Vapoursynth-x64\DGIndex\DGDecodeNV.dll') 	# note the hard-coded folder
#core.avs.LoadPlugin(r'C:\SOFTWARE\Vapoursynth-x64\DGIndex\DGDecodeNV.dll') 	# note the hard-coded folder

#CDLL(r'.\Vapoursynth_x64\MediaInfo.dll')				# note the hard-coded folder # per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
CDLL(r'MediaInfo.dll')				# note the hard-coded folder # per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
#from MediaInfoDLL3 import *

global ZIMG_RANGE_FULL
ZIMG_RANGE_FULL     = 1		# /**< Full (PC) dynamic range, 0-255 in 8 bits. */

TERMINAL_WIDTH = 132
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)

global IS_SILENT
IS_SILENT = False						# start silently
global IS_DEBUG
IS_DEBUG = False						# default DEBUG to False
global IS_DEBUG_SYSTEM_OVERRIDE
IS_DEBUG_SYSTEM_OVERRIDE = False		# for major debugging ONLY: this is always FALSE otherwide ...

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
class ffprobe:
	import os
	import sys
	import subprocess
	from pathlib import Path
	from typing import NamedTuple
	import json
	#
	def __init__(self, file_path):
		# Asume ffprobe.exe is in the current folder and/or path
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
		command_array =	["ffprobe.exe", "-hide_banner", "-v", "quiet", "-print_format", "json", "-show_programs", "-show_format", "-show_streams", "-show_private_data", file_path]
		#
		e = 0
		try:
			result = subprocess.run(command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
		except Exception as e:
			print(f"ffprobe.exe failed to run on '{file_path}', with error: '{result.stderr}'", file=sys.stderr, flush=True)
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
			print(f'ffprobe: ERROR: {file_path} loading ffprobe "json" data. json=\n{objPrettyPrint.pformat(self.streams_list)}', file=sys.stderr, flush=True)
			self.dict = {}
			pass
		self.format_dict = self.dict.get("format")
		if self.format_dict is None:
			print(f'ffprobe: ERROR: {file_path} contains no ffprobe "format" data. json=\n{objPrettyPrint.pformat(self.streams_list)}', file=sys.stderr, flush=True)
			self.format_dict = {}
			pass
		self.streams_list = self.dict.get("streams")
		if self.streams_list is None:
			print(f'ffprobe: ERROR: {file_path} contains no ffprobe "streams" data. json=\n{objPrettyPrint.pformat(self.streams_list)}', file=sys.stderr, flush=True)
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

pic_extensions = [".png", ".jpg", ".jpeg", ".gif"]	#always lowercase
vid_extensions = [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov", ".m2ts"]	#always lowercase

DIRECTORIES = [ r'D:\\ssTEST\\TEST_VIDS_IMAGES', r'E:\\MULTIMEDIA', ]
tn = 0
for d in DIRECTORIES:
	paths = Path(d).glob(f'**/*.*') # recursive
	n = 0
	for path in paths:
		if path.suffix.lower() in vid_extensions:
			tn = tn + 1
			n = n + 1
			print(f'\n{tn}.\tVideo File: {path}', file=sys.stderr, flush=True)
			obj_ffprobe = ffprobe(path)
			if obj_ffprobe.return_code != 0:
				print(f'{tn}. ERROR: ffprobe {path} returned error code {obj_ffprobe.return_code} error_code={obj_ffprobe.error_code} error={obj_ffprobe.error}', file=sys.stderr, flush=True)
		
			if obj_ffprobe.num_video_streams > 0:
				print(f'VIDEO format {objPrettyPrint.pformat(obj_ffprobe.format_dict)}', file=sys.stderr, flush=True)
				if obj_ffprobe.dict.get("format") is None:
					print(f'VIDEO format is None', file=sys.stderr, flush=True)
				else:
					print(f'duration={obj_ffprobe.format_dict.get("duration")}', file=sys.stderr, flush=True)
					print(f'bit_rate={obj_ffprobe.format_dict.get("bit_rate")}', file=sys.stderr, flush=True)
				print(f'video_index_pairs={obj_ffprobe.indices_video} \t audio_index_pairs={obj_ffprobe.indices_audio} \t first_video_stream_pair={obj_ffprobe.first_video_stream_pair} \t first_audio_stream_pair={obj_ffprobe.first_audio_stream_pair}', file=sys.stderr, flush=True)
				print(f'FIRST VIDEO stream {obj_ffprobe.first_video_stream_index}:\n{objPrettyPrint.pformat(obj_ffprobe.first_video)}', file=sys.stderr, flush=True)
				print(f'ff_width={obj_ffprobe.first_video.get("width")} \t ff_height={obj_ffprobe.first_video.get("height")} \t ff_isplay_aspect_ratio={obj_ffprobe.first_video.get("display_aspect_ratio")}', file=sys.stderr, flush=True)
				print(f'ff_codec_name={obj_ffprobe.first_video.get("codec_name")}', file=sys.stderr, flush=True)
				print(f'ff_nb_frames={obj_ffprobe.first_video.get("nb_frames")}', file=sys.stderr, flush=True)
				print(f'ff_rotation={obj_ffprobe.first_video.get("rotation")}', file=sys.stderr, flush=True)
				print(f'ff_r_frame_rate={obj_ffprobe.first_video.get("r_frame_rate")} ({eval(obj_ffprobe.first_video.get("r_frame_rate"))}) \t avg_frame_rate={obj_ffprobe.first_video.get("avg_frame_rate")} ({eval(obj_ffprobe.first_video.get("avg_frame_rate"))})', file=sys.stderr, flush=True)
				print(f'ff_chroma_location={obj_ffprobe.first_video.get("chroma_location")}', file=sys.stderr, flush=True)
				print(f'ff_color_space={obj_ffprobe.first_video.get("color_space")}', file=sys.stderr, flush=True)
				print(f'ff_color_matrix={obj_ffprobe.first_video.get("color_matrix")}', file=sys.stderr, flush=True)
				print(f'ff_color_transfer={obj_ffprobe.first_video.get("color_transfer")}', file=sys.stderr, flush=True)
				print(f'ff_color_primaries={obj_ffprobe.first_video.get("color_primaries")}', file=sys.stderr, flush=True)
				print(f'ff_color_range={obj_ffprobe.first_video.get("color_range")}', file=sys.stderr, flush=True)
				print(f'ff_field_order={obj_ffprobe.first_video.get("field_order")}', file=sys.stderr, flush=True)
				print(f'ff_space={obj_ffprobe.first_video.get("color_space")} ff_matrix={obj_ffprobe.first_video.get("color_matrix")} ff_transfer={obj_ffprobe.first_video.get("color_transfer")} ff_primaries={obj_ffprobe.first_video.get("color_primaries")} ff_range={obj_ffprobe.first_video.get("color_range")} ff_d_matrix={obj_ffprobe.first_video.get("displaymatrix")}', file=sys.stderr, flush=True)
			del obj_ffprobe
	print(f'\nFinished. {n} files ffprobed in "{d}".\n')
print(f'\nFinished. {tn} files ffprobed in total.\n')
