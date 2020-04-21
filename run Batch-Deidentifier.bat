@echo

@echo .bat file received %*

@echo Executing python code...

python "Batch-Deidentifier.py" -x demo.xlsx %*

@pause
