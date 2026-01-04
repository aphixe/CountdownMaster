@echo off
setlocal

REM Change working directory to the folder this .bat lives in
pushd "%~dp0"

REM Run main.py using Python from PATH
python "main.py"

REM Capture exit code before anything else changes it
set "EXITCODE=%errorlevel%"

echo.
echo exit code: %EXITCODE%
echo.

pause

REM Return to original directory
popd

endlocal
exit /b %EXITCODE%
