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
#		portable vapoursynth overlaid in the same folder
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
		x = x - x%calc_ini['MODX']
		x = max(0, min(x,W))
		clip = resize_clip(clip, W-2*x, H)
		if x: return clip.std.AddBorders(left=x, right=x, color=(16,128,128))  #RGB is out then (16,16,16)
		else: return clip
	else:
		h = source_height*W/source_width
		y = int((H-h)/2)
		y = y - y%calc_ini['MODY']
		y = max(0, min(y,H))
		clip = resize_clip(clip, W, H-2*y)
		if y: return clip.std.AddBorders(top=y, bottom=y, color=(16,128,128))
		else: return clip

###
def resize_clip(clip,w,h):		# was resize_clip(clip,w,h, W=TARGET_WIDTH, H=TARGET_HEIGHT):
	W = calc_ini['TARGET_WIDTH']
	H = calc_ini['TARGET_HEIGHT']
	if w>W or h>H:	resize = getattr(clip.resize, calc_ini['DOWNSIZE_KERNEL'])	# get the resize function object ?handle? with the nominated kernel
	else:			resize = getattr(clip.resize, calc_ini['UPSIZE_KERNEL'])	# get the resize function object ?handle? with the nominated kernel
	
	#with clip.get_frame(0) as f:
	#	print(f'DEBUG: incoming frame properties before resize=\n{objPrettyPrint.pformat(f.props)}\n',flush=True)
	
	if clip.format.color_family==vs.RGB:
		#rgb to YUV, perhaps only for png images, figure out what matrix out is needed ... use the HD one REC.709
		#resize.(vnode clip[, int width, int height, int format, enum matrix, enum transfer, enum primaries, enum range, 
		#			enum chromaloc, enum matrix_in, enum transfer_in, enum primaries_in, enum range_in, enum chromaloc_in, 
		#			float filter_param_a, float filter_param_b, string resample_filter_uv, float filter_param_a_uv, float filter_param_b_uv, 
		#			string dither_type="none", string cpu_type, float src_left, float src_top, float src_width, float src_height, float nominal_luminance])
		#print(f'DEBUG: clip.format.color_family==vs.RGB: clip.format.color_family={clip.format.color_family} vs.RGB={vs.RGB}\n',flush=True)

		#c = resize(width=w, height=h, format=calc_ini['TARGET_PIXEL_FORMAT'], matrix_s=calc_ini['TARGET_COLORSPACE_MATRIX_S'])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini['TARGET_PIXEL_FORMAT'], matrix=calc_ini['TARGET_COLORSPACE_MATRIX_I'], transfer=calc_ini['TARGET_COLOR_TRANSFER_I'], primaries=calc_ini['TARGET_COLOR_PRIMARIES_I'], range=calc_ini['TARGET_COLOR_RANGE_I'])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265

		#with clip.get_frame(0) as f:
		#	print(f'DEBUG: outgoing frame properties after resize=\n{objPrettyPrint.pformat(f.props)}\n',flush=True)
		return c
	elif clip.format.color_family==vs.YUV:
		#resize.(vnode clip[, int width, int height, int format, enum matrix, enum transfer, enum primaries, enum range, 
		#			enum chromaloc, enum matrix_in, enum transfer_in, enum primaries_in, enum range_in, enum chromaloc_in, 
		#			float filter_param_a, float filter_param_b, string resample_filter_uv, float filter_param_a_uv, float filter_param_b_uv, 
		#			string dither_type="none", string cpu_type, float src_left, float src_top, float src_width, float src_height, float nominal_luminance])
		#print(f'DEBUG: clip.format.color_family==vs.YUV: clip.format.color_family={clip.format.color_family} vs.YUV={vs.YUV}\n',flush=True)

		#c = resize(width=w, height=h, format=calc_ini['TARGET_PIXEL_FORMAT'], matrix_s=calc_ini['TARGET_COLORSPACE_MATRIX_S'])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini['TARGET_PIXEL_FORMAT'], matrix=calc_ini['TARGET_COLORSPACE_MATRIX_I'], transfer=calc_ini['TARGET_COLOR_TRANSFER_I'], primaries=calc_ini['TARGET_COLOR_PRIMARIES_I'], range=calc_ini['TARGET_COLOR_RANGE_I'])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265

		# AH !!! the above line with matrix_s='709' can cause this error:
		# If you get an error like:
		# 		Resize error 3074: no path between colorspaces (2/2/2 => 1/1/1). May need to specify additional colorspace parameters.
		# It usually means the matrix/transfer/primaries are unknown 
		# *** and you have to specify the input colorspace parameters yourself. *** Note: 2 means “unspecified” according to the ITU-T recommendation.
		#c = resize(width=w, height=h, format=calc_ini['TARGET_PIXEL_FORMAT'])
		#with clip.get_frame(0) as f:
		#	print(f'DEBUG: outgoing frame properties after resize=\n{objPrettyPrint.pformat(f.props)}\n',flush=True)
		return c
	else:
		#resize.(vnode clip[, int width, int height, int format, enum matrix, enum transfer, enum primaries, enum range, 
		#			enum chromaloc, enum matrix_in, enum transfer_in, enum primaries_in, enum range_in, enum chromaloc_in, 
		#			float filter_param_a, float filter_param_b, string resample_filter_uv, float filter_param_a_uv, float filter_param_b_uv, 
		#			string dither_type="none", string cpu_type, float src_left, float src_top, float src_width, float src_height, float nominal_luminance])
		#print(f'DEBUG: NEITHER vs.RGB nor vs.YUV ? clip.format.color_family!=vs.RGB: clip.format.color_family={clip.format.color_family} vs.RGB={vs.RGB} vs.YUV={vs.YUV}\n',flush=True)

		#c = resize(width=w, height=h, format=calc_ini['TARGET_PIXEL_FORMAT'], matrix_s=calc_ini['TARGET_COLORSPACE_MATRIX_S'])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265
		c = resize(width=w, height=h, format=calc_ini['TARGET_PIXEL_FORMAT'], matrix=calc_ini['TARGET_COLORSPACE_MATRIX_I'], transfer=calc_ini['TARGET_COLOR_TRANSFER_I'], primaries=calc_ini['TARGET_COLOR_PRIMARIES_I'], range=calc_ini['TARGET_COLOR_RANGE_I'])	# https://www.vapoursynth.com/doc/functions/video/resize.html# https://www.itu.int/rec/T-REC-H.265

		# AH !!! the avove line with matrix_s='709' can cause this error:
		# If you get an error like:
		# 		Resize error 3074: no path between colorspaces (2/2/2 => 1/1/1). May need to specify additional colorspace parameters.
		# It usually means the matrix/transfer/primaries are unknown 
		# *** and you have to specify the input colorspace parameters yourself. *** Note: 2 means “unspecified” according to the ITU-T recommendation.
		#c = resize(width=w, height=h, format=calc_ini['TARGET_PIXEL_FORMAT'])
		#with clip.get_frame(0) as f:
		#	print(f'DEBUG: outgoing frame properties after resize=\n{objPrettyPrint.pformat(f.props)}\n',flush=True)
		return c

###
def get_clip(path):
	if path.suffix.lower()   in calc_ini['EEK_EXTENSIONS']:
		#print(f'DEBUG: get_clip: lsmas Video: {path.name},flush=True')
		clip = core.lsmas.LWLibavSource(str(path))
		#print(f'DEBUG: get_clip: Video info:\n{clip}',flush=True)
	elif path.suffix.lower() in calc_ini['VID_EXTENSIONS']:
		#print(f'DEBUG: get_clip: ffms2 Video: {path.name}',flush=True)
		clip = core.ffms2.Source(str(path))	#ffms2 leaves *.ffindex files everywhere in folders.
		#clip = core.lsmas.LibavSMASHSource(str(path))
		#print(f'DEBUG: get_clip: Video info:\n{clip}',flush=True)
	elif path.suffix.lower() in calc_ini['PIC_EXTENSIONS']:
		#print(f'DEBUG: get_clip: ffms2 Video: {path.name}',flush=True)
		clip = core.ffms2.Source(str(path))
	#	clip = core.imwri.Read(str(path)) # ImageWriter, if installed into vapoursynth folder
		#print(f'DEBUG: get_clip: Video info:\n{clip}',flush=True)
	else:
		#print(f'DEBUG: get_clip: ffms2 Video: {path.name}',flush=True)
		clip = core.ffms2.Source(str(path))	# if file extension not recognised, use this reader
		#print(f'DEBUG: get_clip: Video info:\n{clip}',flush=True)

	# check for and picture/video rotation specified perhaps in EXIF but not auto-processed here by the file openers
	if path.suffix.lower()   in calc_ini['VID_EEK_EXTENSIONS']:
		clip = rotation_check_MediaInfo(clip, path, save_rotated_image=False)	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678326
	else: # source is not a video type, i.e. an image
		clip = rotation_check_PIL(clip, path, save_rotated_image=False)	# per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678326

	# do video-specific or picture-specific changes
	if path.suffix.lower()   in calc_ini['VID_EEK_EXTENSIONS']:	#if any sort of video, probably an old hand-held camera or phone, sometimes variable fps ...
		#print(f'DEBUG: get_clip: opened Video: {path.name}',flush=True)
		#print(f'DEBUG: get_clip: opened Video: {path.name}\nVideo info:\n{clip}',flush=True)
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
		#print(f'DEBUG: get_clip: {source_width}x{source_height}\nsource_fpsnum:{source_fpsnum} source_fpsden:{source_fpsden}\nsource_fps:{source_fps}\nsource_duration_frames:{source_duration_frames}\nsource_duration_secs:{source_duration_secs}',flush=True)
		# change framerate ? too hard for a small simple video sample, just "assume" target fps and ignore consequences of speed-up or slow-down or VFR
		clip = clip.std.AssumeFPS(fpsnum=calc_ini['TARGET_FPSNUM'], fpsden=calc_ini['TARGET_FPSDEN'])
		# if duration greater than out review maximum, clip it
		if source_duration_frames>(MAX_DURATION_FRAMES-1):
			clip = core.std.Trim(clip, first=0, last=(MAX_DURATION_FRAMES-1))
		# denoise ANY "small" dimension video clips, older videos likely to be noisy
		if source_width<calc_ini['TARGET_WIDTH'] or source_height<calc_ini['TARGET_HEIGHT']:	 
			#print(f'DEBUG: applying DGDenoise to small {source_width}x{source_height} video {path.name}',flush=True)
			# clip must be YUV420P16 for DGDenoise etc
			clip = clip.resize.Point(format=DG_PIXEL_FORMAT)		# convert to DG_PIXEL_FORMAT via resizer which does no resizing
			#clip = core.avs.DGDenoise(clip, strength=0.06, cstrength=0.06)
			clip = core.avs.DGDenoise(clip, strength=0.15, cstrength=0.15)
			clip = clip.resize.Point(format=calc_ini['TARGET_PIXEL_FORMAT'])	# convert to calc_ini['TARGET_PIXEL_FORMAT'] via resizer which does no resizing
	else: # source is not a video type, i.e. an image
		# extend duration of a clip of an image
		clip = clip[0]*calc_ini['MIN_DURATION_FRAMES'] if len(clip)<calc_ini['MIN_DURATION_FRAMES'] else clip # make clip at least calc_ini['MIN_DURATION_FRAMES'] frames long if less than MIN_DURATION_FRAMES frames
	
	# either add borders to maintain aspect ratio (boxing), or just stretch to fit (yuk)
	if calc_ini['BOX']:
		clip = boxing(clip, calc_ini['TARGET_WIDTH'], calc_ini['TARGET_HEIGHT'])
	else:
		clip = resize_clip(clip, calc_ini['TARGET_WIDTH'], calc_ini['TARGET_HEIGHT'])

	# Add a subtitle being the trailing 3 parts of the path
	if calc_ini['ADD_SUBTITLE']:	# Add a subtitle being the trailing 3 parts of the path
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
		clip = core.assrender.Subtitle(clip, text_subpath_for_subtitles, style="sans-serif,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0.9,0.5,3,2,2,2,1", colorspace=calc_ini['TARGET_COLORSPACE'])
	return clip

###
def get_path(path_generator):
	#get next path of desired extensions from generator, ignoring extensions we have not specified
	while 1:	# loop until we do a "return", hitting past the end of the iterator returns None
		try:
			path = next(path_generator)
			#print(f'DEBUG: get_path: get success, path.name=' + path.name,flush=True)
		except StopIteration:
			return None
		if path.suffix.lower() in calc_ini['EXTENSIONS']:	# only return files which are in known extensions
			#print(f'DEBUG: get_path: in calc_ini["EXTENSIONS"] success, path.name=' + path.name,flush=True)
			return path
		  
###
def crossfade(a, b, duration):
	#gets crosfade part from end of clip a and start of clip b
	def fade_image(n, a, b):
		return core.std.Merge(a, b, weight=n/duration)
	if a.format.id != b.format.id or a.height != b.height or a.width != b.width:
		raise ValueError('crossfade: Both clips must have the same dimensions and format.')
	return core.std.FrameEval(a[-duration:], partial(fade_image, a=a[-duration:], b=b[:duration]))

###
def print_exif_data(exif_data):
	for tag_id in exif_data:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_data.get(tag_id)
		print(f'DEBUG: {tag:25}: {content}',flush=True)
	print(f'DEBUG: exif_data:\n{objPrettyPrint.pformat(exif_data)}',flush=True)
	print('',flush=True)
		
###
def print_exif_data2(exif_data):
	for tag_id in exif_data:
		tag = TAGS.get(tag_id, tag_id)
		content = exif_data.get(tag_id)
		if isinstance(content, bytes):
			content = content.decode()
		print(f'DEBUG: {tag:25}: {content}',flush=True)
	print(f'DEBUG: exif_data2:\n{objPrettyPrint.pformat(exif_data)}',flush=True)
	print('',flush=True)

###
def rotation_check_PIL(clip, path, save_rotated_image=False):
	# from PIL import Image, ExifTags, UnidentifiedImageError   # pip install Pillow, or equivalent
	# PIL Pillow module loads an image, checks if EXIF data, checks for 'Orientation'
	# The Python Pillow library is a fork of an older library called PIL. 
	# Older PIL stands for Python Imaging Library, and it's the original library that enabled Python to deal with images. 
	# PIL was discontinued in 2011 (that author died) and only supports Python 2.23 ... so use Pillow instead.
	# https://python-pillow.org/
	#print(f'DEBUG: rotation_check_PIL entered',flush=True)
	try:
		image = Image.open(str(path))
	except UnidentifiedImageError:
		#print(f'DEBUG: rotation_check_PIL except UnidentifiedImageError immediate return now',flush=True)
		return clip
	except PermissionError:
		#print(f'DEBUG: rotation_check_PIL except PermissionError Permission denied to load: {path} immediate return now',flush=True)
		return clip
	except Exception as e:
		#print(f'DEBUG: rotation_check_PIL except Exception {e} immediate return now',flush=True)
		return clip
	#print(f'DEBUG: rotation_check_PIL try on Image.open succeeded',flush=True)
	try:		
		for key in ExifTags.TAGS.keys():
			if ExifTags.TAGS[key] == 'Orientation':
				break
		exif = dict(image.getexif().items())
		value = exif[key]
	except (AttributeError, KeyError, IndexError):
		#print(f'DEBUG: rotation_check_PIL except AttributeError during for key in ExifTags.TAGS.keys(), immediate return now',flush=True)
		return clip
	else:
		if   value == 3:
			print(f'DEBUG: PIL says auto-Rotating by 180 degrees {path}',flush=True)
			clip = clip.std.Turn180()
		elif value == 8:
			print(f'DEBUG: PIL says auto-Rotating by  90 degrees {path}',flush=True)
			clip = clip.std.Transpose().std.FlipVertical()
		elif value == 6:
			print(f'DEBUG: PIL says auto-Rotating by 270 degrees {path}',flush=True)
			clip = clip.std.Transpose().std.FlipHorizontal()
		if save_rotated_image and value in [3,8,6]:
			#rotation degrees are in counterclockwise direction!
			rotate = {3:Image.ROTATE_180, 6:Image.ROTATE_270, 8:Image.ROTATE_90}
			image = image.transpose(rotate[value])
			path2 = path.parent / f'{path.stem}_rotated{path.suffix}'
			##image.save(str(path2))	# comment this out ... no writing new images, please
			#print(f'DEBUG: Rotated image {path} was NOT saved as requested into {path2}',flush=True)
	#exif = image.getexif()
	#print_exif_data(exif,flush=True)
	#print('',flush=True)
	#print_exif_data(exif.get_ifd(0x8769),flush=True)
	#print('',flush=True)
	#
	#print_exif_data2(image.getexif(),flush=True)
	#print('',flush=True)
	#print_exif_data(image._getexif(),flush=True)
	#print('',flush=True)
	image.close()	
	return clip

###
def rotation_check_MediaInfo(clip, path, save_rotated_image=False):
	#print(f'DEBUG: rotation_check_MediaInfo entered',flush=True)
	param = 'Rotation'
	value = mediainfo_value(Stream.Video, 0, param, path)
	if param == 'Rotation':
		if value is None:
			value = 0
		else:
			value = int(float(value)) # for some reason Rotation value type mediainfo carries as a string,  like: '180.00'
	#print(f'DEBUG: rotation_check_MediaInfo: value={value} for {path}',flush=True)
	if   value == 180:
		print(f'DEBUG: MediaInfo says auto-Rotating by 180 degrees {path}',flush=True)
		clip = clip.std.Turn180()
	elif value == 90:
		print(f'DEBUG: MediaInfo says auto-Rotating by 90 degrees {path}',flush=True)
		clip = clip.std.Transpose().std.FlipVertical()
	elif value == 270:
		print(f'DEBUG: MediaInfo says auto-Rotating by 270 degrees {path}',flush=True)
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

###################################################################################################################################################
###################################################################################################################################################
###################################################################################################################################################

if __name__=='__main__':
	#if DIRECTORY[-1:] == "\\"[-1:]:
	#	DIRECTORY = DIRECTORY[:-1]	# remove any trailing backslash
	#else:
	#	DIRECTORY = DIRECTORY
	#
	TERMINAL_WIDTH = 132
	objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc
	MI = MediaInfo()	# initialize per https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio#post2678372
	
	ini_file_speciying_parameters = r'.\SLIDESHOW_PARAMETERS.ini'.strip() # r prefix means the string is treated as a raw string so all escape codes will be ignored.EPT IF THE \ is the last character in the string !
	ini_file_speciying_parameters = fully_qualified_folder_no_trailing_backslash(ini_file_speciying_parameters)
	
	#print(f'DEBUG: ini_file_speciying_parameters="{ini_file_speciying_parameters}"',flush=True)

	#for v in vs.MatrixCoefficients:
	#	print(f'DEBUG: vs.MatrixCoefficients: {v} {objPrettyPrint.pformat(v)}',flush=True)
	#for v in vs.TransferCharacteristics:
	#	print(f'DEBUG: vs.TransferCharacteristics: {v} {objPrettyPrint.pformat(v)}',flush=True)
	#for v in vs.ColorPrimaries:
	#	print(f'DEBUG: vs.ColorPrimaries: {v} {objPrettyPrint.pformat(v)}',flush=True)
	#for v in vs.ColorRange:
	#	print(f'DEBUG: vs.ColorRange: {v} {objPrettyPrint.pformat(v)}',flush=True)

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
								#'TARGET_COLORSPACE_MATRIX_I' :		int(vs.MatrixCoefficients.MATRIX_BT709)+0,			# ugh, "+0" trick to force an integer stored !  https://www.vapoursynth.com/doc/pythonreference.html
								'TARGET_COLORSPACE_MATRIX_I' :		int(vs.MATRIX_BT709)+0,								# ugh, "+0" trick to force an integer stored !  https://www.vapoursynth.com/doc/pythonreference.html
								'TARGET_COLOR_TRANSFER' :			r'BT.709',
								'TARGET_COLOR_TRANSFER_S' :			r'BT.709',											# for resize, shortened name for bt.709 (not "BT.709" nor "BT709")
								#'TARGET_COLOR_TRANSFER_I' :		int(vs.TransferCharacteristics.TRANSFER_BT709)+0,	# ugh, "+0" trick to force an integer stored !  https://www.vapoursynth.com/doc/pythonreference.html
								'TARGET_COLOR_TRANSFER_I' :			int(vs.TRANSFER_BT709)+0,							# ugh, "+0" trick to force an integer stored !  https://www.vapoursynth.com/doc/pythonreference.html
								'TARGET_COLOR_PRIMARIES' :			r'BT.709',
								'TARGET_COLOR_PRIMARIES_S' :		r'BT.709',											# for resize, shortened name for bt.709 (not "BT.709" nor "BT709")
								#'TARGET_COLOR_PRIMARIES_I' :		int(vs.ColorPrimaries.PRIMARIES_BT709)+0,			# ugh, "+0" trick to force an integer stored !  https://www.vapoursynth.com/doc/pythonreference.html
								'TARGET_COLOR_PRIMARIES_I' :		int(vs.PRIMARIES_BT709)+0,							# ugh, "+0" trick to force an integer stored !  https://www.vapoursynth.com/doc/pythonreference.html
								'TARGET_COLOR_RANGE' :				r'pc',	
								'TARGET_COLOR_RANGE_S' :			r'pc',											# for resize
								#'TARGET_COLOR_RANGE_I' :			int(vs.ColorRange.RANGE_FULL)+0,					# ugh, "+0" trick to force an integer stored !  https://www.vapoursynth.com/doc/pythonreference.html
								'TARGET_COLOR_RANGE_I' :			int(vs.RANGE_FULL)+0,								# ugh, "+0" trick to force an integer stored !  https://www.vapoursynth.com/doc/pythonreference.html
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
		print(f'WARNING: default values applied due to missing or invalid .ini file\n{objPrettyPrint.pformat(default_ini_values)}',flush=True)
	# if using ini values fails, even after trying to use default values, exit
	if config.has_section(ini_section_name):
		ini_values[ini_section_name]['DIRECTORY'] = fully_qualified_folder_no_trailing_backslash(config.get(ini_section_name, 'DIRECTORY'))
		ini_values[ini_section_name]['TEMP_DIRECTORY'] = fully_qualified_folder_no_trailing_backslash(config.get(ini_section_name, 'TEMP_DIRECTORY'))
		ini_values[ini_section_name]['RECURSIVE'] = config.getboolean(ini_section_name, 'RECURSIVE')
		ini_values[ini_section_name]['CROSSFADE_DURATION'] = config.getint(ini_section_name, 'CROSSFADE_DURATION')
		ini_values[ini_section_name]['TARGET_COLORSPACE'] = config.get(ini_section_name, 'TARGET_COLORSPACE')
		ini_values[ini_section_name]['TARGET_COLORSPACE_MATRIX'] = config.get(ini_section_name, 'TARGET_COLORSPACE_MATRIX')
		ini_values[ini_section_name]['TARGET_COLORSPACE_MATRIX_S'] = config.get(ini_section_name, 'TARGET_COLORSPACE_MATRIX_S')
		ini_values[ini_section_name]['TARGET_COLORSPACE_MATRIX_I'] = config.get(ini_section_name, 'TARGET_COLORSPACE_MATRIX_I')
		ini_values[ini_section_name]['TARGET_COLOR_TRANSFER'] = config.get(ini_section_name, 'TARGET_COLOR_TRANSFER')
		ini_values[ini_section_name]['TARGET_COLOR_TRANSFER_S'] = config.get(ini_section_name, 'TARGET_COLOR_TRANSFER_S')
		ini_values[ini_section_name]['TARGET_COLOR_TRANSFER_I'] = config.get(ini_section_name, 'TARGET_COLOR_TRANSFER_I')
		ini_values[ini_section_name]['TARGET_COLOR_PRIMARIES'] = config.get(ini_section_name, 'TARGET_COLOR_PRIMARIES')
		ini_values[ini_section_name]['TARGET_COLOR_PRIMARIES_S'] = config.get(ini_section_name, 'TARGET_COLOR_PRIMARIES_S')
		ini_values[ini_section_name]['TARGET_COLOR_PRIMARIES_I'] = config.get(ini_section_name, 'TARGET_COLOR_PRIMARIES_I')
		ini_values[ini_section_name]['TARGET_COLOR_RANGE'] = config.get(ini_section_name, 'TARGET_COLOR_RANGE')
		ini_values[ini_section_name]['TARGET_COLOR_RANGE_S'] = config.get(ini_section_name, 'TARGET_COLOR_RANGE_S')
		ini_values[ini_section_name]['TARGET_COLOR_RANGE_I'] = config.get(ini_section_name, 'TARGET_COLOR_RANGE_I')
		ini_values[ini_section_name]['TARGET_WIDTH'] = config.getint(ini_section_name, 'TARGET_WIDTH')
		ini_values[ini_section_name]['TARGET_HEIGHT'] = config.getint(ini_section_name, 'TARGET_HEIGHT')
		ini_values[ini_section_name]['TARGET_FPSNUM'] = config.getint(ini_section_name, 'TARGET_FPSNUM')
		ini_values[ini_section_name]['TARGET_FPSDEN'] = config.getint(ini_section_name, 'TARGET_FPSDEN')
		ini_values[ini_section_name]['MIN_DURATION_SEC'] = config.getfloat(ini_section_name, 'MIN_DURATION_SEC')
		ini_values[ini_section_name]['MAX_DURATION_SEC'] = config.getint(ini_section_name, 'MAX_DURATION_SEC')
		ini_values[ini_section_name]['MAX_VIDEO_CLIP_DURATION'] = config.getint(ini_section_name, 'MAX_VIDEO_CLIP_DURATION')
		ini_values[ini_section_name]['BOX'] = config.getboolean(ini_section_name, 'BOX')
		ini_values[ini_section_name]['ADD_SUBTITLE'] = config.getboolean(ini_section_name, 'ADD_SUBTITLE')
		ini_values[ini_section_name]['UPSIZE_KERNEL'] = config.get(ini_section_name, 'UPSIZE_KERNEL')
		ini_values[ini_section_name]['DOWNSIZE_KERNEL'] = config.get(ini_section_name, 'DOWNSIZE_KERNEL')
	else:
		print(f'ERROR: .ini file unable to be read or recreated properly',flush=True)
		sys.exit(1)
	# save the updated set of .ini values over the top of the existing set
	with open(ini_file_speciying_parameters, 'w') as configfile:
		# add the new set of .ini value to be saved
		update_config =  configparser.ConfigParser(allow_no_value=True)
		update_config[ini_section_name] = default_ini_values[ini_section_name]
		# add example values to make it easier for a human reader of the .ini file
		tmp_name = 'Enum_vs.MatrixCoefficients'
		tmp_dict = { tmp_name : {}}
		for v in vs.MatrixCoefficients:
			tmp_dict[tmp_name][str(v)] = int(v)+0
			pass
		update_config[tmp_name] = tmp_dict[tmp_name]
		tmp_name = 'Enum_vs.TransferCharacteristics'
		tmp_dict = { tmp_name : {}}
		for v in vs.TransferCharacteristics:
			tmp_dict[tmp_name][str(v)] = int(v)+0
			pass
		update_config[tmp_name] = tmp_dict[tmp_name]
		tmp_name = 'Enum_vs.ColorPrimaries'
		tmp_dict = { tmp_name : {}}
		for v in vs.ColorPrimaries:
			tmp_dict[tmp_name][str(v)] = int(v)+0
			pass
		update_config[tmp_name] = tmp_dict[tmp_name]
		tmp_name = 'Enum_vs.ColorRange'
		tmp_dict = { tmp_name : {}}
		for v in vs.ColorRange:
			tmp_dict[tmp_name][str(v)] = int(v)+0
			pass
		update_config[tmp_name] = tmp_dict[tmp_name]
		# update the .ini file
		update_config.write(configfile)
	print(f'INFO: Saved updated .ini "{ini_file_speciying_parameters}"')
	# calculate some values and create a new updated calculated values dict
	calc_ini = ini_values[ini_section_name]
	calc_ini['PIC_EXTENSIONS']		= [".png", ".jpg", ".jpeg", ".gif", ".pdf"]								# always lower case
	calc_ini['VID_EXTENSIONS']		= [".mp4", ".mpeg4", ".mpg", ".mpeg", ".avi", ".mjpeg", ".3gp", ".mov"]	# always lower case
	calc_ini['EEK_EXTENSIONS']		= [".m2ts"]														# always lower case
	calc_ini['VID_EEK_EXTENSIONS']	= calc_ini['VID_EXTENSIONS'] + calc_ini['EEK_EXTENSIONS']
	calc_ini['EXTENSIONS']			= calc_ini['PIC_EXTENSIONS'] + calc_ini['VID_EXTENSIONS'] + calc_ini['EEK_EXTENSIONS']
	calc_ini['TARGET_PIXEL_FORMAT']	= vs.YUV420P8				# pixel format of the target video
	calc_ini['DG_PIXEL_FORMAT']		= vs.YUV420P16				# pixel format of the video for use by DG tools
	calc_ini['TARGET_FPS']			= round(calc_ini['TARGET_FPSNUM'] / calc_ini['TARGET_FPSDEN'], 3)
	calc_ini['BLANK_CLIP_LENGTH']	= int(math.ceil(0.1*calc_ini['TARGET_FPS']))	# leading and trailing blank clip duration in frames with round-up. int(round(0.1*calc_ini['TARGET_FPS'])) will round up/down
	calc_ini['MIN_DURATION_FRAMES']	= int(math.ceil(calc_ini['MIN_DURATION_SEC'] * calc_ini['TARGET_FPS']))	### duration of display of an image, in frames
	calc_ini['MAX_DURATION_FRAMES']	= int(math.ceil(calc_ini['MAX_DURATION_SEC'] * calc_ini['TARGET_FPS']))	### max duration of display of a video, in frames
	calc_ini['DOT_FFINDEX']			= ".ffindex".lower()		# for removing temporary *.ffindex files at the end
	calc_ini['MODX']				= 2	   # mods for letterboxing calculations, example, for 411 YUV as an extreme
	calc_ini['MODY']				= 2	   # mods would have to be MODX=4, MODY=1 as minimum

	########################################################################################################################################################
	if calc_ini['RECURSIVE']:
		glob_var="**/*.*"			# recursive
		ff_glob_var="**/*.ffindex"	# for .ffindex file deletion recursive
	else:
		glob_var="*.*"				# non-recursive
		ff_glob_var="*.ffindex"		# for .ffindex file deletion non-recursive
	# glob : with DIRECTORY not having a trailing slash !!!
	print(f'INFO: Processing "{calc_ini["DIRECTORY"]}" recursive="{calc_ini["RECURSIVE"]}" glob_var="{glob_var}" \n      with Extensions={objPrettyPrint.pformat(calc_ini["EXTENSIONS"])}',flush=True)
	Count_of_files = 0
	# NOTE: calc_ini['DIRECTORY'] MUST NOT have a trailing backslash ... remove during ini setup
	paths = Path(calc_ini['DIRECTORY']).glob(glob_var) # generator of all paths in a directory, files starting with . won't be matched by default
	path = get_path(paths)	#pre-fetch first path
	if path is None:
		raise ValueError(f'Extensions: {calc_ini["EXTENSIONS"]}, not found in "{calc_ini["DIRECTORY"]}"')
	blank_clip = core.std.BlankClip(format=calc_ini['TARGET_PIXEL_FORMAT'], width=calc_ini['TARGET_WIDTH'], height=calc_ini['TARGET_HEIGHT'], length=calc_ini['BLANK_CLIP_LENGTH'], color=(16,128,128))	 # notice no colorspace,"range" etc can be specified
	clips = blank_clip	# initialize the accumulated clips with a starting small blank clip
	if calc_ini['CROSSFADE_DURATION']>0:	
		crossfade_blank_clip = blank_clip[0]*calc_ini['MIN_DURATION_FRAMES'] if len(blank_clip)<calc_ini['MIN_DURATION_FRAMES'] else blank_clip
		prior_clip_for_crossfade = crossfade_blank_clip
	#---
	while not (path is None):	# first clip already pre-retrieved ready for this while loop
		Count_of_files = Count_of_files + 1
		print(f'DEBUG: processing {Count_of_files} {str(path)}',flush=True)
		#if (Count_of_files % 10)==0:
		#	print(f'{Count_of_files},',end="",flush=True)
		#	if (Count_of_files % (10*10*3))==0:
		#		print(f'',flush=True)
		this_clip = get_clip(path)
		#this_clip = core.text.Text(this_clip, text_subpath_for_subtitles, alignment=9, scale=1)
		#this_clip = core.text.FrameNum(this_clip, alignment=2, scale=1)
		#this_clip = core.text.ClipInfo(this_clip, alignment=8, scale=1)
		#this_clip = core.text.FrameProps(this_clip, alignment=2, scale=1)
		if calc_ini['CROSSFADE_DURATION']>0:	
			#print(f'DEBUG: doing crossfade in while loop',flush=True)
			crossfade_clip = crossfade(prior_clip_for_crossfade, this_clip, calc_ini['CROSSFADE_DURATION'])
			# for now, don't do equivalent of this from _AI_ ... right  = right_clip[calc_ini['CROSSFADE_DURATION']:-calc_ini['CROSSFADE_DURATION']]
			clips = clips + crossfade_clip + this_clip
			prior_clip_for_crossfade = this_clip
		else:
			clips = clips + this_clip
		path = get_path(paths)		# get next path to process in this while loop
	#---
	# perhaps a finishing crossfade to black ?
	if calc_ini['CROSSFADE_DURATION']>0:	
		#print(f'DEBUG: doing final crossfade after while loop',flush=True)
		crossfade_clip = crossfade(prior_clip_for_crossfade, crossfade_blank_clip, calc_ini['CROSSFADE_DURATION'])
		# for now, don't do equivalent of this from _AI_ ... right  = right_clip[calc_ini['CROSSFADE_DURATION']:-calc_ini['CROSSFADE_DURATION']]
		clips = clips + crossfade_clip + this_clip
	clips = clips + blank_clip		# end the accumulated clips with a finishing small blank clip
	clips = clips.std.AssumeFPS(fpsnum=calc_ini['TARGET_FPSNUM'], fpsden=calc_ini['TARGET_FPSDEN'])
	print(f'',flush=True)
	print(f'INFO: Finished processing {Count_of_files} image/video files.',flush=True)
	# Cleanup any temporary .ffindex files created by ffms2
	print(f'DEBUG: Removing temporary *.ffindex files from folder "{calc_ini["DIRECTORY"]}" with recursive="{calc_ini["RECURSIVE"]}" ...',flush=True)
	pp = calc_ini['DIRECTORY'] + "/" + ff_glob_var
	ffindex_files = glob.glob(pp, recursive=calc_ini['RECURSIVE'])
	Count_of_files_removed = 0
	for ff in ffindex_files:
		if ff.lower()[-len(calc_ini['DOT_FFINDEX']):] == calc_ini['DOT_FFINDEX']:	# double check the file really does have ext .ffindex
			try:
				Count_of_files_removed = Count_of_files_removed + 1
				print(f'DEBUG: removing {Count_of_files_removed} {ff}',flush=True)
				os.remove(ff)
				#if (Count_of_files_removed % (10))==0:
				#	print(f'{Count_of_files_removed},',end="",flush=True)
				#	if (Count_of_files_removed % (10*10*3))==0:
				#		print(f'',flush=True)
			except OSError as ee:
				print(f'Error: %s : %s' % (ff, ee.strerror),flush=True)
	print(f'',flush=True)
	print(f'INFO: Finished removing {Count_of_files_removed} .ffindex files.',flush=True)
	# hmm, audio ? maybe later using source filter "bas" ?
	#print(f'DEBUG: Done.',flush=True)
	clips.set_output()
	#------
