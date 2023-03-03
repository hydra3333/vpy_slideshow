@ECHO ON
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

cscript //nologo "%~dp0bulk-rename-command-extension-subfolders-bottom-only.vbs" "%1\"

pause
exit
