import load
'''
Then tha main loop code to work with clips, you had it a bit different, but just how it works with that class Clip():

Code also needs to define attribute video filepath that vapoursynth would get audio parameters from for quiet audio (if image is loaded). For some reason I cannot change samplerate from integer to float and cannot set default BlankAudio with float.
	Code:
	ATTRIBUTE_AUDIO_PATH = r'D:\test2\some_very_short_video.m2ts'
'''

LOADER = load.Sources()
paths = Path(DIRECTORY).glob("*.*")
path = get_path(paths)
if path is None:
    raise ValueError(f'Extensions: {EXTENSIONS}, not found in {DIRECTORY}')
clips = get_clip(path)    #loads obj class Clip() ! not vs.VideoNode
print('wait ...')
while 1:
    path = get_path(paths)
    if path is None:
        break
    clip = get_clip(path)   #again , it always loads obj class Clip(), not vs.VideoNode
    clips += clip  #class Clip() can add, where internally it adds video and audio

clips.video.set_output(0)
clips.audio.set_output(1)