"""
The final output will be a .mp4 file where the video component remains the same as the original video, 
but the audio component is full silence with sections replaced with audio snippets at positions 
corresponding to nominated video frame numbers. 
It calculates the start and end frames for each audio snippet based on the specified video frame numbers
and replaces the corresponding section of silence in the audio with the audio snippet. 
This way, the audio snippets are inserted into the audio track of the video at the desired positions.

Dependencies:
- moviepy: pip install moviepy
- ffmpeg: Download and install FFmpeg from https://ffmpeg.org/

Usage: python script.py video_path snippets_input_file destination_video_path
"""

#	set PYTHONPATH=.\Vapoursynth_x64
# or
#	import sys
#	sys.path.insert(0,".\Vapoursynth_x64")

import sys
import os
import re
import argparse
import pydub
import subprocess

# Path to the FFmpeg executable
FFMPEG_PATH = 'C:\\SOFTWARE\\ffmpeg\\ffmpeg.exe'

def normalize_path(path):
	# Replace single backslashes with double backslashes
	path = path.replace("\\", "\\\\")
	# Add double backslashes before any single backslashes
	path = path.replace("\\\\", "\\\\\\\\")
	return path

# Generate silent audio using FFmpeg
def generate_silent_padding(duration, silent_audio_path):
	print(f"generate_silent_padding: generate silent padding: silent_audio_path='{silent_audio_path}'",flush=True)
	ffmpeg_cmd = [
		FFMPEG_PATH,
		'-hide_banner',
		'-v', 'warning',
		'-nostats',
		'-threads', '2',
		'-f', 'lavfi',
		'-i', 'anullsrc',
		'-t', str(duration),
		'-c:a', 'libfdk_aac',
		'-b:a', '256k',
		'-ar', '48000',
		'-y',
		silent_audio_path
	]
	print(f"generate_silent_padding: ffmpeg_cmd='{ffmpeg_cmd}'",flush=True)
	try:
		subprocess.run(ffmpeg_cmd, check=True)
	except subprocess.CalledProcessError as e:
		print(f"Error: Failed to generate silent padding: {str(e)}",flush=True)
		sys.exit(1)

# Transcode audio to AAC using FFmpeg
def transcode_audio_to_aac(audio_file, output_file):
	print(f"transcode_audio_to_aac: generate silent padding: audio_file='{audio_file}' output_file='{output_file}'",flush=True)
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
	print(f"transcode_audio_to_aac: ffmpeg_cmd='{ffmpeg_cmd}'",flush=True)
	try:
		subprocess.run(ffmpeg_cmd, check=True)
	except subprocess.CalledProcessError as e:
		print(f"Error: Failed to transcode audio: {str(e)}",flush=True)
		sys.exit(1)

def normalize_path(path):
	# Replace single backslashes with double backslashes
	path = path.replace("\\", "\\\\")
	# Add double backslashes before any single backslashes
	path = path.replace("\\\\", "\\\\\\\\")
	return path

# Replace any audio in the video with audio interspersed with audio snippets specified in a file
def replace_audio_with_snippets_from_file(video_path, snippets_input_file, destination_video_path, background_audio_path=None):
	# Check if input file of snippets exists
	if not os.path.exists(snippets_input_file):
		print(f"Error: Input file of snippets '{snippets_input_file}' does not exist.",flush=True)
		sys.exit(1)

	# Check if video file exists
	if not os.path.exists(video_path):
		print(f"Error: Main video/audio file '{video_path}' does not exist.",flush=True)
		sys.exit(1)

	# Check if optional background audo file exists
	if background_audio_path and not os.path.exists(background_audio_path):
		print(f"Error: Specified background audio file '{background_audio_path}' does not exist.",flush=True)
		sys.exit(1)

	try:
		video_object = VideoFileClip(video_path)
	except Exception as e:
		print(f"Error: Failed to load Main video/audio file '{video_path}': {str(e)}",flush=True)
		sys.exit(1)

	try:
		with open(snippets_input_file, 'r') as file:
			lines = file.readlines()
	except IOError as e:
		print(f"Error: Failed to open or read Input file of snippets '{snippets_input_file}': {str(e)}",flush=True)
		sys.exit(1)

	total_snippets = len(lines)
	print(f"Total audio snippets: {total_snippets}",flush=True)

	# Generate or convert background audio to AAC format
	if background_audio_path:
		background_audio_aac_path = 'background_audio.aac'
		transcode_audio_to_aac(background_audio_path, background_audio_aac_path)
		try:
			audio_object = AudioFileClip(background_audio_aac_path)
		except Exception as e:
			print(f"Error: Failed to load background audio file '{background_audio_aac_path}': {str(e)}",flush=True)
			sys.exit(1)
		# Adjust background audio duration to match video duration
		if audio_object.duration < video_object.duration:
			silence_duration = video_object.duration - audio_object.duration
			generate_silent_padding(silence_duration, silent_audio_path)
			try:
				audio_object = AudioFileClip(silent_audio_path)
			except Exception as e:
				print(f"Error: Failed to load silent audio file '{silent_audio_path}': {str(e)}",flush=True)
				sys.exit(1)
		elif audio_object.duration > video_object.duration:
			#audio_object = audio_object[:video_object.duration]
			audio_object = audio_object.subclip(0, video_object.duration)
	else:
		# Generate silent audio
		silent_audio_path = 'silent_audio.aac'
		generate_silent_padding(video_object.duration, silent_audio_path)
		try:
			audio_object = AudioFileClip(silent_audio_path)
		except Exception as e:
			print(f"Error: Failed to load silent audio file '{silent_audio_path}': {str(e)}",flush=True)
			sys.exit(1)

	# line format: 1234 125 'D:\folder1\folder2\audio_snippet_001.m4a'
	for i, line in enumerate(lines):
		#line_parts = re.findall(r"(\d+)\s+(\d+)\s+'([^']*)'", line.strip())	# ChatGPT
		line_parts = re.findall(r"^(\d+)\s+(\d+)\s+'([^']+)'$", line.strip())	# https://stackoverflow.com/questions/76394785/python3-regex-pattern-to-separate-items-on-a-line
		
		#print(f"Snippet Line: {line}",flush=True)
		#print(f"Snippet Line Parts: {line_parts[0]}",flush=True)
		if len(line_parts) == 1:
			start_frame_for_replacement = int(line_parts[0][0])
			snippet_num_frames_to_replace = int(line_parts[0][1])
			snippet_path = normalize_path(line_parts[0][2])
			if start_frame_for_replacement <= 0 or snippet_num_frames_to_replace <=0:
				print(f"replace_audio_with_snippets_from_file: Invalid snippet frame number or number of frames. They must be positive integers.\nLine: {line}\nLine Parts: {line_parts[0]}",flush=True)
				sys.exit(1)
		else:
			print(f"replace_audio_with_snippets_from_file: Invalid snippet line format. It should contain at least 1 part.\nLine: {line}\nLine Parts: {line_parts[0]}", flush=True)
			sys.exit(1)
		#print(f"Snippet Video Frame Number: {start_frame_for_replacement}",flush=True)
		#print(f"Snippet Video Number of Frames: {snippet_num_frames_to_replace}",flush=True)
		#print(f"Snippet Path: {snippet_path}",flush=True)
	
		snippet_output = 'temp_snippet.aac'

		# Transcode audio snippet to AAC using FDK-AAC encoder
		transcode_audio_to_aac(snippet_path, snippet_output)
		try:
			audio_snippet = AudioFileClip(snippet_output)
		except Exception as e:
			print(f"Error: Failed to load audio snippet file '{snippet_output}': {str(e)}",flush=True)
			sys.exit(1)

		print(f"Replacing a piece of silent audio with snippet from: {snippet_path} at Start Frame: {start_frame_for_replacement}, for Number of Frames: {snippet_num_frames_to_replace}",flush=True)
		
		# Incoming from snippet file:
		#		start_frame_for_replacement
		#		snippet_num_frames_to_replace
		end_frame_for_replacement = start_frame_for_replacement + snippet_num_frames_to_replace

		start_time_for_replacement = start_frame_for_replacement / video_object.fps
		end_time_for_replacement = end_frame_for_replacement / video_object.fps
		
		audio_snippet = audio_snippet.subclip(0, snippet_num_frames_to_replace / audio_snippet.fps)

		# Convert AudioFileClip to AudioClip so we get the append method exposed
		#audio_object = audio_object.to_audioclip()
		#new_audio_object = audio_object.subclip(0, start_time_for_replacement)
		#new_audio_object = new_audio_object.append(audio_snippet)
		#new_audio_object = new_audio_object.append(audio_object.subclip(end_time_for_replacement))
		
		new_audio_object = audio_object.subclip(0, start_time_for_replacement)
		new_audio_object = new_audio_object.append(audio_snippet)
		new_audio_object = new_audio_object.append(audio_object.subclip(end_time_for_replacement))

		print(f"Processed audio snippet {i + 1}/{total_snippets}",flush=True)

	final_audio_path = 'output_audio.aac'
	try:
		new_audio_object.write_audiofile(final_audio_path, codec='copy')
	except Exception as e:
		print(f"Error: Failed to write audio file: {str(e)}",flush=True)
		sys.exit(1)

	mux_cmd = [
		FFMPEG_PATH,
		'-i', video_path,
		'-i', final_audio_path,
		'-map', '0:v',
		'-map', '1:a',
		'-c:v', 'copy',
		'-c:a', 'copy',
		'-movflags', '+faststart',
		'-y',
		destination_video_path
	]

	try:
		subprocess.run(mux_cmd, check=True)
	except subprocess.CalledProcessError as e:
		print(f"Error: Failed to mux audio and video: {str(e)}",flush=True)
		sys.exit(1)

	# Check if Destination file exists
	if not os.path.exists(destination_video_path):
		print(f"Error: Failed to write Resulting Destination file of video/audio: '{destination_video_path}'.",flush=True)
		sys.exit(1)

	# Clean up temporary files
	try:
		os.remove(snippet_output)
		os.remove(final_audio_path)
		os.remove(silent_audio_path)
	except Exception as e:
		print(f"Error: Failed to clean up temporary file(s) '{snippet_output}' '{silent_audio_path}' '{final_audio_path}': {str(e)}",flush=True)
		sys.exit(1)

	return destination_video_path

if __name__ == "__main__":
	if len(sys.argv) < 4:
		print("Usage: python script.py -i main_video_path.mp4 -s snippets_input_file.txt -o destination_video_path.mp4 -b background_music.m4a",flush=True)
		sys.exit(1)
	
	parser = argparse.ArgumentParser(description='Replace audio snippets in a video with silence and specified audio snippets.')
	parser.add_argument('-i', '--input', help='Main video/audio file path', required=True)
	parser.add_argument('-s', '--snippets', help='Snippets input file path', required=True)
	parser.add_argument('-o', '--output', help='Resulting Destinaton video/audio file path', required=True)
	parser.add_argument('-b', '--background', help='Background audio file path', required=False)
	args = parser.parse_args()

	video_path = args.input
	snippets_input_file = args.snippets
	destination_video_path = args.output
	background_audio_path = args.background

	print(f"Processing Main video/audio file: {video_path}",flush=True)
	print(f"Input file of snippets: {snippets_input_file}",flush=True)
	print(f"Resulting Destination file of video/audio: {destination_video_path}",flush=True)
	print(f"Background music: {background_audio_path}",flush=True)

	destination_video_path = replace_audio_with_snippets_from_file(video_path, snippets_input_file, destination_video_path, background_audio_path)

	print(f"Finished! Resulting Destination file of video/audio: {destination_video_path}",flush=True)
