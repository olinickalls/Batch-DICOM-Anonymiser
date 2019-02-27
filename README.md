# Batch-DICOM-Anonymiser
Batch anonymisation of DICOM files &amp; directories (cmd line tool)

Simple script to aid in research projects with multiple non-anonymised DICOM files.

Planned improvements:
1- Integrate XLS reading of StudyIDs and writing of pt Data into deident process

 a- change command line method to allow loading a specific XLS document 
 b- potentially support having several XLS files - 1 for each study - how to handle?
 c- possible flow for new features:
     1- read all input DCM files. Identify list of unique studies.
     2- loop through list, and assign each unique study a new StudyID (ie next on the list)
     3- de-identify each input case - lookup to find the necessary StudyID
    issues to consider- 
        each pt allowed to have more than 1 study
        


2- Make simple encryption to obfuscate real pt ID etc in XLS.
