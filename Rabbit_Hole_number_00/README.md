# to produce an .mp4 slideshow from ffmpeg -concat
### ReSize images with ffmpeg to produce an .mp4 slideshow and a DVD .mpg

See https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page2#post2682862    

It doesn't really work.   

Parses a source folder tree and convert images to a slideshow, PAL 25fps    
Also parse full folder name to grab the rightmost foldername and use that
as the destination as well as the filename for the video.   

In explorer, drag and drop a folder name onto the .bat    

There remain real issues, per 
https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page2#post2682862

eg    

Uses native ffmpeg "-f concat" using the "scale" and "pad" filters ... HOWEVER
as soon as it saw an odd dimension then the image was stretched either 
horizontally or vertically no matter what options I tried ... and I tried a lot.    

It is also less than forgiving by delivering bt470gb colorspace etc and
inconsistent "range" (TV or PC) perhaps depending on the first image it encountered.    

Plenty of advice on the net with basically the same options however 
the authors must not have tried a range of old and new and odd-dimensioned images.    

I did not spend enough time to find out how to subtitle each image with aspects of its path and name.    

Ended up giving up on ffmpeg -f concat et al directly, and moving to using
irfanview to resize all the images correctly and THEN using ffmpeg -f concat on those
using an input file of filenames.    

Still issues with delivered inconsistent colorspace etc and inconsistent
"range" (TV or PC) but better than it was.     

Also still not looked into subtitle each image with aspects of its path and name.    

And there's no possibility of including the first few seconds of any video clips
(of arbitrary sizes, eg old/new/portrait/landscape etc) in the mix.    
