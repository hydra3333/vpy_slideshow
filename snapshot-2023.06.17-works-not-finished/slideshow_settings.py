settings = {
	'ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS':	[
													r'D:\ssTEST\TEST_VIDS_IMAGES\0TEST',
													#r'D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania\Angela',
													#r'D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania\Dave',
													#r'D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania\Patricia',
												],	# a list, one or more folders to look in for slideshow pics/videos. the r in front of the string is CRITICAL
	'RECURSIVE':	True,		# case sensitive: whether to recurse the source folder(s) looking for slideshow pics/videos
	'TEMP_FOLDER':	r'G:\ssTEST\TEMP',		# folder where temporary files go; USE A DISK WITH LOTS OF SPARE DISK SPACE - CIRCA 6 GB PER 100 PICS/VIDEOS
	'BACKGROUND_AUDIO_INPUT_FOLDER':	r'D:\ssTEST\BACKGROUND_AUDIO_INPUT_FOLDER',		# Folder containing audio files (in sequence) to make an audio background track (it is not looped if too short). No files = silent background.
	'FINAL_MP4_WITH_AUDIO_FILENAME':	r'D:\ssTEST\slideshow.FINAL_MP4_WITH_AUDIO.TEST_ONLY.mp4',		# the filename of the FINAL slideshow .mp4
	#'FINAL_MP4_WITH_AUDIO_FILENAME':	r'D:\ssTEST\slideshow.FINAL_MP4_WITH_AUDIO.Angela.mp4',		# the filename of the FINAL slideshow .mp4
	#'FINAL_MP4_WITH_AUDIO_FILENAME':	r'D:\ssTEST\slideshow.FINAL_MP4_WITH_AUDIO.Dave.mp4',		# the filename of the FINAL slideshow .mp4
	#'FINAL_MP4_WITH_AUDIO_FILENAME':	r'D:\ssTEST\slideshow.FINAL_MP4_WITH_AUDIO.Patricia.mp4',		# the filename of the FINAL slideshow .mp4
	'SUBTITLE_DEPTH':	0,		# how many folders deep to display in subtitles; use 0 for no subtitling
	'SUBTITLE_FONTSIZE':	18,		# fontsize for subtitles, leave this alone unless confident
	'SUBTITLE_FONTSCALE':	1.0,		# fontscale for subtitles, leave this alone unless confident
	'DURATION_PIC_SEC':	3.0,		# in seconds, duration each pic is shown in the slideshow
	'DURATION_CROSSFADE_SECS':	0.5,		# in seconds duration crossfade between pic, leave this alone unless confident
	'CROSSFADE_TYPE':	'random',		# random is a good choice, leave this alone unless confident
	'CROSSFADE_DIRECTION':	'left',		# Please leave this alone unless really confident
	'DURATION_MAX_VIDEO_SEC':	7200.0,		# in seconds, maximum duration each video clip is shown in the slideshow
	'TARGET_AUDIO_BACKGROUND_NORMALIZE_HEADROOM_DB':	-18,		# normalize background audio to this maximum db
	'TARGET_AUDIO_BACKGROUND_GAIN_DURING_OVERLAY':	-30,		# how many DB to reduce backround audio during video clip audio overlay
	'TARGET_AUDIO_SNIPPET_NORMALIZE_HEADROOM_DB':	-12,		# normalize video clip audio to this maximum db; camera vids are quieter so gain them
	'MAX_FILES_PER_CHUNK':	150,		# how many images/videos to process in each chunk (more=slower)
	'DEBUG':	True,		# see and regret seeing, ginormous debug output
	'FFMPEG_PATH':	r'D:\ssTEST\Vapoursynth_x64\ffmpeg.exe',		# Please leave this alone unless really confident
	'FFPROBE_PATH':	r'D:\ssTEST\Vapoursynth_x64\ffprobe.exe',		# Please leave this alone unless really confident
	'VSPIPE_PATH':	r'D:\ssTEST\Vapoursynth_x64\vspipe.exe',		# Please leave this alone unless really confident
	'FFMPEG_ENCODER':	'h264_nvenc',		# Please leave this alone unless really confident. One of ['libx264', 'h264_nvenc']. h264_nvenc only works on "nvidia 2060 Super" upward.
	'TARGET_RESOLUTION':	'4k',		# eg 1080p : One of ['1080p', '4k', '2160p'] only.
	#'TARGET_VIDEO_BITRATE':	'4.5M',		# Please leave this alone unless really confident. 4.5M is ok (HQ) for h.264 1080p25 slideshow material.
	'slideshow_CONTROLLER_path':	r'D:\ssTEST\slideshow_CONTROLLER.py',		# Please leave this alone unless really confident
	'slideshow_LOAD_SETTINGS_path':	r'D:\ssTEST\slideshow_LOAD_SETTINGS.py',		# Please leave this alone unless really confident
	'slideshow_ENCODER_legacy_path':	r'D:\ssTEST\slideshow_ENCODER_legacy.vpy',		# Please leave this alone unless really confident
}