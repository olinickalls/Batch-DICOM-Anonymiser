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
global stats
global ops

import os         
import sys        
import pydicom    # DICOM file tools
import shutil     # used for just file copying.
import openpyxl   # For excel file access
from deident_helper import *  # helper functions for deident
import study_modules     # Study_Class and methods etc.
import argparse
# Next 2 lines used to get filename and path info
from inspect import currentframe, getframeinfo
from pathlib import Path

stats = study_modules.FileStats_Class()
ops = Ops_Class()
ops.DEBUG = False
ops.VERBOSE = False
ops.QUIET = False

#-------------------------> INITIALISATION <---------------------------------
parser = argparse.ArgumentParser(
		description='Deidentify DICOM files using a .xlsx Template file.'
		)
parser.add_argument('-x',
	metavar='<Study Template filename>', 
	type=str, 
	dest='xlsfilename',
	default='my_study.xlsx',
	help='Study Template .xlsx filename'
	)
parser.add_argument('-d','--debug',
    action="store_true", 
    default=False,
	dest='debug'
	)
parser.add_argument('-v','--verbose',
    action="store_true", 
    default=False,
	dest='verbose',
	help='Prints more info about activity'
	)
parser.add_argument('-q','--quiet',
    action="store_true", 
    default=False,
	dest='quiet',
	help='Prints more info about activity'
	)
parser.add_argument('dicomfiles',  # positional arg -no '-' required
	metavar='<Directories or dicom files>', 
	type=str, nargs='*',  # No limit to number of args expected
	help='<filenames> and <dirnames> for deidentification'
	)
args = parser.parse_args()

# Get script filename and path
filename = getframeinfo(currentframe()).filename
parent = Path(filename).resolve().parent
print( f'CWD: {os.getcwd()}')
print( f'.py file path: {parent}  {filename}')

# Change working directory to the same as the script.
os.chdir( parent )

# ---------------------------------------------------------------------------
# Create Study_Class object
study = study_modules.Study_Class()

# Set basic info
# study.xls_filename = 'my_study.xlsx'
study.xls_filename = args.xlsfilename

print('Formatting input files...\n')

# Use default test directories if no <filenames> given
if len(args.dicomfiles)<1:
	print('Using default test directories.')
	file_paths = [ 'C:\\Users\\oliver\\Documents\\pycode\\Batch-DICOM-Anonymiser\\sample_1' ]
else:
	file_paths = args.dicomfiles


# Set global log level
if args.debug:
	DEBUG = True
	study.GLOBAL_LOGLEVEL = study.LOGLEVEL_DEBUG
	print(f'Logging set to {study.LOGLEVEL_TXT[study.GLOBAL_LOGLEVEL]}')
else:
	study.GLOBAL_LOGLEVEL = study.LOGLEVEL_NORMAL

if args.verbose:
	VERBOSE = True

if args.quiet:
	QUIET = True

#--------------------> Open XLSX to read/write <---------------------------
study.load_xls( study.xls_filename )
print(f'\tFound {len(study.xls_UID_lookup)} deidentified studie(s).')

# Log start of new session
study.log(f'Launched: Examining {str(file_paths)}', study.LOGLEVEL_NORMAL )

#--------------------> Process multiple directories

#loop through all the folders/files in file_paths[]
# each file/path listed is set as rootDir 
for rootDir in file_paths:
	print(f'rootDir = {rootDir}')
	
	# If the IRB code is set then use that as anonymised pt name
	if study.frontsheet[study.XLSFRONT_IRB_CODE_CELL].value:
		study.CurrStudy.AnonName = study.frontsheet[study.XLSFRONT_IRB_CODE_CELL].value
	else:
		# This portion is old and may be deleted.
		# This takes the characters to the right of the last '\\' in the path
		# and makes it the default anonymised pt name 
		# eg if rootDir = 'c:\mydicim\ptZERO' then AnonName becomes 'ptZERO'
		# The slicing /could/ be made more readable...
		study.CurrStudy.AnonName = rootDir[ -rootDir[-1::-1].find('\\') : ] 

	AnonID = 'RESEARCH'  # not stricty necessary- is redefined later.
	
	stats.reset_sub()
	'''
	dir_count = 0
	file_count = 0
	valid_DCM_file = 0
	copyOK = 0
	copyfailed = 0
	anonok = 0
	anonfailed = 0
	'''

	#small bit of code to strip the deepest
	# dir tree from rootDir
	# then append with '-anon'
	#
	# e.g. from C:\mystuff\sub\dcmfiles
	#      to   C:\mystuff\sub\dcmfiles_anon
	#
	#  needs to work within the os.walk() loop below.
	# 1- strip the rootDir from the left of the string
	# 2- insert the anonymised root in that space   
	# This can only work because the final \ is not
	# present at the end of the paths presented by os.walk 
	
	# loop through each directory off the rootDir
	for dirName, subdirList, fileList in os.walk(rootDir):

		stats.start_subdir( subdirList, fileList )	
		dirNameAnon = rootDir + '-anon' + dirName[ len(rootDir): ]
	
		# Create the directories as we come across them.
		# Exits if fails to create
		create_dir( dirNameAnon, verbose=True )
		stats.dir_count += 1  # assumed created OK (error raised if not)

		# loop through each file in current directory
		for fname in fileList:
			study.CurrStudy.testfilename = f'{dirName}\\{fname}'
			study.CurrStudy.savefilename = f'{dirNameAnon}\\{fname}'

			print(f'\t{fname}', end='',flush=True)

			# --------------- Check file before processing
			# File in skip list?
			if fname in study.SKIP_LIST:
				stats.skipped_dcm_filenames.append( fname )
				print(' -on skiplist-')
				continue


			# Check 'fourcc' (bytes from 128 to 132) = "DICM"
			DICOM = check_DICOM_fourCC( study.CurrStudy.testfilename )
			if not DICOM:
				print('\tfourcc says not DICOM -skipping file-')
				stats.not_DCM_filenames.append(f'{fname}: fourcc failed- non-dicom')
				continue
			
			# The meat & bones of deidentification goes on here
			processOK = process_file( study, study.CurrStudy.testfilename, stats )  # need to remove stats- maybe include as returned value
			if not processOK:
				# process_file() returns True if deidentified OK
				# otherwise returns False.
				# Not strictly needed if this is the last in file loop
				continue


	# Stats on rootDir completion----
	#update_stats_done_rootDir( subdirList, fileList )

	print(f'Anonymised: {rootDir}')
	print(f'DICOMs Anonymised:\t{stats.anonok} OK, {stats.anonfailed} failed' )
	print(f'Non-DICOMs Copied:\t{stats.copyOK} OK, {stats.copyfailed} failed' )


if stats.all_dir_count > 1:
	print('\nFinished Batch Job.')
else:
	print('\nFinished Job.')

print(f'all_dir_count \t{stats.all_dir_count}')
print(f'all_file_count \t{stats.all_file_count}')
print(f'all_valid_DCM_file \t{stats.all_valid_DCM_file}')
print(f'all_copyOK \t{stats.all_copyOK}')
print(f'all_copyfailed \t{stats.all_copyfailed}')
print(f'all_anonok \t{stats.all_anonok}')
print(f'all_anonfailed \t{stats.all_anonfailed}')

print(f'\nskipped: ')
if len(stats.skipped_dcm_filenames) > 0:
	for line in stats.skipped_dcm_filenames:
		print(f'\t{line}')
else:
		print('\tNone')

print(f'\npresumed non-DICOM:')
if len(stats.not_DCM_filenames) > 0:
	for line in stats.not_DCM_filenames:
		print(f'\t{line}')
else:
	print('\tNone')

print(f'\n\n{len(stats.tag_warning)} tag warnings:')
if len(stats.tag_warning) > 0:
	for line in stats.tag_warning:
		print(f'\t{line}')
else:
	print('\tNone')

study.log( f'Completed. Deidentified {stats.all_anonok}, failed {stats.all_anonfailed}', study.LOGLEVEL_NORMAL )

#studytools.write_xls_to_disc( study.XLS, study.xls_filename )
study.write_xls_to_disc( study.xls_filename )




#-----------------------> Helper Functions <-----------------------------------


