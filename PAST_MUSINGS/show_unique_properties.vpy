#python3, loading mediainfo readings for a media file using MediaInfo.dll

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
			#print(f'{right_now} DEBUG:', *args, **kwargs, file=sys.stderr, flush=True)
			print(f'DEBUG:', *args, **kwargs, file=sys.stderr, flush=True)

###
def print_NORMAL(*args, **kwargs):	# PRINT TO stderr
	# per https://stackoverflow.com/questions/5574702/how-do-i-print-to-stderr-in-python
	if (not IS_SILENT) or IS_DEBUG_SYSTEM_OVERRIDE:
		right_now = datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
		#print(f'{right_now}', *args, **kwargs, file=sys.stderr, flush=True)
		print(*args, **kwargs, file=sys.stderr, flush=True)

###
def print_missing_VFR_CFR(*args, **kwargs):	# PRINT TO file handle
	# per https://stackoverflow.com/questions/5574702/how-do-i-print-to-stderr-in-python
	if print_missing_VFR_CFR_to_file or IS_DEBUG_SYSTEM_OVERRIDE:
		right_now = datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
		#print(f'{right_now}', *args, **kwargs, file=sys.stderr, flush=True)
		print(*args, **kwargs, file=missing_VFR_CFR_handle, flush=True)

###
def print_VFR(*args, **kwargs):	# PRINT TO file handle
	# per https://stackoverflow.com/questions/5574702/how-do-i-print-to-stderr-in-python
	if print_VFR_to_file or IS_DEBUG_SYSTEM_OVERRIDE:
		right_now = datetime.now().strftime('%Y-%m-%d.%H:%M:%S.%f')
		#print(f'{right_now}', *args, **kwargs, file=sys.stderr, flush=True)
		print(*args, **kwargs, file=VFR_handle, flush=True)

###
def mediainfo_value(stream:int, track:int, param:str, path: Union[Path,str]) -> Union[int,float,str]:
	# A wrapper for mediainfo_value_worker, which gets and returns a single parameter
	# This function permits mediainfo_value_worker to be recycled elsewhere to be called mutiple times per one single MI.open
	global MI	# use the global, since we re-use it across functions
	if not stream in range(0,8):
		raise ValueError(f'ERROR: mediainfo_value: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
	if not isinstance(track, int) or track<0:
		raise ValueError(f'ERROR: mediainfo_value: track must be a positive integer')
	if not isinstance(param, str):
		raise ValueError(f'ERROR: mediainfo_value: param must be a string for particular stream, ion_Static("Info_Parameters")')
	if not isinstance(path, (Path, str)):
		raise ValueError(f'ERROR: mediainfo_value: path must be Path or str class')   
	MI.Open(str(path))
	val = mediainfo_value_worker(stream, track, param, path)
	MI.Close()
	return val

###
def mediainfo_value_worker(stream:int, track:int, param:str, path: Union[Path,str]) -> Union[int,float,str]:
	global MI	# use the global, since we re-use it across functions
	if not stream in range(0,8):
		raise ValueError(f'ERROR: mediainfo_value_worker: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
	if not isinstance(track, int) or track<0:
		raise ValueError(f'ERROR: mediainfo_value_worker: track must be a positive integer')
	if not isinstance(param, str):
		raise ValueError(f'ERROR: mediainfo_value_worker: param must be a string for particular stream, ion_Static("Info_Parameters")')
	if not isinstance(path, (Path, str)):
		raise ValueError(f'ERROR: mediainfo_value_worker: path must be Path or str class')    
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
		raise ValueError(f'ERROR: mediainfo_value_worker: wrong parameter: "{param}" for given stream: {stream}')

###
def get_PIL_exif_values(path):
	try:
		image = Image.open(str(path))
	except UnidentifiedImageError:
		return None
	except PermissionError:
		return None
	except Exception as e:
		return None
	#PIL_dict = {}
	#exif = dict(image.getexif())
	#for k,v in exif.items():
	#	if isinstance(v, bytes):
	#		v = r'byte data' #v.decode()
	#	#print_NORMAL(f'PIL EXIF DATA "{k}" = "{v}"')
	#	k = r'EXIF_' + str(k)
	#	PIL_dict[k] = v
	#exif = image.getexif()
	#exif_0x8769 = exif.get_ifd(0x8769)
	#print_NORMAL(f'type_0x8769={type(exif_0x8769)} exif_0x8769={exif_0x8769}')
	#exif_0x8769_d = dict(exif_0x8769)
	#print_NORMAL(f'type_0x8769_d={type(exif_0x8769)} exif_0x8769_d={exif_0x8769_d}')
	#for k,v in exif_0x8769_d.items():
	#	if isinstance(v, bytes):
	#		v = r'byte data' #v.decode()
	#	k = r'EXIF_0x8769_' + str(k)
	#	PIL_dict[k] = v
	#image.close()
	#
	PIL_dict = {}
	exif = image.getexif()
	for tag_id in exif:
		tag = TAGS.get(tag_id, tag_id)
		content = exif.get(tag_id)
		if isinstance(content, bytes):
			content = r'byte data' #content.decode()
		PIL_dict['EXIF_' + str(tag)] = content
	exif = image.getexif()
	exif_0x8769 = exif.get_ifd(0x8769)
	for tag_id in exif_0x8769:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_0x8769.get(tag_id)
		if isinstance(content, bytes):
			content = r'byte data' #content.decode()
		PIL_dict['EXIF_0x8769_' + str(tag)] = content
	return PIL_dict

###
def auto_rotation_value_PIL(path):
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
		#print_NORMAL(f'auto_rotation_value_PIL: except UnidentifiedImageError immediate return now')
		return rotation_degrees, "anti-clockwise"
	except PermissionError:
		#print_NORMAL(f'auto_rotation_value_PIL: except PermissionError Permission denied to load: {path} immediate return now')
		return rotation_degrees, "anti-clockwise"
	except Exception as e:
		#print_NORMAL(f'auto_rotation_value_PIL: except Exception {e} immediate return now')
		return rotation_degrees, "anti-clockwise"
	#print_NORMAL(f'auto_rotation_value_PIL: try on Image.open succeeded')
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
		#print_NORMAL(f'auto_rotation_value_PIL: except AttributeError during for key in ExifTags.TAGS.keys(), immediate return now {path}')
		return rotation_degrees, "anti-clockwise"
	else:
		if   value == 0:
			rotation_degrees = 0
			#print_NORMAL(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 0 degrees {path}')
		elif   value == 3:
			rotation_degrees = 180
			#print_NORMAL(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 180 degrees {path}')
		elif value == 8:
			rotation_degrees = 90
			#print_NORMAL(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by  90 degrees {path}')
		elif value == 6:
			rotation_degrees = 270
			#print_NORMAL(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 270 degrees {path}')
	image.close()	
	#print_NORMAL(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by {rotation_degrees} degrees {path}')
	return rotation_degrees, "anti-clockwise"

###
def auto_rotation_value_MediaInfo(path):
	# A TRICK FOR NEW PLAYERS ... MEDIAINFO YIELDS ROTATION VALUES FOR CLOCKWISE ROTATIONS for videos !!! NOT ANTI-CLOCKWISE like PIL !!!
	rotation_degrees = 0
	param = 'Rotation'
	value = mediainfo_value(Stream.Video, 0, param, path)
	if param == 'Rotation':
		if value is None:
			rotation_degrees = 0
		else:
			rotation_degrees = int(float(value)) # for some reason Rotation value type mediainfo carries as a string,  like: '180.00'
	#print_NORMAL(f'auto_rotation_value_MediaInfo: MediaInfo says auto-Rotating CLOCKWISE by {rotation_degrees} degrees {path}')
	return rotation_degrees, "clockwise"

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

###
def is_vfr_or_cfr_or_discard(mediainfo_specs):
	discard_video = False
	likely_VFR = False
	likely_VFR_fps = 0
	likely_VFR_fps_num = 0
	likely_VFR_fps_den = 0
	if mediainfo_specs.get("FrameRate_Mode") is not None and mediainfo_specs.get("FrameRate_Mode").lower() == 'CFR'.lower():
		discard_video = False
		likely_VFR = False
		likely_CFR_fps = eval(mediainfo_specs.get("FrameRate"))
		likely_CFR_fps_num = mediainfo_specs.get("FrameRate_Num")
		likely_CFR_fps_den = mediainfo_specs.get("FrameRate_Den")
		return discard_video, likely_VFR, likely_CFR_fps, likely_CFR_fps_num, likely_CFR_fps_den
	elif mediainfo_specs.get("FrameRate_Mode") is not None and mediainfo_specs.get("FrameRate_Mode").lower() == 'VFR'.lower():
		discard_video = False
		likely_VFR = True
		likely_VFR_fps = max(eval(mediainfo_specs.get("FrameRate_Maximum")), eval(mediainfo_specs.get("FrameRate"))) if mediainfo_specs.get("FrameRate_Maximum") <= 240 else (mediainfo_specs.get("FrameRate") * 2.0)	# else represents a rare but occurring edge case
		likely_VFR_fps_num = int(likely_VFR_fps * 10000)	# mediainfo_specs.get("FrameRate_Num")
		likely_VFR_fps_den = 10000							# mediainfo_specs.get("FrameRate_Den")
		return discard_video, likely_VFR, likely_VFR_fps, likely_VFR_fps_num, likely_VFR_fps_den
	#
	# if it gets to here, we likely need ffprobe resuts too
	#
	obj_ffprobe_specs = ffprobe(path)
	#
	if mediainfo_specs.get("FrameRate") is not None and mediainfo_specs.get("FrameRate_Num") is not None and mediainfo_specs.get("FrameRate_Den") is not None and mediainfo_specs.get("FrameRate_Maximum") is not None: # likley VFR if FrameRate_Maximum is not none
		likely_VFR = True
		likely_VFR_fps = max(eval(mediainfo_specs.get("FrameRate_Maximum")), eval(mediainfo_specs.get("FrameRate"))) if eval(mediainfo_specs.get("FrameRate_Maximum")) <= 240 else (eval(mediainfo_specs.get("FrameRate")) * 2.0)
		likely_VFR_fps_num = int(likely_VFR_fps * 10000)	# mediainfo_specs.get("FrameRate_Num")
		likely_VFR_fps_den = 10000							# mediainfo_specs.get("FrameRate_Den")
		del obj_ffprobe_specs
		return discard_video, likely_VFR, likely_VFR_fps, likely_VFR_fps_num, likely_VFR_fps_den
	#
	
	# this next one is WRONG WRONG WRONG since "FrameRate_Maximum is None" definitely exists for VFR
	if mediainfo_specs.get("FrameRate") is not None and mediainfo_specs.get("FrameRate_Num") is not None and mediainfo_specs.get("FrameRate_Den") is not None and mediainfo_specs.get("FrameRate_Maximum") is None: # likely CFR if FrameRate_Maximum is None and the others aren'[t
		discard_video = False
		likely_VFR = False
		likely_CFR_fps = eval(mediainfo_specs.get("FrameRate"))
		likely_CFR_fps_num = mediainfo_specs.get("FrameRate_Num")
		likely_CFR_fps_den = mediainfo_specs.get("FrameRate_Den")
		del obj_ffprobe_specs
		return discard_video, likely_VFR, likely_CFR_fps, likely_CFR_fps_num, likely_CFR_fps_den



	
	#
	if mediainfo_specs.get("FrameRate") is not None and mediainfo_specs.get("FrameRate_Num") is not None and mediainfo_specs.get("FrameRate_Den") is not None and obj_ffprobe_specs.first_video.get("r_frame_rate") is not None and obj_ffprobe_specs.first_video.get("avg_frame_rate") is not None:
		#'FrameRate': 25.0,
		#'FrameRate_Num': 25,
		#'FrameRate_Den': 1,
		#'r_frame_rate': '25/1',
		#'avg_frame_rate': '25/1',
		if (abs(eval(mediainfo_specs.get("FrameRate")) - (mediainfo_specs.get("FrameRate_Num")/mediainfo_specs.get("FrameRate_Den"))) < objSettings.precision_tolerance) and (abs(eval(obj_ffprobe_specs.first_video.get("r_frame_rate")) - eval(obj_ffprobe_specs.first_video.get("avg_frame_rate"))) < objSettings.precision_tolerance) : 
			likely_VFR = False
			likely_CFR_fps = eval(mediainfo_specs.get("FrameRate"))
			likely_CFR_fps_num = mediainfo_specs.get("FrameRate_Num")	
			likely_CFR_fps_den = mediainfo_specs.get("FrameRate_Den")
			return discard_video, likely_VFR, likely_CFR_fps, likely_CFR_fps_num, likely_CFR_fps_den
		else:
		
		
		
			likely_VFR = True
			likely_VFR_fps = max(eval(obj_ffprobe_specs.first_video.get("r_frame_rate")), eval(mediainfo_specs.get("FrameRate")), eval(obj_ffprobe_specs.first_video.get("avg_frame_rate")))
			if likely_VFR_fps > 240: likely_VFR_fps = 1 #??????????????????
			likely_VFR_fps_num = int(likely_VFR_fps * 10000)	# mediainfo_specs.get("FrameRate_Num")
			likely_VFR_fps_den = 10000							# mediainfo_specs.get("FrameRate_Den")



	elif mediainfo_specs.get("FrameRate") is not None and obj_ffprobe_specs.first_video.get("r_frame_rate") is not None and obj_ffprobe_specs.first_video.get("avg_frame_rate") is not None:
		#'FrameRate': 14.907,
		#'FrameRate_Num': None,
		#'FrameRate_Den': None,
		#'r_frame_rate': '20/1',
		#'avg_frame_rate': '10650000/714443', (14.90671754079752)
		if (abs(eval(obj_ffprobe_specs.first_video.get("r_frame_rate")) - eval(obj_ffprobe_specs.first_video.get("avg_frame_rate"))) < objSettings.precision_tolerance) and (abs(eval(obj_ffprobe_specs.first_video.get("avg_frame_rate")) - mediainfo_specs.get("FrameRate")) < objSettings.precision_tolerance): 
			likely_VFR = False
		else:
			likely_VFR = True
			# calculate this ... using split of max obj_ffprobe_specs.first_video.get("r_frame_rate"),obj_ffprobe_specs.first_video.get("avg_frame_rate")
			if eval(obj_ffprobe_specs.first_video.get("r_frame_rate")) >= eval(obj_ffprobe_specs.first_video.get("avg_frame_rate")):
				likely_vfr_split_list = obj_ffprobe_specs.first_video.get("r_frame_rate").split("/")
			else:
				likely_vfr_split_list = obj_ffprobe_specs.first_video.get("avg_frame_rate").split("/")
			likely_VFR_fps_num = likely_vfr_split_list[0]
			likely_VFR_fps_den = likely_vfr_split_list[1]
	elif obj_ffprobe_specs.first_video.get("r_frame_rate") is not None and obj_ffprobe_specs.first_video.get("avg_frame_rate") is not None:
		#'FrameRate': None,
		#'FrameRate_Num': None,
		#'FrameRate_Den': None,
		#'r_frame_rate': '20/1',
		#'avg_frame_rate': '20/1',
		if (abs(eval(obj_ffprobe_specs.first_video.get("r_frame_rate")) - eval(obj_ffprobe_specs.first_video.get("avg_frame_rate"))) < objSettings.precision_tolerance):
			likely_VFR = False
		else:
			likely_VFR = True
			# calculate this ... using split of max obj_ffprobe_specs.first_video.get("r_frame_rate"),obj_ffprobe_specs.first_video.get("avg_frame_rate")
			if eval(obj_ffprobe_specs.first_video.get("r_frame_rate")) >= eval(obj_ffprobe_specs.first_video.get("avg_frame_rate")):
				likely_vfr_split_list = obj_ffprobe_specs.first_video.get("r_frame_rate").split("/")
			else:
				likely_vfr_split_list = obj_ffprobe_specs.first_video.get("avg_frame_rate").split("/")
			likely_VFR_fps_num = likely_vfr_split_list[0]
			likely_VFR_fps_den = likely_vfr_split_list[1]
	else:
		#'FrameRate': None,
		#'FrameRate_Num': None,
		#'FrameRate_Den': None,
		# ff_first_video={} ... so the .get will return None
		#nothing known from mediainfo nor from ffprobe ... it happens
		discard_video = True
	#
	return discard_video, likely_VFR, likely_VFR_fps, likely_VFR_fps_num, likely_VFR_fps_den

#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------
# print available parameters to query - look under the Video section in that.
#print_NORMAL(f'{objPrettyPrint.pformat(MI.Option_Static("Info_Parameters"))}')
#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------

#---
# The Full Lot
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
# Only a few
mi_video_params_2 = [
	'Rotation',                                      # : Rotation as a real number eg 180.00
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

#---
# for the moment, hacked for testing
if  len(sys.argv) < 2:
	#DIRECTORIES = r"E:\\multimedia"
	DIRECTORIES = [ r'D:\\ssTEST\\TEST_VIDS_IMAGES', r"E:\\multimedia", ]
else:
	DIRECTORIES = str(sys.argv[1])

print_missing_VFR_CFR_to_file = True
print_VFR_to_file = True

class Settings():
	precision_tolerance = 0.0005
objSettings = Settings()

if print_missing_VFR_CFR_to_file:
	missing_VFR_CFR_file = str(Path(__file__)) + ".missing_VFR_CFR.log"
	missing_VFR_CFR_handle = open(missing_VFR_CFR_file, 'w')

if print_VFR_to_file:
	VFR_file = str(Path(__file__)) + ".VFR.log"
	VFR_handle = open(VFR_file, 'w')

do_pics = False
MI = MediaInfo()
vid_extensions = [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov", ".m2ts"]	#always lowercase
pic_extensions = [".png", ".jpg", ".jpeg", ".gif"]	#always lowercase
tn = 0
for d in DIRECTORIES:
	paths = Path(d).glob(f'**/*.*') # recursive
	n = 0
	for path in paths:
		if path.suffix.lower() in vid_extensions:
			tn = tn + 1
			n = n + 1
			print_NORMAL(f'\n{tn}. Video File: {path}\n')
			MI.Open(str(path))
			mediainfo_specs = {}
			for param in mi_video_params_1:		# mi_video_params_2
				value = mediainfo_value(Stream.Video, track=0, param=param, path=path)
				#print_NORMAL(f'"{param}" = \t\t\t\t"{value}"\t\t\ttype={type(value)}\t\t\tisinstance(value,str)={isinstance(value,str)}\t\tisinstance(value,int)={isinstance(value,int)}\t\tisinstance(value,bool)={isinstance(value,bool)}\t\tisinstance(value,float)={isinstance(value,float)}')
				mediainfo_specs[param] = value	# any of str, bool, int, float, etc
			MI.Close()
			print_NORMAL(f'{tn}. mediainfo_specs=\n{objPrettyPrint.pformat(mediainfo_specs)}')
			#
			obj_ffprobe_specs = ffprobe(path)
			if obj_ffprobe_specs.return_code != 0:
				print_NORMAL(f'{tn}. ERROR: ffprobe {path} returned error code {obj_ffprobe_specs.return_code} error_code={obj_ffprobe_specs.error_code} error={obj_ffprobe_specs.error}')
			if obj_ffprobe_specs.num_video_streams <= 0:
				print_NORMAL(f'{tn}. ERROR: ffprobe {path} RETURNED VIDEO STREAMS')
			if obj_ffprobe_specs.format_dict is None:
				print_NORMAL(f'{tn}. ERROR: ffprobe VIDEO FORMAT IS None')
			print_NORMAL(f'VIDEO {objPrettyPrint.pformat(obj_ffprobe_specs.dict)}')
			print_NORMAL(f'duration={obj_ffprobe_specs.format_dict.get("duration")}')
			print_NORMAL(f'bit_rate={obj_ffprobe_specs.format_dict.get("bit_rate")}')
			print_NORMAL(f'width/height/dar ff={obj_ffprobe_specs.first_video.get("width")} x {obj_ffprobe_specs.first_video.get("height")} ### ff_dar={obj_ffprobe_specs.first_video.get("display_aspect_ratio")} ... mi={mediainfo_specs.get("width")} x {mediainfo_specs.get("height")} ### mi_dar={mediainfo_specs.get("DisplayAspectRatio")}')
			print_NORMAL(f'ff_codec_name={obj_ffprobe_specs.first_video.get("codec_name")} ... mi_Format={mediainfo_specs.get("Format")}')
			print_NORMAL(f'ff_nb_frames={obj_ffprobe_specs.first_video.get("nb_frames")} ... mi_FrameCount={mediainfo_specs.get("FrameCount")}')
			print_NORMAL(f'ff_rotation={obj_ffprobe_specs.first_video.get("rotation")} ... mi_Rotation={mediainfo_specs.get("Rotation")}')
			print_NORMAL(f'ff_r_frame_rate={obj_ffprobe_specs.first_video.get("r_frame_rate")} ({eval(obj_ffprobe_specs.first_video.get("r_frame_rate")) if obj_ffprobe_specs.first_video.get("r_frame_rate") is not None else None}) ... Mode={mediainfo_specs.get("FrameRate_Mode")} ### mi_Num={mediainfo_specs.get("FrameRate_Num")} ### mi_Den={mediainfo_specs.get("FrameRate_Den")} ### mi_FrameRate={mediainfo_specs.get("FrameRate")} ### ',
						 f' ff_avg={obj_ffprobe_specs.first_video.get("avg_frame_rate")} ### ({eval(obj_ffprobe_specs.first_video.get("avg_frame_rate")) if obj_ffprobe_specs.first_video.get("avg_frame_rate") is not None else None}) ... mi_Minimum={mediainfo_specs.get("FrameRate_Minimum")} ### mi_Nominal={mediainfo_specs.get("FrameRate_Nominal")} ### mi_Maximum={mediainfo_specs.get("FrameRate_Maximum")} ### mi_Real={mediainfo_specs.get("FrameRate_Real")}')
			print_NORMAL(f'ff_chroma_location={obj_ffprobe_specs.first_video.get("chroma_location")} ... mi_ChromaSubsampling={mediainfo_specs.get("ChromaSubsampling")}')
			print_NORMAL(f'ff_color_space={obj_ffprobe_specs.first_video.get("color_space")} ... mi_ColorSpace={mediainfo_specs.get("ColorSpace")} ### mi_Standard={mediainfo_specs.get("Standard")}')
			print_NORMAL(f'ff_color_matrix={obj_ffprobe_specs.first_video.get("color_matrix")} ### ff_matrix={obj_ffprobe_specs.first_video.get("displaymatrix")} ... mi_matrix_coefficients={mediainfo_specs.get("matrix_coefficients")} ### mi_Standard={mediainfo_specs.get("Standard")}')
			print_NORMAL(f'ff_color_transfer={obj_ffprobe_specs.first_video.get("color_transfer")} ... mi_transfer_characteristics={mediainfo_specs.get("transfer_characteristics")} ### mi_Standard={mediainfo_specs.get("Standard")} ... ff_matrix={obj_ffprobe_specs.first_video.get("displaymatrix")}')
			print_NORMAL(f'ff_color_primaries={obj_ffprobe_specs.first_video.get("color_primaries")} ... mi_colour_primaries={mediainfo_specs.get("colour_primaries")} ### mi_Standard={mediainfo_specs.get("Standard")} ... ff_matrix={obj_ffprobe_specs.first_video.get("displaymatrix")}')
			print_NORMAL(f'ff_color_range={obj_ffprobe_specs.first_video.get("color_range")} ... mi_colour_range={mediainfo_specs.get("colour_range")} ### mi_Standard={mediainfo_specs.get("Standard")} ... ff_matrix={obj_ffprobe_specs.first_video.get("displaymatrix")}')
			print_NORMAL(f'ff_field_order={obj_ffprobe_specs.first_video.get("field_order")} ... mi_ScanType={mediainfo_specs.get("ScanType")} ### mi_ScanOrder={mediainfo_specs.get("ScanOrder")} ### mi_ScanOrder_Stored={mediainfo_specs.get("ScanOrder_Stored")} ### mi_ScanOrder_StoredDisplayedInverted={mediainfo_specs.get("ScanOrder_StoredDisplayedInverted")} ### mi_Standard={mediainfo_specs.get("Standard")}')
			#print_NORMAL(f'ff_space={obj_ffprobe_specs.first_video.get("color_space")} ### ff_matrix={obj_ffprobe_specs.first_video.get("color_matrix")} ### ff_transfer={obj_ffprobe_specs.first_video.get("color_transfer")} ### ff_primaries={obj_ffprobe_specs.first_video.get("color_primaries")} ### ff_range={obj_ffprobe_specs.first_video.get("color_range")} ### ff_matrix={obj_ffprobe_specs.first_video.get("displaymatrix")}')
			if mediainfo_specs.get("FrameRate_Mode") is None or mediainfo_specs.get("FrameRate_Mode") == '':
				if print_missing_VFR_CFR_to_file:
					print_missing_VFR_CFR(f'{tn}. Video File: {path}\n')
					print_missing_VFR_CFR(f'ff_r_frame_rate={obj_ffprobe_specs.first_video.get("r_frame_rate")} ({eval(obj_ffprobe_specs.first_video.get("r_frame_rate")) if obj_ffprobe_specs.first_video.get("r_frame_rate") is not None else None}) ... Mode={mediainfo_specs.get("FrameRate_Mode")} ### mi_Num={mediainfo_specs.get("FrameRate_Num")} ### mi_Den={mediainfo_specs.get("FrameRate_Den")} ### mi_FrameRate={mediainfo_specs.get("FrameRate")} ### ',
											f' ff_avg={obj_ffprobe_specs.first_video.get("avg_frame_rate")} ### ({eval(obj_ffprobe_specs.first_video.get("avg_frame_rate")) if obj_ffprobe_specs.first_video.get("avg_frame_rate") is not None else None}) ... mi_Minimum={mediainfo_specs.get("FrameRate_Minimum")} ### mi_Nominal={mediainfo_specs.get("FrameRate_Nominal")} ### mi_Maximum={mediainfo_specs.get("FrameRate_Maximum")} ### mi_Real={mediainfo_specs.get("FrameRate_Real")}')
					print_missing_VFR_CFR(f'{tn}. mediainfo_specs=\n{objPrettyPrint.pformat(mediainfo_specs)}')
					print_missing_VFR_CFR(f'{tn}. ff_format_dict=\n{objPrettyPrint.pformat(obj_ffprobe_specs.format_dict)}')
					print_missing_VFR_CFR(f'{tn}. ff_first_video=\n{objPrettyPrint.pformat(obj_ffprobe_specs.first_video)}')

					if mediainfo_specs.get("FrameRate") is not None and mediainfo_specs.get("FrameRate_Num") is not None and mediainfo_specs.get("FrameRate_Den") is not None and mediainfo_specs.get("FrameRate_Maximum") is not None: # likley VFR if FrameRate_Maximum is not none
						print_missing_VFR_CFR(f'{tn}. POSSIBLE VFR (a): ("FrameRate") {mediainfo_specs.get("FrameRate")} is not None and ("FrameRate_Num") {mediainfo_specs.get("FrameRate_Num")} is not None and ("FrameRate_Den") {mediainfo_specs.get("FrameRate_Den")} is not None and ("FrameRate_Maximum") {mediainfo_specs.get("FrameRate_Maximum")} is not None')

					if mediainfo_specs.get("FrameRate") is not None and mediainfo_specs.get("FrameRate_Maximum") is not None: # likley VFR if FrameRate_Maximum is not none
						print_missing_VFR_CFR(f'{tn}. POSSIBLE VFR (b): ("FrameRate") {mediainfo_specs.get("FrameRate")} is not None and ("FrameRate_Maximum") {mediainfo_specs.get("FrameRate_Maximum")} is not None')

					if mediainfo_specs.get("FrameRate_Maximum") is not None: # likley VFR if FrameRate_Maximum is not none
						print_missing_VFR_CFR(f'{tn}. POSSIBLE VFR (c): ("FrameRate_Maximum") {mediainfo_specs.get("FrameRate_Maximum")} is not None')

					if mediainfo_specs.get("FrameRate") is not None and mediainfo_specs.get("FrameRate_Num") is not None and mediainfo_specs.get("FrameRate_Den") is not None and mediainfo_specs.get("FrameRate_Maximum") is None: # likely CFR if FrameRate_Maximum is None and the others aren'[t
						print_missing_VFR_CFR(f'{tn}. POSSIBLE WRONG CFR DETECTION, ("FrameRate_Maximum") can be NONE for VFR  (d): ("FrameRate") {mediainfo_specs.get("FrameRate")} is not None and ("FrameRate_Num") {mediainfo_specs.get("FrameRate_Num")} is not None and ("FrameRate_Den") {mediainfo_specs.get("FrameRate_Den")} is not None and ("FrameRate_Maximum") {mediainfo_specs.get("FrameRate_Maximum")} is None')

					print_missing_VFR_CFR(f'\n\n')
			if  mediainfo_specs.get("FrameRate_Mode") is not None and mediainfo_specs.get("FrameRate_Mode").lower() == 'VFR'.lower():
				if print_VFR_to_file:
					print_VFR(f'{tn}. Video File: {path}\n')
					print_VFR(f'{tn}. ff_r_frame_rate={obj_ffprobe_specs.first_video.get("r_frame_rate")} ({eval(obj_ffprobe_specs.first_video.get("r_frame_rate")) if obj_ffprobe_specs.first_video.get("r_frame_rate") is not None else None}) ... FrameRate_Mode={mediainfo_specs.get("FrameRate_Mode")} ### mi_FrameRate_Num={mediainfo_specs.get("FrameRate_Num")} ### mi_FrameRate_Den={mediainfo_specs.get("FrameRate_Den")} ### mi_FrameRate={mediainfo_specs.get("FrameRate")} ### ')
					print_VFR(f'{tn}. ff_avg_frame_rate={obj_ffprobe_specs.first_video.get("avg_frame_rate")} ### ({eval(obj_ffprobe_specs.first_video.get("avg_frame_rate")) if obj_ffprobe_specs.first_video.get("avg_frame_rate") is not None else None}) ... mi_FrameRate_Mode={mediainfo_specs.get("FrameRate_Mode")} ### mi_FrameRate_Minimum={mediainfo_specs.get("FrameRate_Minimum")} ### mi_FrameRate_Nominal={mediainfo_specs.get("FrameRate_Nominal")} ### mi_FrameRate_Maximum={mediainfo_specs.get("FrameRate_Maximum")} ### mi_FrameRate_Real={mediainfo_specs.get("FrameRate_Real")}')
					print_VFR(f'{tn}. mediainfo_specs=\n{objPrettyPrint.pformat(mediainfo_specs)}')
					print_VFR(f'{tn}. ff_format_dict=\n{objPrettyPrint.pformat(obj_ffprobe_specs.format_dict)}')
					print_VFR(f'{tn}. ff_first_video=\n{objPrettyPrint.pformat(obj_ffprobe_specs.first_video)}')
					print_VFR(f'\n\n')
			del obj_ffprobe_specs
		if do_pics and path.suffix.lower() in pic_extensions:
			print_NORMAL(f'Image File: {path}')
			print_NORMAL(f'Image File: {path}')
			r, d = auto_rotation_value_PIL(path)
			print_NORMAL(f'PIL Rotation Value={r} {d}')
			PIL_exif_values = get_PIL_exif_values(path)
			print_NORMAL(f'{objPrettyPrint.pformat(PIL_exif_values)}')
	print(f'\nFinished. {n} files ffprobed in "{d}".\n')
print(f'\nFinished. {tn} files ffprobed in total.\n')
del MI
if print_missing_VFR_CFR_to_file:
	missing_VFR_CFR_handle.close()
sys.exit()



'''
MediaInfo parameters which can be queried

('General \r\n'
 'Count                     : Count of objects available in this stream\r\n'
 'Status                    : Status of bit field (0=IsAccepted, 1=IsFilled, 2=IsUpdated, 3=IsFinished)\r\n'
 'StreamCouprint("")
print("Inform with Complete=true")
MI.Option_Static("Complete", "1")
print(MI.Inform())videont               : Count of streams of this kind available (base=1)\r\n'
 'StreamKind                : Stream type name\r\n'
 'StreamKind/String         : Stream type name\r\n'
 'StreamKindID              : Stream number (base=0)\r\n'
 'StreamKindPos             : Number of the stream, when multiple (base=1)\r\n'
 'StreamOrder               : Stream order in the file for type of stream (base=0)\r\n'
 'FirstPacketOrder          : Order of the first fully decodable packet met in the file for stream type (base=0)\r\n'
 'Inform                    : Last **Inform** call\r\n'
 'ID                        : The ID for this stream in this file\r\n'
 'ID/String                 : The ID for this stream in this file\r\n'
 'OriginalSourceMedium_ID   : The ID for this stream in the original medium of the material\r\n'
 'OriginalSourceMedium_ID/S : The ID for this stream in the original medium of the material\r\n'
 'UniqueID                  : The unique ID for this stream, should be copied with stream copy\r\n'
 'UniqueID/String           : The unique ID for this stream, should be copied with stream copy\r\n'
 'MenuID                    : The menu ID for this stream in this file\r\n'
 'MenuID/String             : The menu ID for this stream in this file\r\n'
 'GeneralCount              : Number of general streams\r\n'
 'VideoCount                : Number of video streams\r\n'
 'AudioCount                : Number of audio streams\r\n'
 'TextCount                 : Number of text streams\r\n'
 'OtherCount                : Number of other streams\r\n'
 'ImageCount                : Number of image streams\r\n'
 'MenuCount                 : Number of menu streams\r\n'
 'Video_Format_List         : Video Codecs in this file, separated by /\r\n'
 'Video_Format_WithHint_Lis : Video Codecs in this file with popular name (hint), separated by /\r\n'
 'Video_Codec_List          : Deprecated, do not use in new projects\r\n'
 'Video_Language_List       : Video languages in this file, full names, separated by /\r\n'
 'Audio_Format_List         : Audio Codecs in this file,separated by /\r\n'
 'Audio_Format_WithHint_Lis : Audio Codecs in this file with popular name (hint), separated by /\r\n'
 'Audio_Codec_List          : Deprecated, do not use in new projects\r\n'
 'Audio_Language_List       : Audio languages in this file separated by /\r\n'
 'Text_Format_List          : Text Codecs in this file, separated by /\r\n'
 'Text_Format_WithHint_List : Text Codecs in this file with popular name (hint),separated by /\r\n'
 'Text_Codec_List           : Deprecated, do not use in new projects\r\n'
 'Text_Language_List        : Text languages in this file, separated by /\r\n'
 'Other_Format_List         : Other formats in this file, separated by /\r\n'
 'Other_Format_WithHint_Lis : Other formats in this file with popular name (hint), separated by /\r\n'
 'Other_Codec_List          : Deprecated, do not use in new projects\r\n'
 'Other_Language_List       : Chapters languages in this file, separated by /\r\n'
 'Image_Format_List         : Image Codecs in this file, separated by /\r\n'
 'Image_Format_WithHint_Lis : Image Codecs in this file with popular name (hint), separated by /\r\n'
 'Image_Codec_List          : Deprecated, do not use in new projects\r\n'
 'Image_Language_List       : Image languages in this file, separated by /\r\n'
 'Menu_Format_List          : Menu Codecs in this file, separated by /\r\n'
 'Menu_Format_WithHint_List : Menu Codecs in this file with popular name (hint),separated by /\r\n'
 'Menu_Codec_List           : Deprecated, do not use in new projects\r\n'
 'Menu_Language_List        : Menu languages in this file, separated by /\r\n'
 'CompleteName              : Complete name (Folder+Name+Extension)\r\n'
 'FolderName                : Folder name only\r\n'
 'FileNameExtension         : File name and extension\r\n'
 'FileName                  : File name only\r\n'
 'FileExtension             : File extension only\r\n'
 'CompleteName_Last         : Complete name (Folder+Name+Extension) of the last file (in the case of a sequence of files)\r\n'
 'FolderName_Last           : Folder name only of the last file (in the case of a sequence of files)\r\n'
 'FileNameExtension_Last    : File name and extension of the last file (in the case of a sequence of files)\r\n'
 'FileName_Last             : File name only of the last file (in the case of a sequence of files)\r\n'
 'FileExtension_Last        : File extension only of the last file (in the case of a sequence of files)\r\n'
 'Format                    : Format used\r\n'
 'Format/String             : Format used + additional features\r\n'
 'Format/Info               : Info about this Format\r\n'
 'Format/Url                : Link to a description of this format\r\n'
 'Format/Extensions         : Known extensions of this format\r\n'
 'Format_Commercial         : Commercial name used by vendor for these settings or Format field if there is no difference\r\n'
 'Format_Commercial_IfAny   : Commercial name used by vendor for these settings if there is one\r\n'
 'Format_Version            : Version of this format\r\n'
 "Format_Profile            : Profile of the Format (old XML: 'Profile@Level' format\r\n"
 'Format_Level              : Level of the Format (only MIXML)\r\n'
 'Format_Compression        : Compression method used\r\n'
 'Format_Settings           : Settings needed for decoder used\r\n'
 'Format_AdditionalFeatures : Format features needed for fully supporting the content\r\n'
 'InternetMediaType         : Internet Media Type (aka MIME Type, Content-Type)\r\n'
 'CodecID                   : Codec ID (found in some containers)\r\n'
 'CodecID/String            : Codec ID (found in some containers)\r\n'
 'CodecID/Info              : Info about this Codec\r\n'
 'CodecID/Hint              : A hint/popular name for this Codec\r\n'
 'CodecID/Url               : A link to more details about this Codec ID\r\n'
 'CodecID_Description       : Manual description given by the container\r\n'
 'CodecID_Version           : Version of the CodecID\r\n'
 'CodecID_Compatible        : Compatible CodecIDs\r\n'
 'Interleaved               : If Audio and video are muxed\r\n'
 'Codec                     : Deprecated, do not use in new projects\r\n'
 'Codec/String              : Deprecated, do not use in new projects\r\n'
 'Codec/Info                : Deprecated, do not use in new projects\r\n'
 'Codec/Url                 : Deprecated, do not use in new projects\r\n'
 'Codec/Extensions          : Deprecated, do not use in new projects\r\n'
 'Codec_Settings            : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Automatic  : Deprecated, do not use in new projects\r\n'
 'FileSize                  : File size in bytes\r\n'
 'FileSize/String           : File size (with measure)\r\n'
 'FileSize/String1          : File size (with measure, 1 digit mini)\r\n'
 'FileSize/String2          : File size (with measure, 2 digit mini)\r\n'
 'FileSize/String3          : File size (with measure, 3 digit mini)\r\n'
 'FileSize/String4          : File size (with measure, 4 digit mini)\r\n'
 'Duration                  : Play time of the stream (in ms)\r\n'
 'Duration/String           : Play time in format : XXx YYy only, YYy omitted if zero\r\n'
 'Duration/String1          : Play time in format : HHh MMmn SSs MMMms, XX omitted if zero\r\n'
 'Duration/String2          : Play time in format : XXx YYy only, YYy omitted if zero\r\n'
 'Duration/String3          : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration/String4          : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration/String5          : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_Start \r\n'
 'Duration_End \r\n'
 'OverallBitRate_Mode       : Bit rate mode of all streams (VBR, CBR)\r\n'
 'OverallBitRate_Mode/Strin : Bit rate mode of all streams (Variable, Constant)\r\n'
 'OverallBitRate            : Bit rate of all streams (in bps)\r\n'
 'OverallBitRate/String     : Bit rate of all streams (with measure)\r\n'
 'OverallBitRate_Minimum    : Minimum bit rate (in bps)\r\n'
 'OverallBitRate_Minimum/St : Minimum bit rate (with measurement)\r\n'
 'OverallBitRate_Nominal    : Nominal bit rate (in bps)\r\n'
 'OverallBitRate_Nominal/St : Nominal bit rate (with measurement)\r\n'
 'OverallBitRate_Maximum    : Maximum bit rate (in bps)\r\n'
 'OverallBitRate_Maximum/St : Maximum bit rate (with measurement)\r\n'
 'FrameRate                 : Frames per second\r\n'
 'FrameRate/String          : Frames per second (with measurement)\r\n'
 'FrameRate_Num             : Frames per second, numerator\r\n'
 'FrameRate_Den             : Frames per second, denominator\r\n'
 'FrameCount                : Frame count (if a frame contains a count of samples)\r\n'
 'Delay                     : Delay fixed in the stream (relative) (in ms)\r\n'
 'Delay/String              : Delay with measurement\r\n'
 'Delay/String1             : Delay with measurement\r\n'
 'Delay/String2             : Delay with measurement\r\n'
 'Delay/String3             : format : HH:MM:SS.MMM\r\n'
 'Delay/String4             : Delay in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay/String5             : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Settings            : Delay settings (in case of timecode, for example)\r\n'
 'Delay_DropFrame           : Delay drop frame\r\n'
 'Delay_Source              : Delay source (Container, Stream, empty)\r\n'
 'Delay_Source/String       : Delay source (Container, Stream, empty)\r\n'
 'StreamSize                : Stream size (in bytes)\r\n'
 'StreamSize/String \r\n'
 'StreamSize/String1 \r\n'
 'StreamSize/String2 \r\n'
 'StreamSize/String3 \r\n'
 'StreamSize/String4 \r\n'
 'StreamSize/String5        : Stream size with proportion\r\n'
 'StreamSize_Proportion     : Stream size divided by file size\r\n'
 'StreamSize_Demuxed        : StreamSize after demux (in bytes)\r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed with percentage value\r\n'
 'StreamSize_Demuxed/String1 \r\n'
 'StreamSize_Demuxed/String2 \r\n'
 'StreamSize_Demuxed/String3 \r\n'
 'StreamSize_Demuxed/String4 \r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed with percentage value (note: theoretical value, not for real use)\r\n'
 'HeaderSize \r\n'
 'DataSize \r\n'
 'FooterSize \r\n'
 'IsStreamable \r\n'
 'Album_ReplayGain_Gain     : The gain to apply to reach 89dB SPL on playback\r\n'
 'Album_ReplayGain_Gain/String \r\n'
 'Album_ReplayGain_Peak     : The maximum absolute peak value of the item\r\n'
 'Encryption \r\n'
 'Encryption_Format \r\n'
 'Encryption_Length \r\n'
 'Encryption_Method \r\n'
 'Encryption_Mode \r\n'
 'Encryption_Padding \r\n'
 'Encryption_InitializationVector \r\n'
 'UniversalAdID/String      : Universal Ad-ID, see https://ad-id.org\r\n'
 'UniversalAdID_Registry    : Universal Ad-ID registry\r\n'
 'UniversalAdID_Value       : Universal Ad-ID value\r\n'
 'Title                     : (Generic)Title of file\r\n'
 'Title_More                : (Generic)More info about the title of file\r\n'
 'Title/Url                 : (Generic)Url\r\n'
 'Domain                    : Universe movies belong to, e.g. Star Wars, Stargate, Buffy, Dragonball\r\n'
 'Collection                : Name of the series, e.g. Star Wars movies, Stargate SG-1, Stargate Atlantis, Buffy, Angel\r\n'
 'Season                    : Name of the season, e.g. Star Wars first Trilogy, Season 1\r\n'
 'Season_Position           : Number of the Season\r\n'
 'Season_Position_Total     : Place of the season, e.g. 2 of 7\r\n'
 'Movie                     : Name of the movie. Eg : Star Wars, A New Hope\r\n'
 'Movie_More                : More info about the movie\r\n'
 'Movie/Country             : Country, where the movie was produced\r\n'
 'Movie/Url                 : Homepage for the movie\r\n'
 'Album                     : Name of an audio-album. Eg : The Joshua Tree\r\n'
 'Album_More                : More info about the album\r\n'
 'Album/Sort \r\n'
 'Album/Performer           : Album performer/artist of this file\r\n'
 'Album/Performer/Sort \r\n'
 'Album/Performer/Url       : Homepage of the album performer/artist\r\n'
 'Comic                     : Name of the comic.\r\n'
 'Comic_More                : More info about the comic\r\n'
 'Comic/Position_Total      : Place of the comic, e.g. 1 of 10\r\n'
 'Part                      : Name of the part. e.g. CD1, CD2\r\n'
 'Part/Position             : Number of the part\r\n'
 'Part/Position_Total       : Place of the part e.g. 2 of 3\r\n'
 'Track                     : Name of the track. e.g. track 1, track 2\r\n'
 'Track_More                : More info about the track\r\n'
 'Track/Url                 : Link to a site about this track\r\n'
 'Track/Sort \r\n'
 'Track/Position            : Number of this track\r\n'
 'Track/Position_Total      : Place of this track, e.g. 3 of 15\r\n'
 'PackageName               : Package name i.e. technical flavor of the content\r\n'
 'Grouping                  : iTunes grouping\r\n'
 'Chapter                   : Name of the chapter\r\n'
 'SubTrack                  : Name of the subtrack\r\n'
 'Original/Album            : Original name of the album\r\n'
 'Original/Movie            : Original name of the movie\r\n'
 'Original/Part             : Original name of the part\r\n'
 'Original/Track            : Original name of the track\r\n'
 'Compilation               : iTunes compilation\r\n'
 'Compilation/String        : iTunes compilation\r\n'
 'Performer                 : Main performer(s)/artist(s)\r\n'
 'Performer/Sort \r\n'
 'Performer/Url             : Homepage of the performer/artist\r\n'
 'Original/Performer        : Original artist(s)/performer(s)\r\n'
 'Accompaniment             : Band/orchestra/accompaniment/musician\r\n'
 'Composer                  : Name of the original composer\r\n'
 'Composer/Nationality      : Nationality of the primary composer of the piece (mostly for classical music)\r\n'
 'Composer/Sort \r\n'
 'Arranger                  : The person who arranged the piece (e.g. Ravel)\r\n'
 'Lyricist                  : The person who wrote the lyrics for the piece\r\n'
 'Original/Lyricist         : Original lyricist(s)/text writer(s).\r\n'
 'Conductor                 : The artist(s) who performed the work. In classical music this would be the conductor, orchestra, '
 'soloists, etc.\r\n'
 'Director                  : Name of the director\r\n'
 'CoDirector                : Name of the codirector\r\n'
 'AssistantDirector         : Name of the assistant director\r\n'
 'DirectorOfPhotography     : Name of the director of photography, also known as cinematographer\r\n'
 'SoundEngineer             : Name of the sound engineer or sound recordist\r\n'
 'ArtDirector               : Name of the person who oversees the artists and craftspeople who build the sets\r\n'
 'ProductionDesigner        : Name of the person responsible for designing the overall visual appearance of a movie\r\n'
 'Choreographer             : Name of the choreographer\r\n'
 'CostumeDesigner           : Name of the costume designer\r\n'
 'Actor                     : Real name of an actor/actress playing a role in the movie\r\n'
 'Actor_Character           : Name of the character an actor or actress plays in this movie\r\n'
 'WrittenBy                 : Author of the story or script\r\n'
 'ScreenplayBy              : Author of the screenplay or scenario (used for movies and TV shows)\r\n'
 'EditedBy                  : Editors name\r\n'
 'CommissionedBy            : Name of the person or organization that commissioned the subject of the file\r\n'
 'Producer                  : Name of the producer of the movie\r\n'
 'CoProducer                : Name of a co-producer\r\n'
 'ExecutiveProducer         : Name of an executive producer\r\n'
 'MusicBy                   : Main musical artist for a movie\r\n'
 'DistributedBy             : Company responsible for distribution of the content\r\n'
 'OriginalSourceForm/Distri : Name of the person or organization who supplied the original subject\r\n'
 'MasteredBy                : The engineer who mastered the content for a physical medium or for digital distribution\r\n'
 'EncodedBy                 : Name of the person/organisation that encoded/ripped the audio file.\r\n'
 'RemixedBy                 : Name of the artist(s) that interpreted, remixed, or otherwise modified the content\r\n'
 'ProductionStudio          : Main production studio\r\n'
 'ThanksTo                  : A very general tag for everyone else that wants to be listed\r\n'
 "Publisher                 : Name of the organization publishing the album (i.e. the 'record label') or movie\r\n"
 "Publisher/URL             : Publisher's official webpage\r\n"
 'Label                     : Brand or trademark associated with the marketing of music recordings and music videos\r\n'
 'Genre                     : Main genre of the audio or video. e.g. classical, ambient-house, synthpop, sci-fi, drama, etc.\r\n'
 'PodcastCategory           : Podcast category\r\n'
 'Mood                      : Intended to reflect the mood of the item with a few keywords, e.g. Romantic, Sad, Uplifting, etc.\r\n'
 'ContentType               : The type or genre of the content. e.g. Documentary, Feature Film, Cartoon, Music Video, Music, Sound '
 'FX, etc.\r\n'
 "Subject                   : Describes the topic of the file, such as 'Aerial view of Seattle.'\r\n"
 "Description               : A short description of the contents, such as 'Two birds flying.'\r\n"
 'Keywords                  : Keywords for the content separated by a comma, used for searching\r\n'
 'Summary                   : Plot outline or a summary of the story\r\n'
 'Synopsis                  : Description of the story line of the item\r\n'
 'Period                    : Describes the period that the piece is from or about. e.g. Renaissance.\r\n'
 'LawRating                 : Legal rating of a movie. Format depends on country of origin (e.g. PG or R in the USA, an age in '
 'other countries or a URI defining a logo)\r\n'
 'LawRating_Reason          : Reason for the law rating\r\n'
 'ICRA                      : The ICRA rating (previously RSACi)\r\n'
 'Released_Date             : Date/year that the content was released\r\n'
 'Original/Released_Date    : Date/year that the content was originally released\r\n'
 'Recorded_Date             : Time/date/year that the recording began\r\n'
 'Encoded_Date              : Time/date/year that the encoding of this content was completed\r\n'
 'Tagged_Date               : Time/date/year that the tags were added to this content\r\n'
 'Written_Date              : Time/date/year that the composition of the music/script began\r\n'
 'Mastered_Date             : Time/date/year that the content was transferred to a digital medium.\r\n'
 'File_Created_Date         : Time that the file was created on the file system\r\n'
 'File_Created_Date_Local   : Time that the file was created on the file system (Warning: this field depends of local '
 'configuration, do not use it in an international database)\r\n'
 'File_Modified_Date        : Time that the file was last modified on the file system\r\n'
 'File_Modified_Date_Local  : Time that the file was last modified on the file system (Warning: this field depends of local '
 'configuration, do not use it in an international database)\r\n'
 'Recorded_Location         : Location where track was recorded (See COMPOSITION_LOCATION for format)\r\n'
 'Written_Location          : Location that the item was originally designed/written. Information should be stored in the '
 'following format: country code, state/province, city where the country code is the same 2 octets as in Internet domains, or '
 'possibly ISO-3166. e.g. US, Texas, Austin or US, , Austin.\r\n'
 'Archival_Location         : Location where an item is archived (e.g. Louvre, Paris, France)\r\n'
 'Encoded_Application       : Name of the software package used to create the file, such as Microsoft WaveEdiTY\r\n'
 'Encoded_Application/Strin : Name of the software package used to create the file, such as Microsoft WaveEdit, trying to have the '
 "format 'CompanyName ProductName (OperatingSystem) Version (Date)'\r\n"
 'Encoded_Application_Compa : Name of the company of the encoding application\r\n'
 'Encoded_Application_Name  : Name of the encoding product\r\n'
 'Encoded_Application_Versi : Version of the encoding product\r\n'
 'Encoded_Application_Url   : URL associated with the encoding software\r\n'
 'Encoded_Library           : Software used to create the file\r\n'
 "Encoded_Library/String    : Software used to create the file, trying to have the format 'CompanyName ProductName "
 "(OperatingSystem) Version (Date)'\r\n"
 'Encoded_Library_CompanyNa : Name of the company\r\n'
 'Encoded_Library_Name      : Name of the the encoding library\r\n'
 'Encoded_Library_Version   : Version of encoding library\r\n'
 'Encoded_Library_Date      : Release date of encoding library\r\n'
 'Encoded_Library_Settings  : Parameters used by the encoding library\r\n'
 'Encoded_OperatingSystem   : Operating System used by encoding application\r\n'
 'Cropped                   : Describes whether an image has been cropped and, if so, how it was cropped\r\n'
 'Dimensions                : Specifies the size of the original subject of the file (e.g. 8.5 in h, 11 in w)\r\n'
 'DotsPerInch               : Stores dots per inch setting of the digitization mechanism used to produce the file\r\n'
 'Lightness                 : Describes the changes in lightness settings on the digitization mechanism made during the production '
 'of the file\r\n'
 'OriginalSourceMedium      : Original medium of the material (e.g. vinyl, Audio-CD, Super8 or BetaMax)\r\n'
 'OriginalSourceForm        : Original form of the material (e.g. slide, paper, map)\r\n'
 'OriginalSourceForm/NumCol : Number of colors requested when digitizing (e.g. 256 for images or 32 bit RGB for video)\r\n'
 'OriginalSourceForm/Name   : Name of the product the file was originally intended for\r\n'
 'OriginalSourceForm/Croppe : Describes whether the original image has been cropped and, if so, how it was cropped (e.g. 16:9 to '
 '4:3, top and bottom)\r\n'
 'OriginalSourceForm/Sharpn : Identifies changes in sharpness the digitization mechanism made during the production of the file\r\n'
 'Tagged_Application        : Software used to tag the file\r\n'
 'BPM                       : Average number of beats per minute\r\n'
 'ISRC                      : International Standard Recording Code, excluding the ISRC prefix and including hyphens\r\n'
 'ISBN                      : International Standard Book Number.\r\n'
 'BarCode                   : EAN-13 (13-digit European Article Numbering) or UPC-A (12-digit Universal Product Code) bar code '
 'identifier\r\n'
 'LCCN                      : Library of Congress Control Number\r\n'
 'CatalogNumber             : A label-specific catalogue number used to identify the release. e.g. TIC 01\r\n'
 'LabelCode                 : A 4-digit or 5-digit number to identify the record label, typically printed as (LC) xxxx or (LC) '
 '0xxxx on CDs medias or covers, with only the number being stored\r\n'
 'Owner                     : Owner of the file\r\n'
 'Copyright                 : Copyright attribution\r\n'
 'Copyright/Url             : Link to a site with copyright/legal information\r\n'
 'Producer_Copyright        : Copyright information as per the production copyright holder\r\n'
 'TermsOfUse                : License information (e.g. All Rights Reserved, Any Use Permitted)\r\n'
 'ServiceName \r\n'
 'ServiceChannel \r\n'
 'Service/Url \r\n'
 'ServiceProvider \r\n'
 'ServiceProvider/Url \r\n'
 'ServiceType \r\n'
 'NetworkName \r\n'
 'OriginalNetworkName \r\n'
 'Country \r\n'
 'TimeZone \r\n'
 'Cover                     : Is there a cover\r\n'
 'Cover_Description         : Short description (e.g. Earth in space)\r\n'
 'Cover_Type \r\n'
 'Cover_Mime                : Mime type of cover file\r\n'
 'Cover_Data                : Cover, in binary format, encoded as BASE64\r\n'
 'Lyrics                    : Text of a song\r\n'
 'Comment                   : Any comment related to the content\r\n'
 'Rating                    : A numeric value defining how much a person likes the song/movie. The number is between 0 and 5 with '
 'decimal values possible (e.g. 2.7), 5(.0) being the highest possible rating.\r\n'
 'Added_Date                : Date/year the item was added to the owners collection\r\n'
 'Played_First_Date         : Date the owner first played an item\r\n'
 'Played_Last_Date          : Date the owner last played an item\r\n'
 'Played_Count              : Number of times an item was played\r\n'
 'EPG_Positions_Begin \r\n'
 'EPG_Positions_End \r\n'
 ' \r\n'
 
 
 'Video \r\n'
 'Count                     : Count of objects available in this stream\r\n'
 'Status                    : bit field (0=IsAccepted, 1=IsFilled, 2=IsUpdated, 3=IsFinished)\r\n'
 'StreamCount               : Count of streams of that kind available\r\n'
 'StreamKind                : Stream type name\r\n'
 'StreamKind/String         : Stream type name\r\n'
 'StreamKindID              : Number of the stream (base=0)\r\n'
 'StreamKindPos             : When multiple streams, number of the stream (base=1)\r\n'
 'StreamOrder               : Stream order in the file, whatever is the kind of stream (base=0)\r\n'
 'FirstPacketOrder          : Order of the first fully decodable packet met in the file, whatever is the kind of stream '
 '(base=0)\r\n'
 'Inform                    : Last **Inform** call\r\n'
 'ID                        : The ID for this stream in this file\r\n'
 'ID/String                 : The ID for this stream in this file\r\n'
 'OriginalSourceMedium_ID   : The ID for this stream in the original medium of the material\r\n'
 'OriginalSourceMedium_ID/S : The ID for this stream in the original medium of the material\r\n'
 'UniqueID                  : The unique ID for this stream, should be copied with stream copy\r\n'
 'UniqueID/String           : The unique ID for this stream, should be copied with stream copy\r\n'
 'MenuID                    : The menu ID for this stream in this file\r\n'
 'MenuID/String             : The menu ID for this stream in this file\r\n'
 'Format                    : Format used\r\n'
 'Format/String             : Format used + additional features\r\n'
 'Format/Info               : Info about Format\r\n'
 'Format/Url                : Link\r\n'
 'Format_Commercial         : Commercial name used by vendor for theses setings or Format field if there is no difference\r\n'
 'Format_Commercial_IfAny   : Commercial name used by vendor for theses setings if there is one\r\n'
 'Format_Version            : Version of this format\r\n'
 "Format_Profile            : Profile of the Format (old XML: 'Profile@Level@Tier' format\r\n"
 'Format_Level              : Level of the Format (only MIXML)\r\n'
 'Format_Tier               : Tier of the Format (only MIXML)\r\n'
 'Format_Compression        : Compression method used\r\n'
 'Format_AdditionalFeatures : Format features needed for fully supporting the content\r\n'
 'MultiView_BaseProfile     : Multiview, profile of the base stream\r\n'
 'MultiView_Count           : Multiview, count of views\r\n'
 'MultiView_Layout          : Multiview, how views are muxed in the container in case of it is not muxing in the stream\r\n'
 'HDR_Format                : Format used\r\n'
 'HDR_Format/String         : Format used + version + profile + level + layers + settings + compatibility\r\n'
 'HDR_Format_Commercial     : Commercial name used by vendor for theses HDR settings or HDR Format field if there is no '
 'difference\r\n'
 'HDR_Format_Version        : Version of this format\r\n'
 'HDR_Format_Profile        : Profile of the Format\r\n'
 'HDR_Format_Level          : Level of the Format\r\n'
 'HDR_Format_Settings       : Settings of the Format\r\n'
 'HDR_Format_Compatibility  : Compatibility with some commercial namings\r\n'
 'Format_Settings           : Settings needed for decoder used, summary\r\n'
 'Format_Settings_BVOP      : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_BVOP/Stri : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_QPel      : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_QPel/Stri : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_GMC       : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_GMC/String \r\n'
 'Format_Settings_Matrix    : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_Matrix/St : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_Matrix_Da : Matrix, in binary format encoded BASE64. Order = intra, non-intra, gray intra, gray non-intra\r\n'
 'Format_Settings_CABAC     : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_CABAC/Str : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_RefFrames : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_RefFrames : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_Pulldown  : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_Endianness \r\n'
 'Format_Settings_Packing \r\n'
 'Format_Settings_FrameMode : Settings needed for decoder used, detailled\r\n'
 'Format_Settings_GOP       : Settings needed for decoder used, detailled (M=x N=y)\r\n'
 'Format_Settings_PictureSt : Settings needed for decoder used, detailled (Type of frame, and field/frame info)\r\n'
 'Format_Settings_Wrapping  : Wrapping mode (Frame wrapped or Clip wrapped)\r\n'
 'InternetMediaType         : Internet Media Type (aka MIME Type, Content-Type)\r\n'
 'MuxingMode                : How this file is muxed in the container\r\n'
 'CodecID                   : Codec ID (found in some containers)\r\n'
 'CodecID/String            : Codec ID (found in some containers)\r\n'
 'CodecID/Info              : Info on the codec\r\n'
 'CodecID/Hint              : Hint/popular name for this codec\r\n'
 'CodecID/Url               : Homepage for more details about this codec\r\n'
 'CodecID_Description       : Manual description given by the container\r\n'
 'Codec                     : Deprecated, do not use in new projects\r\n'
 'Codec/String              : Deprecated, do not use in new projects\r\n'
 'Codec/Family              : Deprecated, do not use in new projects\r\n'
 'Codec/Info                : Deprecated, do not use in new projects\r\n'
 'Codec/Url                 : Deprecated, do not use in new projects\r\n'
 'Codec/CC                  : Deprecated, do not use in new projects\r\n'
 'Codec_Profile             : Deprecated, do not use in new projects\r\n'
 'Codec_Description         : Deprecated, do not use in new projects\r\n'
 'Codec_Settings            : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_PacketBitS : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_BVOP       : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_QPel       : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_GMC        : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_GMC/String : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Matrix     : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Matrix_Dat : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_CABAC      : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_RefFrames  : Deprecated, do not use in new projects\r\n'
 'Duration                  : Play time of the stream in ms\r\n'
 'Duration/String           : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String1          : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration/String2          : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String3          : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration/String4          : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration/String5          : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_FirstFrame       : Duration of the first frame if it is longer than others, in ms\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX omited '
 'if zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Duration_FirstFrame/Strin : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration_FirstFrame/Strin : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_LastFrame        : Duration of the last frame if it is longer than others, in ms\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Duration_LastFrame/String : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration_LastFrame/String : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Source_Duration           : Source Play time of the stream, in ms\r\n'
 'Source_Duration/String    : Source Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Source_Duration/String1   : Source Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Source_Duration/String2   : Source Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Source_Duration/String3   : Source Play time in format : HH:MM:SS.MMM\r\n'
 'Source_Duration/String4   : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Source_Duration/String5   : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in ms\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX '
 'omited if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Source_Duration_FirstFram : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Source_Duration_FirstFram : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in ms\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX '
 'omited if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Source_Duration_LastFrame : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Source_Duration_LastFrame : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'BitRate_Mode              : Bit rate mode (VBR, CBR)\r\n'
 'BitRate_Mode/String       : Bit rate mode (Variable, Cconstant)\r\n'
 'BitRate                   : Bit rate in bps\r\n'
 'BitRate/String            : Bit rate (with measurement)\r\n'
 'BitRate_Minimum           : Minimum Bit rate in bps\r\n'
 'BitRate_Minimum/String    : Minimum Bit rate (with measurement)\r\n'
 'BitRate_Nominal           : Nominal Bit rate in bps\r\n'
 'BitRate_Nominal/String    : Nominal Bit rate (with measurement)\r\n'
 'BitRate_Maximum           : Maximum Bit rate in bps\r\n'
 'BitRate_Maximum/String    : Maximum Bit rate (with measurement)\r\n'
 'BitRate_Encoded           : Encoded (with forced padding) bit rate in bps, if some container padding is present\r\n'
 'BitRate_Encoded/String    : Encoded (with forced padding) bit rate (with measurement), if some container padding is present\r\n'
 'Width                     : Width (aperture size if present) in pixel\r\n'
 'Width/String              : Width (aperture size if present) with measurement (pixel)\r\n'
 'Width_Offset              : Offset between original width and displayed width in pixel\r\n'
 'Width_Offset/String       : Offset between original width and displayed width in pixel\r\n'
 'Width_Original            : Original (in the raw stream) width in pixel\r\n'
 'Width_Original/String     : Original (in the raw stream) width with measurement (pixel)\r\n'
 'Width_CleanAperture       : Clean Aperture width in pixel\r\n'
 'Width_CleanAperture/Strin : Clean Aperture width with measurement (pixel)\r\n'
 'Height                    : Height in pixel\r\n'
 'Height/String             : Height with measurement (pixel)\r\n'
 'Height_Offset             : Offset between original height and displayed height in pixel\r\n'
 'Height_Offset/String      : Offset between original height and displayed height  in pixel\r\n'
 'Height_Original           : Original (in the raw stream) height in pixel\r\n'
 'Height_Original/String    : Original (in the raw stream) height with measurement (pixel)\r\n'
 'Height_CleanAperture      : Clean Aperture height in pixel\r\n'
 'Height_CleanAperture/Stri : Clean Aperture height with measurement (pixel)\r\n'
 'Stored_Width              : Stored width\r\n'
 'Stored_Height             : Stored height\r\n'
 'Sampled_Width             : Sampled width\r\n'
 'Sampled_Height            : Sampled height\r\n'
 'PixelAspectRatio          : Pixel Aspect ratio\r\n'
 'PixelAspectRatio/String   : Pixel Aspect ratio\r\n'
 'PixelAspectRatio_Original : Original (in the raw stream) Pixel Aspect ratio\r\n'
 'PixelAspectRatio_Original : Original (in the raw stream) Pixel Aspect ratio\r\n'
 'PixelAspectRatio_CleanApe : Clean Aperture Pixel Aspect ratio\r\n'
 'PixelAspectRatio_CleanApe : Clean Aperture Pixel Aspect ratio\r\n'
 'DisplayAspectRatio        : Display Aspect ratio\r\n'
 'DisplayAspectRatio/String : Display Aspect ratio\r\n'
 'DisplayAspectRatio_Origin : Original (in the raw stream) Display Aspect ratio\r\n'
 'DisplayAspectRatio_Origin : Original (in the raw stream) Display Aspect ratio\r\n'
 'DisplayAspectRatio_CleanA : Clean Aperture Display Aspect ratio\r\n'
 'DisplayAspectRatio_CleanA : Clean Aperture Display Aspect ratio\r\n'
 'ActiveFormatDescription   : Active Format Description (AFD value)\r\n'
 'ActiveFormatDescription/S : Active Format Description (text)\r\n'
 'ActiveFormatDescription_M : Active Format Description (AFD value) muxing mode (Ancillary or Raw stream)\r\n'
 'Rotation                  : Rotation\r\n'
 'Rotation/String           : Rotation (if not horizontal)\r\n'
 'FrameRate_Mode            : Frame rate mode (CFR, VFR)\r\n'
 'FrameRate_Mode/String     : Frame rate mode (Constant, Variable)\r\n'
 'FrameRate_Mode_Original   : Original frame rate mode (CFR, VFR)\r\n'
 'FrameRate_Mode_Original/S : Original frame rate mode (Constant, Variable)\r\n'
 'FrameRate                 : Frames per second\r\n'
 'FrameRate/String          : Frames per second (with measurement)\r\n'
 'FrameRate_Num             : Frames per second, numerator\r\n'
 'FrameRate_Den             : Frames per second, denominator\r\n'
 'FrameRate_Minimum         : Minimum Frames per second\r\n'
 'FrameRate_Minimum/String  : Minimum Frames per second (with measurement)\r\n'
 'FrameRate_Nominal         : Nominal Frames per second\r\n'
 'FrameRate_Nominal/String  : Nominal Frames per second (with measurement)\r\n'
 'FrameRate_Maximum         : Maximum Frames per second\r\n'
 'FrameRate_Maximum/String  : Maximum Frames per second (with measurement)\r\n'
 'FrameRate_Original        : Original (in the raw stream) frames per second\r\n'
 'FrameRate_Original/String : Original (in the raw stream) frames per second (with measurement)\r\n'
 'FrameRate_Original_Num    : Frames per second, numerator\r\n'
 'FrameRate_Original_Den    : Frames per second, denominator\r\n'
 'FrameRate_Real            : Real (capture) frames per second\r\n'
 'FrameRate_Real/String     : Real (capture) frames per second (with measurement)\r\n'
 'FrameCount                : Number of frames\r\n'
 'Source_FrameCount         : Source Number of frames\r\n'
 'Standard                  : NTSC or PAL\r\n'
 'Resolution                : Deprecated, do not use in new projects\r\n'
 'Resolution/String         : Deprecated, do not use in new projects\r\n'
 'Colorimetry               : Deprecated, do not use in new projects\r\n'
 
 
 'ColorSpace \r\n'
 'ChromaSubsampling \r\n'
 'ChromaSubsampling/String \r\n'
 'ChromaSubsampling_Position \r\n'
 'BitDepth                  : 16/24/32\r\n'
 'BitDepth/String           : 16/24/32 bits\r\n'
 'ScanType \r\n'
 'ScanType/String \r\n'
 'ScanType_Original \r\n'
 'ScanType_Original/String \r\n'
 'ScanType_StoreMethod \r\n'
 'ScanType_StoreMethod_FieldsPerBlock \r\n'
 'ScanType_StoreMethod/String \r\n'
 'ScanOrder \r\n'
 'ScanOrder/String \r\n'
 'ScanOrder_Stored \r\n'
 'ScanOrder_Stored/String \r\n'
 'ScanOrder_StoredDisplayedInverted \r\n'
 'ScanOrder_Original \r\n'
 'ScanOrder_Original/String \r\n'
 'Interlacement             : Deprecated, do not use in new projects\r\n'
 'Interlacement/String      : Deprecated, do not use in new projects\r\n'
 'Compression_Mode          : Compression mode (Lossy or Lossless)\r\n'
 'Compression_Mode/String   : Compression mode (Lossy or Lossless)\r\n'
 'Compression_Ratio         : Current stream size divided by uncompressed stream size\r\n'
 'Bits-(Pixel*Frame)        : bits/(Pixel*Frame) (like Gordian Knot)\r\n'
 'Delay                     : Delay fixed in the stream (relative) IN MS\r\n'
 'Delay/String              : Delay with measurement\r\n'
 'Delay/String1             : Delay with measurement\r\n'
 'Delay/String2             : Delay with measurement\r\n'
 'Delay/String3             : Delay in format : HH:MM:SS.MMM\r\n'
 'Delay/String4             : Delay in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay/String5             : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Settings            : Delay settings (in case of timecode for example)\r\n'
 'Delay_DropFrame           : Delay drop frame\r\n'
 'Delay_Source              : Delay source (Container or Stream or empty)\r\n'
 'Delay_Source/String       : Delay source (Container or Stream or empty)\r\n'
 'Delay_Original            : Delay fixed in the raw stream (relative) IN MS\r\n'
 'Delay_Original/String     : Delay with measurement\r\n'
 'Delay_Original/String1    : Delay with measurement\r\n'
 'Delay_Original/String2    : Delay with measurement\r\n'
 'Delay_Original/String3    : Delay in format: HH:MM:SS.MMM\r\n'
 'Delay_Original/String4    : Delay in format: HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay_Original/String5    : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Original_Settings   : Delay settings (in case of timecode for example)\r\n'
 'Delay_Original_DropFrame  : Delay drop frame info\r\n'
 'Delay_Original_Source     : Delay source (Stream or empty)\r\n'
 'TimeStamp_FirstFrame      : TimeStamp fixed in the stream (relative) IN MS\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp with measurement\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp with measurement\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp with measurement\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp in format : HH:MM:SS.MMM\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp in format: HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'TimeCode_FirstFrame       : Time code in HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available format\r\n'
 'TimeCode_LastFrame        : Time code of the last frame (excluding the duration of the last frame) in HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available format\r\n'
 'TimeCode_DropFrame        : Delay drop frame\r\n'
 'TimeCode_Settings         : Time code settings\r\n'
 'TimeCode_Source           : Time code source (Container, Stream, SystemScheme1, SDTI, ANC...)\r\n'
 'Gop_OpenClosed            : Time code information about Open/Closed\r\n'
 'Gop_OpenClosed/String     : Time code information about Open/Closed\r\n'
 'Gop_OpenClosed_FirstFrame : Time code information about Open/Closed of first frame if GOP is Open for the other GOPs\r\n'
 'Gop_OpenClosed_FirstFrame : Time code information about Open/Closed of first frame if GOP is Open for the other GOPs\r\n'
 'StreamSize                : Streamsize in bytes\r\n'
 'StreamSize/String         : Streamsize in with percentage value\r\n'
 'StreamSize/String1 \r\n'
 'StreamSize/String2 \r\n'
 'StreamSize/String3 \r\n'
 'StreamSize/String4 \r\n'
 'StreamSize/String5        : Streamsize in with percentage value\r\n'
 'StreamSize_Proportion     : Stream size divided by file size\r\n'
 'StreamSize_Demuxed        : StreamSize in bytes of hte stream after demux\r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value\r\n'
 'StreamSize_Demuxed/String1 \r\n'
 'StreamSize_Demuxed/String2 \r\n'
 'StreamSize_Demuxed/String3 \r\n'
 'StreamSize_Demuxed/String4 \r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value (note: theoritical value, not for real use)\r\n'
 'Source_StreamSize         : Source Streamsize in bytes\r\n'
 'Source_StreamSize/String  : Source Streamsize in with percentage value\r\n'
 'Source_StreamSize/String1 \r\n'
 'Source_StreamSize/String2 \r\n'
 'Source_StreamSize/String3 \r\n'
 'Source_StreamSize/String4 \r\n'
 'Source_StreamSize/String5 : Source Streamsize in with percentage value\r\n'
 'Source_StreamSize_Proport : Source Stream size divided by file size\r\n'
 'StreamSize_Encoded        : Encoded Streamsize in bytes\r\n'
 'StreamSize_Encoded/String : Encoded Streamsize in with percentage value\r\n'
 'StreamSize_Encoded/String1 \r\n'
 'StreamSize_Encoded/String2 \r\n'
 'StreamSize_Encoded/String3 \r\n'
 'StreamSize_Encoded/String4 \r\n'
 'StreamSize_Encoded/String : Encoded Streamsize in with percentage value\r\n'
 'StreamSize_Encoded_Propor : Encoded Stream size divided by file size\r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in bytes\r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in with percentage value\r\n'
 'Source_StreamSize_Encoded/String1 \r\n'
 'Source_StreamSize_Encoded/String2 \r\n'
 'Source_StreamSize_Encoded/String3 \r\n'
 'Source_StreamSize_Encoded/String4 \r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in with percentage value\r\n'
 'Source_StreamSize_Encoded : Source Encoded Stream size divided by file size\r\n'
 'Alignment                 : How this stream file is aligned in the container\r\n'
 'Alignment/String \r\n'
 'Title                     : Name of the track\r\n'
 'Encoded_Application       : Name of the software package used to create the file, such as Microsoft WaveEdit\r\n'
 'Encoded_Application/Strin : Name of the software package used to create the file, such as Microsoft WaveEdit, trying to have the '
 "format 'CompanyName ProductName (OperatingSystem) Version (Date)'\r\n"
 'Encoded_Application_Compa : Name of the company\r\n'
 'Encoded_Application_Name  : Name of the product\r\n'
 'Encoded_Application_Versi : Version of the product\r\n'
 'Encoded_Application_Url   : Name of the software package used to create the file, such as Microsoft WaveEdit.\r\n'
 'Encoded_Library           : Software used to create the file\r\n'
 "Encoded_Library/String    : Software used to create the file, trying to have the format 'CompanyName ProductName "
 "(OperatingSystem) Version (Date)'\r\n"
 'Encoded_Library_CompanyNa : Name of the company\r\n'
 'Encoded_Library_Name      : Name of the the encoding-software\r\n'
 'Encoded_Library_Version   : Version of encoding-software\r\n'
 'Encoded_Library_Date      : Release date of software\r\n'
 'Encoded_Library_Settings  : Parameters used by the software\r\n'
 'Encoded_OperatingSystem   : Operating System of encoding-software\r\n'
 'Language                  : Language (2-letter ISO 639-1 if exists, else 3-letter ISO 639-2, and with optional ISO 3166-1 '
 'country separated by a dash if available, e.g. en, en-us, zh-cn)\r\n'
 'Language/String           : Language (full)\r\n'
 'Language/String1          : Language (full)\r\n'
 'Language/String2          : Language (2-letter ISO 639-1 if exists, else empty)\r\n'
 'Language/String3          : Language (3-letter ISO 639-2 if exists, else empty)\r\n'
 'Language/String4          : Language (2-letter ISO 639-1 if exists with optional ISO 3166-1 country separated by a dash if '
 'available, e.g. en, en-us, zh-cn, else empty)\r\n'
 "Language_More             : More info about Language (e.g. Director's Comment)\r\n"
 'ServiceKind               : Service kind, e.g. visually impaired, commentary, voice over\r\n'
 'ServiceKind/String        : Service kind (full)\r\n'
 'Disabled                  : Set if that track should not be used\r\n'
 'Disabled/String           : Set if that track should not be used\r\n'
 'Default                   : Set if that track should be used if no language found matches the user preference.\r\n'
 'Default/String            : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced                    : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced/String             : Set if that track should be used if no language found matches the user preference.\r\n'
 'AlternateGroup            : Number of a group in order to provide versions of the same track\r\n'
 'AlternateGroup/String     : Number of a group in order to provide versions of the same track\r\n'
 'Encoded_Date              : UTC time that the encoding of this item was completed began.\r\n'
 'Tagged_Date               : UTC time that the tags were done for this item.\r\n'
 'Encryption \r\n'
 'BufferSize                : Defines the size of the buffer needed to decode the sequence.\r\n'
 'colour_description_presen : Presence of colour description\r\n'
 'colour_description_presen : Presence of colour description (source)\r\n'
 'colour_description_presen : Presence of colour description (if incoherencies)\r\n'
 'colour_description_presen : Presence of colour description (source if incoherencies)\r\n'
 'colour_range              : Colour range for YUV colour space\r\n'
 'colour_range_Source       : Colour range for YUV colour space (source)\r\n'
 'colour_range_Original     : Colour range for YUV colour space (if incoherencies)\r\n'
 'colour_range_Original_Sou : Colour range for YUV colour space (source if incoherencies)\r\n'
 'colour_primaries          : Chromaticity coordinates of the source primaries\r\n'
 'colour_primaries_Source   : Chromaticity coordinates of the source primaries (source)\r\n'
 'colour_primaries_Original : Chromaticity coordinates of the source primaries (if incoherencies)\r\n'
 'colour_primaries_Original : Chromaticity coordinates of the source primaries (source if incoherencies)\r\n'
 'transfer_characteristics  : Opto-electronic transfer characteristic of the source picture\r\n'
 'transfer_characteristics_ : Opto-electronic transfer characteristic of the source picture (source)\r\n'
 'transfer_characteristics_ : Opto-electronic transfer characteristic of the source picture (if incoherencies)\r\n'
 'transfer_characteristics_ : Opto-electronic transfer characteristic of the source picture (source if incoherencies)\r\n'
 'matrix_coefficients       : Matrix coefficients used in deriving luma and chroma signals from the green, blue, and red '
 'primaries\r\n'
 'matrix_coefficients_Sourc : Matrix coefficients used in deriving luma and chroma signals from the green, blue, and red primaries '
 '(source)\r\n'
 'matrix_coefficients_Origi : Matrix coefficients used in deriving luma and chroma signals from the green, blue, and red primaries '
 '(if incoherencies)\r\n'
 'matrix_coefficients_Origi : Matrix coefficients used in deriving luma and chroma signals from the green, blue, and red primaries '
 '(source if incoherencies)\r\n'
 'MasteringDisplay_ColorPri : Chromaticity coordinates of the source primaries of the mastering display\r\n'
 'MasteringDisplay_ColorPri : Chromaticity coordinates of the source primaries of the mastering display (source)\r\n'
 'MasteringDisplay_ColorPri : Chromaticity coordinates of the source primaries of the mastering display (if incoherencies)\r\n'
 'MasteringDisplay_ColorPri : Chromaticity coordinates of the source primaries of the mastering display (source if '
 'incoherencies)\r\n'
 'MasteringDisplay_Luminanc : Luminance of the mastering display\r\n'
 'MasteringDisplay_Luminanc : Luminance of the mastering display (source)\r\n'
 'MasteringDisplay_Luminanc : Luminance of the mastering display (if incoherencies)\r\n'
 'MasteringDisplay_Luminanc : Luminance of the mastering display (source if incoherencies)\r\n'
 'MaxCLL                    : Maximum content light level\r\n'
 'MaxCLL_Source             : Maximum content light level (source)\r\n'
 'MaxCLL_Original           : Maximum content light level (if incoherencies)\r\n'
 'MaxCLL_Original_Source    : Maximum content light level (source if incoherencies)\r\n'
 'MaxFALL                   : Maximum frame average light level\r\n'
 'MaxFALL_Source            : Maximum frame average light level (source)\r\n'
 'MaxFALL_Original          : Maximum frame average light level (if incoherencies)\r\n'
 'MaxFALL_Original_Source   : Maximum frame average light level (source if incoherencies)\r\n'
 ' \r\n'
 
 
 'Audio \r\n'
 'Count                     : Count of objects available in this stream\r\n'
 'Status                    : bit field (0=IsAccepted, 1=IsFilled, 2=IsUpdated, 3=IsFinished)\r\n'
 'StreamCount               : Count of streams of that kind available\r\n'
 'StreamKind                : Stream type name\r\n'
 'StreamKind/String         : Stream type name\r\n'
 'StreamKindID              : Number of the stream (base=0)\r\n'
 'StreamKindPos             : When multiple streams, number of the stream (base=1)\r\n'
 'StreamOrder               : Stream order in the file, whatever is the kind of stream (base=0)\r\n'
 'FirstPacketOrder          : Order of the first fully decodable packet met in the file, whatever is the kind of stream '
 '(base=0)\r\n'
 'Inform                    : Last **Inform** call\r\n'
 'ID                        : The ID for this stream in this file\r\n'
 'ID/String                 : The ID for this stream in this file\r\n'
 'OriginalSourceMedium_ID   : The ID for this stream in the original medium of the material\r\n'
 'OriginalSourceMedium_ID/S : The ID for this stream in the original medium of the material\r\n'
 'UniqueID                  : The unique ID for this stream, should be copied with stream copy\r\n'
 'UniqueID/String           : The unique ID for this stream, should be copied with stream copy\r\n'
 'MenuID                    : The menu ID for this stream in this file\r\n'
 'MenuID/String             : The menu ID for this stream in this file\r\n'
 'Format                    : Format used\r\n'
 'Format/String             : Format used + additional features\r\n'
 'Format/Info               : Info about the format\r\n'
 'Format/Url                : Homepage of this format\r\n'
 'Format_Commercial         : Commercial name used by vendor for theses setings or Format field if there is no difference\r\n'
 'Format_Commercial_IfAny   : Commercial name used by vendor for theses setings if there is one\r\n'
 'Format_Version            : Version of this format\r\n'
 "Format_Profile            : Profile of the Format (old XML: 'Profile@Level' format\r\n"
 'Format_Level              : Level of the Format (only MIXML)\r\n'
 'Format_Compression        : Compression method used\r\n'
 'Format_Settings           : Settings needed for decoder used, summary\r\n'
 'Format_Settings_SBR \r\n'
 'Format_Settings_SBR/String \r\n'
 'Format_Settings_PS \r\n'
 'Format_Settings_PS/String \r\n'
 'Format_Settings_Mode \r\n'
 'Format_Settings_ModeExtension \r\n'
 'Format_Settings_Emphasis \r\n'
 'Format_Settings_Floor \r\n'
 'Format_Settings_Firm \r\n'
 'Format_Settings_Endianness \r\n'
 'Format_Settings_Sign \r\n'
 'Format_Settings_Law \r\n'
 'Format_Settings_ITU \r\n'
 'Format_Settings_Wrapping  : Wrapping mode (Frame wrapped or Clip wrapped)\r\n'
 'Format_AdditionalFeatures : Format features needed for fully supporting the content\r\n'
 'Matrix_Format             : Matrix format (e.g. DTS Neural)\r\n'
 'InternetMediaType         : Internet Media Type (aka MIME Type, Content-Type)\r\n'
 'MuxingMode                : How this stream is muxed in the container\r\n'
 'MuxingMode_MoreInfo       : More info (text) about the muxing mode\r\n'
 'CodecID                   : Codec ID (found in some containers)\r\n'
 'CodecID/String            : Codec ID (found in some containers)\r\n'
 'CodecID/Info              : Info about codec ID\r\n'
 'CodecID/Hint              : Hint/popular name for this codec ID\r\n'
 'CodecID/Url               : Homepage for more details about this codec ID\r\n'
 'CodecID_Description       : Manual description given by the container\r\n'
 'Codec                     : Deprecated, do not use in new projects\r\n'
 'Codec/String              : Deprecated, do not use in new projects\r\n'
 'Codec/Family              : Deprecated, do not use in new projects\r\n'
 'Codec/Info                : Deprecated, do not use in new projects\r\n'
 'Codec/Url                 : Deprecated, do not use in new projects\r\n'
 'Codec/CC                  : Deprecated, do not use in new projects\r\n'
 'Codec_Description         : Deprecated, do not use in new projects\r\n'
 'Codec_Profile             : Deprecated, do not use in new projects\r\n'
 'Codec_Settings            : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Automatic  : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Floor      : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Firm       : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Endianness : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Sign       : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_Law        : Deprecated, do not use in new projects\r\n'
 'Codec_Settings_ITU        : Deprecated, do not use in new projects\r\n'
 'Duration                  : Play time of the stream, in ms\r\n'
 'Duration/String           : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String1          : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration/String2          : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String3          : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration/String4          : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration/String5          : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_FirstFrame       : Duration of the first frame if it is longer than others, in ms\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX omited '
 'if zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Duration_FirstFrame/Strin : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration_FirstFrame/Strin : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_LastFrame        : Duration of the last frame if it is longer than others, in ms\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Duration_LastFrame/String : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration_LastFrame/String : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Source_Duration           : Source Play time of the stream, in ms\r\n'
 'Source_Duration/String    : Source Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Source_Duration/String1   : Source Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Source_Duration/String2   : Source Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Source_Duration/String3   : Source Play time in format : HH:MM:SS.MMM\r\n'
 'Source_Duration/String4   : Source Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if '
 'available\r\n'
 'Source_Duration/String5   : Source Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in ms\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX '
 'omited if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HH:MM:SS.mmm '
 '(HH:MM:SS:FF)\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in ms\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX '
 'omited if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HH:MM:SS.mmm '
 '(HH:MM:SS:FF)\r\n'
 'BitRate_Mode              : Bit rate mode (VBR, CBR)\r\n'
 'BitRate_Mode/String       : Bit rate mode (Constant, Variable)\r\n'
 'BitRate                   : Bit rate in bps\r\n'
 'BitRate/String            : Bit rate (with measurement)\r\n'
 'BitRate_Minimum           : Minimum Bit rate in bps\r\n'
 'BitRate_Minimum/String    : Minimum Bit rate (with measurement)\r\n'
 'BitRate_Nominal           : Nominal Bit rate in bps\r\n'
 'BitRate_Nominal/String    : Nominal Bit rate (with measurement)\r\n'
 'BitRate_Maximum           : Maximum Bit rate in bps\r\n'
 'BitRate_Maximum/String    : Maximum Bit rate (with measurement)\r\n'
 'BitRate_Encoded           : Encoded (with forced padding) bit rate in bps, if some container padding is present\r\n'
 'BitRate_Encoded/String    : Encoded (with forced padding) bit rate (with measurement), if some container padding is present\r\n'
 'Channel(s)                : Number of channels\r\n'
 'Channel(s)/String         : Number of channels (with measurement)\r\n'
 'Channel(s)_Original       : Number of channels\r\n'
 'Channel(s)_Original/Strin : Number of channels (with measurement)\r\n'
 'Matrix_Channel(s)         : Number of channels after matrix decoding\r\n'
 'Matrix_Channel(s)/String  : Number of channels after matrix decoding (with measurement)\r\n'
 'ChannelPositions          : Position of channels\r\n'
 'ChannelPositions_Original : Position of channels\r\n'
 'ChannelPositions/String2  : Position of channels (x/y.z format)\r\n'
 'ChannelPositions_Original : Position of channels (x/y.z format)\r\n'
 'Matrix_ChannelPositions   : Position of channels after matrix decoding\r\n'
 'Matrix_ChannelPositions/S : Position of channels after matrix decoding (x/y.z format)\r\n'
 'ChannelLayout             : Layout of channels (in the stream)\r\n'
 'ChannelLayout_Original    : Layout of channels (in the stream)\r\n'
 'ChannelLayoutID           : ID of layout of channels (e.g. MXF descriptor channel assignment). Warning, sometimes this is not '
 'enough for uniquely identifying a layout (e.g. MXF descriptor channel assignment is SMPTE 377-4). For AC-3, the form is x,y with '
 'x=acmod and y=lfeon.\r\n'
 'SamplesPerFrame           : Sampling rate\r\n'
 'SamplingRate              : Sampling rate\r\n'
 'SamplingRate/String       : in KHz\r\n'
 'SamplingCount             : Sample count (based on sampling rate)\r\n'
 'Source_SamplingCount      : Source Sample count (based on sampling rate)\r\n'
 'FrameRate                 : Frames per second\r\n'
 'FrameRate/String          : Frames per second (with measurement)\r\n'
 'FrameRate_Num             : Frames per second, numerator\r\n'
 'FrameRate_Den             : Frames per second, denominator\r\n'
 'FrameCount                : Frame count (a frame contains a count of samples depends of the format)\r\n'
 'Source_FrameCount         : Source Frame count (a frame contains a count of samples depends of the format)\r\n'
 'Resolution                : Deprecated, do not use in new projects\r\n'
 'Resolution/String         : Deprecated, do not use in new projects\r\n'
 'BitDepth                  : Resolution in bits (8, 16, 20, 24). Note: significant bits in case the stored bit depth is '
 'different\r\n'
 'BitDepth/String           : Resolution in bits (8, 16, 20, 24). Note: significant bits in case the stored bit depth is '
 'different\r\n'
 'BitDepth_Detected         : Detected (during scan of the input by the muxer) resolution in bits\r\n'
 'BitDepth_Detected/String  : Detected (during scan of the input by the muxer) resolution in bits\r\n'
 'BitDepth_Stored           : Stored Resolution in bits (8, 16, 20, 24)\r\n'
 'BitDepth_Stored/String    : Stored Resolution in bits (8, 16, 20, 24)\r\n'
 'Compression_Mode          : Compression mode (Lossy or Lossless)\r\n'
 'Compression_Mode/String   : Compression mode (Lossy or Lossless)\r\n'
 'Compression_Ratio         : Current stream size divided by uncompressed stream size\r\n'
 'Delay                     : Delay fixed in the stream (relative) IN MS\r\n'
 'Delay/String              : Delay with measurement\r\n'
 'Delay/String1             : Delay with measurement\r\n'
 'Delay/String2             : Delay with measurement\r\n'
 'Delay/String3             : Delay in format : HH:MM:SS.MMM\r\n'
 'Delay/String4             : Delay in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay/String5             : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Settings            : Delay settings (in case of timecode for example)\r\n'
 'Delay_DropFrame           : Delay drop frame\r\n'
 'Delay_Source              : Delay source (Container or Stream or empty)\r\n'
 'Delay_Source/String       : Delay source (Container or Stream or empty)\r\n'
 'Delay_Original            : Delay fixed in the raw stream (relative) IN MS\r\n'
 'Delay_Original/String     : Delay with measurement\r\n'
 'Delay_Original/String1    : Delay with measurement\r\n'
 'Delay_Original/String2    : Delay with measurement\r\n'
 'Delay_Original/String3    : Delay in format: HH:MM:SS.MMM\r\n'
 'Delay_Original/String4    : Delay in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay_Original/String5    : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Original_Settings   : Delay settings (in case of timecode for example)\r\n'
 'Delay_Original_DropFrame  : Delay drop frame info\r\n'
 'Delay_Original_Source     : Delay source (Stream or empty)\r\n'
 'Video_Delay               : Delay fixed in the stream (absolute / video)\r\n'
 'Video_Delay/String \r\n'
 'Video_Delay/String1 \r\n'
 'Video_Delay/String2 \r\n'
 'Video_Delay/String3 \r\n'
 'Video_Delay/String4 \r\n'
 'Video_Delay/String5 \r\n'
 'Video0_Delay              : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String       : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String1      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String2      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String3      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String4      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String5      : Deprecated, do not use in new projects\r\n'
 'TimeCode_FirstFrame       : Time code in HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available format\r\n'
 'TimeCode_LastFrame        : Time code of the last frame (excluding the duration of the last frame) in HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available format\r\n'
 'TimeCode_DropFrame        : Delay drop frame\r\n'
 'TimeCode_Settings         : Time code settings\r\n'
 'TimeCode_Source           : Time code source (Container, Stream, SystemScheme1, SDTI, ANC...)\r\n'
 'ReplayGain_Gain           : The gain to apply to reach 89dB SPL on playback\r\n'
 'ReplayGain_Gain/String \r\n'
 'ReplayGain_Peak           : The maximum absolute peak value of the item\r\n'
 'StreamSize                : Streamsize in bytes\r\n'
 'StreamSize/String         : Streamsize in with percentage value\r\n'
 'StreamSize/String1 \r\n'
 'StreamSize/String2 \r\n'
 'StreamSize/String3 \r\n'
 'StreamSize/String4 \r\n'
 'StreamSize/String5        : Streamsize in with percentage value\r\n'
 'StreamSize_Proportion     : Stream size divided by file size\r\n'
 'StreamSize_Demuxed        : StreamSize in bytes of hte stream after demux\r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value\r\n'
 'StreamSize_Demuxed/String1 \r\n'
 'StreamSize_Demuxed/String2 \r\n'
 'StreamSize_Demuxed/String3 \r\n'
 'StreamSize_Demuxed/String4 \r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value (note: theoritical value, not for real use)\r\n'
 'Source_StreamSize         : Source Streamsize in bytes\r\n'
 'Source_StreamSize/String  : Source Streamsize in with percentage value\r\n'
 'Source_StreamSize/String1 \r\n'
 'Source_StreamSize/String2 \r\n'
 'Source_StreamSize/String3 \r\n'
 'Source_StreamSize/String4 \r\n'
 'Source_StreamSize/String5 : Source Streamsize in with percentage value\r\n'
 'Source_StreamSize_Proport : Source Stream size divided by file size\r\n'
 'StreamSize_Encoded        : Encoded Streamsize in bytes\r\n'
 'StreamSize_Encoded/String : Encoded Streamsize in with percentage value\r\n'
 'StreamSize_Encoded/String1 \r\n'
 'StreamSize_Encoded/String2 \r\n'
 'StreamSize_Encoded/String3 \r\n'
 'StreamSize_Encoded/String4 \r\n'
 'StreamSize_Encoded/String : Encoded Streamsize in with percentage value\r\n'
 'StreamSize_Encoded_Propor : Encoded Stream size divided by file size\r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in bytes\r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in with percentage value\r\n'
 'Source_StreamSize_Encoded/String1 \r\n'
 'Source_StreamSize_Encoded/String2 \r\n'
 'Source_StreamSize_Encoded/String3 \r\n'
 'Source_StreamSize_Encoded/String4 \r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in with percentage value\r\n'
 'Source_StreamSize_Encoded : Source Encoded Stream size divided by file size\r\n'
 'Alignment                 : How this stream file is aligned in the container\r\n'
 'Alignment/String          : Where this stream file is aligned in the container\r\n'
 'Interleave_VideoFrames    : Between how many video frames the stream is inserted\r\n'
 'Interleave_Duration       : Between how much time (ms) the stream is inserted\r\n'
 'Interleave_Duration/Strin : Between how much time and video frames the stream is inserted (with measurement)\r\n'
 'Interleave_Preload        : How much time is buffered before the first video frame\r\n'
 'Interleave_Preload/String : How much time is buffered before the first video frame (with measurement)\r\n'
 'Title                     : Name of the track\r\n'
 'Encoded_Application       : Name of the software package used to create the file, such as Microsoft WaveEdit\r\n'
 'Encoded_Application/Strin : Name of the software package used to create the file, such as Microsoft WaveEdit, trying to have the '
 "format 'CompanyName ProductName (OperatingSystem) Version (Date)'\r\n"
 'Encoded_Application_Compa : Name of the company\r\n'
 'Encoded_Application_Name  : Name of the product\r\n'
 'Encoded_Application_Versi : Version of the product\r\n'
 'Encoded_Application_Url   : Name of the software package used to create the file, such as Microsoft WaveEdit.\r\n'
 'Encoded_Library           : Software used to create the file\r\n'
 "Encoded_Library/String    : Software used to create the file, trying to have the format 'CompanyName ProductName "
 "(OperatingSystem) Version (Date)'\r\n"
 'Encoded_Library_CompanyNa : Name of the company\r\n'
 'Encoded_Library_Name      : Name of the the encoding-software\r\n'
 'Encoded_Library_Version   : Version of encoding-software\r\n'
 'Encoded_Library_Date      : Release date of software\r\n'
 'Encoded_Library_Settings  : Parameters used by the software\r\n'
 'Encoded_OperatingSystem   : Operating System of encoding-software\r\n'
 'Language                  : Language (2-letter ISO 639-1 if exists, else 3-letter ISO 639-2, and with optional ISO 3166-1 '
 'country separated by a dash if available, e.g. en, en-us, zh-cn)\r\n'
 'Language/String           : Language (full)\r\n'
 'Language/String1          : Language (full)\r\n'
 'Language/String2          : Language (2-letter ISO 639-1 if exists, else empty)\r\n'
 'Language/String3          : Language (3-letter ISO 639-2 if exists, else empty)\r\n'
 'Language/String4          : Language (2-letter ISO 639-1 if exists with optional ISO 3166-1 country separated by a dash if '
 'available, e.g. en, en-us, zh-cn, else empty)\r\n'
 "Language_More             : More info about Language (e.g. Director's Comment)\r\n"
 'ServiceKind               : Service kind, e.g. visually impaired, commentary, voice over\r\n'
 'ServiceKind/String        : Service kind (full)\r\n'
 'Disabled                  : Set if that track should not be used\r\n'
 'Disabled/String           : Set if that track should not be used\r\n'
 'Default                   : Set if that track should be used if no language found matches the user preference.\r\n'
 'Default/String            : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced                    : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced/String             : Set if that track should be used if no language found matches the user preference.\r\n'
 'AlternateGroup            : Number of a group in order to provide versions of the same track\r\n'
 'AlternateGroup/String     : Number of a group in order to provide versions of the same track\r\n'
 'Encoded_Date              : UTC time that the encoding of this item was completed began.\r\n'
 'Tagged_Date               : UTC time that the tags were done for this item.\r\n'
 'Encryption \r\n'
 ' \r\n'
 
 
 'Text \r\n'
 'Count                     : Count of objects available in this stream\r\n'
 'Status                    : bit field (0=IsAccepted, 1=IsFilled, 2=IsUpdated, 3=IsFinished)\r\n'
 'StreamCount               : Count of streams of that kind available\r\n'
 'StreamKind                : Stream type name\r\n'
 'StreamKind/String         : Stream type name\r\n'
 'StreamKindID              : Number of the stream (base=0)\r\n'
 'StreamKindPos             : When multiple streams, number of the stream (base=1)\r\n'
 'StreamOrder               : Stream order in the file, whatever is the kind of stream (base=0)\r\n'
 'FirstPacketOrder          : Order of the first fully decodable packet met in the file, whatever is the kind of stream '
 '(base=0)\r\n'
 'Inform                    : Last **Inform** call\r\n'
 'ID                        : The ID for this stream in this file\r\n'
 'ID/String                 : The ID for this stream in this file\r\n'
 'OriginalSourceMedium_ID   : The ID for this stream in the original medium of the material\r\n'
 'OriginalSourceMedium_ID/S : The ID for this stream in the original medium of the material\r\n'
 'UniqueID                  : The unique ID for this stream, should be copied with stream copy\r\n'
 'UniqueID/String           : The unique ID for this stream, should be copied with stream copy\r\n'
 'MenuID                    : The menu ID for this stream in this file\r\n'
 'MenuID/String             : The menu ID for this stream in this file\r\n'
 'Format                    : Format used\r\n'
 'Format/String             : Format used + additional features\r\n'
 'Format/Info               : Info about Format\r\n'
 'Format/Url                : Link\r\n'
 'Format_Commercial         : Commercial name used by vendor for theses setings or Format field if there is no difference\r\n'
 'Format_Commercial_IfAny   : Commercial name used by vendor for theses setings if there is one\r\n'
 'Format_Version            : Version of this format\r\n'
 'Format_Profile            : Profile of the Format\r\n'
 'Format_Compression        : Compression method used\r\n'
 'Format_Settings           : Settings needed for decoder used\r\n'
 'Format_Settings_Wrapping  : Wrapping mode (Frame wrapped or Clip wrapped)\r\n'
 'Format_AdditionalFeatures : Format features needed for fully supporting the content\r\n'
 'InternetMediaType         : Internet Media Type (aka MIME Type, Content-Type)\r\n'
 'MuxingMode                : How this stream is muxed in the container\r\n'
 'MuxingMode_MoreInfo       : More info (text) about the muxing mode\r\n'
 'CodecID                   : Codec ID (found in some containers)\r\n'
 'CodecID/String            : Codec ID (found in some containers)\r\n'
 'CodecID/Info              : Info about codec ID\r\n'
 'CodecID/Hint              : A hint for this codec ID\r\n'
 'CodecID/Url               : A link for more details about this codec ID\r\n'
 'CodecID_Description       : Manual description given by the container\r\n'
 'Codec                     : Deprecated\r\n'
 'Codec/String              : Deprecated\r\n'
 'Codec/Info                : Deprecated\r\n'
 'Codec/Url                 : Deprecated\r\n'
 'Codec/CC                  : Deprecated\r\n'
 'Duration                  : Play time of the stream, in ms\r\n'
 'Duration/String           : Play time (formated)\r\n'
 'Duration/String1          : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration/String2          : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String3          : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration/String4          : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop Duration\r\n'
 'Duration/String5          : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_Start2End        : Play time of the stream, in ms\r\n'
 'Duration_Start2End/String : Play time (formated)\r\n'
 'Duration_Start2End/String : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration_Start2End/String : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration_Start2End/String : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration_Start2End/String : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop Duration\r\n'
 'Duration_Start2End/String : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_Start_Command    : Play time of the stream, in ms\r\n'
 'Duration_Start_Command/St : Play time (formated)\r\n'
 'Duration_Start_Command/St : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration_Start_Command/St : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration_Start_Command/St : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration_Start_Command/St : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop Duration\r\n'
 'Duration_Start_Command/St : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_Start            : Play time of the stream, in ms\r\n'
 'Duration_Start/String     : Play time (formated)\r\n'
 'Duration_Start/String1    : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration_Start/String2    : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration_Start/String3    : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration_Start/String4    : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop Duration\r\n'
 'Duration_Start/String5    : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_End              : Play time of the stream, in ms\r\n'
 'Duration_End/String       : Play time (formated)\r\n'
 'Duration_End/String1      : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration_End/String2      : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration_End/String3      : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration_End/String4      : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration_End/String5      : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_End_Command      : Play time of the stream, in ms\r\n'
 'Duration_End_Command/Stri : Play time (formated)\r\n'
 'Duration_End_Command/Stri : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration_End_Command/Stri : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration_End_Command/Stri : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration_End_Command/Stri : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop Duration\r\n'
 'Duration_End_Command/Stri : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_FirstFrame       : Duration of the first frame if it is longer than others, in ms\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX omited '
 'if zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available\r\n'
 'Duration_FirstFrame/Strin : Duration of the first frame if it is longer than others, in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_LastFrame        : Duration of the last frame if it is longer than others, in ms\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited if '
 'zero\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : HH:MM:SS:FF, last colon replaced '
 'by semicolon for drop frame if available\r\n'
 'Duration_LastFrame/String : Duration of the last frame if it is longer than others, in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_Base \r\n'
 'Source_Duration           : Source Play time of the stream, in ms\r\n'
 'Source_Duration/String    : Source Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Source_Duration/String1   : Source Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Source_Duration/String2   : Source Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Source_Duration/String3   : Source Play time in format : HH:MM:SS.MMM\r\n'
 'Source_Duration/String4   : Source Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if '
 'available\r\n'
 'Source_Duration/String5   : Source Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in ms\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX '
 'omited if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HH:MM:SS.mmm '
 '(HH:MM:SS:FF)\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in ms\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX '
 'omited if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HH:MM:SS.mmm '
 '(HH:MM:SS:FF)\r\n'
 'BitRate_Mode              : Bit rate mode (VBR, CBR)\r\n'
 'BitRate_Mode/String       : Bit rate mode (Constant, Variable)\r\n'
 'BitRate                   : Bit rate in bps\r\n'
 'BitRate/String            : Bit rate (with measurement)\r\n'
 'BitRate_Minimum           : Minimum Bit rate in bps\r\n'
 'BitRate_Minimum/String    : Minimum Bit rate (with measurement)\r\n'
 'BitRate_Nominal           : Nominal Bit rate in bps\r\n'
 'BitRate_Nominal/String    : Nominal Bit rate (with measurement)\r\n'
 'BitRate_Maximum           : Maximum Bit rate in bps\r\n'
 'BitRate_Maximum/String    : Maximum Bit rate (with measurement)\r\n'
 'BitRate_Encoded           : Encoded (with forced padding) bit rate in bps, if some container padding is present\r\n'
 'BitRate_Encoded/String    : Encoded (with forced padding) bit rate (with measurement), if some container padding is present\r\n'
 'Width                     : Width\r\n'
 'Width/String \r\n'
 'Height                    : Height\r\n'
 'Height/String \r\n'
 'DisplayAspectRatio        : Display Aspect ratio\r\n'
 'DisplayAspectRatio/String : Display Aspect ratio\r\n'
 'DisplayAspectRatio_Origin : Original (in the raw stream) Display Aspect ratio\r\n'
 'DisplayAspectRatio_Origin : Original (in the raw stream) Display Aspect ratio\r\n'
 'FrameRate_Mode            : Frame rate mode (CFR, VFR)\r\n'
 'FrameRate_Mode/String     : Frame rate mode (Constant, Variable)\r\n'
 'FrameRate_Mode_Original   : Original frame rate mode (CFR, VFR)\r\n'
 'FrameRate_Mode_Original/S : Original frame rate mode (Constant, Variable)\r\n'
 'FrameRate                 : Frames per second\r\n'
 'FrameRate/String          : Frames per second (with measurement)\r\n'
 'FrameRate_Num             : Frames per second, numerator\r\n'
 'FrameRate_Den             : Frames per second, denominator\r\n'
 'FrameRate_Minimum         : Minimum Frames per second\r\n'
 'FrameRate_Minimum/String  : Minimum Frames per second (with measurement)\r\n'
 'FrameRate_Nominal         : Nominal Frames per second\r\n'
 'FrameRate_Nominal/String  : Nominal Frames per second (with measurement)\r\n'
 'FrameRate_Maximum         : Maximum Frames per second\r\n'
 'FrameRate_Maximum/String  : Maximum Frames per second (with measurement)\r\n'
 'FrameRate_Original        : Original (in the raw stream) frames per second\r\n'
 'FrameRate_Original/String : Original (in the raw stream) frames per second (with measurement)\r\n'
 'FrameRate_Original_Num    : Frames per second, numerator\r\n'
 'FrameRate_Original_Den    : Frames per second, denominator\r\n'
 'FrameCount                : Number of frames\r\n'
 'ElementCount              : Number of displayed elements\r\n'
 'Source_FrameCount         : Source Number of frames\r\n'
 'ColorSpace \r\n'
 'ChromaSubsampling \r\n'
 'Resolution                : Deprecated, do not use in new projects\r\n'
 'Resolution/String         : Deprecated, do not use in new projects\r\n'
 'BitDepth \r\n'
 'BitDepth/String \r\n'
 'Compression_Mode          : Compression mode (Lossy or Lossless)\r\n'
 'Compression_Mode/String   : Compression mode (Lossy or Lossless)\r\n'
 'Compression_Ratio         : Current stream size divided by uncompressed stream size\r\n'
 'Delay                     : Delay fixed in the stream (relative) IN MS\r\n'
 'Delay/String              : Delay with measurement\r\n'
 'Delay/String1             : Delay with measurement\r\n'
 'Delay/String2             : Delay with measurement\r\n'
 'Delay/String3             : Delay in format : HH:MM:SS.MMM\r\n'
 'Delay/String4             : Delay in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay/String5             : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Settings            : Delay settings (in case of timecode for example)\r\n'
 'Delay_DropFrame           : Delay drop frame\r\n'
 'Delay_Source              : Delay source (Container or Stream or empty)\r\n'
 'Delay_Source/String       : Delay source (Container or Stream or empty)\r\n'
 'Delay_Original            : Delay fixed in the raw stream (relative) IN MS\r\n'
 'Delay_Original/String     : Delay with measurement\r\n'
 'Delay_Original/String1    : Delay with measurement\r\n'
 'Delay_Original/String2    : Delay with measurement\r\n'
 'Delay_Original/String3    : Delay in format: HH:MM:SS.MMM\r\n'
 'Delay_Original/String4    : Delay in format: HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay_Original/String5    : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Original_Settings   : Delay settings (in case of timecode for example)\r\n'
 'Delay_Original_DropFrame  : Delay drop frame info\r\n'
 'Delay_Original_Source     : Delay source (Stream or empty)\r\n'
 'Video_Delay               : Delay fixed in the stream (absolute / video)\r\n'
 'Video_Delay/String \r\n'
 'Video_Delay/String1 \r\n'
 'Video_Delay/String2 \r\n'
 'Video_Delay/String3 \r\n'
 'Video_Delay/String4 \r\n'
 'Video_Delay/String5 \r\n'
 'Video0_Delay              : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String       : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String1      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String2      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String3      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String4      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String5      : Deprecated, do not use in new projects\r\n'
 'TimeCode_FirstFrame       : Time code in HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available format\r\n'
 'TimeCode_LastFrame        : Time code of the last frame (excluding the duration of the last frame) in HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available format\r\n'
 'TimeCode_DropFrame        : Delay drop frame\r\n'
 'TimeCode_Settings         : Time code settings\r\n'
 'TimeCode_Source           : Time code source (Container, Stream, SystemScheme1, SDTI, ANC...)\r\n'
 'TimeCode_MaxFrameNumber \r\n'
 'TimeCode_MaxFrameNumber_Theory \r\n'
 'StreamSize                : Streamsize in bytes\r\n'
 'StreamSize/String         : Streamsize in with percentage value\r\n'
 'StreamSize/String1 \r\n'
 'StreamSize/String2 \r\n'
 'StreamSize/String3 \r\n'
 'StreamSize/String4 \r\n'
 'StreamSize/String5        : Streamsize in with percentage value\r\n'
 'StreamSize_Proportion     : Stream size divided by file size\r\n'
 'StreamSize_Demuxed        : StreamSize in bytes of hte stream after demux\r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value\r\n'
 'StreamSize_Demuxed/String1 \r\n'
 'StreamSize_Demuxed/String2 \r\n'
 'StreamSize_Demuxed/String3 \r\n'
 'StreamSize_Demuxed/String4 \r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value (note: theoritical value, not for real use)\r\n'
 'Source_StreamSize         : Source Streamsize in bytes\r\n'
 'Source_StreamSize/String  : Source Streamsize in with percentage value\r\n'
 'Source_StreamSize/String1 \r\n'
 'Source_StreamSize/String2 \r\n'
 'Source_StreamSize/String3 \r\n'
 'Source_StreamSize/String4 \r\n'
 'Source_StreamSize/String5 : Source Streamsize in with percentage value\r\n'
 'Source_StreamSize_Proport : Source Stream size divided by file size\r\n'
 'StreamSize_Encoded        : Encoded Streamsize in bytes\r\n'
 'StreamSize_Encoded/String : Encoded Streamsize in with percentage value\r\n'
 'StreamSize_Encoded/String1 \r\n'
 'StreamSize_Encoded/String2 \r\n'
 'StreamSize_Encoded/String3 \r\n'
 'StreamSize_Encoded/String4 \r\n'
 'StreamSize_Encoded/String : Encoded Streamsize in with percentage value\r\n'
 'StreamSize_Encoded_Propor : Encoded Stream size divided by file size\r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in bytes\r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in with percentage value\r\n'
 'Source_StreamSize_Encoded/String1 \r\n'
 'Source_StreamSize_Encoded/String2 \r\n'
 'Source_StreamSize_Encoded/String3 \r\n'
 'Source_StreamSize_Encoded/String4 \r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in with percentage value\r\n'
 'Source_StreamSize_Encoded : Source Encoded Stream size divided by file size\r\n'
 'Title                     : Name of the track\r\n'
 'Encoded_Application       : Name of the software package used to create the file, such as Microsoft WaveEdit\r\n'
 'Encoded_Application/Strin : Name of the software package used to create the file, such as Microsoft WaveEdit, trying to have the '
 "format 'CompanyName ProductName (OperatingSystem) Version (Date)'\r\n"
 'Encoded_Application_Compa : Name of the company\r\n'
 'Encoded_Application_Name  : Name of the product\r\n'
 'Encoded_Application_Versi : Version of the product\r\n'
 'Encoded_Application_Url   : Name of the software package used to create the file, such as Microsoft WaveEdit.\r\n'
 'Encoded_Library           : Software used to create the file\r\n'
 "Encoded_Library/String    : Software used to create the file, trying to have the format 'CompanyName ProductName "
 "(OperatingSystem) Version (Date)'\r\n"
 'Encoded_Library_CompanyNa : Name of the company\r\n'
 'Encoded_Library_Name      : Name of the the encoding-software\r\n'
 'Encoded_Library_Version   : Version of encoding-software\r\n'
 'Encoded_Library_Date      : Release date of software\r\n'
 'Encoded_Library_Settings  : Parameters used by the software\r\n'
 'Encoded_OperatingSystem   : Operating System of encoding-software\r\n'
 'Language                  : Language (2-letter ISO 639-1 if exists, else 3-letter ISO 639-2, and with optional ISO 3166-1 '
 'country separated by a dash if available, e.g. en, en-us, zh-cn)\r\n'
 'Language/String           : Language (full)\r\n'
 'Language/String1          : Language (full)\r\n'
 'Language/String2          : Language (2-letter ISO 639-1 if exists, else empty)\r\n'
 'Language/String3          : Language (3-letter ISO 639-2 if exists, else empty)\r\n'
 'Language/String4          : Language (2-letter ISO 639-1 if exists with optional ISO 3166-1 country separated by a dash if '
 'available, e.g. en, en-us, zh-cn, else empty)\r\n'
 "Language_More             : More info about Language (e.g. Director's Comment)\r\n"
 'ServiceKind               : Service kind, e.g. visually impaired, commentary, voice over\r\n'
 'ServiceKind/String        : Service kind (full)\r\n'
 'Disabled                  : Set if that track should not be used\r\n'
 'Disabled/String           : Set if that track should not be used\r\n'
 'Default                   : Set if that track should be used if no language found matches the user preference.\r\n'
 'Default/String            : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced                    : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced/String             : Set if that track should be used if no language found matches the user preference.\r\n'
 'AlternateGroup            : Number of a group in order to provide versions of the same track\r\n'
 'AlternateGroup/String     : Number of a group in order to provide versions of the same track\r\n'
 'Summary \r\n'
 'Encoded_Date              : The time that the encoding of this item was completed began.\r\n'
 'Tagged_Date               : The time that the tags were done for this item.\r\n'
 'Encryption \r\n'
 'Events_Total \r\n'
 'Events_MinDuration \r\n'
 'Events_MinDuration/String : Minimum duration per event (formated)\r\n'
 'Events_MinDuration/String : Minimum duration per event in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Events_MinDuration/String : Minimum duration per event in format : XXx YYy only, YYy omited if zero\r\n'
 'Events_MinDuration/String : Minimum duration per event in format : HH:MM:SS.MMM\r\n'
 'Events_MinDuration/String : Minimum duration per event in format : HH:MM:SS:FF, last colon replaced by semicolon for drop '
 'Duration\r\n'
 'Events_MinDuration/String : Minimum duration per event in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Events_PopOn \r\n'
 'Events_RollUp \r\n'
 'Events_PaintOn \r\n'
 'Lines_Count \r\n'
 'Lines_MaxCountPerEvent \r\n'
 'FirstDisplay_Delay_Frames \r\n'
 'FirstDisplay_Type \r\n'
 ' \r\n'
 
 
 'Other \r\n'
 'Count                     : Count of objects available in this stream\r\n'
 'Status                    : bit field (0=IsAccepted, 1=IsFilled, 2=IsUpdated, 3=IsFinished)\r\n'
 'StreamCount               : Count of streams of that kind available\r\n'
 'StreamKind                : Stream type name\r\n'
 'StreamKind/String         : Stream type name\r\n'
 'StreamKindID              : Number of the stream (base=0)\r\n'
 'StreamKindPos             : When multiple streams, number of the stream (base=1)\r\n'
 'StreamOrder               : Stream order in the file, whatever is the kind of stream (base=0)\r\n'
 'FirstPacketOrder          : Order of the first fully decodable packet met in the file, whatever is the kind of stream '
 '(base=0)\r\n'
 'Inform                    : Last **Inform** call\r\n'
 'ID                        : The ID for this stream in this file\r\n'
 'ID/String                 : The ID for this stream in this file\r\n'
 'OriginalSourceMedium_ID   : The ID for this stream in the original medium of the material\r\n'
 'OriginalSourceMedium_ID/S : The ID for this stream in the original medium of the material\r\n'
 'UniqueID                  : The unique ID for this stream, should be copied with stream copy\r\n'
 'UniqueID/String           : The unique ID for this stream, should be copied with stream copy\r\n'
 'MenuID                    : The menu ID for this stream in this file\r\n'
 'MenuID/String             : The menu ID for this stream in this file\r\n'
 'Type                      : Type\r\n'
 'Format                    : Format used\r\n'
 'Format/String             : Format used + additional features\r\n'
 'Format/Info               : Info about Format\r\n'
 'Format/Url                : Link\r\n'
 'Format_Commercial         : Commercial name used by vendor for theses setings or Format field if there is no difference\r\n'
 'Format_Commercial_IfAny   : Commercial name used by vendor for theses setings if there is one\r\n'
 'Format_Version            : Version of this format\r\n'
 'Format_Profile            : Profile of the Format\r\n'
 'Format_Compression        : Compression method used\r\n'
 'Format_Settings           : Settings needed for decoder used\r\n'
 'Format_AdditionalFeatures : Format features needed for fully supporting the content\r\n'
 'MuxingMode                : How this file is muxed in the container\r\n'
 'CodecID                   : Codec ID (found in some containers)\r\n'
 'CodecID/String            : Codec ID (found in some containers)\r\n'
 'CodecID/Info              : Info about this codec\r\n'
 'CodecID/Hint              : A hint/popular name for this codec\r\n'
 'CodecID/Url               : A link to more details about this codec ID\r\n'
 'CodecID_Description       : Manual description given by the container\r\n'
 'Duration                  : Play time of the stream in ms\r\n'
 'Duration/String           : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String1          : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration/String2          : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String3          : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration/String4          : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration/String5          : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_Start \r\n'
 'Duration_End \r\n'
 'Source_Duration           : Source Play time of the stream, in ms\r\n'
 'Source_Duration/String    : Source Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Source_Duration/String1   : Source Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Source_Duration/String2   : Source Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Source_Duration/String3   : Source Play time in format : HH:MM:SS.MMM\r\n'
 'Source_Duration/String4   : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Source_Duration/String5   : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in ms\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX '
 'omited if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_FirstFram : Source Duration of the first frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Source_Duration_FirstFram : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Source_Duration_FirstFram : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in ms\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HHh MMmn SSs MMMms, XX '
 'omited if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : XXx YYy only, YYy omited '
 'if zero\r\n'
 'Source_Duration_LastFrame : Source Duration of the last frame if it is longer than others, in format : HH:MM:SS.MMM\r\n'
 'Source_Duration_LastFrame : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Source_Duration_LastFrame : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'BitRate_Mode              : Bit rate mode (VBR, CBR)\r\n'
 'BitRate_Mode/String       : Bit rate mode (Variable, Cconstant)\r\n'
 'BitRate                   : Bit rate in bps\r\n'
 'BitRate/String            : Bit rate (with measurement)\r\n'
 'BitRate_Minimum           : Minimum Bit rate in bps\r\n'
 'BitRate_Minimum/String    : Minimum Bit rate (with measurement)\r\n'
 'BitRate_Nominal           : Nominal Bit rate in bps\r\n'
 'BitRate_Nominal/String    : Nominal Bit rate (with measurement)\r\n'
 'BitRate_Maximum           : Maximum Bit rate in bps\r\n'
 'BitRate_Maximum/String    : Maximum Bit rate (with measurement)\r\n'
 'BitRate_Encoded           : Encoded (with forced padding) bit rate in bps, if some container padding is present\r\n'
 'BitRate_Encoded/String    : Encoded (with forced padding) bit rate (with measurement), if some container padding is present\r\n'
 'FrameRate                 : Frames per second\r\n'
 'FrameRate/String          : Frames per second (with measurement)\r\n'
 'FrameRate_Num             : Frames per second, numerator\r\n'
 'FrameRate_Den             : Frames per second, denominator\r\n'
 'FrameCount                : Number of frames\r\n'
 'Source_FrameCount         : Source Number of frames\r\n'
 'Delay                     : Delay fixed in the stream (relative) IN MS\r\n'
 'Delay/String              : Delay with measurement\r\n'
 'Delay/String1             : Delay with measurement\r\n'
 'Delay/String2             : Delay with measurement\r\n'
 'Delay/String3             : Delay in format : HH:MM:SS.MMM\r\n'
 'Delay/String4             : Delay in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay/String5             : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Settings            : Delay settings (in case of timecode for example)\r\n'
 'Delay_DropFrame           : Delay drop frame\r\n'
 'Delay_Source              : Delay source (Container or Stream or empty)\r\n'
 'Delay_Source/String       : Delay source (Container or Stream or empty)\r\n'
 'Delay_Original            : Delay fixed in the raw stream (relative) IN MS\r\n'
 'Delay_Original/String     : Delay with measurement\r\n'
 'Delay_Original/String1    : Delay with measurement\r\n'
 'Delay_Original/String2    : Delay with measurement\r\n'
 'Delay_Original/String3    : Delay in format: HH:MM:SS.MMM\r\n'
 'Delay_Original/String4    : Delay in format: HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay_Original/String5    : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Original_Settings   : Delay settings (in case of timecode for example)\r\n'
 'Delay_Original_DropFrame  : Delay drop frame info\r\n'
 'Delay_Original_Source     : Delay source (Stream or empty)\r\n'
 'Video_Delay               : Delay fixed in the stream (absolute / video)\r\n'
 'Video_Delay/String \r\n'
 'Video_Delay/String1 \r\n'
 'Video_Delay/String2 \r\n'
 'Video_Delay/String3 \r\n'
 'Video_Delay/String4 \r\n'
 'Video_Delay/String5 \r\n'
 'Video0_Delay              : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String       : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String1      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String2      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String3      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String4      : Deprecated, do not use in new projects\r\n'
 'Video0_Delay/String5      : Deprecated, do not use in new projects\r\n'
 'TimeStamp_FirstFrame      : TimeStamp fixed in the stream (relative) IN MS\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp with measurement\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp with measurement\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp with measurement\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp in format : HH:MM:SS.MMM\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'TimeStamp_FirstFrame/Stri : TimeStamp in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'TimeCode_FirstFrame       : Time code in HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available format\r\n'
 'TimeCode_LastFrame        : Time code of the last frame (excluding the duration of the last frame) in HH:MM:SS:FF, last colon '
 'replaced by semicolon for drop frame if available format\r\n'
 'TimeCode_DropFrame        : Delay drop frame\r\n'
 'TimeCode_Settings         : Time code settings\r\n'
 'TimeCode_Stripped         : Time code is Stripped (only 1st time code, no discontinuity)\r\n'
 'TimeCode_Stripped/String  : Time code is Stripped (only 1st time code, no discontinuity)\r\n'
 'TimeCode_Source           : Time code source (Container, Stream, SystemScheme1, SDTI, ANC...)\r\n'
 'StreamSize                : Streamsize in bytes\r\n'
 'StreamSize/String         : Streamsize in with percentage value\r\n'
 'StreamSize/String1 \r\n'
 'StreamSize/String2 \r\n'
 'StreamSize/String3 \r\n'
 'StreamSize/String4 \r\n'
 'StreamSize/String5        : Streamsize in with percentage value\r\n'
 'StreamSize_Proportion     : Stream size divided by file size\r\n'
 'StreamSize_Demuxed        : StreamSize in bytes of hte stream after demux\r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value\r\n'
 'StreamSize_Demuxed/String1 \r\n'
 'StreamSize_Demuxed/String2 \r\n'
 'StreamSize_Demuxed/String3 \r\n'
 'StreamSize_Demuxed/String4 \r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value (note: theoritical value, not for real use)\r\n'
 'Source_StreamSize         : Source Streamsize in bytes\r\n'
 'Source_StreamSize/String  : Source Streamsize in with percentage value\r\n'
 'Source_StreamSize/String1 \r\n'
 'Source_StreamSize/String2 \r\n'
 'Source_StreamSize/String3 \r\n'
 'Source_StreamSize/String4 \r\n'
 'Source_StreamSize/String5 : Source Streamsize in with percentage value\r\n'
 'Source_StreamSize_Proport : Source Stream size divided by file size\r\n'
 'StreamSize_Encoded        : Encoded Streamsize in bytes\r\n'
 'StreamSize_Encoded/String : Encoded Streamsize in with percentage value\r\n'
 'StreamSize_Encoded/String1 \r\n'
 'StreamSize_Encoded/String2 \r\n'
 'StreamSize_Encoded/String3 \r\n'
 'StreamSize_Encoded/String4 \r\n'
 'StreamSize_Encoded/String : Encoded Streamsize in with percentage value\r\n'
 'StreamSize_Encoded_Propor : Encoded Stream size divided by file size\r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in bytes\r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in with percentage value\r\n'
 'Source_StreamSize_Encoded/String1 \r\n'
 'Source_StreamSize_Encoded/String2 \r\n'
 'Source_StreamSize_Encoded/String3 \r\n'
 'Source_StreamSize_Encoded/String4 \r\n'
 'Source_StreamSize_Encoded : Source Encoded Streamsize in with percentage value\r\n'
 'Source_StreamSize_Encoded : Source Encoded Stream size divided by file size\r\n'
 'Title                     : Name of this menu\r\n'
 'Language                  : Language (2-letter ISO 639-1 if exists, else 3-letter ISO 639-2, and with optional ISO 3166-1 '
 'country separated by a dash if available, e.g. en, en-us, zh-cn)\r\n'
 'Language/String           : Language (full)\r\n'
 'Language/String1          : Language (full)\r\n'
 'Language/String2          : Language (2-letter ISO 639-1 if exists, else empty)\r\n'
 'Language/String3          : Language (3-letter ISO 639-2 if exists, else empty)\r\n'
 'Language/String4          : Language (2-letter ISO 639-1 if exists with optional ISO 3166-1 country separated by a dash if '
 'available, e.g. en, en-us, zh-cn, else empty)\r\n'
 "Language_More             : More info about Language (e.g. Director's Comment)\r\n"
 'ServiceKind               : Service kind, e.g. visually impaired, commentary, voice over\r\n'
 'ServiceKind/String        : Service kind (full)\r\n'
 'Disabled                  : Set if that track should not be used\r\n'
 'Disabled/String           : Set if that track should not be used\r\n'
 'Default                   : Set if that track should be used if no language found matches the user preference.\r\n'
 'Default/String            : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced                    : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced/String             : Set if that track should be used if no language found matches the user preference.\r\n'
 'AlternateGroup            : Number of a group in order to provide versions of the same track\r\n'
 'AlternateGroup/String     : Number of a group in order to provide versions of the same track\r\n'
 ' \r\n'
 
 
 'Image \r\n'
 'Count                     : Count of objects available in this stream\r\n'
 'Status                    : bit field (0=IsAccepted, 1=IsFilled, 2=IsUpdated, 3=IsFinished)\r\n'
 'StreamCount               : Count of streams of that kind available\r\n'
 'StreamKind                : Stream type name\r\n'
 'StreamKind/String         : Stream type name\r\n'
 'StreamKindID              : Number of the stream (base=0)\r\n'
 'StreamKindPos             : When multiple streams, number of the stream (base=1)\r\n'
 'StreamOrder               : Stream order in the file, whatever is the kind of stream (base=0)\r\n'
 'FirstPacketOrder          : Order of the first fully decodable packet met in the file, whatever is the kind of stream '
 '(base=0)\r\n'
 'Inform                    : Last **Inform** call\r\n'
 'ID                        : The ID for this stream in this file\r\n'
 'ID/String                 : The ID for this stream in this file\r\n'
 'OriginalSourceMedium_ID   : The ID for this stream in the original medium of the material\r\n'
 'OriginalSourceMedium_ID/S : The ID for this stream in the original medium of the material\r\n'
 'UniqueID                  : The unique ID for this stream, should be copied with stream copy\r\n'
 'UniqueID/String           : The unique ID for this stream, should be copied with stream copy\r\n'
 'MenuID                    : The menu ID for this stream in this file\r\n'
 'MenuID/String             : The menu ID for this stream in this file\r\n'
 'Title                     : Name of the track\r\n'
 'Format                    : Format used\r\n'
 'Format/String             : Format used + additional features\r\n'
 'Format/Info               : Info about Format\r\n'
 'Format/Url                : Link\r\n'
 'Format_Commercial         : Commercial name used by vendor for theses setings or Format field if there is no difference\r\n'
 'Format_Commercial_IfAny   : Commercial name used by vendor for theses setings if there is one\r\n'
 'Format_Version            : Version of this format\r\n'
 'Format_Profile            : Profile of the Format\r\n'
 'Format_Settings_Endianness \r\n'
 'Format_Settings_Packing \r\n'
 'Format_Compression        : Compression method used\r\n'
 'Format_Settings           : Settings needed for decoder used\r\n'
 'Format_Settings_Wrapping  : Wrapping mode (Frame wrapped or Clip wrapped)\r\n'
 'Format_AdditionalFeatures : Format features needed for fully supporting the content\r\n'
 'InternetMediaType         : Internet Media Type (aka MIME Type, Content-Type)\r\n'
 'CodecID                   : Codec ID (found in some containers)\r\n'
 'CodecID/String            : Codec ID (found in some containers)\r\n'
 'CodecID/Info              : Info about codec ID\r\n'
 'CodecID/Hint              : A hint for this codec ID\r\n'
 'CodecID/Url               : A link for more details about this codec ID\r\n'
 'CodecID_Description       : Manual description given by the container\r\n'
 'Codec                     : Deprecated, do not use in new projects\r\n'
 'Codec/String              : Deprecated, do not use in new projects\r\n'
 'Codec/Family              : Deprecated, do not use in new projects\r\n'
 'Codec/Info                : Deprecated, do not use in new projects\r\n'
 'Codec/Url                 : Deprecated, do not use in new projects\r\n'
 'Width                     : Width (aperture size if present) in pixel\r\n'
 'Width/String              : Width (aperture size if present) with measurement (pixel)\r\n'
 'Width_Offset              : Offset between original width and displayed width (aperture size) in pixel\r\n'
 'Width_Offset/String       : Offset between original width and displayed width (aperture size)  in pixel\r\n'
 'Width_Original            : Original (in the raw stream) width in pixel\r\n'
 'Width_Original/String     : Original (in the raw stream) width with measurement (pixel)\r\n'
 'Height                    : Height (aperture size if present) in pixel\r\n'
 'Height/String             : Height (aperture size if present) with measurement (pixel)\r\n'
 'Height_Offset             : Offset between original height and displayed height (aperture size) in pixel\r\n'
 'Height_Offset/String      : Offset between original height and displayed height (aperture size)  in pixel\r\n'
 'Height_Original           : Original (in the raw stream) height in pixel\r\n'
 'Height_Original/String    : Original (in the raw stream) height with measurement (pixel)\r\n'
 'PixelAspectRatio          : Pixel Aspect ratio\r\n'
 'PixelAspectRatio/String   : Pixel Aspect ratio\r\n'
 'PixelAspectRatio_Original : Original (in the raw stream) Pixel Aspect ratio\r\n'
 'PixelAspectRatio_Original : Original (in the raw stream) Pixel Aspect ratio\r\n'
 'DisplayAspectRatio        : Display Aspect ratio\r\n'
 'DisplayAspectRatio/String : Display Aspect ratio\r\n'
 'DisplayAspectRatio_Origin : Original (in the raw stream) Display Aspect ratio\r\n'
 'DisplayAspectRatio_Origin : Original (in the raw stream) Display Aspect ratio\r\n'
 'ColorSpace \r\n'
 'ChromaSubsampling \r\n'
 'Resolution                : Deprecated, do not use in new projects\r\n'
 'Resolution/String         : Deprecated, do not use in new projects\r\n'
 'BitDepth \r\n'
 'BitDepth/String \r\n'
 'Compression_Mode          : Compression mode (Lossy or Lossless)\r\n'
 'Compression_Mode/String   : Compression mode (Lossy or Lossless)\r\n'
 'Compression_Ratio         : Current stream size divided by uncompressed stream size\r\n'
 'StreamSize                : Stream size in bytes\r\n'
 'StreamSize/String \r\n'
 'StreamSize/String1 \r\n'
 'StreamSize/String2 \r\n'
 'StreamSize/String3 \r\n'
 'StreamSize/String4 \r\n'
 'StreamSize/String5        : With proportion\r\n'
 'StreamSize_Proportion     : Stream size divided by file size\r\n'
 'StreamSize_Demuxed        : StreamSize in bytes of hte stream after demux\r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value\r\n'
 'StreamSize_Demuxed/String1 \r\n'
 'StreamSize_Demuxed/String2 \r\n'
 'StreamSize_Demuxed/String3 \r\n'
 'StreamSize_Demuxed/String4 \r\n'
 'StreamSize_Demuxed/String : StreamSize_Demuxed in with percentage value (note: theoritical value, not for real use)\r\n'
 'Encoded_Library           : Software used to create the file\r\n'
 'Encoded_Library/String    : Software used to create the file\r\n'
 'Encoded_Library_Name      : Info from the software\r\n'
 'Encoded_Library_Version   : Version of software\r\n'
 'Encoded_Library_Date      : Release date of software\r\n'
 'Encoded_Library_Settings  : Parameters used by the software\r\n'
 'Language                  : Language (2-letter ISO 639-1 if exists, else 3-letter ISO 639-2, and with optional ISO 3166-1 '
 'country separated by a dash if available, e.g. en, en-us, zh-cn)\r\n'
 'Language/String           : Language (full)\r\n'
 'Language/String1          : Language (full)\r\n'
 'Language/String2          : Language (2-letter ISO 639-1 if exists, else empty)\r\n'
 'Language/String3          : Language (3-letter ISO 639-2 if exists, else empty)\r\n'
 'Language/String4          : Language (2-letter ISO 639-1 if exists with optional ISO 3166-1 country separated by a dash if '
 'available, e.g. en, en-us, zh-cn, else empty)\r\n'
 "Language_More             : More info about Language (e.g. Director's Comment)\r\n"
 'ServiceKind               : Service kind, e.g. visually impaired, commentary, voice over\r\n'
 'ServiceKind/String        : Service kind (full)\r\n'
 'Disabled                  : Set if that track should not be used\r\n'
 'Disabled/String           : Set if that track should not be used\r\n'
 'Default                   : Set if that track should be used if no language found matches the user preference.\r\n'
 'Default/String            : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced                    : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced/String             : Set if that track should be used if no language found matches the user preference.\r\n'
 'AlternateGroup            : Number of a group in order to provide versions of the same track\r\n'
 'AlternateGroup/String     : Number of a group in order to provide versions of the same track\r\n'
 'Summary \r\n'
 'Encoded_Date              : The time that the encoding of this item was completed began.\r\n'
 'Tagged_Date               : The time that the tags were done for this item.\r\n'
 'Encryption \r\n'
 'colour_description_presen : Presence of colour description\r\n'
 'colour_primaries          : Chromaticity coordinates of the source primaries\r\n'
 'transfer_characteristics  : Opto-electronic transfer characteristic of the source picture\r\n'
 'matrix_coefficients       : Matrix coefficients used in deriving luma and chroma signals from the green, blue, and red '
 'primaries\r\n'
 'colour_description_presen : Presence of colour description\r\n'
 'colour_primaries_Original : Chromaticity coordinates of the source primaries\r\n'
 'transfer_characteristics_ : Opto-electronic transfer characteristic of the source picture\r\n'
 'matrix_coefficients_Origi : Matrix coefficients used in deriving luma and chroma signals from the green, blue, and red '
 'primaries\r\n'
 ' \r\n'
 
 
 'Menu \r\n'
 'Count                     : Count of objects available in this stream\r\n'
 'Status                    : bit field (0=IsAccepted, 1=IsFilled, 2=IsUpdated, 3=IsFinished)\r\n'
 'StreamCount               : Count of streams of that kind available\r\n'
 'StreamKind                : Stream type name\r\n'
 'StreamKind/String         : Stream type name\r\n'
 'StreamKindID              : Number of the stream (base=0)\r\n'
 'StreamKindPos             : When multiple streams, number of the stream (base=1)\r\n'
 'StreamOrder               : Stream order in the file, whatever is the kind of stream (base=0)\r\n'
 'FirstPacketOrder          : Order of the first fully decodable packet met in the file, whatever is the kind of stream '
 '(base=0)\r\n'
 'Inform                    : Last **Inform** call\r\n'
 'ID                        : The ID for this stream in this file\r\n'
 'ID/String                 : The ID for this stream in this file\r\n'
 'OriginalSourceMedium_ID   : The ID for this stream in the original medium of the material\r\n'
 'OriginalSourceMedium_ID/S : The ID for this stream in the original medium of the material\r\n'
 'UniqueID                  : The unique ID for this stream, should be copied with stream copy\r\n'
 'UniqueID/String           : The unique ID for this stream, should be copied with stream copy\r\n'
 'MenuID                    : The menu ID for this stream in this file\r\n'
 'MenuID/String             : The menu ID for this stream in this file\r\n'
 'Format                    : Format used\r\n'
 'Format/String             : Format used + additional features\r\n'
 'Format/Info               : Info about Format\r\n'
 'Format/Url                : Link\r\n'
 'Format_Commercial         : Commercial name used by vendor for theses setings or Format field if there is no difference\r\n'
 'Format_Commercial_IfAny   : Commercial name used by vendor for theses setings if there is one\r\n'
 'Format_Version            : Version of this format\r\n'
 'Format_Profile            : Profile of the Format\r\n'
 'Format_Compression        : Compression method used\r\n'
 'Format_Settings           : Settings needed for decoder used\r\n'
 'Format_AdditionalFeatures : Format features needed for fully supporting the content\r\n'
 'CodecID                   : Codec ID (found in some containers)\r\n'
 'CodecID/String            : Codec ID (found in some containers)\r\n'
 'CodecID/Info              : Info about this codec\r\n'
 'CodecID/Hint              : A hint/popular name for this codec\r\n'
 'CodecID/Url               : A link to more details about this codec ID\r\n'
 'CodecID_Description       : Manual description given by the container\r\n'
 'Codec                     : Deprecated\r\n'
 'Codec/String              : Deprecated\r\n'
 'Codec/Info                : Deprecated\r\n'
 'Codec/Url                 : Deprecated\r\n'
 'Duration                  : Play time of the stream in ms\r\n'
 'Duration/String           : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String1          : Play time in format : HHh MMmn SSs MMMms, XX omited if zero\r\n'
 'Duration/String2          : Play time in format : XXx YYy only, YYy omited if zero\r\n'
 'Duration/String3          : Play time in format : HH:MM:SS.MMM\r\n'
 'Duration/String4          : Play time in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Duration/String5          : Play time in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Duration_Start \r\n'
 'Duration_End \r\n'
 'Delay                     : Delay fixed in the stream (relative) IN MS\r\n'
 'Delay/String              : Delay with measurement\r\n'
 'Delay/String1             : Delay with measurement\r\n'
 'Delay/String2             : Delay with measurement\r\n'
 'Delay/String3             : Delay in format : HH:MM:SS.MMM\r\n'
 'Delay/String4             : Delay in format : HH:MM:SS:FF, last colon replaced by semicolon for drop frame if available\r\n'
 'Delay/String5             : Delay in format : HH:MM:SS.mmm (HH:MM:SS:FF)\r\n'
 'Delay_Settings            : Delay settings (in case of timecode for example)\r\n'
 'Delay_DropFrame           : Delay drop frame\r\n'
 'Delay_Source              : Delay source (Container or Stream or empty)\r\n'
 'List_StreamKind           : List of programs available\r\n'
 'List_StreamPos            : List of programs available\r\n'
 'List                      : List of programs available\r\n'
 'List/String               : List of programs available\r\n'
 'Title                     : Name of this menu\r\n'
 'Language                  : Language (2-letter ISO 639-1 if exists, else 3-letter ISO 639-2, and with optional ISO 3166-1 '
 'country separated by a dash if available, e.g. en, en-us, zh-cn)\r\n'
 'Language/String           : Language (full)\r\n'
 'Language/String1          : Language (full)\r\n'
 'Language/String2          : Language (2-letter ISO 639-1 if exists, else empty)\r\n'
 'Language/String3          : Language (3-letter ISO 639-2 if exists, else empty)\r\n'
 'Language/String4          : Language (2-letter ISO 639-1 if exists with optional ISO 3166-1 country separated by a dash if '
 'available, e.g. en, en-us, zh-cn, else empty)\r\n'
 "Language_More             : More info about Language (e.g. Director's Comment)\r\n"
 'ServiceKind               : Service kind, e.g. visually impaired, commentary, voice over\r\n'
 'ServiceKind/String        : Service kind (full)\r\n'
 'ServiceName \r\n'
 'ServiceChannel \r\n'
 'Service/Url \r\n'
 'ServiceProvider \r\n'
 'ServiceProvider/Url \r\n'
 'ServiceType \r\n'
 'NetworkName \r\n'
 'Original/NetworkName \r\n'
 'Countries \r\n'
 'TimeZones \r\n'
 "LawRating                 : Depending on the country it's the format of the rating of a movie (P, R, X in the USA, an age in "
 'other countries or a URI defining a logo).\r\n'
 'LawRating_Reason          : Reason for the law rating\r\n'
 'Disabled                  : Set if that track should not be used\r\n'
 'Disabled/String           : Set if that track should not be used\r\n'
 'Default                   : Set if that track should be used if no language found matches the user preference.\r\n'
 'Default/String            : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced                    : Set if that track should be used if no language found matches the user preference.\r\n'
 'Forced/String             : Set if that track should be used if no language found matches the user preference.\r\n'
 'AlternateGroup            : Number of a group in order to provide versions of the same track\r\n'
 'AlternateGroup/String     : Number of a group in order to provide versions of the same track\r\n'
 'Chapters_Pos_Begin        : Used by third-party developers to know about the beginning of the chapters list, to be used by '
 'Get(Stream_Menu, x, Pos), where Pos is an Integer between Chapters_Pos_Begin and Chapters_Pos_End\r\n'
 'Chapters_Pos_End          : Used by third-party developers to know about the end of the chapters list (this position excluded)')
'''