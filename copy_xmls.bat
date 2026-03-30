@echo off
set "SOURCE=C:\Astrod\Programacion\eyes\xml"
set "DEST=C:\Users\astro\AndroidStudioProjects\Eyes\app\src\main\res\drawable"

echo Syncing XML files...

:: & C:\Users\astro\AppData\Local\Microsoft\WindowsApps\python3.11.exe c:/Astrod/Programacion/eyes/main3.py ; C:\Astrod\Programacion\eyes\copy_xmls.bat

:: /Y  Suppresses prompting to confirm you want to overwrite an existing destination file.
:: /I  If destination does not exist and copying more than one file, assumes that destination must be a directory.
:: /Q  Does not display file names while copying.
xcopy "%SOURCE%\*.xml" "%DEST%\" /Y /I

if %ERRORLEVEL% EQU 0 (
    echo Sync complete! Files copied to drawable folder.
) else (
    echo An error occurred during copy.
)