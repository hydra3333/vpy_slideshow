import pairs
ATTRIBUTE_AUDIO_PATH = r'D:\test2\some_very_short_video.m2ts'

def get_clip(path):
    #get video
    data = LOADER.get_data([str(path),])[0] 
    video = data.clip
    if data.load_isError:
        raise ValueError(f'{data.load_log}\nload.py could not create vs.VideoNode from {path}')
    video = rotation_check(video, path, save_rotated_image=SAVE_ROTATED_IMAGES)
    video = video.std.AssumeFPS(fpsnum=FPSNUM, fpsden=FPSDEN)
    if BOX:  video = boxing(video, WIDTH, HEIGHT)
    else:    video = resize_clip(video, WIDTH, HEIGHT)
    video = video[0]*LENGTH if len(video)<5 else video
    
    #get_audio
    try:
        audio = core.bas.Source(str(path))
    except AttributeError:
        raise ImportError('Vapoursynth audio source plugin "BestAudioSource.dll" could not be loaded\n'
                          'download: https://github.com/vapoursynth/bestaudiosource/releases/tag/R1')
    except vs.Error as e:
        print(f'BestAudioSource could not load audio for: {path}\n{e}')
        clip = pairs.Clip(video, attribute_audio_path=ATTRIBUTE_AUDIO_PATH) #will generate quiet clip with desired parameters
    except Exception as e:
        print(f'Error loading audio for: {path}\n{e}')
        clip = pairs.Clip(video, attribute_audio_path=ATTRIBUTE_AUDIO_PATH)
    else:
        clip = pairs.Clip(video, audio)    
    return clip