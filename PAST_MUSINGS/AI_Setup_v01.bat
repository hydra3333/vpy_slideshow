@echo on
mkdir C:\AI
mkdir C:\000-tasmania-renamed
mkdir C:\TEMP

REM Create a Initialization bat to run after the sandbox has fired up, for the user to double-click on in the sandbox
set "f=%USERPROFILE%\Desktop\000-INIT.bat"
DEL "%f%">NUL 2>&1
echo @ECHO ON >> "%f%"
echo mkdir C:\AI >> "%f%"
echo mkdir C:\000-tasmania-renamed\ >> "%f%"
echo mkdir C:\TEMP >> "%f%"
echo CD C:\TEMP >> "%f%"
REM echo copy /Y C:\host_software\wget\wget.exe C:\AI\ >> "%f%"
echo xcopy C:\HOST_AI\*.* C:\AI\ /e /v /f /h /r /y >> "%f%"
echo xcopy C:\HOST_000-tasmania-renamed\*.* C:\000-tasmania-renamed\ /e /v /f /h /r /y >> "%f%"
echo pause >> "%f%"
echo goto :eof >> "%f%"

REM Create a .bat to save any .py .vpy .bat results of runnng AI back in the sandbox system onto the host system
REM won't work for the moment, as we set C:\AI to readonly 
set "f=%USERPROFILE%\Desktop\111-SAVE_AI.bat"
DEL "%f%">NUL 2>&1
echo @ECHO ON >> "%f%"
echo REM THE FOLLOWING IS TO SAVE AI .bat and .vpy back to the non-sandbox host>> "%f%"
echo copy /Y C:\AI\*.bat  C:\HOST_AI\ >> "%f%"
echo copy /Y C:\AI\*.py   C:\HOST_AI\ >> "%f%"
echo copy /Y C:\AI\*.vpy  C:\HOST_AI\ >> "%f%"
echo pause >> "%f%"
echo goto :eof >> "%f%"

REM Create a link on the sandbox desktop which is mapped to the read-only C:\SOFTWARE folder on the host system
REM which contains our set of downloaded software that we use all the time. ie make it available in the sandbox.
REM We rely on this for stuff like notepad++ ... it C:\SOFTWARE or any other mapped folders do not exist on the host, the sandbox won't start
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

REM Create a link on the sandbox desktop which is mapped to our readonly D:\ssTEST\_AI_2023.06.05\AI folder on the host system
REM This is where we originally downloaded and extracted AI's lovely software on the host
set create_shortcut_SCRIPT="%TEMP%\create_HOST_AI_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\HOST AI.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\HOST_AI\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "HOST AI" >> %create_shortcut_SCRIPT%
echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
echo oLink.Save >> %create_shortcut_SCRIPT%
cscript /nologo %create_shortcut_SCRIPT%
del %create_shortcut_SCRIPT%

REM Create a link on the sandbox desktop which is mapped to our read-only D:\ssTEST\_AI_2023.06.05\000-tasmania-renamed folder on the host system
REM This is where our original images/videos are
set create_shortcut_SCRIPT="%TEMP%\create_HOST_000-tasmania-renamed_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\HOST_000-tasmania-renamed.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\HOST_000-tasmania-renamed\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "HOST_000-tasmania-renamed" >> %create_shortcut_SCRIPT%
echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
echo oLink.Save >> %create_shortcut_SCRIPT%
cscript /nologo %create_shortcut_SCRIPT%
del %create_shortcut_SCRIPT%

REM Create a link on the sandbox desktop which is mapped to C:\AI in the local sandbox system
REM This is where our sandbox copies of original folders of AI software is
set create_shortcut_SCRIPT="%TEMP%\create_AI_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\AI.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\AI\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "AI" >> %create_shortcut_SCRIPT%
echo 'oLink.HotKey = "" >> %create_shortcut_SCRIPT%
echo 'oLink.IconLocation = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WindowStyle = "" >> %create_shortcut_SCRIPT%
echo 'oLink.WorkingDirectory = "" >> %create_shortcut_SCRIPT%
echo oLink.Save >> %create_shortcut_SCRIPT%
cscript /nologo %create_shortcut_SCRIPT%
del %create_shortcut_SCRIPT%

REM Create a link on the sandbox desktop which is mapped to "C:\000-tasmania-renamed in the local sandbox system
REM This is where our sandbox copies of original folders of images are
set create_shortcut_SCRIPT="%TEMP%\create_000-tasmania-renamed_desktop_link_%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
del %create_shortcut_SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %create_shortcut_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\000-tasmania-renamed.lnk" >> %create_shortcut_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %create_shortcut_SCRIPT%
echo oLink.TargetPath = "C:\000-tasmania-renamed\" >> %create_shortcut_SCRIPT%
echo oLink.Arguments = "" >> %create_shortcut_SCRIPT%
echo oLink.Description = "000-tasmania-renamed" >> %create_shortcut_SCRIPT%
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
ECHO [HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced] >> %fnpp%
ECHO "UseCompactMode"=dword:00000001 >> %fnpp%
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
explorer.exe "C:\AI\"

REM start an explorer window at the specified directory
explorer.exe "C:\000-tasmania-renamed\"

goto :eof
