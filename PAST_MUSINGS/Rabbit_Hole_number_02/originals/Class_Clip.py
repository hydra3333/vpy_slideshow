class Clip:
    '''
	 FROM: https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page2#post2678789
	 
     Creates class that carries both vs.VideoNode and vs.AudioNode.
     Using the same syntax as for vs.VideoNode on this class object for: trim/slice, add, multiply or print,
     the same operation is also done to the audio at the same time
     examples:
     from vapoursynth import core
     video = core.lsmas.LibavSMASHSource('video.mp4')
     audio = core.bas.Source('video.mp4')
     clip = Clip(video, audio)
     clip = clip[0] + clip[20:1001] + clip[1500:2000] + clip[2500:]
     #clip = clip.trim(first=0, length=1) + clip.trim(firt=20, last=1000) + clip.trim(1500, length=500) + clip.trim(2500)
     clip = clip*2
     clip = clip + clip
     print(clip)
     clip.video.set_output(0)
     clip.audio.set_output(1)
     '''

    def __init__(self, video = None, audio=None, attribute_audio_path=None):
        self.video = video
        self.audio = audio
        if self.video is None:
            self.video = core.std.BlankClip()
        if self.audio is None:
            if attribute_audio_path is None:
                raise ValueError('argument attribute_audio_path is needed to get default audio for images (could be a really short video')
            attr_audio = core.bas.Source(attribute_audio_path)
            length = int(attr_audio.sample_rate/self.video.fps*self.video.num_frames)
            self.audio = attr_audio.std.BlankAudio(length=length)

    def trim(self, first=0, last=None, length=None):
        afirst  = self.to_samples(first)    if first  is not None else None
        alast   = self.to_samples(last+1)-1 if last   is not None else None
        alength = self.to_samples(length)   if length is not None else None
        return Clip( self.video.std.Trim(first=first, last=last, length=length),
                     self.audio.std.AudioTrim(first=afirst,last=alast,length=alength)
                    )
    def to_samples(self, frame):
        return int((self.audio.sample_rate/self.video.fps)*frame)

    def __add__(self, other):
        return Clip(self.video + other.video, self.audio + other.audio)

    def __mul__(self, multiple):
        return Clip(self.video*multiple, self.audio*multiple)

    def __getitem__(self, val):
        if isinstance(val, slice):
            if val.step is not None:
                raise ValueError('Using steps while slicing AudioNode together with VideoNode makes no sense')
            start = self.to_samples(val.start) if val.start is not None else None
            stop =  self.to_samples(val.stop)  if val.stop  is not None else None
            return Clip( self.video.__getitem__(val),
                         self.audio.__getitem__(slice(start,stop))
                         )
        elif isinstance(val, int):
            start = self.to_samples(val)
            stop = int(start + self.audio.sample_rate/self.video.fps)
            return Clip( self.video[val],
                         self.audio.__getitem__(slice(start,stop))
                         )        
    def __repr__(self):
        return '{}\n{}\n{}'.format('Clip():\n-------', repr(self.video), repr(self.audio))

    def __str__(self):
        return '{}\n{}\n{}'.format('Clip():\n-------', str(self.video), str(self.audio))