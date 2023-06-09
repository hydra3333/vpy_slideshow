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

global DEBUG
DEBUG = False
TERMINAL_WIDTH_3333 = 250
objPrettyPrint_3333 = pprint.PrettyPrinter(width=TERMINAL_WIDTH_3333, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc


# Based on ChatGPT, we are no longer using settings.json, we will use settings.py
# This will allow us to use descriptive comments in settings.py which a user must edit.
# If the user mucks up python syntax, we rely on the module crashing on import.

# What we are doing instead is to re-import settings.py every time load_settings() is called.
# Like this
#	import importlib
#	importlib.reload(mymodule)  # Reload the module


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

import pprint
TERMINAL_WIDTH_3333 = 250
objPrettyPrint_3333 = pprint.PrettyPrinter(width=TERMINAL_WIDTH_3333, compact=False, sort_dicts=False)	# facilitates formatting and printing of text and dicts etc


ee = r'd:\folder\file.txt'
ff = r'd:\\folder\\file.txt'
string_with_escaped_characters = 'escaped characters: \a\b\c'
# the format of this is STRICTLY : variable_name in quotes, value, annotation comment
a = [
	["a", 1, "# annotation a"],
	["b", 12.3, "# annotation b"],
	["c", ["item1", "item2", "item3", 1, 1.1, True, {"a": 1, "b": 2}, r'd:\temp\file.txt', [1, 2, 2.1, True]], "# annotation c"],
	["d", True, "# annotation d"],
	["e", r'd:\folder\file.txt', "# annotation d"],
	["f", r'd:\\folder\\file.txt', "# annotation d"],
	["ee", ee, "# annotation d"],
	["ff", ff, "# annotation d"],
	["string_with_escaped_characters", string_with_escaped_characters, " # string_with_escaped_characters"],
]
# and the resulting file from create_py_file_from_formatted_dict('test_result.py', a) will contain this text:
#settings = {
#	'a': 1,							 # annotation a
#	'b': 12.3,						  # annotation b
#	'c': ['item1', 'item2', 'item3', 1, 1.1, True, {'a': 1, 'b': 2}, r'd:\temp\file.txt', [1, 2, 2.1, True]],	# annotation c
#	'd': True,						  # annotation d
#	'e': r'd:\folder\file.txt',		  # annotation d
#	'f': r'd:\\folder\\file.txt',		# annotation d
#	'ee': r'd:\folder\file.txt',		 # annotation d
#	'ff': r'd:\\folder\\file.txt',	   # annotation d
#	'string_with_escaped_characters': r'escaped characters: \x07\x08\c',	# string_with_escaped_characters
#}
#--------
def create_py_file_from_formatted_dict(filename, a):
	def make_r_prefix(value):
		if isinstance(value, str):
			if  '\\' in repr(value):
				return 'r' + repr(value).replace('\\\\', '\\')
			else:
				return repr(value)
		elif isinstance(value, list):
			return '[' + ', '.join(make_r_prefix(item) for item in value) + ']'
		elif isinstance(value, dict):
			return '{' + ', '.join(f'{make_r_prefix(k)}: {make_r_prefix(v)}' for k, v in value.items()) + '}'
		elif isinstance(value, tuple):
			return '(' + ', '.join(make_r_prefix(item) for item in value) + ')'
		else:
			return repr(value)
	with open(filename, "w") as file:
		file.write("settings = {\n")
		for item in a:
			key, value, annotation = item
			file.write(f'\t{make_r_prefix(key)}: {make_r_prefix(value)},\t\t\t\t{annotation}\n')
		file.write("}\n")
#--------

create_py_file_from_formatted_dict('test_result.py', a)