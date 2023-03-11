# PYTHON3
#
# Version:	as at 2023.03.04
#
# Description:
#
#	Attempt to create a HD video slideshow of images and hopefully video clips from a folder tree.
#	Does 8-bit only, does not handle HDR conversions etc.
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
#	With all due respect to _AI_
#	Original per _AI_ as updated in this thread and below
#		https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678241
#
# Environment:
#
#	One has to setup a suitable environment ... eg
#		portable python into a nominated folder
#		portable vapoursynth overlaid in the same folder ... Assume vapoursynth API4 using release >= R60
#		an ffmpeg build with options for vapoursynth and NVenc enabled, copied into the same folder
#		portable pip downloaded into the same folder
#		a pip install of Pillow etc (refer below)
#		Donald Graft's DGDecNV extracted into the subfolder DGIndex (refer below)
#		suitable filters (refer below)
#	Thread for interest https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678484
#
# Python modules and Pip stuff
#
#		set "vs_path=C:\SOFTWARE\Vapoursynth-x64\"
#		REM set "vs_path=C:\SOFTWARE\Vapoursynth-x64-noPython\"
#		if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")
#		set "py_exe=%vs_path%python.exe"
#
#		pushd C:\TEMP
#		del "pip.pyz"
#		c:\software\wget\wget.exe -v -t 1 --server-response --timeout=360 -nd -np -nH --no-cookies --output-document="pip.pyz" "https://bootstrap.pypa.io/pip/pip.pyz"
#		python pip.pyz --help
#		python pip.pyz --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager install pip
#		python -m pip --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager pip
#		python -m pip --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --use-pep517 pip-review
#		REM install latest certificates for python requests.get
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose certifi 
#		REM cffi NEEDS to get done BEFORE sudo pip3 --no-cache-dir check
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose cffi
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose numpy
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose pillow
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose pathlib 
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose pymediainfo
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose sockets
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose requests
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose datetime
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose packaging
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose setuptools
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose python-utils
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose progressbar2
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose pyyaml
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose html5lib
#		pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose configparser
#		pip3 cache purge
#		pip3 --no-cache-dir list
#		pip3  --no-cache-dir list --outdated
#		pip3  --no-cache-dir check
#		pip-review --verbose
#		pip-review --verbose --auto --continue-on-fail
#		popd
# OR if we don't have python installed:
#		pushd %vs_path%
#		del "pip.pyz"
#		c:\software\wget\wget.exe -v -t 1 --server-response --timeout=360 -nd -np -nH --no-cookies --output-document="pip.pyz" "https://bootstrap.pypa.io/pip/pip.pyz"
#		"%py_exe%" pip.pyz --help
#		REM NOTE: NO QUOTES around %vs_path% or these abort !!!
#		"%py_exe%" pip.pyz install pip --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install setuptools --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install pip-review --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		REM install latest certificates for python requests.get
#		"%py_exe%" pip.pyz install certifi --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install cffi --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install numpy --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install pillow --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install pathlib --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install pymediainfo --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install sockets --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install requests --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install datetime --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install packaging --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install python-utils --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install progressbar2 --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install pyyaml --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install html5lib --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz install configparser --target %vs_path% --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose
#		"%py_exe%" pip.pyz cache purge
#		"%py_exe%" pip.pyz --no-cache-dir list
#		"%py_exe%" pip.pyz --no-cache-dir list --outdated
#		"%py_exe%" pip.pyz --no-cache-dir check
#		REM note the underscores next
#		"%py_exe%" -m pip_review --verbose
#		"%py_exe%" -m pip_review --verbose --auto --continue-on-fail
#		popd
#
# Filters:
#
#	Choose your own vapoursynth Filters, however here's the ones (actually or potentially) currently used in this script ...
#
#	Filter Dependencies with example installs into portable vapoursynth x64:
#
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" update
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install "FFTW3 Library"
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install AssRender
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install LSMASHSource
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install FFmpegSource2
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install imwri
#
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install Subtext
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install MVTools
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install Cnr2
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install TCanny
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install DCTFilter
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install Deblock
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install DFTTest
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install LimitedSharpen2 
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install Deblockpp7
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install AWarpSharp AWarpSharp2
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install LGhost
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install Histogram
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install adjust
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install mvmulti
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install muvsfunc
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install mvsfunc
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install havsfunc
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install hqdn3d
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install yadifmod
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install degrainmedian 
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install dfttest 
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install fft3dfilter
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install eedi2 nnedi3 nnedi3_resample nnedi3_rpow2 nnedi3_weights
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" install sangnom
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" upgrade-all
#
#	And then mediainfo readings for a media file using MediaInfo.dll
#		REM https://mediaarea.net/en/MediaInfo/Download/Windows
#		REM edit this for the latest version ...
#		MKDIR C:\TEMP >NUL 2>&1
#		pushd C:\TEMP
#		del "MediaInfo*.zip" >NUL 2>&1
#		del "MediaInfo*.dll" >NUL 2>&1
#		del "MediaInfo*.py" >NUL 2>&1
#		del "%vs_path%MediaInfo*.zip" >NUL 2>&1
#		del "%vs_path%MediaInfo*.dll" >NUL 2>&1
#		del "%vs_path%MediaInfo*.py" >NUL 2>&1
#		set "f=MediaInfo_DLL_22.12_Windows_x64_WithoutInstaller"
#		echo c:\software\wget\wget.exe -v -t 1 --server-response --timeout=360 -nd -np -nH --no-cookies --output-document="!f!.zip" "https://mediaarea.net/download/binary/libmediainfo0/22.12/!f!.zip" 
#		c:\software\wget\wget.exe -v -t 1 --server-response --timeout=360 -nd -np -nH --no-cookies --output-document="!f!.zip" "https://mediaarea.net/download/binary/libmediainfo0/22.12/!f!.zip" 
#		echo dir "!f!.zip"
#		dir "!f!.zip"
#		echo "C:\Program Files\WinZip\WZUNZIP.EXE" -e -o -^^ "!f!.zip" "%vs_path%" MediaInfo.dll Developers\Source\MediaInfoDLL\MediaInfoDLL.py Developers\Source\MediaInfoDLL\MediaInfoDLL3.py
#		"C:\Program Files\WinZip\WZUNZIP.EXE" -e -o -^^^^ "!f!.zip" "%vs_path%" MediaInfo.dll Developers\Source\MediaInfoDLL\MediaInfoDLL.py Developers\Source\MediaInfoDLL\MediaInfoDLL3.py
#		popd
#		copy /b /y /z "%vs_path%MediaInfo*.py" "%vs_path%vapoursynth64\scripts\"
#
#		echo COPY /Y /V "%vs_path%vapoursynth64\plugins\libfftw3*.dll" "%vs_path%"
#		COPY /Y /V "%vs_path%vapoursynth64\plugins\libfftw3*.dll" "%vs_path%"
#
#		echo copy /Y /V "%vs_path%vapoursynth64\scripts"\*.py "%vs_path%"
#		copy /Y /V "%vs_path%vapoursynth64\scripts"\*.py "%vs_path%"
#		REM
#		XCOPY /v /f /s /r /h /y /z "%vs_path%vapoursynth64\plugins\" "%vs_path%vapoursynth64\plugins\"
#		REM
#
#	And then DGDenoise as a part of DGDecodeNV in the DGDecNV package which is Donald Graft's very handy GPU-accelerated toolset 
#		per https://www.rationalqm.us/dgdecnv/dgdecnv.html and https://www.rationalqm.us/board/viewforum.php?f=8
#			which can be installed by extracting dgdecnv_???.zip into C:\SOFTWARE\Vapoursynth-x64\DGIndex\ per LoadPlugin usage below.
#
#	Finally
#
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" installed | SORT > "%vs_path%run_vsrepo_installed.txt"
#		"%py_exe%" "%vs_path%vsrepo.py" -p -t win64 -f -b "%vs_path%vapoursynth64\plugins" -s "%vs_path%vapoursynth64\scripts" available | SORT > "%vs_path%run_vsrepo_available.txt"
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
#			"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --filter-time --container y4m ".\_AI_05.vpy" - | "C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -f yuv4mpegpipe -i pipe: -f null NUL
#			"C:\SOFTWARE\Vapoursynth-x64\VSPipe.exe" --progress --filter-time --container y4m ".\_AI_05.vpy" - > NUL
#			"C:\SOFTWARE\Vapoursynth-x64\ffmpeg_OpenCL.exe" -f vapoursynth -i ".\_AI_05.vpy" -f null NUL
#	or for non-vapoursynth testing:
#			pushd "C:\SOFTWARE\Vapoursynth-x64\
#			"C:\SOFTWARE\Vapoursynth-x64\python.exe" "G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\_AI_05.vpy"
#			popd
#
import vapoursynth as vs
from vapoursynth import core
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
core.std.LoadPlugin(r'C:\SOFTWARE\Vapoursynth-x64\DGIndex\DGDecodeNV.dll') 	# note the hard-coded folder
core.avs.LoadPlugin(r'C:\SOFTWARE\Vapoursynth-x64\DGIndex\DGDecodeNV.dll') 	# note the hard-coded folder
CDLL(r'C:\SOFTWARE\Vapoursynth-x64\MediaInfo.dll')				# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372

###
global IS_DEBUG
IS_DEBUG = False
global last_file_opened_with_ffms2
global last_file_opened_with_imwri
global last_file_opened_with_LWLibavSource
global last_file_opened_with_LibavSMASHSource
###
def mediainfo_value(stream:int, track:int, param:str, path: Union[Path,str]) -> Union[int,float,str]:
	# NOTE: global MI is already setup as if a "constant" global variable
    if not stream in range(0,8):
        raise ValueError(f'ERROR: mediainfo_value: stream must be a Stream attribute: General, Video, Audio, Text, Other, Image, Menu, Max')
    if not isinstance(track, int) or track<0:
        raise ValueError(f'ERROR: mediainfo_value: track must be a positive integer')
    if not isinstance(param, str):
        raise ValueError(f'ERROR: mediainfo_value: param must be a string for particular stream, ion_Static("Info_Parameters")')
    if not isinstance(path, (Path, str)):
        raise ValueError(f'ERROR: mediainfo_value: path must be Path or str class')    
    MI.Open(str(path))
    str_value = MI.Get(stream, track, param)
    info_option =  MI.Get(stream, track, param, InfoKind=Info.Options)
    MI.Close()
    if not str_value:
        return None
    if info_option:
        #returning a proper value type, int, float or str for particular parameter
        type_ = info_option[InfoOption.TypeOfValue] #type_=info_option[3] #_type will be 'I', 'F', 'T', 'D' or 'B'
        val = {'I':int, 'F':float, 'T':str, 'D':str, 'B':str}[type_](str_value)
        return val
    else:
        raise ValueError(f'ERROR: mediainfo_value: wrong parameter: "{param}" for given stream: {stream}')

###
def boxing(clip, W, H):	# was def boxing(clip, W=TARGET_WIDTH, H=TARGET_HEIGHT):
	source_width, source_height = clip.width, clip.height
	if W/H > source_width/source_height:
		w = source_width*H/source_height
		x = int((W-w)/2)
		x = x - x%calc_ini["MODX"]
		x = max(0, min(x,W))
		clip = resize_clip(clip, W-2*x, H)
		if x: return clip.std.AddBorders(left=x, right=x, color=(16,128,128))  #RGB is out then (16,16,16)
		else: return clip
	else:
		h = source_height*W/source_width
		y = int((H-h)/2)
		y = y - y%calc_ini["MODY"]
		y = max(0, min(y,H))
		clip = resize_clip(clip, W, H-2*y)
		if y: return clip.std.AddBorders(top=y, bottom=y, color=(16,128,128))
		else: return clip

###
def resize_clip(clip,w,h):		# was resize_clip(clip,w,h, W=TARGET_WIDTH, H=TARGET_HEIGHT):
	W = calc_ini["TARGET_WIDTH"]
	H = calc_ini["TARGET_HEIGHT"]
	if w>W or h>H:	resize = getattr(clip.resize, calc_ini["DOWNSIZE_KERNEL"])	# get the resize function object ?handle? with the nominated kernel
	else:			resize = getattr(clip.resize, calc_ini["UPSIZE_KERNEL"])	# get the resize function object ?handle? with the nominated kernel
	
	if clip.format.color_family==vs.RGB:
		#rgb to YUV, perhaps only for png images, figure out what matrix out is needed ... use the HD one REC.709
		#resize.(vnode clip[, int width, int height, int format, enum matrix, enum transfer, enum primaries, enum range, 
		#			enum chromaloc, enum matrix_in, enum transfer_in, enum primaries_in, enum range_in, enum chromaloc_in, 
		#			float filter_param_a, float filter_param_b, string resample_filter_uv, float filter_param_a_uv, float filter_param_b_uv, 
		#			string dither_type="none", string cpu_type, float src_left, float src_top, float src_width, float src_height, float nominal_luminance])
		#print_DEBUG(f'resize_clip: clip.format.color_family==vs.RGB: clip.format.color_family={clip.format.color_family} vs.RGB={vs.RGB}')
		#with clip.get_frame(0) as f:
		#	print_DEBUG(f'resize_clip: incoming frame properties after RGB resize={objPrettyPrint.pformat(f.props)}')
		#print_DEBUG(f'resize_clip: TARGET frame properties: width={w}, height={h}, format={calc_ini["TARGET_PIXEL_FORMAT"]}, range={calc_ini["TARGET_COLOR_RANGE_I"]}, primaries={calc_ini["TARGET_COLOR_PRIMARIES_I"]}, transfer={calc_ini["TARGET_COLOR_TRANSFER_I"]},  matrix={calc_ini["TARGET_COLORSPACE_MATRIX_I"]}')
		#c = resize(width=w, height=h, format=calc_ini["TARGET_PIXEL_FORMAT"], matrix_s=calc_ini["TARGET_COLORSPACE_MATRIX_S"])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini["TARGET_PIXEL_FORMAT"], matrix=calc_ini["TARGET_COLORSPACE_MATRIX_I"], transfer=calc_ini["TARGET_COLOR_TRANSFER_I"], primaries=calc_ini["TARGET_COLOR_PRIMARIES_I"], range=calc_ini["TARGET_COLOR_RANGE_I"])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		#with c.get_frame(0) as f:
		#	print_DEBUG(f'resize_clip: outgoing frame properties after RGB resize={objPrettyPrint.pformat(f.props)}')
		return c
	elif clip.format.color_family==vs.YUV:
		#resize.(vnode clip[, int width, int height, int format, enum matrix, enum transfer, enum primaries, enum range, 
		#			enum chromaloc, enum matrix_in, enum transfer_in, enum primaries_in, enum range_in, enum chromaloc_in, 
		#			float filter_param_a, float filter_param_b, string resample_filter_uv, float filter_param_a_uv, float filter_param_b_uv, 
		#			string dither_type="none", string cpu_type, float src_left, float src_top, float src_width, float src_height, float nominal_luminance])
		
		#print_DEBUG(f'resize_clip: clip.format.color_family==vs.YUV: clip.format.color_family={clip.format.color_family} vs.YUV={vs.YUV}')
		#with clip.get_frame(0) as f:
		#	print_DEBUG(f'resize_clip: incoming frame properties after RGB resize={objPrettyPrint.pformat(f.props)}')
		#print_DEBUG(f'resize_clip: TARGET frame properties: width={w}, height={h}, format={calc_ini["TARGET_PIXEL_FORMAT"]}, range={calc_ini["TARGET_COLOR_RANGE_I"]}, primaries={calc_ini["TARGET_COLOR_PRIMARIES_I"]}, transfer={calc_ini["TARGET_COLOR_TRANSFER_I"]},  matrix={calc_ini["TARGET_COLORSPACE_MATRIX_I"]}')
		#c = resize(width=w, height=h, format=calc_ini["TARGET_PIXEL_FORMAT"], matrix_s=calc_ini["TARGET_COLORSPACE_MATRIX_S"])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini["TARGET_PIXEL_FORMAT"], matrix=calc_ini["TARGET_COLORSPACE_MATRIX_I"], transfer=calc_ini["TARGET_COLOR_TRANSFER_I"], primaries=calc_ini["TARGET_COLOR_PRIMARIES_I"], range=calc_ini["TARGET_COLOR_RANGE_I"])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		# AH !!! the above line with matrix_s='709' can cause this error:
		# If you get an error like:
		# 		Resize error 3074: no path between colorspaces (2/2/2 => 1/1/1). May need to specify additional colorspace parameters.
		# It usually means the matrix/transfer/primaries are unknown 
		# *** and you have to specify the input colorspace parameters yourself. *** Note: 2 means “unspecified” according to the ITU-T recommendation.
		#c = resize(width=w, height=h, format=calc_ini["TARGET_PIXEL_FORMAT"])
		#with c.get_frame(0) as f:
		#	print_DEBUG(f'resize_clip: outgoing frame properties after YUV resize={objPrettyPrint.pformat(f.props)}')
		return c
	else:
		#resize.(vnode clip[, int width, int height, int format, enum matrix, enum transfer, enum primaries, enum range, 
		#			enum chromaloc, enum matrix_in, enum transfer_in, enum primaries_in, enum range_in, enum chromaloc_in, 
		#			float filter_param_a, float filter_param_b, string resample_filter_uv, float filter_param_a_uv, float filter_param_b_uv, 
		#			string dither_type="none", string cpu_type, float src_left, float src_top, float src_width, float src_height, float nominal_luminance])
		#print_DEBUG(f'resize_clip: non-vs.RGB,non-vs.YUV clip.format.color_family!=vs.RGB: clip.format.color_family={clip.format.color_family} vs.RGB={vs.RGB} vs.YUV={vs.YUV}')
		#with clip.get_frame(0) as f:
		#	print_DEBUG(f'resize_clip: incoming frame properties after RGB resize={objPrettyPrint.pformat(f.props)}')
		#print_DEBUG(f'resize_clip: TARGET frame properties: width={w}, height={h}, format={calc_ini["TARGET_PIXEL_FORMAT"]}, range={calc_ini["TARGET_COLOR_RANGE_I"]}, primaries={calc_ini["TARGET_COLOR_PRIMARIES_I"]}, transfer={calc_ini["TARGET_COLOR_TRANSFER_I"]},  matrix={calc_ini["TARGET_COLORSPACE_MATRIX_I"]}')
		#c = resize(width=w, height=h, format=calc_ini["TARGET_PIXEL_FORMAT"], matrix_s=calc_ini["TARGET_COLORSPACE_MATRIX_S"])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini["TARGET_PIXEL_FORMAT"], matrix=calc_ini["TARGET_COLORSPACE_MATRIX_I"], transfer=calc_ini["TARGET_COLOR_TRANSFER_I"], primaries=calc_ini["TARGET_COLOR_PRIMARIES_I"], range=calc_ini["TARGET_COLOR_RANGE_I"])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		# AH !!! the avove line with matrix_s='709' can cause this error:
		# If you get an error like:
		# 		Resize error 3074: no path between colorspaces (2/2/2 => 1/1/1). May need to specify additional colorspace parameters.
		# It usually means the matrix/transfer/primaries are unknown 
		# *** and you have to specify the input colorspace parameters yourself. *** Note: 2 means “unspecified” according to the ITU-T recommendation.
		#c = resize(width=w, height=h, format=calc_ini["TARGET_PIXEL_FORMAT"])
		#with c.get_frame(0) as f:
		#	print_DEBUG(f'resize_clip: outgoing frame properties after non-vs.RGB,non-vs.YUV resize={objPrettyPrint.pformat(f.props)}')
		return c

###
def get_clip_specs(clip=None, path=None, ext=None):
	global last_file_opened_with_ffms2
	global last_file_opened_with_imwri
	global last_file_opened_with_LWLibavSource
	global last_file_opened_with_LibavSMASHSource
	#
	if clip is None:
		raise ValueError(f'ERROR: get_clip_specs: "clip" not passed as an argument to get_clip_specs')
	if path is None:
		raise ValueError(f'ERROR: get_clip_specs: "path" not passed as an argument to get_clip_specs')
	if ext is None:
		raise ValueError(f'ERROR: get_clip_specs: "ext" not passed as an argument to get_clip_specs')
	#
	# https://www.vapoursynth.com/doc/api/vapoursynth.h.html#enum-vspresetformat
	#print_DEBUG(f'----------------------------------------------------------------------')
	#for v in vs.PresetFormat:	# eg vs.YUV420P8
	#	print_DEBUG(f'get_clip_specs: vs.PresetFormat ENUM: {str(v)} = {v.value}')
	#for v in vs.MatrixCoefficients:
	#	print_DEBUG(f'get_clip_specs: vs.MatrixCoefficients ENUM: {str(v)} = {v.value}')
	#for v in vs.TransferCharacteristics:
	#	print_DEBUG(f'get_clip_specs: vs.TransferCharacteristics ENUM: {str(v)} = {v.value}')
	#for v in vs.ColorPrimaries:
	#	print_DEBUG(f'get_clip_specs: vs.ColorPrimaries ENUM: {str(v)} = {v.value}')
	#for v in vs.ColorRange:
	#	print_DEBUG(f'get_clip_specs: vs.ColorRange ENUM: {str(v)} = {v.value}')
	#for v in vs.ColorFamily:
	#	print_DEBUG(f'get_clip_specs: vs.ColorFamily ENUM: {str(v)} = {v.value}')
	#for v in vs.ChromaLocation:
	#	print_DEBUG(f'get_clip_specs: vs.ChromaLocation ENUM: {str(v)} = {v.value}')
	#for v in vs.FieldBased:
	#	print_DEBUG(f'get_clip_specs: vs.FieldBased ENUM: {str(v)} = {v.value}')
	#print_DEBUG(f'NOTE can use both: resize_clip: vs.ColorRange.RANGE_FULL.value = {vs.ColorRange.RANGE_FULL.value}')
	#print_DEBUG(f'NOTE can use both: resize_clip: vs.RANGE_FULL.value = {vs.RANGE_FULL.value}')
	#print_DEBUG(f'NOTE can use both: resize_clip: vs.ColorRange.RANGE_LIMITED.value = {vs.ColorRange.RANGE_LIMITED.value}')
	#print_DEBUG(f'NOTE can use both: resize_clip: vs.RANGE_LIMITED.value = {vs.RANGE_LIMITED.value}')
	#print_DEBUG(f'----------------------------------------------------------------------')
	#print_DEBUG(f'get_clip_specs: clip=\n{clip}')
	## https://www.vapoursynth.com/doc/pythonreference.html
	#print_DEBUG(f'get_clip_specs: clip.format=\n{clip.format}')
	#print_DEBUG(f'get_clip_specs: clip.width={clip.width}')
	#print_DEBUG(f'get_clip_specs: clip.height={clip.height}')
	#print_DEBUG(f'get_clip_specs: clip.num_frames={clip.num_frames}')
	#print_DEBUG(f'get_clip_specs: clip.fps={clip.fps}')
	#print_DEBUG(f'get_clip_specs: clip.format.name={clip.format.name} clip.format.id={clip.format.id} (see enum vs.PresetFormat')
	#print_DEBUG(f'get_clip_specs: clip.format.color_family={clip.format.color_family}')
	#print_DEBUG(f'get_clip_specs: clip.format.sample_type={clip.format.sample_type}')	# If the format is integer or floating point based.
	#print_DEBUG(f'get_clip_specs: clip.format.bits_per_sample={clip.format.bits_per_sample}')
	#print_DEBUG(f'get_clip_specs: clip.format.bytes_per_sample={clip.format.bytes_per_sample}')
	#print_DEBUG(f'get_clip_specs: clip.format.num_planes={clip.format.num_planes}') # per https://www.vapoursynth.com/doc/pythonreference.html
	#print_DEBUG(f'get_clip_specs: clip.format.subsampling_w={clip.format.subsampling_w}')
	#print_DEBUG(f'get_clip_specs: clip.format.subsampling_h={clip.format.subsampling_h}')
	#with clip.get_frame(0) as f:
	#	print_DEBUG(f'get_clip_specs: incoming frame properties =\n{f.props}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_Matrix"] = {f.props["_Matrix"]}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_Transfer"] = {f.props["_Transfer"]}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_Primaries"] = {f.props["_Primaries"]}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_ColorRange"] = {f.props["_ColorRange"]}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_ChromaLocation"] = {f.props["_ChromaLocation"]}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_DurationDen"] = {f.props["_DurationDen"]}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_DurationNum"] = {f.props["_DurationNum"]}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_FieldBased"] = {f.props["_FieldBased"]}')
	#	print_DEBUG(f'get_clip_specs: frame properties f.props["_PictType"] = {f.props["_PictType"]}') # a byte character eg 'I'
	#
	# Create a local dict of Clip and Frame properties, ready for later validation/resetting if need be of _Matrix/_Transfer/_Primaries/_ColorRange
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
	with clip.get_frame(0) as f:
		clip_specs["_Matrix"] = f.props["_Matrix"] if "_Matrix" in f.props else None
		clip_specs["_Transfer"] = f.props["_Transfer"] if "_Transfer" in f.props else None
		clip_specs["_Primaries"] = f.props["_Primaries"] if "_Primaries" in f.props else None
		clip_specs["_ColorRange"] = f.props["_ColorRange"] if "_ColorRange" in f.props else None
		clip_specs["_ChromaLocation"] = f.props["_ChromaLocation"] if  "_ChromaLocation" in f.props else None
		clip_specs["_DurationDen"] = f.props["_DurationDen"] if "_DurationDen" in f.props else None
		clip_specs["_DurationNum"] = f.props["_DurationNum"] if "_DurationNum" in f.props else None
		clip_specs["_FieldBased"] = f.props["_FieldBased"] if "_FieldBased" in f.props else None
		clip_specs["_PictType"] = f.props["_PictType"] if "_PictType" in f.props else None
	# check for picture/video rotation specified perhaps in EXIF but not auto-processed here by the file openers
	if ext in calc_ini["VID_EEK_EXTENSIONS"]:
		rotation_value = auto_rotation_value_MediaInfo(clip, path)	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678326
	else: # source is not a video type, i.e. an image
		rotation_value = clip = auto_rotation_value_PIL(clip, path)	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678326
	clip_specs["auto_rotation_degrees"] = rotation_value
	clip_specs["opened_with_ffms2"] = last_file_opened_with_ffms2
	clip_specs["opened_with_imwri"] = last_file_opened_with_imwri
	clip_specs["opened_with_LWLibavSource"] = last_file_opened_with_LWLibavSource
	clip_specs["opened_with_LibavSMASHSource"] = last_file_opened_with_LibavSMASHSource
	
	# **********
	# if not already specified, guess a new _Matrix
	# explainer https://docs.rs/av-data/0.4.1/av_data/pixel/index.html https://docs.rs/av-data/0.4.1/av_data/pixel/enum.MatrixCoefficients.html
	clip_specs["guessed_Matrix"] = False
	clip_specs["proposed_Matrix"] = clip_specs["_Matrix"]
	if  clip_specs["_Matrix"] == vs.MatrixCoefficients.MATRIX_UNSPECIFIED:	# _Matrix is usually defined and the rest may not be. (ffms2 usually yields MATRIX_BT470_BG)
		#print_DEBUG(f'get_clip_specs: MatrixCoefficients.MATRIX_UNSPECIFIED: incoming clip_specs=\n{objPrettyPrint.pformat(clip_specs)}')
		clip_specs["guessed_Matrix"] = True
		if ext in calc_ini["PIC_EXTENSIONS"]:	#PIC # assume opened by ffms2 (ffms2 usually yields MATRIX_BT470_BG for images)
			print_DEBUG(f'get_clip_specs: PIC: MatrixCoefficients.MATRIX_UNSPECIFIED in PIC, choosing a default')
			if last_file_opened_with_ffms2:
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT470_BG
				#print_DEBUG(f'get_clip_specs: PIC: MatrixCoefficients.MATRIX_UNSPECIFIED in PIC, opened by ffms2, replacement _Matrix={clip_specs["proposed_Matrix"]}')
			else:
				print_DEBUG(f'get_clip_specs: PIC: MatrixCoefficients.MATRIX_UNSPECIFIED in PIC, opened by non-ffms2')
				#### This is a poor guess, last resort, if there is no other way to deduce matrix.
				# NOTE: ffms2 usually yields MATRIX_BT470_BG for IMAGES regardless of what width/height they may be.
				if  clip_specs["width"] <= 720 and clip_specs["height"] <= 480:				# Likely NTSC SD
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_ST170_M
				elif clip_specs["width"]  <= 720 and clip_specs["height"] <= 576:				# Likely PAL SD
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT470_BG
				elif clip_specs["width"]  <= 1280 and clip_specs["height"] <= 720:				# Likely PAL HD
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT709
				elif clip_specs["width"]  <= 1920 and clip_specs["height"] <= 1088:				# Likely PAL HD
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT709
				elif clip_specs["width"]  <= 3840 and clip_specs["height"] <= 2160:				# Likely UHD
					# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
					# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
					# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
					# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
					# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
					# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
					# because the benefits are considered modest and entail some additional complexity
					#clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_CL					#     Constant Luminance
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_NCL				# Non-Constant Luminance
				elif clip_specs["width"]  <= 7680 and clip_specs["height"] <= 4320:				# Likely 8K
					# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
					# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
					# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
					# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
					# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
					# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
					# because the benefits are considered modest and entail some additional complexity
					#clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_CL					#     Constant Luminance
					clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_NCL 				# Non-Constant Luminance
				else:
					raise ValueError(f'ERROR: get_clip_specs: PIC: unable to guess default _Matrix in PIC to replace MatrixCoefficients.MATRIX_UNSPECIFIED')
				#print_DEBUG(f'get_clip_specs: PIC: MatrixCoefficients.MATRIX_UNSPECIFIED ({vs.MatrixCoefficients.MATRIX_UNSPECIFIED}) in PIC, opened by non-ffms2, replacement _Matrix={clip_specs["proposed_Matrix"]}')
		elif ext in calc_ini["VID_EEK_EXTENSIONS"]:	#VID 
			print_DEBUG(f'get_clip_specs: VID: MatrixCoefficients.MATRIX_UNSPECIFIED in VID')
			#### This is a poor guess, last resort, if there is no other way to deduce matrix.
			# NOTE: ffms2 usually yields MATRIX_BT470_BG for IMAGES regardless of what width/height they may be.
			if  clip_specs["width"] <= 720 and clip_specs["height"] <= 480:	# Likely NTSC SD
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_ST170_M
			elif clip_specs["width"]  <= 720 and clip_specs["height"] <= 576:				# Likely PAL SD
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT470_BG
			elif clip_specs["width"]  <= 1280 and clip_specs["height"] <= 720:				# Likely PAL HD
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT709						# HD
			elif clip_specs["width"]  <= 1920 and clip_specs["height"] <= 1088:				# Likely PAL HD
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT709						# HD
			elif clip_specs["width"]  <= 3840 and clip_specs["height"] <= 2160:				# Likely UHD
				# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
				# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
				# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
				# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
				# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
				# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
				# because the benefits are considered modest and entail some additional complexity
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_CL					#     Constant Luminance
				#clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_NCL				# Non-Constant Luminance
			elif clip_specs["width"]  <= 7680 and clip_specs["height"] <= 4320:				# Likely 8K
				# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
				# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
				# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
				# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
				# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
				# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
				# because the benefits are considered modest and entail some additional complexity
				clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_CL					#     Constant Luminance
				#clip_specs["proposed_Matrix"] = vs.MatrixCoefficients.MATRIX_BT2020_NCL 				# Non-Constant Luminance
			else:
				raise ValueError(f'ERROR: get_clip_specs: VID: unable to guess default _Matrix in PIC to replace MatrixCoefficients.MATRIX_UNSPECIFIED')
			#print_DEBUG(f'get_clip_specs: VID: MatrixCoefficients.MATRIX_UNSPECIFIED ({vs.MatrixCoefficients.MATRIX_UNSPECIFIED}) in VID, replacement _Matrix={clip_specs["proposed_Matrix"]}')
		else:
			raise ValueError(f'ERROR: get_clip_specs: VID: ext "{ext}" not recognised in VID to replace MatrixCoefficients.MATRIX_UNSPECIFIED')
	
	# **********
	# if not already specified, guess new _Primaries
	# explainer https://docs.rs/av-data/0.4.1/av_data/pixel/index.html https://docs.rs/av-data/0.4.1/av_data/pixel/enum.ColorPrimaries.html
	clip_specs["guessed_Primaries"] = False
	clip_specs["proposed_Primaries"] = clip_specs["_Primaries"]
	if  clip_specs["_Primaries"] == vs.ColorPrimaries.PRIMARIES_UNSPECIFIED:
		#print_DEBUG(f'get_clip_specs: ColorPrimaries.PRIMARIES_UNSPECIFIED: incoming clip_specs=\n{objPrettyPrint.pformat(clip_specs)}')
		clip_specs["guessed_Primaries"] = True
		if clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_ST170_M:
			clip_specs["proposed_Primaries"] = vs.ColorPrimaries.PRIMARIES_ST170_M
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT470_BG:
			clip_specs["proposed_Primaries"] = vs.ColorPrimaries.PRIMARIES_BT470_BG
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT709:
			clip_specs["proposed_Primaries"] = vs.ColorPrimaries.PRIMARIES_BT709
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT2020_CL or clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT2020_NCL:
			clip_specs["proposed_Primaries"] = vs.ColorPrimaries.PRIMARIES_BT2020
		else:
			raise ValueError(f'ERROR: get_clip_specs: unable to guess default _Primaries to replace ColorPrimaries.PRIMARIES_UNSPECIFIED')
		#print_DEBUG(f'get_clip_specs: ColorPrimaries.PRIMARIES_UNSPECIFIED ({vs.ColorPrimaries.PRIMARIES_UNSPECIFIED}), replacement _Primaries={clip_specs["proposed_Primaries"]}')
		
	# **********
	# if not already specified, guess new _Transfer
	# explainer https://docs.rs/av-data/0.4.1/av_data/pixel/index.html https://docs.rs/av-data/0.4.1/av_data/pixel/enum.TransferCharacteristic.html
	clip_specs["guessed_Transfer"] = False
	clip_specs["proposed_Transfer"] = clip_specs["_Transfer"]
	if  clip_specs["_Transfer"] == vs.TransferCharacteristics.TRANSFER_UNSPECIFIED:
		#print_DEBUG(f'get_clip_specs: ColorPrimaries.PRIMARIES_UNSPECIFIED: incoming clip_specs=\n{objPrettyPrint.pformat(clip_specs)}')
		clip_specs["guessed_Transfer"] = True
		if clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_ST170_M:
			clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT601
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT470_BG:
			clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT470_BG
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT709:
			clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT709
		elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT2020_CL or clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT2020_NCL:
			if clip_specs["bits_per_sample"] == 10:
				# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
				# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
				# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
				# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
				# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
				# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
				# because the benefits are considered modest and entail some additional complexity
				clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT2020_10
			elif clip_specs["bits_per_sample"] == 12:
				# https://www.benq.com/en-us/knowledge-center/knowledge/bt2020.html
				# HDR is defined by contrast/brightness enhancements which are not explicitly outlined in BT.2020’s package of specifications
				# To address this gap, the ITU in 2016 released its newest recommendations, BT.2100, to include HDR in its specifications, essentially making BT.2100 just BT.2020 plus HDR
				# https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2390-1-2016-PDF-E.pdf
				# The constant luminance (CL) method specified in Recommendation ITU-R BT.2020 helps reduce Error propagation from chroma to luma channels 
				# BUT THIS SOLUTION IS NOT BEING WIDELY ADOPTED 
				# because the benefits are considered modest and entail some additional complexity
				clip_specs["proposed_Transfer"] = vs.TransferCharacteristics.TRANSFER_BT2020_12
			else:
				raise ValueError(f'ERROR: get_clip_specs: unable to guess {clip_specs["bits_per_sample"]}-bit default _Transfer to replace TransferCharacteristics.TRANSFER_UNSPECIFIED')
		else:
			raise ValueError(f'ERROR: get_clip_specs: unable to guess default _Transfer to replace TransferCharacteristics.TRANSFER_UNSPECIFIED')
		#print_DEBUG(f'get_clip_specs: TransferCharacteristics.TRANSFER_UNSPECIFIED ({vs.TransferCharacteristics.TRANSFER_UNSPECIFIED}), replacement _Transfer={clip_specs["proposed_Transfer"]}')
	
	# **********
	# if not already specified, guess new _ColorRange
	# explainer https://docs.rs/av-data/0.4.1/av_data/pixel/index.html https://docs.rs/av-data/0.4.1/av_data/pixel/enum.YUVRange.html
	clip_specs["guessed_ColorRange"] = False
	clip_specs["proposed_ColorRange"] = clip_specs["_ColorRange"]
	#clip_specs["proposed_ColorRange"] = vs.ColorRange.RANGE_FULL

	# **********
	# guess at a possible incoming colour source
	if   clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_BT470_BG:
		clip_specs["possible_colour_source"] = "PAL".upper()
	elif clip_specs["proposed_Matrix"] == vs.MatrixCoefficients.MATRIX_ST170_M:
		clip_specs["possible_colour_source"] = "NTSC".upper()
	elif clip_specs["proposed_Transfer"] == vs.TransferCharacteristics.TRANSFER_BT470_BG:
		clip_specs["possible_colour_source"] = "PAL".upper()
	elif clip_specs["proposed_Transfer"] in [vs.TransferCharacteristics.TRANSFER_BT470_M, vs.TransferCharacteristics.TRANSFER_ST240_M]:
		clip_specs["possible_colour_source"] = "NTSC".upper()
	elif clip_specs["proposed_Primaries"] == vs.ColorPrimaries.PRIMARIES_BT470_BG:
		clip_specs["possible_colour_source"] = "PAL".upper()
	elif clip_specs["proposed_Primaries"] in [vs.ColorPrimaries.PRIMARIES_ST170_M, vs.ColorPrimaries.PRIMARIES_BT470_M, vs.ColorPrimaries.PRIMARIES_ST170_M, vs.ColorPrimaries.PRIMARIES_ST240_M]:
		clip_specs["possible_colour_source"] = "PAL".upper()
	# allow for incoming errors in fps, use ranges instead of values
	elif (clip_specs["fps"] >=23.5 and clip_specs["fps"] <= 24.49) or (clip_specs["fps"] >=29 and clip_specs["fps"] <= 31):
		clip_specs["possible_colour_source"] = "NTSC".upper()		# possibly NTSC although 30fps could still be PAL in phone cameras :(
	elif (clip_specs["fps"] >=24.5 and clip_specs["fps"] <= 25.5):
		clip_specs["possible_colour_source"] = "PAL".upper()
	else:	# deault to PAL since, well, I'm in a PAL country
		clip_specs["possible_colour_source"] = "PAL".upper()

	#print_DEBUG(f'get_clip_specs: clip_specs=\n{objPrettyPrint.pformat(clip_specs)}')
	return clip_specs

###
def get_clip(path):
	global last_file_opened_with_ffms2
	global last_file_opened_with_imwri
	global last_file_opened_with_LWLibavSource
	global last_file_opened_with_LibavSMASHSource
	#
	last_file_opened_with_ffms2 = False
	last_file_opened_with_imwri = False
	last_file_opened_with_LWLibavSource = False
	last_file_opened_with_LibavSMASHSource = False
	#
	if path.suffix.lower()   in calc_ini["EEK_EXTENSIONS"]:
		#print_DEBUG(f'get_clip: lsmas Video: {path.name}')
		clip = core.lsmas.LWLibavSource(str(path))
		last_file_opened_with_LWLibavSource = True
		#print_DEBUG(f'get_clip: lsmas Video info:\n{clip}')
	elif path.suffix.lower() in calc_ini["VID_EXTENSIONS"]:
		#print_DEBUG(f'get_clip: ffms2 Video: {path.name}')
		clip = core.ffms2.Source(str(path))	#ffms2 leaves *.ffindex files everywhere in folders.
		last_file_opened_with_ffms2 = True
		#clip = core.lsmas.LibavSMASHSource(str(path))
		#last_file_opened_with_LibavSMASHSource = True
		#print_DEBUG(f'get_clip: ffms2 Video info:\n{clip}')
	elif path.suffix.lower() in calc_ini["PIC_EXTENSIONS"]:
		#print_DEBUG(f'get_clip: ffms2 PIC: {path.name}')
		clip = core.ffms2.Source(str(path))
		last_file_opened_with_ffms2 = True
		#print_DEBUG(f'get_clip: ffms2 PIC info:\n{clip}')
		# NOTE: imwri returns no frame properties ! eg "_Matrix" ! and thus IS NO GOOD AT ALL FOR US
		#clip = core.imwri.Read(str(path)) # ImageMagick Writer-Reader, if installed into vapoursynth folder
		#last_file_opened_with_imwri = True
		#print_DEBUG(f'get_clip: imwri Video info:\n{clip}')
	else: # UNKNOWN TYPE
		#print_DEBUG(f'get_clip: ffms2 UNKNOWN TYPE: {path.name}')
		clip = core.ffms2.Source(str(path))	# if file extension not recognised, use this reader
		last_file_opened_with_ffms2 = True
		#print_DEBUG(f'get_clip: ffms2 Video info:\n{clip}')
	#
	clip_specs = get_clip_specs(clip, path, ext=path.suffix.lower())
	#
	#++++++++++++++++++++
	if clip_specs["guessed_Matrix"]:
		#print_DEBUG(f'get_clip: SetFrameProps _Matrix from existing "{clip_specs["_Matrix"]}" to guessed "{clip_specs["proposed_Matrix"]}"')
		clip = core.std.SetFrameProps(clip, _Matrix=clip_specs["proposed_Matrix"])
	if clip_specs["guessed_Primaries"]:
		#print_DEBUG(f'get_clip: SetFrameProps _Primaries from existing "{clip_specs["_Primaries"]}" to guessed "{clip_specs["proposed_Primaries"]}"')
		clip = core.std.SetFrameProps(clip, _Primaries=clip_specs["proposed_Primaries"])
	if clip_specs["guessed_Transfer"]:
		#print_DEBUG(f'get_clip: SetFrameProps _Transfer from existing "{clip_specs["_Transfer"]}" to guessed "{clip_specs["proposed_Transfer"]}"')
		clip = core.std.SetFrameProps(clip, _Transfer=clip_specs["proposed_Transfer"])
	if clip_specs["guessed_ColorRange"]:
		#print_DEBUG(f'get_clip: SetFrameProps _ColorRange from existing "{clip_specs["_ColorRange"]}" to guessed "{clip_specs["proposed_ColorRange"]}"')
		clip = core.std.SetFrameProps(clip, _Transfer=clip_specs["proposed_Transfer"])
	#
	#++++++++++++++++++++
	# Apply an auto-rotate if specified in the source file (perhaps in an image, some do, if at all)
	if clip_specs["auto_rotation_degrees"] == 0:
		#print_DEBUG(f'get_clip: zero auto-rotation of clip {path}')
		pass
	elif clip_specs["auto_rotation_degrees"] == 90:
		#print_DEBUG(f'get_clip: auto-Rotating by 90 degrees {path}')
		clip = clip.std.Transpose().std.FlipVertical()
	elif clip_specs["auto_rotation_degrees"] == 180:
		#print_DEBUG(f'get_clip: auto-Rotating by 180 degrees {path}')
		clip = clip.std.Turn180()
	elif clip_specs["auto_rotation_degrees"] == 270:
		#print_DEBUG(f'get_clip: auto-Rotating by 270 degrees {path}')
		clip = clip.std.Transpose().std.FlipHorizontal()
	else:
		raise ValueError('ERROR: get_clip: auto_rotation_degrees "{clip_specs["auto_rotation_degrees"]}" unable to be processed for "{path}" : only 0,90,180,270 are valid')
	#++++++++++++++++++++

	# do video-specific or picture-specific changes
	if path.suffix.lower()   in calc_ini["VID_EEK_EXTENSIONS"]:	#if any sort of video, probably an old hand-held camera or phone, sometimes variable fps ...
		#print_DEBUG(f'get_clip: opened Video: {path.name}')
		#print_DEBUG(f'get_clip: opened Video: {path.name}\nVideo info:\n{clip}')
		#clip = core.text.Text(clip, path.name, alignment=3, scale=1)
		#clip = core.text.FrameNum(clip, alignment=5, scale=1)
		#clip = core.text.ClipInfo(clip, alignment=8, scale=1)
		#clip = core.text.FrameProps(clip, alignment=2, scale=1)
		source_fpsnum = clip.fps.numerator		# eg 25	# numerator   is 0 when the clip has a variable framerate.
		source_fpsden = clip.fps.denominator	# eg 1	# denominator is 1 when the clip has a variable framerate.
		source_fps = round(source_fpsnum / source_fpsden,3)
		source_duration_frames = clip.num_frames
		source_duration_secs = round((source_duration_frames / source_fps),3)
		source_width, source_height = clip.width, clip.height
		#print_DEBUG(f'get_clip: {source_width}x{source_height}\nsource_fpsnum:{source_fpsnum} source_fpsden:{source_fpsden}\nsource_fps:{source_fps}\nsource_duration_frames:{source_duration_frames}\nsource_duration_secs:{source_duration_secs}')
		# change framerate ? too hard for a small simple video sample, just "assume" target fps and ignore consequences of speed-up or slow-down or VFR
		clip = clip.std.AssumeFPS(fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
		# if duration greater than out review maximum, clip it
		if source_duration_frames>(calc_ini["MAX_DURATION_FRAMES"]-1):
			clip = core.std.Trim(clip, first=0, last=(calc_ini["MAX_DURATION_FRAMES"]-1))
		# denoise ANY "small" dimension video clips, older videos likely to be noisy
		if source_width<calc_ini["TARGET_WIDTH"] or source_height<calc_ini["TARGET_HEIGHT"]:	 
			#print_DEBUG(f'applying DGDenoise to small {source_width}x{source_height} video {path.name}')
			# clip must be YUV420P16 for DGDenoise etc
			clip = clip.resize.Point(format=calc_ini["DG_PIXEL_FORMAT"])		# convert to DG_PIXEL_FORMAT via resizer which does no resizing
			#clip = core.avs.DGDenoise(clip, strength=0.06, cstrength=0.06)
			clip = core.avs.DGDenoise(clip, strength=0.15, cstrength=0.15)
			clip = clip.resize.Point(format=calc_ini["TARGET_PIXEL_FORMAT"])	# convert to calc_ini["TARGET_PIXEL_FORMAT"] via resizer which does no resizing
	else: # source is not a video type, i.e. it must be an image (picture)
		# extend duration of a clip of an image
		clip = clip[0]*calc_ini["MIN_DURATION_FRAMES"] if len(clip)<calc_ini["MIN_DURATION_FRAMES"] else clip # make clip at least calc_ini["MIN_DURATION_FRAMES"] frames long if less than MIN_DURATION_FRAMES frames
	
	# either add borders to maintain aspect ratio (boxing), or just stretch to fit (yuk)
	if calc_ini["BOX"]:
		clip = boxing(clip, calc_ini["TARGET_WIDTH"], calc_ini["TARGET_HEIGHT"])
	else:
		clip = resize_clip(clip, calc_ini["TARGET_WIDTH"], calc_ini["TARGET_HEIGHT"])

	# Add a subtitle being the trailing 3 parts of the path
	if calc_ini["ADD_SUBTITLE"]:	# Add a subtitle being the trailing 3 parts of the path
		pwp = PureWindowsPath(path)
		n = len(pwp.parts)
		#text_subpath_for_subtitles = "/" + pwp.parts[n-3] + "/" + pwp.parts[n-2] + "/" +  pwp.parts[n-1]
		text_subpath_for_subtitles = "/" + pwp.parts[n-2] + "/" +  pwp.parts[n-1]
		# To tinker with .ass subs, see https://snapcraft.io/install/aegisub-procles/ubuntu
		# Also note from an aegisub created .ass file
		#	Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
		#	Style: h3333,Arial,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0.9,0.5,3,2,2,2,1
		# whereas default .assrender.Subtitle style="sans-serif,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,7,10,10,10,1"
		# https://github.com/AmusementClub/assrender
		# assrender.Subtitle(clip clip, string[] text, [string style="sans-serif,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,7,10,10,10,1", int[] start, int[] end, string vfr, int hinting=0, float scale=1.0, float line_spacing=1.0, float dar, float sar, bool set_default_storage_size=True, int top=0, int bottom=0, int left=0, int right=0, string charset, int debuglevel, string fontdir="", string srt_font="sans-serif", string colorspace])
		#	colorspace Rec2020, BT.2020 Rec709, BT.709, Rec601, BT.601, PC.709, PC.601, TV.fcc, PC.fcc, TV.240m, PC.240m
		#	When no hint found in ASS script and colorspace parameter is empty then the default is BT.601
		clip = core.assrender.Subtitle(clip, text_subpath_for_subtitles, style="sans-serif,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0.9,0.5,3,2,2,2,1", colorspace=calc_ini["TARGET_COLORSPACE"])
	return clip

###
def get_path(path_generator):
	#get next path of desired extensions from generator, ignoring extensions we have not specified
	while 1:	# loop until we do a "return", hitting past the end of the iterator returns None
		try:
			path = next(path_generator)
			#print_DEBUG(f'get_path: get success, path.name=' + path.name)
		except StopIteration:
			return None
		if path.suffix.lower() in calc_ini["EXTENSIONS"]:	# only return files which are in known extensions
			#print_DEBUG(f'get_path: in calc_ini["EXTENSIONS"] success, path.name=' + path.name)
			return path
		  
###
def crossfade(a, b, duration):
	#gets crosfade part from end of clip a and start of clip b
	def fade_image(n, a, b):
		return core.std.Merge(a, b, weight=n/duration)
	if a.format.id != b.format.id or a.height != b.height or a.width != b.width:
		raise ValueError('ERROR: crossfade: Both clips must have the same dimensions and format.')
	return core.std.FrameEval(a[-duration:], partial(fade_image, a=a[-duration:], b=b[:duration]))

###
def print_exif_data(exif_data):
	for tag_id in exif_data:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_data.get(tag_id)
		print_DEBUG(f'{tag:25}: {content}')
	print_DEBUG(f'exif_data:\n{objPrettyPrint.pformat(exif_data)}\n')
		
###
def print_exif_data2(exif_data):
	for tag_id in exif_data:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_data.get(tag_id)
		if isinstance(content, bytes):
			content = content.decode()
		print_DEBUG(f'{tag:25}: {content}')
	print_DEBUG(f'exif_data2:\n{objPrettyPrint.pformat(exif_data)}\n')

###
def auto_rotation_value_PIL(clip, path):
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
		#print_DEBUG(f'auto_rotation_value_PIL: except UnidentifiedImageError immediate return now')
		return rotation_degrees
	except PermissionError:
		#print_DEBUG(f'auto_rotation_value_PIL: except PermissionError Permission denied to load: {path} immediate return now')
		return rotation_degrees
	except Exception as e:
		#print_DEBUG(f'auto_rotation_value_PIL: except Exception {e} immediate return now')
		return rotation_degrees
	#print_DEBUG(f'auto_rotation_value_PIL: try on Image.open succeeded')
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
		#print_DEBUG(f'auto_rotation_value_PIL: except AttributeError during for key in ExifTags.TAGS.keys(), immediate return now')
		return rotation_degrees
	else:
		if   value == 0:
			rotation_degrees = 0
			##print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating by 0 degrees {path}')
		elif   value == 3:
			rotation_degrees = 180
			##print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating by 180 degrees {path}')
		elif value == 8:
			rotation_degrees = 90
			##print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating by  90 degrees {path}')
		elif value == 6:
			rotation_degrees = 270
			##print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating by 270 degrees {path}')
	image.close()	
	#print_DEBUG(f'auto_rotation_value_PIL: PIL says auto-Rotating by {rotation_degrees} degrees {path}')
	return rotation_degrees

###
def auto_rotation_value_MediaInfo(clip, path):
	rotation_degrees = 0
	param = 'Rotation'
	value = mediainfo_value(Stream.Video, 0, param, path)
	if param == 'Rotation':
		if value is None:
			rotation_degrees = 0
		else:
			rotation_degrees = int(float(value)) # for some reason Rotation value type mediainfo carries as a string,  like: '180.00'
	#print_DEBUG(f'auto_rotation_value_MediaInfo: MediaInfo says auto-Rotating by {rotation_degrees} degrees {path}')
	return rotation_degrees

###
def perform_rotation_PIL(clip, path, save_rotated_image=False):
	# from PIL import Image, ExifTags, UnidentifiedImageError   # pip install Pillow, or equivalent
	# PIL Pillow module loads an image, checks if EXIF data, checks for 'Orientation'
	# The Python Pillow library is a fork of an older library called PIL. 
	# Older PIL stands for Python Imaging Library, and it's the original library that enabled Python to deal with images. 
	# PIL was discontinued in 2011 (that author died) and only supports Python 2.23 ... so use Pillow instead.
	# https://python-pillow.org/
	#print_DEBUG(f'perform_rotation_PIL entered')
	try:
		image = Image.open(str(path))
	except UnidentifiedImageError:
		#print_DEBUG(f'perform_rotation_PIL except UnidentifiedImageError immediate return now')
		return clip
	except PermissionError:
		#print_DEBUG(f'perform_rotation_PIL except PermissionError Permission denied to load: {path} immediate return now')
		return clip
	except Exception as e:
		#print_DEBUG(f'perform_rotation_PIL except Exception {e} immediate return now')
		return clip
	#print_DEBUG(f'perform_rotation_PIL try on Image.open succeeded')
	try:		
		for key in ExifTags.TAGS.keys():
			if ExifTags.TAGS[key] == 'Orientation':
				break
		exif = dict(image.getexif().items())
		value = exif[key]
	except (AttributeError, KeyError, IndexError):
		#print_DEBUG(f'perform_rotation_PIL except AttributeError during for key in ExifTags.TAGS.keys(), immediate return now')
		return clip
	else:
		if   value == 3:
			print_DEBUG(f'PIL says auto-Rotating by 180 degrees {path}')
			clip = clip.std.Turn180()
		elif value == 8:
			print_DEBUG(f'PIL says auto-Rotating by  90 degrees {path}')
			clip = clip.std.Transpose().std.FlipVertical()
		elif value == 6:
			print_DEBUG(f'PIL says auto-Rotating by 270 degrees {path}')
			clip = clip.std.Transpose().std.FlipHorizontal()
		if save_rotated_image and value in [3,8,6]:
			#rotation degrees are in counterclockwise direction!
			rotate = {3:Image.ROTATE_180, 6:Image.ROTATE_270, 8:Image.ROTATE_90}
			image = image.transpose(rotate[value])
			path2 = path.parent / f'{path.stem}_rotated{path.suffix}'
			##image.save(str(path2))	# comment this out ... no writing new images, please
			#print_DEBUG(f'Rotated image {path} was NOT saved as requested into {path2}')
	#exif = image.getexif()
	#print_exif_data(exif)
	#print_DEBUG('', flush=True)
	#print_exif_data(exif.get_ifd(0x8769), flush=True)
	#print_DEBUG('', flush=True)
	#
	#print_exif_data2(image.getexif())
	#print_DEBUG('', flush=True)
	#print_exif_data(image._getexif(), flush=True)
	#print_DEBUG('', flush=True)
	image.close()	
	return clip

###
def perform_rotation_MediaInfo(clip, path, save_rotated_image=False):
	#print_DEBUG(f'perform_rotation_MediaInfo entered')
	param = 'Rotation'
	value = mediainfo_value(Stream.Video, 0, param, path)
	if param == 'Rotation':
		if value is None:
			value = 0
		else:
			value = int(float(value)) # for some reason Rotation value type mediainfo carries as a string,  like: '180.00'
	#print_DEBUG(f'perform_rotation_MediaInfo: value={value} for {path}')
	if   value == 180:
		print_DEBUG(f'MediaInfo says auto-Rotating by 180 degrees {path}')
		clip = clip.std.Turn180()
	elif value == 90:
		print_DEBUG(f'MediaInfo says auto-Rotating by 90 degrees {path}')
		clip = clip.std.Transpose().std.FlipVertical()
	elif value == 270:
		print_DEBUG(f'MediaInfo says auto-Rotating by 270 degrees {path}')
		clip = clip.std.Transpose().std.FlipHorizontal()
	else:
		clip = clip
	return clip

###
def fully_qualified_folder_no_trailing_backslash(folder_name):
	# make into a fully qualified folder string without a trailing backslash
	new_folder_name = os.path.abspath(folder_name)
	if folder_name[-1:] == r'\ '.strip():		# r prefix means the string is treated as a raw string so all escape codes will be ignored. EXCEPT IF THE \ IS THE LAST CHARACTER IN THE STRING !
		new_folder_name = folder_name[:-1]		# remove any trailing backslash
	return new_folder_name
	print(f'INFO: Done.', flush=True)

###
def print_DEBUG(txt):
	if IS_DEBUG:
		print(f'DEBUG: {txt}', flush=True)

###################################################################################################################################################
###################################################################################################################################################
###################################################################################################################################################

### NEVER EVER hide .vpy behind "if __name__=='__main__':"
### BECAUSE IT NEVER GETS RUN BY VSPIPE NOR FFMPEG

TERMINAL_WIDTH = 132
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc
MI = MediaInfo()	# initialize per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
	
ini_file_speciying_parameters = r'.\SLIDESHOW_PARAMETERS.ini'.strip() # r prefix means the string is treated as a raw string so all escape codes will be ignored.EPT IF THE \ is the last character in the string !
ini_file_speciying_parameters = fully_qualified_folder_no_trailing_backslash(ini_file_speciying_parameters)
	
#print_DEBUG(f'ini_file_speciying_parameters="{ini_file_speciying_parameters}"')
#for v in vs.MatrixCoefficients:
#	print_DEBUG(f'vs.MatrixCoefficients: {v} {objPrettyPrint.pformat(v)}')
#for v in vs.TransferCharacteristics:
#	print_DEBUG(f'vs.TransferCharacteristics: {v} {objPrettyPrint.pformat(v)}')
#for v in vs.ColorPrimaries:
#	print_DEBUG(f'vs.ColorPrimaries: {v} {objPrettyPrint.pformat(v)}')
#for v in vs.ColorRange:
#	print_DEBUG(f'vs.ColorRange: {v} {objPrettyPrint.pformat(v)}')

ini_section_name = 'slideshow'
default_ini_values =	{ ini_section_name : {
							#'DIRECTORY' :						fully_qualified_folder_no_trailing_backslash(os.getcwd().strip()),		# r prefix means the string is treated as a raw string so all escape codes will be ignored. EXCEPT IF THE \ IS THE LAST CHARACTER IN THE STRING !
							'DIRECTORY' :						fully_qualified_folder_no_trailing_backslash(r'G:\DVD\PAT-SLIDESHOWS\_AI_05_in_development\0TEST\ '.strip()),		# r prefix means the string is treated as a raw string so all escape codes will be ignored. EXCEPT IF THE \ IS THE LAST CHARACTER IN THE STRING !
							'TEMP_DIRECTORY' :					fully_qualified_folder_no_trailing_backslash(r'D:\TEMP\ '.strip()),	# r prefix means the string is treated as a raw string so all escape codes will be ignored. EXCEPT IF THE \ IS THE LAST CHARACTER IN THE STRING !
							'RECURSIVE' :						True,
							'CROSSFADE_DURATION':				1,
							'TARGET_COLORSPACE' : 				r'BT.709',											# colorspace Rec2020, BT.2020 Rec709, BT.709, Rec601, BT.601, PC.709, PC.601, TV.fcc, PC.fcc, TV.240m, PC.240m; When no hint found in ASS script and colorspace parameter is empty then the default is BT.601
							'TARGET_COLORSPACE_MATRIX' :		r'BT.709',
							'TARGET_COLORSPACE_MATRIX_S' :		r'709',												# for resize, shortened name for bt.709 (not "BT.709" nor "BT709")
							'TARGET_COLORSPACE_MATRIX_I' :		vs.MatrixCoefficients.MATRIX_BT709.value,			
							#'TARGET_COLORSPACE_MATRIX_I' :		vs.MATRIX_BT709,								
							'TARGET_COLOR_TRANSFER' :			r'BT.709',
							'TARGET_COLOR_TRANSFER_S' :			r'BT.709',											# for resize, shortened name for bt.709 (not "BT.709" nor "BT709")
							'TARGET_COLOR_TRANSFER_I' :			vs.TransferCharacteristics.TRANSFER_BT709.value,	
							#'TARGET_COLOR_TRANSFER_I' :		vs.TRANSFER_BT709.value,							
							'TARGET_COLOR_PRIMARIES' :			r'BT.709',
							'TARGET_COLOR_PRIMARIES_S' :		r'BT.709',											# for resize, shortened name for bt.709 (not "BT.709" nor "BT709")
							'TARGET_COLOR_PRIMARIES_I' :		vs.ColorPrimaries.PRIMARIES_BT709.value,			
							#'TARGET_COLOR_PRIMARIES_I' :		vs.PRIMARIES_BT709.value,							
							'TARGET_COLOR_RANGE' :				r'pc',	
							'TARGET_COLOR_RANGE_S' :			r'pc',												# for resize
							'TARGET_COLOR_RANGE_I' :			vs.ColorRange.RANGE_FULL.value,					
							#'TARGET_COLOR_RANGE_I' :			vs.RANGE_FULL.value,								
							'TARGET_WIDTH' :					1920,
							'TARGET_HEIGHT' :					1080,
							'TARGET_FPSNUM' :					25,													# for fps numerator		... PAL world bias
							'TARGET_FPSDEN' :					1,													# for fps denominator	... PAL world bias
							'MIN_DURATION_SEC' :				0.5,												### MINIMUM duration of display of an image, in seconds
							'MAX_DURATION_SEC' :				4,													### MAXIMUM duration of display of an image, in seconds
							'MAX_VIDEO_CLIP_DURATION' :			10,													# Maximum diraction of a video clip in seconds
							'BOX' :								True,												# True would initiate letterboxing or pillarboxing. False fills to TARGET_WIDTH,TARGET_HEIGHT
							'ADD_SUBTITLE' :					True,												# True adds a subtitle in the bottom right corner containing the last few parts of the path to the image/video
							'UPSIZE_KERNEL' :					r'Lanczos',
							'DOWNSIZE_KERNEL' :					r'Spline36',
							}
						}
ini_values = default_ini_values
config = configparser.ConfigParser(default_ini_values[ini_section_name], allow_no_value=True)
config.read(ini_file_speciying_parameters)
# if a missing not badly formatted .ini, save and use default ini valies
if not config.has_section(ini_section_name):
	config = configparser.ConfigParser(allow_no_value=True)
	config.read_dict(default_ini_values)
	with open(ini_file_speciying_parameters, 'w') as configfile:
		config.write(configfile)
	config = configparser.ConfigParser(default_ini_values[ini_section_name], allow_no_value=True)
	config.read(ini_file_speciying_parameters)
	print(f'WARNING: default values applied due to missing or invalid .ini file\n{objPrettyPrint.pformat(default_ini_values)}', flush=True)
# if using ini values fails, even after trying to use default values, exit
if config.has_section(ini_section_name):
	ini_values[ini_section_name]["DIRECTORY"] = fully_qualified_folder_no_trailing_backslash(config.get(ini_section_name, 'DIRECTORY'))
	ini_values[ini_section_name]["TEMP_DIRECTORY"] = fully_qualified_folder_no_trailing_backslash(config.get(ini_section_name, 'TEMP_DIRECTORY'))
	ini_values[ini_section_name]["RECURSIVE"] = config.getboolean(ini_section_name, 'RECURSIVE')
	ini_values[ini_section_name]["CROSSFADE_DURATION"] = config.getint(ini_section_name, 'CROSSFADE_DURATION')
	ini_values[ini_section_name]["TARGET_COLORSPACE"] = config.get(ini_section_name, 'TARGET_COLORSPACE')
	ini_values[ini_section_name]["TARGET_COLORSPACE_MATRIX"] = config.get(ini_section_name, 'TARGET_COLORSPACE_MATRIX')
	ini_values[ini_section_name]["TARGET_COLORSPACE_MATRIX_S"] = config.get(ini_section_name, 'TARGET_COLORSPACE_MATRIX_S')
	ini_values[ini_section_name]["TARGET_COLORSPACE_MATRIX_I"] = config.get(ini_section_name, 'TARGET_COLORSPACE_MATRIX_I')
	ini_values[ini_section_name]["TARGET_COLOR_TRANSFER"] = config.get(ini_section_name, 'TARGET_COLOR_TRANSFER')
	ini_values[ini_section_name]["TARGET_COLOR_TRANSFER_S"] = config.get(ini_section_name, 'TARGET_COLOR_TRANSFER_S')
	ini_values[ini_section_name]["TARGET_COLOR_TRANSFER_I"] = config.get(ini_section_name, 'TARGET_COLOR_TRANSFER_I')
	ini_values[ini_section_name]["TARGET_COLOR_PRIMARIES"] = config.get(ini_section_name, 'TARGET_COLOR_PRIMARIES')
	ini_values[ini_section_name]["TARGET_COLOR_PRIMARIES_S"] = config.get(ini_section_name, 'TARGET_COLOR_PRIMARIES_S')
	ini_values[ini_section_name]["TARGET_COLOR_PRIMARIES_I"] = config.get(ini_section_name, 'TARGET_COLOR_PRIMARIES_I')
	ini_values[ini_section_name]["TARGET_COLOR_RANGE"] = config.get(ini_section_name, 'TARGET_COLOR_RANGE')
	ini_values[ini_section_name]["TARGET_COLOR_RANGE_S"] = config.get(ini_section_name, 'TARGET_COLOR_RANGE_S')
	ini_values[ini_section_name]["TARGET_COLOR_RANGE_I"] = config.get(ini_section_name, 'TARGET_COLOR_RANGE_I')
	ini_values[ini_section_name]["TARGET_WIDTH"] = config.getint(ini_section_name, 'TARGET_WIDTH')
	ini_values[ini_section_name]["TARGET_HEIGHT"] = config.getint(ini_section_name, 'TARGET_HEIGHT')
	ini_values[ini_section_name]["TARGET_FPSNUM"] = config.getint(ini_section_name, 'TARGET_FPSNUM')
	ini_values[ini_section_name]["TARGET_FPSDEN"] = config.getint(ini_section_name, 'TARGET_FPSDEN')
	ini_values[ini_section_name]["MIN_DURATION_SEC"] = config.getfloat(ini_section_name, 'MIN_DURATION_SEC')
	ini_values[ini_section_name]["MAX_DURATION_SEC"] = config.getint(ini_section_name, 'MAX_DURATION_SEC')
	ini_values[ini_section_name]["MAX_VIDEO_CLIP_DURATION"] = config.getint(ini_section_name, 'MAX_VIDEO_CLIP_DURATION')
	ini_values[ini_section_name]["BOX"] = config.getboolean(ini_section_name, 'BOX')
	ini_values[ini_section_name]["ADD_SUBTITLE"] = config.getboolean(ini_section_name, 'ADD_SUBTITLE')
	ini_values[ini_section_name]["UPSIZE_KERNEL"] = config.get(ini_section_name, 'UPSIZE_KERNEL')
	ini_values[ini_section_name]["DOWNSIZE_KERNEL"] = config.get(ini_section_name, 'DOWNSIZE_KERNEL')
else:
	raise ValueError(f'ERROR: .ini file unable to be read or recreated properly')
# save the updated set of .ini values over the top of the existing set
with open(ini_file_speciying_parameters, 'w') as configfile:
	# add the new set of .ini value to be saved
	update_config =  configparser.ConfigParser(allow_no_value=True)
	update_config[ini_section_name] = default_ini_values[ini_section_name]
	# add example values to make it easier for a human reader of the .ini file
	tmp_name = 'Enum_vs.MatrixCoefficients'
	tmp_dict = { tmp_name : {}}
	for v in vs.MatrixCoefficients:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.TransferCharacteristics'
	tmp_dict = { tmp_name : {}}
	for v in vs.TransferCharacteristics:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.ColorPrimaries'
	tmp_dict = { tmp_name : {}}
	for v in vs.ColorPrimaries:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.ColorRange'
	tmp_dict = { tmp_name : {}}
	for v in vs.ColorRange:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.PresetFormat'
	tmp_dict = { tmp_name : {}}
	for v in vs.PresetFormat:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.ColorFamily'
	tmp_dict = { tmp_name : {}}
	for v in vs.ColorFamily:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.ChromaLocation'
	tmp_dict = { tmp_name : {}}
	for v in vs.ChromaLocation:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	tmp_name = 'Enum_vs.FieldBased'
	tmp_dict = { tmp_name : {}}
	for v in vs.FieldBased:
		tmp_dict[tmp_name][str(v)] = v.value
		pass
	update_config[tmp_name] = tmp_dict[tmp_name]
	# update the .ini file
	update_config.write(configfile)
print(f'INFO: Saved updated .ini "{ini_file_speciying_parameters}"', flush=True)
# calculate some values and create a new updated calculated values dict
calc_ini = ini_values[ini_section_name]
calc_ini["PIC_EXTENSIONS"]		= [".png", ".jpg", ".jpeg", ".gif"]								# always lower case
calc_ini["VID_EXTENSIONS"]		= [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov"]	# always lower case
calc_ini["EEK_EXTENSIONS"]		= [".m2ts"]														# always lower case
calc_ini["VID_EEK_EXTENSIONS"]	= calc_ini["VID_EXTENSIONS"] + calc_ini["EEK_EXTENSIONS"]
calc_ini["EXTENSIONS"]			= calc_ini["PIC_EXTENSIONS"] + calc_ini["VID_EXTENSIONS"] + calc_ini["EEK_EXTENSIONS"]
calc_ini["TARGET_PIXEL_FORMAT"]	= vs.YUV420P8				# pixel format of the target video
calc_ini["DG_PIXEL_FORMAT"]		= vs.YUV420P16				# pixel format of the video for use by DG tools
calc_ini["TARGET_FPS"]			= round(calc_ini["TARGET_FPSNUM"] / calc_ini["TARGET_FPSDEN"], 3)
calc_ini["BLANK_CLIP_LENGTH"]	= int(math.ceil(0.1*calc_ini["TARGET_FPS"]))	# leading and trailing blank clip duration in frames with round-up. int(round(0.1*calc_ini["TARGET_FPS"])) will round up/down
calc_ini["MIN_DURATION_FRAMES"]	= int(math.ceil(calc_ini["MIN_DURATION_SEC"] * calc_ini["TARGET_FPS"]))	### duration of display of an image, in frames
calc_ini["MAX_DURATION_FRAMES"]	= int(math.ceil(calc_ini["MAX_DURATION_SEC"] * calc_ini["TARGET_FPS"]))	### max duration of display of a video, in frames
calc_ini["DOT_FFINDEX"]			= ".ffindex".lower()		# for removing temporary *.ffindex files at the end
calc_ini["MODX"]				= 2	   # mods for letterboxing calculations, example, for 411 YUV as an extreme
calc_ini["MODY"]				= 2	   # mods would have to be MODX=4, MODY=1 as minimum

########################################################################################################################################################
if calc_ini["RECURSIVE"]:
	glob_var="**/*.*"			# recursive
	ff_glob_var="**/*.ffindex"	# for .ffindex file deletion recursive
else:
	glob_var="*.*"				# non-recursive
	ff_glob_var="*.ffindex"		# for .ffindex file deletion non-recursive
# glob : with DIRECTORY not having a trailing slash !!!
print(f'INFO: Start processing image/video files in "{calc_ini["DIRECTORY"]}" recursive="{calc_ini["RECURSIVE"]}" glob_var="{glob_var}" \n      with Extensions={objPrettyPrint.pformat(calc_ini["EXTENSIONS"])}', flush=True)
Count_of_files = 0
# NOTE: calc_ini["DIRECTORY"] MUST NOT have a trailing backslash ... remove during ini setup
paths = Path(calc_ini["DIRECTORY"]).glob(glob_var) # generator of all paths in a directory, files starting with . won't be matched by default
path = get_path(paths)	#pre-fetch first path
if path is None:
	raise ValueError(f'ERROR: File Extensions: {calc_ini["EXTENSIONS"]}, not found in "{calc_ini["DIRECTORY"]}"')
blank_clip = core.std.BlankClip(format=calc_ini["TARGET_PIXEL_FORMAT"], width=calc_ini["TARGET_WIDTH"], height=calc_ini["TARGET_HEIGHT"], length=calc_ini["BLANK_CLIP_LENGTH"], color=(16,128,128))	 # notice no colorspace,"range" etc can be specified
clips = blank_clip	# initialize the accumulated clips with a starting small blank clip
if calc_ini["CROSSFADE_DURATION"]>0:	
	crossfade_blank_clip = blank_clip[0]*calc_ini["MIN_DURATION_FRAMES"] if len(blank_clip)<calc_ini["MIN_DURATION_FRAMES"] else blank_clip
	prior_clip_for_crossfade = crossfade_blank_clip
#---
while not (path is None):	# first clip already pre-retrieved ready for this while loop
	Count_of_files = Count_of_files + 1
	print(f'INFO: processing {Count_of_files} {str(path)}', flush=True)
	#if (Count_of_files % 10)==0:
	#	print(f'{Count_of_files},',end="", flush=True)	# https://www.geeksforgeeks.org/gfact-50-python-end-parameter-in-print/
	#	if (Count_of_files % (10*10*3))==0:
	#		print(f'', flush=True)
	this_clip = get_clip(path)
	#this_clip = core.text.Text(this_clip, text_subpath_for_subtitles, alignment=9, scale=1)
	#this_clip = core.text.FrameNum(this_clip, alignment=2, scale=1)
	#this_clip = core.text.ClipInfo(this_clip, alignment=8, scale=1)
	#this_clip = core.text.FrameProps(this_clip, alignment=2, scale=1)
	if calc_ini["CROSSFADE_DURATION"]>0:	
		#print_DEBUG(f'doing crossfade in while loop', flush=True)
		crossfade_clip = crossfade(prior_clip_for_crossfade, this_clip, calc_ini["CROSSFADE_DURATION"])
		# for now, don't do equivalent of this from _AI_ ... right  = right_clip[calc_ini["CROSSFADE_DURATION"]:-calc_ini["CROSSFADE_DURATION"]]
		clips = clips + crossfade_clip + this_clip
		prior_clip_for_crossfade = this_clip
	else:
		clips = clips + this_clip
	path = get_path(paths)		# get next path to process in this while loop
#---
# perhaps a finishing crossfade to black ?
if calc_ini["CROSSFADE_DURATION"]>0:	
	#print_DEBUG(f'doing final crossfade after while loop')
	crossfade_clip = crossfade(prior_clip_for_crossfade, crossfade_blank_clip, calc_ini["CROSSFADE_DURATION"])
	# for now, don't do equivalent of this from _AI_ ... right  = right_clip[calc_ini["CROSSFADE_DURATION"]:-calc_ini["CROSSFADE_DURATION"]]
	clips = clips + crossfade_clip + this_clip
clips = clips + blank_clip		# end the accumulated clips with a finishing small blank clip
clips = clips.std.AssumeFPS(fpsnum=calc_ini["TARGET_FPSNUM"], fpsden=calc_ini["TARGET_FPSDEN"])
print(f'INFO: Finished processing {Count_of_files} image/video files.', flush=True)
# Cleanup any temporary .ffindex files created by ffms2
print(f'INFO: Start removing temporary *.ffindex files from folder "{calc_ini["DIRECTORY"]}" with recursive="{calc_ini["RECURSIVE"]}" ...')
pp = calc_ini["DIRECTORY"] + "/" + ff_glob_var
ffindex_files = glob.glob(pp, recursive=calc_ini["RECURSIVE"])
Count_of_files_removed = 0
for ff in ffindex_files:
	if ff.lower()[-len(calc_ini["DOT_FFINDEX"]):] == calc_ini["DOT_FFINDEX"]:	# double check the file really does have ext .ffindex
		try:
			Count_of_files_removed = Count_of_files_removed + 1
			print_DEBUG(f'INFO: removing {Count_of_files_removed} {ff}')
			os.remove(ff)
			#if (Count_of_files_removed % (10))==0:
			#	print_DEBUG(f'{Count_of_files_removed},', end='', flush=True)	# https://www.geeksforgeeks.org/gfact-50-python-end-parameter-in-print/
			#	if (Count_of_files_removed % (10*10*3))==0:
			#		print_DEBUG(f'', flush=True)
		except OSError as ee:
			print(f'ERROR:  error during removal of ffindex file: {ff} :{ee} : {ee.strerror}', flush=True)
			raise ValueError(f'ERROR: error during removal of ffindex file: {ff} :{ee} : {ee.strerror}')
print(f'INFO: Finished removing {Count_of_files_removed} temporary .ffindex files from folder "{calc_ini["DIRECTORY"]}" with recursive="{calc_ini["RECURSIVE"]}"', flush=True)
# hmm, audio ? maybe later using source filter "bas" ?
print(f'INFO: Done.', flush=True)
clips.set_output()
#------
