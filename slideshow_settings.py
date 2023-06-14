settings = {
	'ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS':	[
													r'D:\ssTEST\TEST_VIDS_IMAGES\0TEST', 
													#r'D:\ssTEST\TEST_VIDS_IMAGES\2022-11-Tasmania_renamed\ORIGINALS',
													#r'D:\ssTEST\TEST_VIDS_IMAGES\2TEST_rotations', 
												],	# a list, one or more folders to look in for slideshow pics/videos. the r in front of the string is CRITICAL
	'RECURSIVE':	True,		# case sensitive: whether to recurse the source folder(s) looking for slideshow pics/videos
	'ROOT_FOLDER_FOR_OUTPUTS':	r'D:\ssTEST',		# folder in which outputs are to be placed
	'TEMP_FOLDER':	r'G:\ssTEST\TEMP',		# folder where temporary files go; USE A DISK WITH LOTS OF SPARE DISK SPACE - CIRCA 6 GB PER 100 PICS/VIDEOS
	'BACKGROUND_AUDIO_INPUT_FILENAME':	r'D:\ssTEST\background_audio_pre_snippet_editing.m4a',		# Use the word None to generate a silence background, or specify a .m4a audio file if you want a background track (it is not looped if too short)
	'FINAL_MP4_WITH_AUDIO_FILENAME':	r'D:\ssTEST\slideshow.TEST.LEVEL.BITRATE.mp4',		# the filename of the FINAL slideshow .mp4
	'SUBTITLE_DEPTH':	0,		# how many folders deep to display in subtitles; use 0 for no subtitling
	'SUBTITLE_FONTSIZE':	18,		# fontsize for subtitles, leave this alone unless confident
	'SUBTITLE_FONTSCALE':	1.0,		# fontscale for subtitles, leave this alone unless confident
	'DURATION_PIC_SEC':	3.0,		# in seconds, duration each pic is shown in the slideshow
	'DURATION_CROSSFADE_SECS':	0.5,		# in seconds duration crossfade between pic, leave this alone unless confident
	'CROSSFADE_TYPE':	'random',		# random is a good choice, leave this alone unless confident
	'CROSSFADE_DIRECTION':	'left',		# Please leave this alone unless really confident
	'DURATION_MAX_VIDEO_SEC':	7200.0,		# in seconds, maximum duration each video clip is shown in the slideshow
	'TARGET_AUDIO_BACKGROUND_NORMALIZE_HEADROOM_DB':	-16,		# normalize background audio to this maximum db
	'TARGET_AUDIO_BACKGROUND_GAIN_DURING_OVERLAY':	-28,		# how many DB to reduce backround audio during video clip audio overlay
	'TARGET_AUDIO_SNIPPET_NORMALIZE_HEADROOM_DB':	-6,		# normalize video clip audio to this maximum db
	'MAX_FILES_PER_CHUNK':	100,	# how many images/videos to process in each chunk (more=slower)
	'DEBUG':	True,		# see and regret seeing, ginormous debug output
	'FFMPEG_PATH':	r'D:\ssTEST\Vapoursynth_x64\ffmpeg.exe',		# Please leave this alone unless really confident
	'FFPROBE_PATH':	r'D:\ssTEST\Vapoursynth_x64\ffprobe.exe',		# Please leave this alone unless really confident
	'VSPIPE_PATH':	r'D:\ssTEST\Vapoursynth_x64\vspipe.exe',		# Please leave this alone unless really confident
	'slideshow_CONTROLLER_path':	r'D:\ssTEST\slideshow_CONTROLLER.py',		# Please leave this alone unless really confident
	'slideshow_LOAD_SETTINGS_path':	r'D:\ssTEST\slideshow_LOAD_SETTINGS.py',		# Please leave this alone unless really confident
	'slideshow_ENCODER_legacy_path':	r'D:\ssTEST\slideshow_ENCODER_legacy.vpy',		# Please leave this alone unless really confident
}
