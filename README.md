# Batch-DICOM-Anonymiser
Batch anonymisation of DICOM files &amp; directories (cmd line tool)

Simple script to aid in research projects with multiple non-anonymised DICOM files.

## Planned improvements:

- Needs refactoring and code cleanup (PEP8)
- ?GUI for the deidentification process? - ?BeeWare for front end [and packaging?]
- support having several XLS files - 1 for each study - how to handle?
- improve date obfuscation- perhaps reset to an index date- eg. 1 Jan 2000. Store the offset in the data tab and apply the same offset to all studies for the same patient
- allow tags to have variables inserted - not just statics from the XLS - prefix & tag reference?
    - make filename and base directory names available for tag data changes
- allow filename changes- based on eg. prefix, study ID... 
- Tag replace does not currently differentiate between tags that do and don't exist in the original file
    - would have 'Add' and 'Replace' as separate, and define behaviour of 'Replace'
- How to improve the way flags are referred to- ie how to create a stable list of flags so they can be written into template (by iterating) from a list in the const defs of study_modules.py.
- helper class to provide simple shortcuts to XLS file cell locations etc.

### XLS improvement
- allow autofill of DICOM tag names while in Excel. Probably simple lookup from dictionary tab within Excel.  This needs to be creted with the basic XLSX file. ?Template .XLSX instead of hardcode the creation of the file?
    - currently run the xls through the deident once and it will populate the tag names

- possible flow for new features:
     1- read all input DCM files. Identify list of unique studies.
     2- loop through list, and assign each unique study a new StudyID (ie next on the list)
     3- de-identify each input case - cmd line lookup option based on studyID(?) to find the necessary StudyID
    issues to consider- 
        each pt allowed to have more than 1 study
        


2- Make simple encryption to obfuscate real pt ID etc in XLS- is this useful?
    - ie. hash the field rather than replace

### Completed Improvements

- allow customisation of the deident process in the XLS - currently hardcoded
- allow loading a specific XLS document
