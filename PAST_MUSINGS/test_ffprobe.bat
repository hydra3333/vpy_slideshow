@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions


set "vs_CD=%CD%"
if /I NOT "%vs_CD:~-1%" == "\" (set "vs_CD=%vs_CD%\")
set "pwd=%vs_CD%"

set "vs_temp=%vs_CD%temp"
if /I NOT "%vs_temp:~-1%" == "\" (set "vs_temp=%vs_temp%\")

set "vs_path=%vs_CD%Vapoursynth_x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

REM py_path and vs_path should ALWAYS be the same
set "py_path=%vs_path%"

set "py_exe=%py_path%python.exe"
set "ffmpeg_exe=%vs_path%ffmpeg.exe"
set "ffprobe_exe=%vs_path%ffprobe.exe"

set "script=%pwd%test_ffprobe.py"
set "log=%script%.log"

REM "%vs_path%python.exe" "%script%" "[ 'D:\\ssTEST\\TEST_VIDS_IMAGES\\0TEST', ]"  >>"%log%"
REM "%vs_path%python.exe" "%script%" "[ 'E:\\MULTIMEDIA', ]"  >>"%log%" 2>&1
"%vs_path%python.exe" "%script%"  >>"%log%" 2>&1
dir "%log%"

REM find unique occurrences of interesting properties in the fields of interest
REM https://www.computerhope.com/findstr.htm#:~:text=The%20findstr%20(short%20for%20find,specific%20string%20of%20plain%20text.

call :find_unique_thing "frame_rate"
call :find_unique_thing "tff"
call :find_unique_thing "interlace"
call :find_unique_thing "field"
call :find_unique_thing "display_aspect_ratio"
call :find_unique_thing "color_space"
call :find_unique_thing "color_matrix"
call :find_unique_thing "color_transfer"
call :find_unique_thing "color_primaries"
call :find_unique_thing "color_range"
call :find_unique_thing "c_matrix"
call :find_unique_thing "pix_fmt"
call :find_unique_thing "probe_score"
call :find_unique_thing "ERROR"
pause
goto :eof


:find_unique_thing
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions
echo.
set "f=%~1"
set "f=%f: =%"
set "f=%f:'=%"
set "f=%f:"=%"
set "f=%f:/=%"
set "f=%f:\=%"
set "f=%script%.unique.%f%.log"
@echo on
findstr /L /I /c:"%~1" "%log%" | sort /unique > "%f%"
@echo off
echo Unique "%~1"
type "%f%"
echo.
goto :eof






VIDEO STREAM examples:
'width': 1920,
'height': 1080,
'color_range': 'tv',
'color_space': 'bt709',
'color_transfer': 'bt709',
'color_primaries': 'bt709',
'field_order': 'progressive',
'chroma_location': 'left',
'display_aspect_ratio': '16:9'
'nb_frames': '220'
'r_frame_rate': '30/1',
'avg_frame_rate': '660000/22039',

'r_frame_rate': '30000/1001'
'r_frame_rate': '30000/1001'

'r_frame_rate': '50/1',
'avg_frame_rate': '50/1',

USUAL FRAME RATES
25/1
50/1
30000/1001 (29.970)
24000/1001 (23.976)


FORMAT:
'duration': '7.346333',
'bit_rate': '17458632',
			

obj_ffprobe.return_code = "0"
obj_ffprobe.dict = "{'programs': [],
 'streams': [{'index': 0,
              'codec_name': 'h264',
              'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
              'profile': 'High',
              'codec_type': 'video',
              'codec_tag_string': 'avc1',
              'codec_tag': '0x31637661',
              'width': 1920,
              'height': 1080,
              'coded_width': 1920,
              'coded_height': 1080,
              'closed_captions': 0,
              'film_grain': 0,
              'has_b_frames': 0,
              'sample_aspect_ratio': '1:1',
              'display_aspect_ratio': '16:9',
              'pix_fmt': 'yuv420p',
              'level': 40,
              'color_range': 'tv',
              'color_space': 'bt709',
              'color_transfer': 'bt709',
              'color_primaries': 'bt709',
              'field_order': 'progressive',
              'refs': 1,
              'is_avc': 'true',
              'nal_length_size': '4',
              'id': '0x1',
              'r_frame_rate': '30/1',
              'avg_frame_rate': '660000/22039',
              'time_base': '1/90000',
              'start_pts': 0,
              'start_time': '0.000000',
              'duration_ts': 661170,
              'duration': '7.346333',
              'bit_rate': '17198084',
              'bits_per_raw_sample': '8',
              'nb_frames': '220',
              'extradata_size': 26,
              'disposition': {'default': 1,
                              'dub': 0,
                              'original': 0,
                              'comment': 0,
                              'lyrics': 0,
                              'karaoke': 0,
                              'forced': 0,
                              'hearing_impaired': 0,
                              'visual_impaired': 0,
                              'clean_effects': 0,
                              'attached_pic': 0,
                              'timed_thumbnails': 0,
                              'captions': 0,
                              'descriptions': 0,
                              'metadata': 0,
                              'dependent': 0,
                              'still_image': 0},
              'tags': {'creation_time': '2022-11-16T00:18:30.000000Z', 'language': 'eng', 'handler_name': 'VideoHandle', 'vendor_id': '[0][0][0][0]'},
              'side_data_list': [{'side_data_type': 'Display Matrix',
                                  'displaymatrix': '\n00000000:            0       65536           0\n00000001:       -65536           0           0\n00000002:            0           0  1073741824\n',
                                  'rotation': -90}]},
             {'index': 1,
              'codec_name': 'aac',
              'codec_long_name': 'AAC (Advanced Audio Coding)',
              'profile': 'LC',
              'codec_type': 'audio',
              'codec_tag_string': 'mp4a',
              'codec_tag': '0x6134706d',
              'sample_fmt': 'fltp',
              'sample_rate': '48000',
              'channels': 2,
              'channel_layout': 'stereo',
              'bits_per_sample': 0,
              'initial_padding': 0,
              'id': '0x2',
              'r_frame_rate': '0/0',
              'avg_frame_rate': '0/0',
              'time_base': '1/48000',
              'start_pts': 0,
              'start_time': '0.000000',
              'duration_ts': 351232,
              'duration': '7.317333',
              'bit_rate': '256061',
              'nb_frames': '343',
              'extradata_size': 2,
              'disposition': {'default': 1,
                              'dub': 0,
                              'original': 0,
                              'comment': 0,
                              'lyrics': 0,
                              'karaoke': 0,
                              'forced': 0,
                              'hearing_impaired': 0,
                              'visual_impaired': 0,
                              'clean_effects': 0,
                              'attached_pic': 0,
                              'timed_thumbnails': 0,
                              'captions': 0,
                              'descriptions': 0,
                              'metadata': 0,
                              'dependent': 0,
                              'still_image': 0},
              'tags': {'creation_time': '2022-11-16T00:18:30.000000Z', 'language': 'eng', 'handler_name': 'SoundHandle', 'vendor_id': '[0][0][0][0]'}}],
 'format': {'filename': 'D:\\ssTEST\\TEST_VIDS_IMAGES\\2TEST_rotations\\20221116_111821.mp4',
            'nb_streams': 2,
            'nb_programs': 0,
            'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
            'format_long_name': 'QuickTime / MOV',
            'start_time': '0.000000',
            'duration': '7.346333',
            'size': '16032116',
            'bit_rate': '17458632',
            'probe_score': 100,
            'tags': {'major_brand': 'mp42',
                     'minor_version': '0',
                     'compatible_brands': 'isommp42',
                     'creation_time': '2022-11-16T00:18:30.000000Z',
                     'location': '+00.0000+000.0000/',
                     'location-eng': '+00.0000+000.0000/',
                     'com.android.version': '9'}}}"
obj_ffprobe.error_code = "0"
obj_ffprobe.error = ""

Container number of streams: 2

indices_video = [{'list_index': 0, 'stream_index': 0}]
indices_audio = [{'list_index': 1, 'stream_index': 1}]

First Video Stream: List entry number=[0] Container stream index=0
First Audio Stream: List entry number=[1] Container stream index=1




obj_ffprobe.dict = "{'programs': [],
 'streams': [{'index': 0,
              'codec_name': 'h264',
              'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
              'profile': 'High',
              'codec_type': 'video',
              'codec_tag_string': 'avc1',
              'codec_tag': '0x31637661',
              'width': 1920,
              'height': 1080,
              'coded_width': 1920,
              'coded_height': 1080,
              'closed_captions': 0,
              'film_grain': 0,
              'has_b_frames': 1,
              'sample_aspect_ratio': '1:1',
              'display_aspect_ratio': '16:9',
              'pix_fmt': 'yuv420p',
              'level': 52,
              'color_range': 'tv',
              'chroma_location': 'left',
              'field_order': 'progressive',
              'refs': 1,
              'is_avc': 'true',
              'nal_length_size': '4',
              'id': '0x1',
              'r_frame_rate': '50/1',
              'avg_frame_rate': '50/1',
              'time_base': '1/12800',
              'start_pts': 0,
              'start_time': '0.000000',
              'duration_ts': 158807552,
              'duration': '12406.840000',
              'bit_rate': '7143054',
              'bits_per_raw_sample': '8',
              'nb_frames': '620342',
              'extradata_size': 56,
              'disposition': {'default': 1,
                              'dub': 0,
                              'original': 0,
                              'comment': 0,
                              'lyrics': 0,
                              'karaoke': 0,
                              'forced': 0,
                              'hearing_impaired': 0,
                              'visual_impaired': 0,
                              'clean_effects': 0,
                              'attached_pic': 0,
                              'timed_thumbnails': 0,
                              'captions': 0,
                              'descriptions': 0,
                              'metadata': 0,
                              'dependent': 0,
                              'still_image': 0},
              'tags': {'language': 'und', 'handler_name': 'VideoHandler', 'vendor_id': '[0][0][0][0]', 'encoder': 'Lavc59.39.100 h264_nvenc'}},
             {'index': 1,
              'codec_name': 'aac',
              'codec_long_name': 'AAC (Advanced Audio Coding)',
              'profile': 'LC',
              'codec_type': 'audio',
              'codec_tag_string': 'mp4a',
              'codec_tag': '0x6134706d',
              'sample_fmt': 'fltp',
              'sample_rate': '48000',
              'channels': 2,
              'channel_layout': 'stereo',
              'bits_per_sample': 0,
              'initial_padding': 0,
              'id': '0x2',
              'r_frame_rate': '0/0',
              'avg_frame_rate': '0/0',
              'time_base': '1/48000',
              'start_pts': 0,
              'start_time': '0.000000',
              'duration_ts': 595527168,
              'duration': '12406.816000',
              'bit_rate': '256000',
              'nb_frames': '581572',
              'extradata_size': 2,
              'disposition': {'default': 1,
                              'dub': 0,
                              'original': 0,
                              'comment': 0,
                              'lyrics': 0,
                              'karaoke': 0,
                              'forced': 0,
                              'hearing_impaired': 0,
                              'visual_impaired': 0,
                              'clean_effects': 0,
                              'attached_pic': 0,
                              'timed_thumbnails': 0,
                              'captions': 0,
                              'descriptions': 0,
                              'metadata': 0,
                              'dependent': 0,
                              'still_image': 0},
              'tags': {'language': 'eng', 'handler_name': 'SoundHandler', 'vendor_id': '[0][0][0][0]'}}],
 'format': {'filename': 'T:\\HDTV\\VRDTVSP-Converted\\AFL-Sport-AFL-Championship_Season.2022-Round_20-Adelaide_Crows_v_Carlton.2022-07-30.mp4',
            'nb_streams': 2,
            'nb_programs': 0,
            'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
            'format_long_name': 'QuickTime / MOV',
            'start_time': '0.000000',
            'duration': '12406.840000',
            'size': '11492552950',
            'bit_rate': '7410462',
            'probe_score': 100,
            'tags': {'major_brand': 'isom', 'minor_version': '512', 'compatible_brands': 'isomiso2avc1mp41', 'encoder': 'Lavf59.29.100'}}}"
			