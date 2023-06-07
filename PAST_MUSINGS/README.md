# vpy_slideshow   
### a python/vapoursynth script consumed by ffmpeg   
### to produce a 'HD' .mp4 slideshow from images and video clips.   
no audio, at this stage
___
### \_AI\_ has elegant code which works with audio   
#### please go here to review \_AI\_ code instead of this git:      
https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page2#post2678789   and   https://github.com/UniversalAl/load  
___

___
### under development 
___

# NONE OF THIS IS WORKING   
# DO NOT TRY TO USE   


This GIT nearly works, after a fashion.  As an example only.   
No, it's currently broken again.   
No, it nearly works again.

But don't use this as it's a terrible hack-up of good stuff provided by \_AI\_ in thread   
https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio 


### Installation (x64 only)

Look at this url in a browser: https://github.com/hydra3333/vpy_slideshow   
Notice file `Setup.bat`   
And other files 
```SLIDESHOW_PARAMETERS.ini
vpy_slideshow.bat
vpy_slideshow.vpy
vs_transitions.py
```

#### 1. Create a fresh directory
Create a new empty directory somewhere with a reasonable bit of free disk space. Say, 5-25Gb not that you will use all of that.   
eg `D:\slideshow`   

#### 2. Create a fresh install of portable Python and portable Vapoursynth and pip dependencies and VSREPO dependencues
Note:   
Many people are wary of downloading exe files etc.   
If you are too, look in `Setup.bat` to gather what you need to manually download and unzip and put where;
and what `portable pip` and `vsrepo` commands you need to do in a dos window when cd'd into the right directories.   

Download `Setup.bat` with this link https://raw.githubusercontent.com/hydra3333/vpy_slideshow/main/Setup.bat and
save it into the fresh new directory you created above.   

Download the ubuquitous wget with this link https://eternallybored.org/misc/wget/1.21.3/64/wget.exe and
save it into the fresh new directory you created above.  Wget will be used to download stuff like portable Python,
portable VapourSynth, a recent ffmpeg build, and the other files necessary to make a slideshow.
Nothing gets "installed", everything is just all files in the directory tree under the fresh new directory you created above. Except for pip module installs ... pip puts bits of them (eg dependencies which get collected) in your username's temporary folder, i.e. something like `C:\Users\your_username\AppData\Local\Temp`, instead of where we tell pip to install the module for which the collecting is occurring.    

Double-click on `Setup.bat` to run it.
A DOS window should pop up showing all the downloads and pip's and vsrepo's and unzips as they happen.   

When `Setup.bat` is finished, you should see all of the files in the directory tree in and under the directory you created above.
These give you   
- portable Python x64 (3.11.2 last time I looked)   
- portable Vapoursynth x64 (R62 last time I looked, depends on python 3.11.x)   
- relevant Python x64 pip dependencies   
- relevant Vapoursynth vsrepo x64 dependencies   
- a few files necessary to run the vpy_slideshow   

### Configuration and Running

There's a few ways to do this.   

All options involve editing one or more files in the fresh directory you created above.   

We're OK for a thousand or so images/videos in a directory tree per run; doing that manually with a gui tool may be somewhat tedious, especially if you need to rearrange files and re-run.  
This is *VERY SLOW* though; let it run overnight.   

#### Configuration and Running Option 1 - editing `vpy_slideshow.bat`   

In your favourite text editor (notepad++ ?) edit file `vpy_slideshow.bat`.   
Don't be afraid, it's easy.   
Find the area that looks a bit like this:   
```
set "output_mp4_file=%vs_CD%vpy_slideshow.2005-2006.mp4"
DEL "%ini_file%">NUL 2>&1
IF NOT EXIST "%ini_file%" (
	echo [slideshow]>>"%ini_file%"
	echo directory_list = ['G:\\DVD\\PAT-SLIDESHOWS\\2005', 'G:\\DVD\\PAT-SLIDESHOWS\\2006' ]>>"%ini_file%"
	echo temp_directory_list = ['.\\temp',]>>"%ini_file%"
	REM echo temp_directory_list = ['D:\\TEMP',]>>"%ini_file%"
	echo recursive = True>>"%ini_file%"
	echo duration_pic_sec = 4.0>>"%ini_file%"
	echo duration_max_video_sec = 15.0>>"%ini_file%"
	echo duration_crossfade_secs = 0.5>>"%ini_file%"
	echo subtitle_depth = 3>>"%ini_file%"
	echo debug_mode = False>>"%ini_file%"
	echo silent_mode = False>>"%ini_file%"
	echo crossfade_type = random>>"%ini_file%"
	echo crossfade_direction = left>>"%ini_file%"
	type "%ini_file%"
)
```
Notice a REM statement means that line is "commented out" and thus does not have any effect.   
Change values as you see fit. 

_At a minimum:_   
Change the filename of the HD .mp4 file that will be created from `vpy_slideshow.1TEST.mp4` to whatever you like.   
Change `directory_list` to whatever directory is at the top of a directory tree containing your images/videos; you can specify multiple directory trees; notice **double-backslashes are mandatory or a result may not happen**.   

_Optionally:_   
You can leave `temp_directory_list` alone or change it to another directory where scratch files can temporarily go.   
Then,   
`recursive` to False if you only want to processs the one folder and not all its subfolders.   
`duration_pic_sec` to how long each image gets displayed (including transitions).   
`duration_max_video_sec` to the maximum time you wish a video to be shown in the slideshow (from its start).   
`duration_crossfade_secs` to the time a transition change takes (1/2 a second is about right).   
`subtitle_depth` to the subtitling depth of each image/video (how many directory tree names and the filename); Set to 0 to disable.   
`crossfade_type` to one of the values shown; `random` is usually a good choise.   
`crossfade_direction` for `curtain_` type crossfades use horizintal or vertical, for the rest of the types use one of left,right,up,down.   

Save the changes to you made to `vpy_slideshow.bat`.   

Double-click on `vpy_slideshow.bat` and wait a very long time.   

At the end you'll see 2 new files   
(a) a .mp4 mainly for use on PCs and with casting, and   
(b) a .mpg which can be burned to DVD.   
There's no audio.  Another day we may add a facility to add audio, but not yet.   

#### Configuration and Running Option 2 - editing `SLIDESHOW_PARAMETERS.ini`   

In your favourite text editor (notepad++ ?) edit file `SLIDESHOW_PARAMETERS.ini`.  
Don't be afraid, it's easy. There's an explanation of each parameter in the file just above its setting.   
A bit like option 1, change the parameters to suit yourself, then save your changes.   
Remember, double-backslashes are **mandatory** or a result may not happen.   
Locate file `run_slideshow_from_ini_settings.bat` an double-click on it and wait a very long time. Check for error messages in case you accidentally edited something incorrectly.   

At the end you'll see 2 new files   
(a) a .mp4 mainly for use on PCs and with casting, and   
(b) a .mpg which can be burned to DVD.   
The output .mp4 and .mpg filenames are "fixed" and will be over-written the next time you run it via this option.   
There's no audio.  Another day we may add a facility to add audio, but not yet.   

#### Configuration and Running Option 3 - editing `SLIDESHOW_PARAMETERS.ini` and rolling your own   

Like Option 2, edit file `SLIDESHOW_PARAMETERS.ini` and save your changes.   
Look at file `run_slideshow_from_ini_settings.bat` as a template, to create your own `.bat` with your own ffmpeg settings etc.   
Run your own `.bat`.   

___
### of no possible interest to anyone

I ran the 'show_unique_properties' thing over our archive of home pics and videos, and found a variety of cameras used. Each camera probably had its own issues with, and settings for, video and image properties.

```
 'EXIF_Model': '',
 'EXIF_Model': '<KENOX S630  / Samsung S630>',
 'EXIF_Model': '1234',
 'EXIF_Model': '5300',
 'EXIF_Model': '5800 Xpres',
 'EXIF_Model': '5MP-9Q3',
 'EXIF_Model': '6120c',
 'EXIF_Model': '6288',
 'EXIF_Model': '6300',
 'EXIF_Model': 'A411',
 'EXIF_Model': 'C4100Z,C4000Z',
 'EXIF_Model': 'C8080WZ',
 'EXIF_Model': 'Canon DIGITAL IXUS 430',
 'EXIF_Model': 'Canon DIGITAL IXUS 50',
 'EXIF_Model': 'Canon DIGITAL IXUS 500',
 'EXIF_Model': 'Canon DIGITAL IXUS 980 IS',
 'EXIF_Model': 'Canon DIGITAL IXUS v3',
 'EXIF_Model': 'Canon EOS-1D',
 'EXIF_Model': 'Canon EOS-1D X',
 'EXIF_Model': 'Canon EOS-1Ds Mark II',
 'EXIF_Model': 'Canon EOS 10D',
 'EXIF_Model': 'Canon EOS 200D',
 'EXIF_Model': 'Canon EOS 20D',
 'EXIF_Model': 'Canon EOS 20D\x00',
 'EXIF_Model': 'Canon EOS 300D DIGITAL',
 'EXIF_Model': 'Canon EOS 30D',
 'EXIF_Model': 'Canon EOS 350D DIGITAL',
 'EXIF_Model': 'Canon EOS 40D',
 'EXIF_Model': 'Canon EOS 550D',
 'EXIF_Model': 'Canon EOS 5D',
 'EXIF_Model': 'Canon EOS 60D',
 'EXIF_Model': 'Canon EOS 6D',
 'EXIF_Model': 'Canon EOS 7D',
 'EXIF_Model': 'Canon EOS DIGITAL REBEL',
 'EXIF_Model': 'Canon EOS DIGITAL REBEL XT',
 'EXIF_Model': 'Canon EOS DIGITAL REBEL XTi',
 'EXIF_Model': 'Canon EOS Kiss Digital N',
 'EXIF_Model': 'Canon MG3600 series Network',
 'EXIF_Model': 'Canon PowerShot A3100 IS',
 'EXIF_Model': 'Canon PowerShot A3200 IS',
 'EXIF_Model': 'Canon PowerShot A3200 IS\x00\x00\x00\x00\x00\x00\x00',
 'EXIF_Model': 'Canon PowerShot A400',
 'EXIF_Model': 'Canon PowerShot A520',
 'EXIF_Model': 'Canon PowerShot A570 IS',
 'EXIF_Model': 'Canon PowerShot A620',
 'EXIF_Model': 'Canon PowerShot A720 IS',
 'EXIF_Model': 'Canon PowerShot A75',
 'EXIF_Model': 'Canon PowerShot A80',
 'EXIF_Model': 'Canon PowerShot A95',
 'EXIF_Model': 'Canon PowerShot A95\x00',
 'EXIF_Model': 'Canon PowerShot G5',
 'EXIF_Model': 'Canon PowerShot G6',
 'EXIF_Model': 'Canon PowerShot S1 IS',
 'EXIF_Model': 'Canon PowerShot S2 IS',
 'EXIF_Model': 'Canon PowerShot S3 IS',
 'EXIF_Model': 'Canon PowerShot S50',
 'EXIF_Model': 'CONTAX i4R    ',
 'EXIF_Model': 'COOLPIX P530',
 'EXIF_Model': 'COOLPIX P600',
 'EXIF_Model': 'COOLPIX S6100',
 'EXIF_Model': 'CYBERSHOT',
 'EXIF_Model': 'DC-3305    ',
 'EXIF_Model': 'Digimax 201',
 'EXIF_Model': 'DiMAGE A1',
 'EXIF_Model': 'DiMAGE Z5',
 'EXIF_Model': 'DMC-FT2',
 'EXIF_Model': 'DMC-FT3',
 'EXIF_Model': 'DMC-FT5',
 'EXIF_Model': 'DMC-FT6',
 'EXIF_Model': 'DMC-FX7',
 'EXIF_Model': 'DMC-FX8',
 'EXIF_Model': 'DMC-FZ30',
 'EXIF_Model': 'DMC-TS2',
 'EXIF_Model': 'DMC-TS3',
 'EXIF_Model': 'DSC-H2',
 'EXIF_Model': 'DSC-H5',
 'EXIF_Model': 'DSC-N1',
 'EXIF_Model': 'DSC-P10',
 'EXIF_Model': 'DSC-P92',
 'EXIF_Model': 'DSC-P93',
 'EXIF_Model': 'DSC-RX100',
 'EXIF_Model': 'DSC-T7',
 'EXIF_Model': 'DSC-TX20',
 'EXIF_Model': 'DSC-W1',
 'EXIF_Model': 'DSC-W40',
 'EXIF_Model': 'DSLR-A100',
 'EXIF_Model': 'DYNAX 5D',
 'EXIF_Model': 'E-300',
 'EXIF_Model': 'E-300           ',
 'EXIF_Model': 'E-500           ',
 'EXIF_Model': 'E-500           \x00',
 'EXIF_Model': 'E-510           ',
 'EXIF_Model': 'E4500',
 'EXIF_Model': 'E5653\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
 'EXIF_Model': 'E5700',
 'EXIF_Model': 'E5900',
 'EXIF_Model': 'E65',
 'EXIF_Model': 'E8700',
 'EXIF_Model': 'FinePix F50fd  ',
 'EXIF_Model': 'FinePix L30',
 'EXIF_Model': 'FinePix S5600  ',
 'EXIF_Model': 'FinePix S9100',
 'EXIF_Model': 'GT-C5510',
 'EXIF_Model': 'GT-I9100',
 'EXIF_Model': 'GT-I9100\x00',
 'EXIF_Model': 'GT-I9305T',
 'EXIF_Model': 'HERO4 Silver',
 'EXIF_Model': 'HERO7 Black\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
 'EXIF_Model': 'HP pstc6100',
 'EXIF_Model': 'HTC Desire',
 'EXIF_Model': 'iPad',
 'EXIF_Model': 'iPhone 3GS',
 'EXIF_Model': 'iPhone 4',
 'EXIF_Model': 'iPhone 5c',
 'EXIF_Model': 'iPhone 6',
 'EXIF_Model': 'iPhone 6 Plus',
 'EXIF_Model': 'iPhone 6s',
 'EXIF_Model': 'iPhone SE (2nd generation)',
 'EXIF_Model': 'iPhone X',
 'EXIF_Model': 'KODAK CX6330 ZOOM DIGITAL CAMERA',
 'EXIF_Model': 'KODAK EASYSHARE C1013 DIGITAL CAMERA',
 'EXIF_Model': 'KODAK EASYSHARE DX3700 Digital Camera',
 'EXIF_Model': 'KS360',
 'EXIF_Model': 'MG6200 series',
 'EXIF_Model': 'MP270 series',
 'EXIF_Model': 'my411X',
 'EXIF_Model': 'NIKON D200',
 'EXIF_Model': 'NIKON D50',
 'EXIF_Model': 'NIKON D70',
 'EXIF_Model': 'NIKON D70\x00',
 'EXIF_Model': 'NIKON D7000',
 'EXIF_Model': 'NIKON D70s',
 'EXIF_Model': 'NIKON D7200',
 'EXIF_Model': 'NIKON D80',
 'EXIF_Model': 'NIKON D800',
 'EXIF_Model': 'Omni-vision OV9655-SXGA',
 'EXIF_Model': 'OPPO A72',
 'EXIF_Model': 'PENTAX *ist DS     ',
 'EXIF_Model': 'PENTAX Optio 33LF',
 'EXIF_Model': 'PENTAX Optio WP',
 'EXIF_Model': 'Perfection V600',
 'EXIF_Model': 'Portable Scanner',
 'EXIF_Model': 'RS4110Z     ',
 'EXIF_Model': 'S8300',
 'EXIF_Model': 'SAMSUNG ES30/VLUU '
 'EXIF_Model': 'SLP1000SE',
 'EXIF_Model': 'SM-A520F',
 'EXIF_Model': 'SM-G900I',
 'EXIF_Model': 'SM-G925I',
 'EXIF_Model': 'SM-G935F',
 'EXIF_Model': 'SM-G955F',
 'EXIF_Model': 'SM-G973F',
 'EXIF_Model': 'SM-G975F',
 'EXIF_Model': 'SM-J100Y',
 'EXIF_Model': 'SM-J250G',
 'EXIF_Model': 'ST66 / ST68',
 'EXIF_Model': 'Sx500A',
 'EXIF_Model': 'T4_T04',
 'EXIF_Model': 'u20D,S400D,u400D',
 'EXIF_Model': 'u30D,S410D,u410D',
 'EXIF_Model': 'u790SW,S790SW   ',
 'EXIF_Model': 'uD800,S800      ',
 'EXIF_Model': 'Unknown',
 'EXIF_Model': 'VG140,D715      ',
 'EXIF_Model': 'Z610i',
{'EXIF_Model': 'Canon EOS 300D DIGITAL',
{'EXIF_Model': 'KODAK Z740 ZOOM DIGITAL CAMERA',
{'EXIF_Model': 'Sony Visual Communication Camera', 'EXIF_Software': 'ArcSoft WebCam Companion 3', 'EXIF_Copyright': 'ArcSoft Inc.'}
```
