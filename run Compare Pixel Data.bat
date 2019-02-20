@echo off
@echo .bat file received %*
@echo Executing python code...
python "CompareDCMPixelData.py" %*
pause
