settings = {
	'ROOT_FOLDER_SOURCES_LIST_FOR_IMAGES_PICS':	[r'D:\ssTEST\TEST_VIDS_IMAGES\0TEST', r'D:\ssTEST\TEST_VIDS_IMAGES\2TEST_rotations'],		# a list, one or more folders to look in for slideshow pics/videos
	'RECURSIVE':	True,		# case sensitive: whether to recurse the source folder(s) looking for slideshow pics/videos
	'ROOT_FOLDER_FOR_OUTPUTS':	r'D:\ssTEST',		# folder in which outputs are to be placed
	'TEMP_FOLDER':	r'D:\ssTEST\TEMP',		# folder where temporary files go ... use on a disk with LOTS of spare disk space !!
	'BACKGROUND_AUDIO_INPUT_FILENAME':	r'D:\ssTEST\background_audio_pre_snippet_editing.m4a',		# specify a .m4a audio file ifg you want a background track (it is not looped if too short)
	'FINAL_MP4_WITH_AUDIO_FILENAME':	r'D:\ssTEST\slideshow.FINAL_MP4_WITH_AUDIO_FILENAME.mp4',		# the filename of the FINAL slideshow .mp4
	'SUBTITLE_DEPTH':	3,		# how many folders deep to display in subtitles; use 0 for no subtitling
	'SUBTITLE_FONTSIZE':	18,		# fontsize for subtitles, leave this alone unless confident
	'SUBTITLE_FONTSCALE':	1.0,		# fontscale for subtitles, leave this alone unless confident
	'DURATION_PIC_SEC':	3.0,		# in seconds, duration each pic is shown in the slideshow
	'DURATION_CROSSFADE_SECS':	0.5,		# in seconds duration crossfade between pic, leave this alone unless confident
	'CROSSFADE_TYPE':	'random',		# random is a good choice, leave this alone unless confident
	'CROSSFADE_DIRECTION':	'left',		# Please leave this alone unless really confident
	'DURATION_MAX_VIDEO_SEC':	7200.0,		# in seconds, maximum duration each video clip is shown in the slideshow
	'DEBUG':	True,		# see and regret seeing, ginormous debug output
}
