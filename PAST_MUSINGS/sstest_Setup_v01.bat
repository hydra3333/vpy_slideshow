@echo on

REM
REM    <MappedFolder>
REM      <HostFolder>D:\ssTEST</HostFolder>
REM      <SandboxFolder>C:\HOST_ssTEST</SandboxFolder>
REM      <ReadOnly>false</ReadOnly>
REM    </MappedFolder>
REM

mkdir C:\ssTEST
mkdir C:\TEMP

REM Create a .bat to Download MABS and extract it onto the sandbox system
set "f=%USERPROFILE%\Desktop\000-RUNME_init_ssTEST.bat"
DEL "%f%">NUL 2>&1
echo @ECHO ON >> "%f%"
echo mkdir C:\ssTEST >> "%f%"
echo mkdir C:\MULTIMEDIA\2021.06.14-Pat.and.Ted-Photos >> "%f%"
echo mkdir C:\TEMP >> "%f%"
echo subst d: /D >> "%f%"
echo subst d: c:\ >> "%f%"
echo CD C:\TEMP >> "%f%"
echo copy /Y C:\host_software\wget\wget.exe C:\ssTEST >> "%f%"
echo REM download and extract ssTEST >> "%f%"
echo curl -L --verbose --output "C:\TEMP\sstest.zip" https://github.com/hydra3333/vpy_slideshow/archive/refs/heads/main.zip >> "%f%"
echo powershell -NoLogo -ExecutionPolicy Unrestricted -Sta -NonInteractive -WindowStyle Normal -command "Expand-Archive -Force -LiteralPath 'C:\TEMP\sstest.zip' -DestinationPath C:\TEMP" >> "%f%"
echo xcopy C:\TEMP\vpy_slideshow-main\*.* C:\ssTEST\ /e /v /f /h /r /y >> "%f%"
echo xcopy C:\HOST_ssTEST\TEST_VIDS_IMAGES\0TEST\*.* C:\ssTEST\TEST_VIDS_IMAGES\0TEST\ /e /v /f /h /r /y >> "%f%"
echo xcopy C:\HOST_ssTEST\TEST_VIDS_IMAGES\1TEST\*.* C:\ssTEST\TEST_VIDS_IMAGES\1TEST\ /e /v /f /h /r /y >> "%f%"
echo xcopy C:\HOST_ssTEST\TEST_VIDS_IMAGES\2TEST_rotations\*.* C:\ssTEST\TEST_VIDS_IMAGES\2TEST_rotations\ /e /v /f /h /r /y >> "%f%"
echo xcopy C:\HOST_ssTEST\TEST_VIDS_IMAGES\SlideshowMusic\*.* C:\ssTEST\TEST_VIDS_IMAGES\SlideshowMusic\ /e /v /f /h /r /y >> "%f%"
echo xcopy C:\HOST_ssTEST\TEST_VIDS_IMAGES\TEST_SLIDESHOW_IMAGES\*.* C:\ssTEST\TEST_VIDS_IMAGES\TEST_SLIDESHOW_IMAGES\ /e /v /f /h /r /y >> "%f%"
echo pause >> "%f%"
echo goto :eof >> "%f%"

REM Create a .bat to save any .vpy and .bat results of runnng ssTEST back in the sandbox system onto the host system
set "f=%USERPROFILE%\Desktop\111-SAVE_ssTEST.bat"
DEL "%f%">NUL 2>&1
echo @ECHO ON >> "%f%"
echo REM THE FOLLOWING IS TO SAVE ssTEST .bat and .vpy back to the non-sandbox host>> "%f%"
echo copy /Y C:\ssTEST\*.bat  C:\HOST_ssTEST\ >> "%f%"
echo copy /Y C:\ssTEST\*.vpy  C:\HOST_ssTEST\ >> "%f%"
echo pause >> "%f%"
echo goto :eof >> "%f%"

REM Create a link on the sandbox desktop which is mapped to our read-only SOFTWARE folder on the host system
REM which contains our set of downloaded software that we use all the time. ie make it available in the sandbox.
set create_shortcut_SCRIPT="%TEMP%\create_HOST_software_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\HOST software.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\host_software\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "HOST software" >> %create_shortcut_SCRIPT%
echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
echo oLink.Save >> %create_shortcut_SCRIPT%
cscript /nologo %create_shortcut_SCRIPT%
del %create_shortcut_SCRIPT%

REM Create a link on the sandbox desktop which is mapped to the local copy of vscode on the sandbox
REM set create_shortcut_SCRIPT="%TEMP%\create_vscode_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
REM del %create_shortcut_SCRIPT%
REM echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
REM echo sLinkFile = "%USERPROFILE%\Desktop\VScode.lnk" >> %create_shortcut_SCRIPT%
REM echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
REM echo oLink.TargetPath = "C:\software\vscode\Code.exe" >> %create_shortcut_SCRIPT%
REM echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
REM echo oLink.Description = "VScode" >> %create_shortcut_SCRIPT%
REM echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
REM echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
REM echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
REM echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
REM echo oLink.Save >> %create_shortcut_SCRIPT%
REM cscript /nologo %create_shortcut_SCRIPT%
REM del %create_shortcut_SCRIPT%

REM Create a link on the sandbox desktop which is mapped to our read-write ssTEST folder on the host system
REM which is where we will eventually copy the results of running ssTEST. i.e. the newly built ffmpeg.exe etc
set create_shortcut_SCRIPT="%TEMP%\create_HOST_ssTEST_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\HOST ssTEST.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\HOST_ssTEST\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "HOST ssTEST" >> %create_shortcut_SCRIPT%
echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
echo oLink.Save >> %create_shortcut_SCRIPT%
cscript /nologo %create_shortcut_SCRIPT%
del %create_shortcut_SCRIPT%

REM Create a link on the sandbox desktop which is mapped to our read-only MULTIMEDIA\2021.06.14-Pat.and.Ted-Photos folder on the host system
set create_shortcut_SCRIPT="%TEMP%\create_HOST_2021.06.14-Pat.and.Ted-Photos_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\HOST_HOST_2021.06.14-Pat.and.Ted-Photos.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\HOST_2021.06.14-Pat.and.Ted-Photos\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "HOST MULTIMEDIA_2021.06.14-Pat.and.Ted-Photos" >> %create_shortcut_SCRIPT%
echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
echo oLink.Save >> %create_shortcut_SCRIPT%
cscript /nologo %create_shortcut_SCRIPT%
del %create_shortcut_SCRIPT%

REM Create a link on the sandbox desktop which is mapped to the folder in which we build ssTEST in the local sandbox system
set create_shortcut_SCRIPT="%TEMP%\create_ssTEST_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\ssTEST.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\ssTEST\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "ssTEST" >> %create_shortcut_SCRIPT%
echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
echo oLink.Save >> %create_shortcut_SCRIPT%
cscript /nologo %create_shortcut_SCRIPT%
del %create_shortcut_SCRIPT%

REM Create a link on the sandbox desktop which is mapped to a local TEMP folder in the local sandbox system
set create_shortcut_SCRIPT="%TEMP%\create_TEMP_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\TEMP.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\TEMP\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "TEMP" >> %create_shortcut_SCRIPT%
echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
echo oLink.Save >> %create_shortcut_SCRIPT%
cscript /nologo %create_shortcut_SCRIPT%
del %create_shortcut_SCRIPT%

REM change explorer View settings to be as we like them
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V AlwaysShowMenus /T REG_DWORD /D 00000001 /F
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V SeparateProcess /T REG_DWORD /D 00000001 /F
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V NavPaneExpandToCurrentFolder /T REG_DWORD /D 00000001 /F
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V NavPaneShowAllFolders /T REG_DWORD /D 00000001 /F
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V HideFileExt /T REG_DWORD /D 00000000 /F
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V Hidden /T REG_DWORD /D 00000001 /F
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V ShowSuperHidden /T REG_DWORD /D 00000001 /F
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V ShowEncryptCompressedColor /T REG_DWORD /D 00000001 /F
REG Add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /V ShowStatusBar /T REG_DWORD /D 00000001 /F

REM add "Edit with Notepad++" to right click context pop-up
REM ... Notepad++ is located in the host's SOFTWARE\NPP folder
set fnpp="C:\TEMP\EDIT_WITH_NPP.REG"
del %fnpp%
ECHO Windows Registry Editor Version 5.00                     > %fnpp%
ECHO.                                                        >> %fnpp%
ECHO [HKEY_CLASSES_ROOT\*\shell\Edit with Notepad++]         >> %fnpp%
REM ECHO "Icon"="C:\\SOFTWARE\\NPP\\notepad++.exe"
ECHO "Icon"="C:\\HOST_SOFTWARE\\NPP\\notepad++.exe"               >> %fnpp%
ECHO [HKEY_CLASSES_ROOT\*\shell\Edit with Notepad++\command] >> %fnpp%
REM ECHO @="\"C:\\SOFTWARE\\NPP\\notepad++.exe\" \"%%1\""
ECHO @="\"C:\\HOST_SOFTWARE\\NPP\\notepad++.exe\" \"%%1\""        >> %fnpp%
regedit /s %fnpp%

REM restart explorer so that eveything appears including on the desktop
taskkill /f /im explorer.exe
start explorer.exe

REM start an explorer window at the specified directory
explorer.exe "C:\ssTEST\"

goto :eof
