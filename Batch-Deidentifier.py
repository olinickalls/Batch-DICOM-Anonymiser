'''
*****************************
By Oliver Nickalls Jan 2019

Enter 1 or more directories as cmd line arguments to create
duplicate directories, containing copies of original non-DICOM files too.


This expands on the previous version 'recurseDIR.py' that only takes a
single directory as an argument.

Much borrowed from the pyDICOM anonymiser example from the userguide
https://pydicom.github.io/pydicom/dev/auto_examples/metadata_processing/plot_anonymize.html
PyDICOM Version 1.2.1

=====================
Planned enhancements:
=====================
-Logging with variable on-screen verbosity
-Support taking IDs/Name from an external list to allow reversible
    anonymisation the user may or may not be blinded to the process
-?encrypt / scramble log output?
'''

import os
# import sys
# import pydicom    # DICOM file tools
# import shutil     # used for just file copying.
# import openpyxl   # For excel file access
from deidenttools import Ops_Class, process_file, create_dir, check_fourCC
import studymodules     # Study_Class and methods etc.
import argparse
# Next 2 lines used to get filename and path info
from inspect import currentframe, getframeinfo
from pathlib import Path

global stats
stats = studymodules.FileStats_Class()
ops = Ops_Class()

# -------------------------> INITIALISATION <---------------------------------
parser = argparse.ArgumentParser(
        description='Deidentify DICOM files using a .xlsx Template file.'
        )
parser.add_argument(
    '-x',
    metavar='<Study Template filename>',
    type=str,
    dest='xlsfilename',
    default='my_study.xlsx',
    help='Study Template .xlsx filename'
    )
parser.add_argument(
    '-d',
    '--debug',
    action="store_true",
    default=False,
    dest='debug'
    )
parser.add_argument(
    '-v',
    '--verbose',
    action="store_true",
    default=False,
    dest='verbose',
    help='Prints more info about activity'
    )
parser.add_argument(
    '-q',
    '--quiet',
    action="store_true",
    default=False,
    dest='quiet',
    help='Prints more info about activity'
    )
parser.add_argument(
    'dicomfiles',  # positional arg -no '-' required
    metavar='<Directories or dicom files>',
    type=str, nargs='*',  # No limit to number of args expected
    help='<filenames> and <dirnames> for deidentification'
    )
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Create Study_Class object- ops class as argument to pass environ data
study = studymodules.Study_Class(
    QUIET=args.quiet,
    VERBOSE=args.verbose,
    DEBUG=args.debug
    )

# Get script filename and path
filename = getframeinfo(currentframe()).filename
parent = Path(filename).resolve().parent
study.msg(f'CWD: {os.getcwd()}', level='VERBOSE')
study.msg(f'.py file path: {parent}  {filename}', level='VERBOSE')

# Change working directory to the same as the script.
os.chdir(parent)

# -------------------------------------------------------------------

# Set basic info
# study.xls_filename = 'my_study.xlsx'
if args.xlsfilename == "":
    print("No XLSX file specified. Defaulting to 'demo.xlsx'")
    args.filename = "demo.xlsx"
study.xls_filename = args.xlsfilename

study.msg('Reading input files...\n')

# Use default test directories if no <filenames> given
if len(args.dicomfiles) < 1:
    file_paths = ['.\\sample_1']
    study.msg('Using default DEBUG test directory:')
    study.msg(file_paths)
else:
    file_paths = args.dicomfiles


# --------------------> Open XLSX to read/write <---------------------------
study.load_xls(study.xls_filename)
old_study_count = len(study.xls_UID_lookup)
study.msg(f'\tFound {old_study_count} deidentified studies.', 'VERBOSE')

# Log start of new session
study.log(f'Launched: Examining {str(file_paths)}', study.LOGLEVEL_NORMAL)

# --------------------> Pre-Process multiple directories

# Loop through all the folders/files in file_paths[]
# each file/path listed is set as baseDir
# Initial dir & file count.
files = 0
dirs = 1  # +1 as the root dir is not counted.
for baseDir in file_paths:
    for dirName, subdirList, fileList in os.walk(baseDir):
        files += len(fileList)
        dirs += len(subdirList)

study.msg(f'\nFound {files} files in {dirs} directories.\n')

# --------------------> Process multiple directories

# Loop through all the folders/files in file_paths[]
# each file/path listed is set as baseDir
for baseDir in file_paths:
    study.msg(f'{baseDir}\\')

    # If the IRB code is set then use that as anonymised pt name
    if study.frontsheet[study.XLSFRONT_IRB_CODE_CELL].value:
        study.CurrStudy.AnonName = study.frontsheet[study.XLSFRONT_IRB_CODE_CELL].value
    else:
        # If no IRB code then this:
        # This takes the characters to the right of the last '\\' in the path
        # and makes it the default anonymised pt name
        # eg if baseDir = 'c:\mydicim\ptZERO' then AnonName becomes 'ptZERO'
        # The slicing /could/ be made more readable...
        study.CurrStudy.AnonName = baseDir[-baseDir[-1::-1].find('\\'):]

    stats.reset_sub()

    # small bit of code to strip the deepest
    # dir tree from baseDir
    # then append with '-anon'
    #
    # e.g. from C:\mystuff\sub\dcmfiles
    #      to   C:\mystuff\sub\dcmfiles_anon
    #
    #  needs to work within the os.walk() loop below.
    # 1- strip the baseDir from the left of the string
    # 2- insert the anonymised root in that space
    # This can only work because the final \ is not
    # present at the end of the paths presented by os.walk

    # loop through each directory off the baseDir
    for dirName, subdirList, fileList in os.walk(baseDir):

        stats.start_subdir(subdirList, fileList)
        dirNameAnon = baseDir + '-anon' + dirName[len(baseDir):]

        # Create the directories as we come across them.
        create_dir(dirNameAnon, verbose=True)
        stats.dir_count += 1  # assumed created OK (error raised if not)

        # loop through each file in current directory
        for fname in fileList:
            study.CurrStudy.clean()
            study.CurrStudy.testfilename = f'{dirName}\\{fname}'
            study.CurrStudy.savefilename = f'{dirNameAnon}\\{fname}'

            fname_str = "'" + fname + "'"
            study.msg(f"\t{fname_str.ljust(30,' ')} ", endstr='')

            # --------------- Checks before deidentifying
            # File in skip list?
            if fname in study.SKIP_LIST:
                stats.skipped_dcm_filenames.append(fname)
                study.msg(' - file ignored.')
                stats.ignored += 1
                continue

            # Check 'fourCC' (bytes from 128 to 132) = "DICM"
            DICOM_fourCC = check_fourCC(study.CurrStudy.testfilename)
            if not DICOM_fourCC:
                study.msg('Invalid DICOM: Missing or wrong fourCC')
                stats.not_DCM_filenames.append(f'{fname}: non-dicom fourcc')
                stats.nondicom += 1
                continue

            # The meat & bones of deidentification goes on here
            # Would like to remove stats arg- maybe include as returned value
            deidOK = process_file(study, study.CurrStudy.testfilename)
            if deidOK:
                stats.anonok += 1
            else:
                # process_file() returns True if deidentified OK
                # otherwise returns False.
                # Not strictly needed if this is the last in file loop
                stats.anonfailed += 1

    # Stats on baseDir completion----
    # update_stats_done_rootDir( subdirList, fileList )

    study.msg('\n')
    study.msg(f'\tDICOMs Anonymised:\t{stats.anonok} OK, ', endstr='')
    study.msg(f'{stats.anonfailed} failed')
    study.msg(f'\tFiles ignored: {stats.ignored}')
    study.msg(f'\tNon-DICOM: {stats.nondicom}')

if stats.all_dir_count > 1:
    study.msg('\nFinished Batch Job.')
else:
    study.msg('\nFinished Job.')

study.msg(f'all_dir_count \t{stats.all_dir_count}', level='VERBOSE')
study.msg(f'all_file_count \t{stats.all_file_count}', level='VERBOSE')
study.msg(f'all_valid_DCM_file \t{stats.all_valid_DCM_file}', level='VERBOSE')
study.msg(f'all_copyOK \t{stats.all_copyOK}', level='VERBOSE')
study.msg(f'all_copyfailed \t{stats.all_copyfailed}', level='VERBOSE')
study.msg(f'all_anonok \t{stats.all_anonok}', level='VERBOSE')
study.msg(f'all_anonfailed \t{stats.all_anonfailed}', level='VERBOSE')

print(f'\nskipped: ')
if len(stats.skipped_dcm_filenames) > 0:
    for line in stats.skipped_dcm_filenames:
        study.msg(f'\t{line}', level='VERBOSE')
else:
    study.msg('\tNone')

study.msg(f'\npresumed non-DICOM:', level='VERBOSE')
if len(stats.not_DCM_filenames) > 0:
    for line in stats.not_DCM_filenames:
        study.msg(f'\t{line}', level='VERBOSE')
else:
    study.msg('\tNone', level='VERBOSE')

study.msg(f'\n\n{len(stats.tag_warning)} tag warnings:')
if len(stats.tag_warning) > 0:
    for line in stats.tag_warning:
        study.msg(f'\t{line}')
else:
    study.msg('\tNone')

study.log(f'Done: {stats.all_anonok} OK', study.LOGLEVEL_NORMAL)
study.log(f'Done: {stats.all_anonfailed} failed', study.LOGLEVEL_NORMAL)

study.write_xls_to_disc(study.xls_filename)

# -----------------------> End of main routine <------------------------------
