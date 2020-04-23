@echo off

@echo .bat file received %*

@echo Executing python code...

python "Batch-Deidentifier.py" -x my_study.xlsx %*

@pause
