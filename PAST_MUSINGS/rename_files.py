
# https://mediaarea.net/download/binary/libmediainfo0/
# https://mediaarea.net/en/MediaInfo/Download/Windows
# download 64bit DLL without installer, unzip, find Media
# put MediaInfoDLL3.py in your directory (portable setup) or site-packages directory

import vapoursynth as vs
from vapoursynth import core
import os
import sys
import re
from functools import partial
from pathlib import Path, PureWindowsPath
import subprocess
import datetime
from datetime import datetime, date, time, timezone
import itertools
import math
from fractions import Fraction
from ctypes import *		# for mediainfo ... load via ctypes.CDLL(r'.\MediaInfo.dll')
from typing import Union	# for mediainfo
from typing import NamedTuple
import glob
import yaml
import json
import pprint
from collections import defaultdict, OrderedDict

from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.ExifTags import TAGS

#---
global vid_extensions
global pic_extensions
vid_extensions = (".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov", ".m2ts")	#always lowercase
pic_extensions = (".png", ".jpg", ".jpeg", ".gif")	#always lowercase
#---

#---
CDLL(r'MediaInfo.dll')				# note the hard-coded folder # per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
#from MediaInfoDLL3 import *
global MI
MI = MediaInfo()
#---

def parse_folder_copying_files(source_folder_path, target_folder_path):
	for root, dirs, files in os.walk(source_folder_path):
		for file_name in files:
			file_path = os.path.join(root, file_name)
			if file_name.lower().endswith(pic_extensions):
				#print(f"process_image('{file_path}')")
				process_image(file_path)
			elif file_name.lower().endswith(vid_extensions):
				#print(f"process_video('{file_path}')")
				process_video(file_path)

def process_image(file_path):
	image_metadata_dict = image_get_metadata_via_PIL(file_path)
	rotation = image_metadata_dict["Rotation_Flipping"]["exif_clockwise_rotation_degrees"]
	width = image_metadata_dict["Width after rotation"]
	height = image_metadata_dict["Height after rotation"]
	datetime_recorded = image_metadata_dict["Date Recorded"]
	new_name = ""
	if datetime_recorded:
		new_name += datetime_recorded.strftime("%Y_%m_%d_%H_%M_%S_%f_")
	if rotation is not None:
		new_name += f"rot_{'+' if rotation > 0 else '-'}{abs(rotation):03d}_"
	new_name += f"{width:04d}x{height:04d}_{os.path.splitext(os.path.basename(file_path))[0]}{os.path.splitext(file_path)[1]}"
	new_file_path = os.path.join(os.path.dirname(file_path), new_name)
	# copy /Y to a new folder with a new filename, rather than rename
	#os.rename(file_path, new_file_path)
	print(f"Copied: {file_path} -> {new_file_path}")

def process_video(file_path):
	video_metadata_dict = video_extract_metadata_via_MEDIAINFO(file_path)
	rotation = int(float(video_metadata_dict["Rotation"]))
	
	THIS IS WIDTH AND HEIGHT BEFORE ROTATION  ... 	IT NEEDS FIXING

	width = video_metadata_dict["Width"] 	#???????? ... need BEFORE and AFTER rotation ...
	height = video_metadata_dict["Height"] 	#???????? ... need BEFORE and AFTER rotation ...
	
	
	#print(f"process_video: '{file_path}' rotation={rotation} BEFORE_ROTATION width={width} height={height}")
	datetime_recorded = datetime.strptime(video_metadata_dict["Encoded_Date"], "%Y-%m-%d %H:%M:%S UTC")
	new_name = ""
	if datetime_recorded:
		new_name += datetime_recorded.strftime("%Y_%m_%d_%H_%M_%S_%f_")
	if rotation is not None:
		new_name += f"rot_{'+' if rotation > 0 else '-'}{abs(rotation):03d}_"
	new_name += f"{width:04d}x{height:04d}_{os.path.splitext(os.path.basename(file_path))[0]}{os.path.splitext(file_path)[1]}"
	new_file_path = os.path.join(os.path.dirname(file_path), new_name)
	# copy /Y to a new folder with a new filename, rather than rename
	#os.rename(file_path, new_file_path)
	print(f"Copied: {file_path} -> {new_file_path}")
#--------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------

def image_get_metadata_via_PIL(image_path):
	with Image.open(image_path) as image:
		exif_data = image._getexif()
		if exif_data is None:
			return {
				"Date Recorded": None,
				"Rotation_Flipping": None,
				"Width before rotation": None,
				"Height before rotation": None,
				"Width after rotation": None,
				"Height after rotation": None
			}
		# fetch and calulate the exif data
		date_recorded = image_get_date_recorded_from_exif(exif_data)
		rotation_flipping_dict = image_calculate_rotation_flipping(exif_data)
		width_before_rotation = image.width
		height_before_rotation = image.height
		# Calculate width and height after rotation (if rotation is applied)
		if rotation_flipping_dict["exif_clockwise_rotation_degrees"] == 90 or rotation_flipping_dict["exif_clockwise_rotation_degrees"] == 270:
			width_after_rotation = height_before_rotation
			height_after_rotation = width_before_rotation
		else:
			width_after_rotation = width_before_rotation
			height_after_rotation = height_before_rotation

		return {
			"Date Recorded": date_recorded,
			"Rotation_Flipping": rotation_flipping_dict,
			"Width before rotation": width_before_rotation,
			"Height before rotation": height_before_rotation,
			"Width after rotation": width_after_rotation,
			"Height after rotation": height_after_rotation
		}

def image_get_date_recorded_from_exif(exif_data):
	date_tag = 36867  # Exif tag for DateTimeOriginal
	if date_tag in exif_data:
		date_recorded = exif_data[date_tag]
		return datetime.strptime(date_recorded, "%Y:%m:%d %H:%M:%S")	#.strftime("%Y_%m_%d_%H_%M_%S_%f")
	return None

def image_calculate_rotation_flipping(exif_data):
	# https://sirv.com/help/articles/rotate-photos-to-be-upright/
	#	Exif Orientation values 1,3,6,8 have no flipping
	#	Exif Orientation values 2.4.5.7 involve flipping as well as rotations.
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
	#	Therefore, the optimal rotation and flip values for each orientation are as follows:
	#	Orientation Value: 1
	#		Optimal Rotation: No rotation
	#		Optimal Flip: No flip
	#	Orientation Value: 2
	#		Optimal Rotation: 0 degrees clockwise rotation
	#		Optimal Flip: Horizontal flip
	#	Orientation Value: 3
	#		Optimal Rotation: 180 degrees clockwise rotation
	#		Optimal Flip: No flip
	#	Orientation Value: 4
	#		Optimal Rotation: 0 degrees clockwise rotation
	#		Optimal Flip: Vertical flip
	#	Orientation Value: 5
	#		Optimal Rotation: 90 degrees clockwise rotation
	#		Optimal Flip: Horizontal flip
	#	Orientation Value: 6
	#		Optimal Rotation: 90 degrees clockwise rotation
	#		Optimal Flip: No flip
	#	Orientation Value: 7
	#		Optimal Rotation: 90 degrees clockwise rotation
	#		Optimal Flip: Vertical flip
	#	Orientation Value: 8
	#		Optimal Rotation: 270 degrees clockwise rotation
	#		Optimal Flip: No flip
	#
	exif_orientation_value = 1
	if hasattr(exif_data, '__getitem__'):
		exif_orientation_value = exif_data.get(0x0112)
		if exif_orientation_value == 1:
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 0,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			}
		elif exif_orientation_value == 2:
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 0,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 1,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 1
			}
		elif exif_orientation_value == 3:
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 180,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 1,
				'reversal_horizontal_flips': 1
			}
		elif exif_orientation_value == 4:
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 180,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 1,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 1,
				'reversal_horizontal_flips': 0
			}
		elif exif_orientation_value == 5:
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 90,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 1,
				'reversal_clockwise_rotation_degrees': 90,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 1
			}
		elif exif_orientation_value == 6:
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 270,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_clockwise_rotation_degrees': 90,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			}
		elif exif_orientation_value == 7:
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 270,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 1,
				'reversal_clockwise_rotation_degrees': 90,
				'reversal_vertical_flips': 1,
				'reversal_horizontal_flips': 0
			}
		elif exif_orientation_value == 8:
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 90,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_clockwise_rotation_degrees': 270,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			}
		else: # unknown exif value, assume no rotation and no flipping
			return {
				'exif_orientation_value': exif_orientation_value,
				'exif_clockwise_rotation_degrees': 0,
				'exif_vertical_flips': 0,
				'exif_horizontal_flips': 0,
				'reversal_clockwise_rotation_degrees': 0,
				'reversal_vertical_flips': 0,
				'reversal_horizontal_flips': 0
			} 
	return {  # no exif data, assume no rotation and no flipping
		'exif_orientation_value': exif_orientation_value,
		'exif_clockwise_rotation_degrees': 0,
		'exif_vertical_flips': 0,
		'exif_horizontal_flips': 0,
		'reversal_clockwise_rotation_degrees': 0,
		'reversal_vertical_flips': 0,
		'reversal_horizontal_flips': 0
	}

#--------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------
#
# use ffprobe class like this:
#
#	obj_ffprobe = ffprobe(file_path)
#	print(f'{objPrettyPrint.pformat(obj_ffprobe.dict)}')	# to print everything. take care to notice stream indexing to correctly find your video stream metadata
#	encoded_date = obj_ffprobe.format_dict.get("Encoded_Date")	# 'Encoded_Date': '2013-09-01 03:46:29 UTC'
#	duration = obj_ffprobe.format_dict.get("duration")
#	rotation = obj_ffprobe.first_video.get("rotation")
#	r_frame_rate = obj_ffprobe.first_video.get("r_frame_rate")
#
class ffprobe:
	# This is a beaut class
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
	# 
	import os
	import sys
	import subprocess
	from pathlib import Path
	from typing import NamedTuple
	import json
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

#
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
#
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
	# Most useful stuff
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
		'Recorded_Date',								 # : Time/date/year that the recording bega
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
	MI.Open(str(file_path))
	mi_dict = {}
	for param in mi_video_params_1:
		#value = mediainfo_value(Stream.Video, track=0, param=param, path=file_path)	# version: single-value retrieval and lots of open/close
		value = video_mediainfo_value_worker(Stream.Video, track=0, param=param, path=file_path)
		video_mediainfo_value_worker
		mi_dict[param] = value	# any of str, bool, int, float, etc
	MI.Close()
	#print(f'\n====================mi_dict=\n{objPrettyPrint.pformat(mi_dict)}')
	return mi_dict

#--------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------

def is_valid_windows_path(path):
	# Regular expression pattern for validating Windows file path
	pattern = r'^[a-zA-Z]:\\(((?![<>:"/|?*]).)+((?<![ .])\\)?)*$'
	# Check if the path matches the pattern
	return re.match(pattern, path) is not None

def check_and_create_folder(folder_path):
	if os.path.exists(folder_path):
		print(f"The folder '{folder_path}' already exists.")
	else:
		try:
			os.makedirs(folder_path)
			print(f"The folder '{folder_path}' did not exist and has now been created.")
			return
		except Exception as e:
			print(f"An error occurred while creating the folder '{target_folder_path}': {str(e)}")
			sys.exit(1)

#--------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------

if len(sys.argv) < 2:
	print(f"Error: Please provide the source-folder-path and target-folder-path as arguments. eg \npython.exe 'D:\ssTEST\TEST_VIDS_IMAGES\2TEST_rotations' 'D:\ssTEST\TEST_VIDS_IMAGES\2TEST_rotations_renamed'")
	sys.exit(1)

source_folder_path = sys.argv[1]
target_folder_path = sys.argv[2]

if not is_valid_windows_path(source_folder_path):
	print(f"Invalid Windows path format for source '{source_folder_path}'.")
	sys.exit(1)

if not os.path.exists(source_folder_path):
	print(f"The source folder '{source_folder_path}' does not exist exist.")
	sys.exit(1)

if not is_valid_windows_path(target_folder_path):
	print(f"Invalid Windows path format for target '{target_folder_path}'.")
	sys.exit(1)

check_and_create_folder(target_folder_path)
	
parse_folder_copying_files(source_folder_path, target_folder_path)
