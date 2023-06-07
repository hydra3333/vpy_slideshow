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
from collections import defaultdict, OrderedDict
import itertools
import math
import sys
import os
import glob
import configparser	# or in v3: configparser 
import yaml
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
			#print(f'CONVERSION EXCEPTION ON val =["I":int, "F":float, "T":str, "D":str, "B":str][type_](str_value) ... type_="{type_}" param="{param}" str_value="{str_value}" path={path}')
			#print(f"Unexpected Error {err=}, {type(err)=}")
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
	#	#print(f'PIL EXIF DATA "{k}" = "{v}"')
	#	k = r'EXIF_' + str(k)
	#	PIL_dict[k] = v
	#exif = image.getexif()
	#exif_0x8769 = exif.get_ifd(0x8769)
	#print(f'type_0x8769={type(exif_0x8769)} exif_0x8769={exif_0x8769}')
	#exif_0x8769_d = dict(exif_0x8769)
	#print(f'type_0x8769_d={type(exif_0x8769)} exif_0x8769_d={exif_0x8769_d}')
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
		#print(f'auto_rotation_value_PIL: except UnidentifiedImageError immediate return now')
		return rotation_degrees, "anti-clockwise"
	except PermissionError:
		#print(f'auto_rotation_value_PIL: except PermissionError Permission denied to load: {path} immediate return now')
		return rotation_degrees, "anti-clockwise"
	except Exception as e:
		#print(f'auto_rotation_value_PIL: except Exception {e} immediate return now')
		return rotation_degrees, "anti-clockwise"
	#print(f'auto_rotation_value_PIL: try on Image.open succeeded')
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
		#print(f'auto_rotation_value_PIL: except AttributeError during for key in ExifTags.TAGS.keys(), immediate return now {path}')
		return rotation_degrees, "anti-clockwise"
	else:
		if   value == 0:
			rotation_degrees = 0
			#print(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 0 degrees {path}')
		elif   value == 3:
			rotation_degrees = 180
			#print(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 180 degrees {path}')
		elif value == 8:
			rotation_degrees = 90
			#print(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by  90 degrees {path}')
		elif value == 6:
			rotation_degrees = 270
			#print(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by 270 degrees {path}')
	image.close()	
	#print(f'auto_rotation_value_PIL: PIL says auto-Rotating ANTI-CLOCKWISE by {rotation_degrees} degrees {path}')
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
	#print(f'auto_rotation_value_MediaInfo: MediaInfo says auto-Rotating CLOCKWISE by {rotation_degrees} degrees {path}')
	return rotation_degrees, "clockwise"

###
def get_partial_clip_specs(clip=None):
	if clip is None:
		raise ValueError(f'ERROR: get_clip_specs: "clip" not passed as an argument to get_clip_specs')
	clip_specs = {}
	clip_specs["width"] = clip.width
	clip_specs["height"] = clip.height
	clip_specs["num_frames"] = clip.num_frames
	clip_specs["fps"] = clip.fps
	clip_specs["format_name"] = clip.format.name
	clip_specs["color_family"] = clip.format.color_family.value		# .value
	clip_specs["sample_type"] = clip.format.sample_type.value		# .value	If the format is integer or floating point based.
	clip_specs["bits_per_sample"] = clip.format.bits_per_sample
	clip_specs["bytes_per_sample"] = clip.format.bytes_per_sample
	clip_specs["num_planes"] = clip.format.num_planes
	clip_specs["subsampling_w"] = clip.format.subsampling_w
	clip_specs["subsampling_h"] = clip.format.subsampling_h
	print_DEBUG(f'get_clip_specs: JUST BEFORE "with clip.get_frame(0) as f:" clip={clip} clip_specs={objPrettyPrint.pformat(clip_specs)}')
	with clip.get_frame(0) as f:
		clip_specs["_Matrix"] = f.props["_Matrix"] if "_Matrix" in f.props else None
		clip_specs["_Transfer"] = f.props["_Transfer"] if "_Transfer" in f.props else None
		clip_specs["_Primaries"] = f.props["_Primaries"] if "_Primaries" in f.props else None
		clip_specs["_ColorRange"] = f.props["_ColorRange"] if "_ColorRange" in f.props else None
		clip_specs["_ChromaLocation"] = f.props["_ChromaLocation"] if  "_ChromaLocation" in f.props else None
		clip_specs["_DurationDen"] = f.props["_DurationDen"] if "_DurationDen" in f.props else None
		clip_specs["_DurationNum"] = f.props["_DurationNum"] if "_DurationNum" in f.props else None
		clip_specs["_FieldBased"] = f.props["_FieldBased"] if "_FieldBased" in f.props else None	# 0=frame based (progressive), 1=bottom field first, 2=top field first. # https://www.vapoursynth.com/doc/apireference.html?highlight=_FieldBased
		clip_specs["_PictType"] = f.props["_PictType"] if "_PictType" in f.props else None
	return clip_specs

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
	#DIRECTORY = r"E:\\multimedia"
	#DIRECTORY = r'D:\\ssTEST\\TEST_VIDS_IMAGES\\0TEST'
	DIRECTORY = r'D:\\ssTEST\\TEST_VIDS_IMAGES\\1TEST'
else:
	DIRECTORY = str(sys.argv[1])

paths = Path(DIRECTORY).glob(f'**/*.*') # recursive

MI = MediaInfo()

pic_extensions = [".png", ".jpg", ".jpeg", ".gif"]	#always lowercase
vid_extensions = [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov", ".m2ts"]	#always lowercase
## for now, ignore 3gp because we aren't fixing missing colourspace properties in this script
##vid_extensions = [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".mov", ".m2ts"]	#always lowercase ... 

clips = None

for path in paths:
	if path.suffix.lower() in vid_extensions:
		p_dict = {}
		print_NORMAL(f'Video File: {path}')
		MI.Open(str(path))
		for param in mi_video_params_1:
			value = mediainfo_value(Stream.Video, track=0, param=param, path=path)
			#print_NORMAL(f'"{param}" = \t\t\t\t"{value}"\t\t\ttype={type(value)}\t\t\tisinstance(value,str)={isinstance(value,str)}\t\tisinstance(value,int)={isinstance(value,int)}\t\tisinstance(value,bool)={isinstance(value,bool)}\t\tisinstance(value,float)={isinstance(value,float)}')
			p_dict[param] = value	# any of str, bool, int, float, etc
		MI.Close()
		#print_NORMAL(f'{objPrettyPrint.pformat(p_dict)}')
	
		if p_dict["FrameRate_Mode"] is None:	p_dict["FrameRate_Mode"] = "CFR"
		if p_dict["ScanType"] is None:			p_dict["ScanType"] = "Progressive"
		if p_dict["ScanOrder"] is None:			p_dict["ScanOrder"] = "TFF"
		if p_dict["FrameRate_Nominal"] is None:	p_dict["FrameRate_Nominal"] = p_dict["FrameRate"]
		# sometimes, who knows why, mediainfo returnes NO FrameRate_Num/FrameRate_Den although FrameRate is returned
		if p_dict["FrameRate_Num"] is None:		
			p_dict["FrameRate_Num"] = int(p_dict["FrameRate"] * 1000.0)
			p_dict["FrameRate_Den"] = 1000
		
		if p_dict["FrameRate_Mode"].lower() != "VFR".lower():	# assume CFR if not "VFR"
			###print_NORMAL(f'CFR ("{p_dict["FrameRate_Mode"]}")\t"{path}"')
			pass
		else:
			#print_NORMAL(f'VFR ("{p_dict["FrameRate_Mode"]}")\t"{path}" ' \
			#		f'\n\tFrameRate={p_dict["FrameRate"]} FrameRate_Num={p_dict["FrameRate_Num"]} FrameRate_Den={p_dict["FrameRate_Den"]} ' \
			#		f'\n\tFrameRate_Mode={p_dict["FrameRate_Mode"]} ' \
			#		f'\n\tFrameRate_Minimum={p_dict["FrameRate_Minimum"]} ' \
			#		f'\n\tFrameRate_Nominal={p_dict["FrameRate_Nominal"]} ' \
			#		f'\n\tFrameRate_Maximum={p_dict["FrameRate_Maximum"]} ' \
			#		f'\n\tFrameRate_Real={p_dict["FrameRate_Real"]} ' \
			#		f'\n\tScanType={p_dict["ScanType"]} ' \
			#		f'\n\tScanOrder={p_dict["ScanOrder"]} ' \
			#		f'\n\tScanOrder_Stored={p_dict["ScanOrder_Stored"]} ' \
			#		f'\n\tScanOrder_StoredDisplayedInverted={p_dict["ScanOrder_StoredDisplayedInverted"]} ' \
			#		)
			if p_dict["ScanType"].lower() != "Progressive".lower():
				raise ValueError(f'{path} is  VFR and not PROGRESSIVE')
			#
			# for now, try 50FPS, later do 100FPS and select every TFF from 2nd FRAME
			clip = core.ffms2.Source(str(path), fpsnum=50, fpsden=1) # make CFR by dups and drops, so make FPS HIGH since some clips are 60fps ... (for PAL target 25fps in the end) ... or do VFRtoCFR above if that works better

			before_clip_specs = get_partial_clip_specs(clip)
			print_NORMAL(f'SPECS BEFORE: {objPrettyPrint.pformat(before_clip_specs)}')

			# https://forum.doom9.org/showthread.php?p=1921016#post1921016
			# https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page3#post2685569

			clip = core.std.SetFieldBased(clip=clip, value=2)	# AssumeTFF #SetFieldBased sets _FieldBased to value and deletes the _Field frame property. 0 = Frame Based 1 = Bottom Field First 2 = Top Field First 
			clip = core.std.AssumeFPS(clip=clip, fpsnum=50, fpsden=1)
			# THIS IS 50p->50i TFF (aka 25i TFF):
			clip = core.std.SeparateFields(clip,tff=True).std.SelectEvery(cycle=4,offsets=[0,3]).std.DoubleWeave(tff=True).std.SelectEvery(cycle=2,offsets=0)
			clip = core.std.AssumeFPS(clip=clip, fpsnum=25, fpsden=1)
			# deinterlace
			# znedi3 
			#	field: 0: Same rate, keep bottom field. 1: Same rate, keep top field.2: Double rate, start with bottom field. 3: Double rate, start with top field.
			# yadifmod
			#	order: Sets the field order  in the source frames. 0 = bff 1 = tff
			#	field: Controls which field to keep when using same rate output. -1 = set equal to order 0 = keep bottom field 1 = keep top field
			#	mode: Controls double rate vs same rate output, and whether or not the spatial interlacing check is performed.
			#			0 = same rate, do spatial check 1 = double rate, do spatial check 2 = same rate, no spatial check 3 = double rate, no spatial check
			clip = core.yadifmod.Yadifmod(clip=clip, edeint=core.znedi3.nnedi3(clip=clip,field=1), order=1, field=1, mode=0) 
			try:
				clip = core.resize.Spline36(clip, width=1920, height=1080, format=vs.YUV420P8, matrix=vs.MatrixCoefficients.MATRIX_BT709, transfer=vs.TransferCharacteristics.TRANSFER_BT709, primaries=vs.ColorPrimaries.PRIMARIES_BT709, range=ZIMG_RANGE_FULL)
				after_clip_specs = get_partial_clip_specs(clip)
				print_NORMAL(f'SPECS AFTER: {objPrettyPrint.pformat(after_clip_specs)}')
				if clips is None:
					clips = clip
				else:
					clips = clips + clip
			except Exception as e:
				print_NORMAL(f'WARNING: error RESIZING {path}; ignoring video. The error was:\n{e}\n{type(e)}\n{str(e)}')
			del clip
clips.set_output()


