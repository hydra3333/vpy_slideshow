import vapoursynth as vs
from vapoursynth import core
core = vs.core
import sys
import os
import importlib
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

# Ensure we can import modules from ".\" by adding the current default folder to the python path.
# (tried using just PYTHONPATH environment variable but it was unreliable)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

global TERMINAL_WIDTH					# for use by PrettyPrinter
TERMINAL_WIDTH = 250
global objPrettyPrint
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc

import load_settings_3333
global settings_module
global DEBUG
DEBUG = False

def normalize_path(path):
	if DEBUG: print(f"DEBUG: normalize_path:  incoming path='{path}'",flush=True)
	# Replace single backslashes with double backslashes
	path = path.rstrip(os.linesep).strip('\r').strip('\n').strip()
	r1 = r'\\'
	r2 = r1 + r1
	r4 = r2 + r2
	path = path.replace(r1, r4)
	# Add double backslashes before any single backslashes
	for i in range(0,20):
		path = path.replace(r2, r1)
	if DEBUG: print(f"DEBUG: normalize_path: outgoing path='{path}'",flush=True)
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
	#	print(repr(converted_string),flush=True)
	# yields 'D:\\a\\b\\c\\d\\e\\f\\filename.txt'
	new_file_name = os.path.abspath(file_name).rstrip(os.linesep).strip('\r').strip('\n').strip()
	if new_file_name.endswith('\\'):
		new_file_name = new_file_name[:-1]  # Remove trailing backslash
	new_file_name = normalize_path(new_file_name)
	return new_file_name

# ------------------------------------------------------------------------------------------------------

#SLIDESHOW_SETTINGS_MODULE_NAME = 'settings_3333'

import load_settings_3333


# read the user-edited settings from SLIDESHOW_SETTINGS_MODULE_NAME (settings.py)
#if SLIDESHOW_SETTINGS_MODULE_NAME not in sys.modules:
#	# Import the module dynamically, if it is not done already
#	try:
#		settings_module = importlib.import_module(SLIDESHOW_SETTINGS_MODULE_NAME)
#	except ImportError as e:
#		# Handle the ImportError if the module cannot be imported
#		print(f"load_settings: ERROR: ImportError, failed to dynamically import user specified Settings from import module: '{SLIDESHOW_SETTINGS_MODULE_NAME}'\n{str(e)}",flush=True,file=sys.stderr)
#		sys.exit(1)	
#	except Exception as e:
#		print(f"load_settings: ERROR: Exception, failed to dynamically import user specified Settings from import module: '{SLIDESHOW_SETTINGS_MODULE_NAME}'\n{str(e)}",flush=True,file=sys.stderr)
#		sys.exit(1)	
#else:
#	# Reload the module since it had been dynamically loaded already ... remember, global variables in thee module are not scrubbed by reloading
#	try:
#		#importlib.invalidate_caches()
#		importlib.reload(settings_module)
#	except Exception as e:
#		print(f"load_settings: ERROR: Exception, failed to RELOAD user specified Settings from import module: '{SLIDESHOW_SETTINGS_MODULE_NAME}'\n{str(e)}",flush=True,file=sys.stderr)
# retrieve the settigns from SLIDESHOW_SETTINGS_MODULE_NAME (settings.py)
#user_specified_settings_dict = settings_module.settings
#print(f"loaded user_specified_settings_dict=\n{user_specified_settings_dict}\n\n",flush=True)

print(f'\nCalling load_settings_3333.load_settings()\n',flush=True)

settings_dict, old_ini_dict, old_calc_ini_dict = load_settings_3333.load_settings()	# this will force reload of 'setup.py' from the current default folder

print(f'\nReturned from load_settings_3333.load_settings()\n',flush=True)

print(f'settings_dict=\n{objPrettyPrint.pformat(settings_dict)}\n',flush=True)
print(f'old_ini_dict=\n{objPrettyPrint.pformat(old_ini_dict)}\n',flush=True)
print(f'old_calc_ini_dict=\n{objPrettyPrint.pformat(old_calc_ini_dict)}\n',flush=True)

print(f'Finished successfully.\n',flush=True)

# ------------------------------------------------------------------------------------------------------

