# MORE Good Stuff #2 from \_AI\_   
## to produce an .mp4 slideshow from a vapoursynth script and ffmpeg   
### A work in progress.   

See these from \_AI\_   
https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page2#post2678789   
https://github.com/UniversalAl/load    


For now, perhaps use something like:   
```
python "\path_to\main_encode.py" "\path_to\video_script.vpy" "\path_to\audio_script_or_file.vpy" "\path_to\slideshow.mp4"
```

We could, of course, forego the `main_encode.py` thing and just use vspipe/ffmpeg directly ourselves.   
May even end up like that in a batch script which we usually create, it allows finer control all in one place :)   

Note:   
- temporary audio and video files are created in the current-working-folder
- under development, it may only create the intermediate video/audio file(s) and not the final "\path_to\slideshow.mp4"
- the load thingy has a gui ... we aren't into that, only cli, so will look at fiddling with that later ...
