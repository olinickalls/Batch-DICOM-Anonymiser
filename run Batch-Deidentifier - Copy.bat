@echo
rem ---- Explicit running of the script with full path helps prevent issues with drag & drop
rem which seems to prevent python running the script when dragging files from another dir.
@echo .bat file received %*
@echo Executing python code...
python "C:\Users\oliver\Documents\pycode\Batch-DICOM-Anonymiser\Batch-Deidentifier.py" %*
pause
