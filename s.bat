@echo on
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

set "vs_CD=%CD%"
if /I NOT "%vs_CD:~-1%" == "\" (set "vs_CD=%vs_CD%\")

set "vs_temp=%vs_CD%temp"
if /I NOT "%vs_temp:~-1%" == "\" (set "vs_temp=%vs_temp%\")

set "vs_path=%vs_CD%Vapoursynth_x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

REM set "git_path=%vs_CD%PortableGit_x64"
REM if /I NOT "%git_path:~-1%" == "\" (set "git_path=%git_path%\")

REM py_path and vs_path should ALWAYS be the same as should PYTHONPATH
set "py_path=%vs_path%"
set "PYTHONPATH=%py_path%"

set "py_exe=%py_path%python.exe"
set "ffmpeg_exe=%vs_path%ffmpeg.exe"
set "mediainfo_exe=%vs_path%mediainfo.exe"

ECHO DO NOT NOT ever run this as admin %%%% or it will install python stuff into an inaccessible admin user's folder
ECHO DO NOT NOT ever run this as admin %%%% or it will install python stuff into an inaccessible admin user's folder
ECHO DO NOT NOT ever run this as admin %%%% or it will install python stuff into an inaccessible admin user's folder

IF NOT EXIST "%vs_CD%wget.exe" (
	echo Also, Please download wget.exe into this folder "%vs_CD%" first.
	echo Exiting without success.
	pause
	exit
)

CD "%py_path%"
set "PYTHONPATH=!vs_path!"


REM "%py_exe%" pip.pyz uninstall pydub --verbose
REM "%py_exe%" -m pip_review --verbose --auto --continue-on-fail 

REM "%py_exe%" pip.pyz install pydub --target=%vs_path% --no-cache-dir --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose

"%py_exe%" pip.pyz install python-dotenv --target=%vs_path% --no-cache-dir --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --verbose

REM del /f "%vs_temp%pydub.zip"
REM "%vs_CD%wget.exe" -v -t 1 --server-response --no-check-certificate --timeout=360 -nd -np -nH --no-cookies --output-document="%vs_temp%pydub.zip" https://github.com/jiaaro/pydub/archive/refs/heads/master.zip
REM rmdir /s /q "%vs_path%pydub\"
REM dir /b "%vs_path%pydub"
REM "%vs_path%7za.exe" e -y -aoa "%vs_temp%pydub.zip" -o"%vs_path%pydub" "pydub-master\pydub\*"
REM dir /s "%vs_path%pydub"


CD "%vs_CD%"
pause
exit
