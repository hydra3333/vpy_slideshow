# vpy_slideshow
### a python/vapoursynth script consumed by ffmpeg
### to produce an .mp4 slideshow from images and video clips.

It works, after a fashion.  As an example only.

But don't use this as it's a terrible hack-up of good stuff provided by \_AI\_ in thread   
https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio 

\_AI\_ has shown different stuff in   
https://forum.videohelp.com/threads/408230-ffmpeg-avc-from-jpgs-of-arbitrary-dimensions-maintaining-aspect-ratio/page2#post2678789  and   https://github.com/UniversalAl/load   
which caused me to change my thinking and not use .vpy directly into standalone python/vapoursynth/ffmpeg, and instead install python (ugh, I avoid installers) and try it that way instead since it appears to be more flexible. Yes, there'd a be also need for vspipe and piping as runtime however other things are simplified eg pip and whatnot.

For info only, after we install python, pip is missing.   
Depending on the o/s and whatnot that can be difficult to fix.   
We get around it by first using portable pip to install real pip and then we're away.   
We **ALWAYS ALWAYS ONLY** run the stuff below as Administrator to ensure it all gets installed into a global place, otherwise it will be installed on a per-user basis into temporary per-user folders :(
```
ECHO ONLY ONLY ONLY EVER RUN THIS AS ADMIN !!!!
ECHO ONLY ONLY ONLY EVER RUN THIS AS ADMIN !!!!
ECHO ONLY ONLY ONLY EVER RUN THIS AS ADMIN !!!!

pause

pushd d:\temp
REM A trick for new players, I install vapoursynth into the same folder as extracted portable Python x64 and it had no pip to install Pillow.
REM Some googled instructions on how to install pip didn't work.
REM Ended up using portable pip, run in the same folder as the extracted portable python, and it works:
REM 
REM Code:
REM https://packaging.python.org/en/latest/tutorials/installing-packages/#ensure-you-can-r...e-command-line
REM https://pip.pypa.io/en/latest/installation/
del "pip.pyz"
c:\software\wget\wget.exe -v -t 1 --server-response --timeout=360 -nd -np -nH --no-cookies --output-document="pip.pyz" "https://bootstrap.pypa.io/pip/pip.pyz"
python pip.pyz --help
python pip.pyz install pip
popd

python -m pip --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager pip

python -m pip --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager --use-pep517 pip-review

pip3 cache purge
pip3 --no-cache-dir list
pip3 list --outdated

REM install latest certificates for python requests.get
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager certifi 
REM cffi NEEDS to get done BEFORE sudo pip3 --no-cache-dir check
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager cffi
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager numpy
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager pillow
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager pathlib 
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager pymediainfo
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager sockets
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager requests
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager datetime
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager packaging
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager setuptools
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager python-utils
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager progressbar2
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager pyyaml
pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager html5lib
REM pip3 --no-cache-dir install --upgrade --check-build-dependencies --force-reinstall --upgrade-strategy eager https://github.com/yt-dlp/yt-dlp/archive/master.zip

REM auto-install everything we missed
pip3 cache purge
pip3 --no-cache-dir list
pip3  --no-cache-dir list --outdated
pip3  --no-cache-dir check

pip-review --verbose
pip-review --verbose --auto --continue-on-fail
```
