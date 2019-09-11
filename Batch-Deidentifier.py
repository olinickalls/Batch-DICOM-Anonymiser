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
import sys        
import pydicom    # DICOM file tools
import shutil     # used for just file copying.
import openpyxl   # For excel file access
import study_modules     # Class re-write of BA Modules.py and studytools.py
import argparse
# Next 2 lines used to get filename and path info
from inspect import currentframe, getframeinfo
from pathlib import Path

#-------------------------> INITIALISATION <---------------------------------
parser = argparse.ArgumentParser(
		description='Deidentify DICOM files using a .xlsx Template file.'
		)
parser.add_argument('-x',
	metavar='<Study Template filename>', 
	type=str, 
	dest='xlsfilename',
	default='default.xlsx',
	help='Study Template .xlsx filename'
	)
parser.add_argument('-d','--debug',
    action="store_true", 
    default=False,
	metavar='<debug loglevel>', 
	dest='debug',
	help='Debug level logs'
	)
parser.add_argument('-v','--verbose',
    action="store_true", 
    default=False,
	metavar='<increase verbosity>', 
	dest='verbose',
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
#file_paths = sys.argv[1:]  # remove the name of this script from list
file_paths = args.dicomfiles

# Set global log level
if args.debug:
	study.GLOBAL_LOGLEVEL = study.LOGLEVEL_DEBUG
	print(f'Logging set to {study.LOGLEVEL_TXT[study.GLOBAL_LOGLEVEL]}')
else:
	study.GLOBAL_LOGLEVEL = study.LOGLEVEL_NORMAL

#--------------------> Open XLSX to read/write <---------------------------
study.load_xls( study.xls_filename )
print(f'\tFound {len(study.xls_UID_lookup)} deidentified studie(s).')

# Log start of new session
study.log(f'Launched: Examining {str(file_paths)}', study.LOGLEVEL_NORMAL )

#--------------------> Process multiple directories
all_dir_count = 0
all_file_count = 0
all_valid_DCM_file = 0
all_copyOK = 0
all_copyfailed = 0
all_anonok = 0
all_anonfailed = 0
skipped_dcm_filenames = []
not_DCM_filenames = []
tag_warning = []

#loop through all the folders/files in file_paths[]
# each file/path listed is set as rootDir 
for rootDir in file_paths:
	print(f'rootDir = {rootDir}')
	
	# If the IRB code is set then use that as anonymised pt name
	if study.frontsheet[study.XLSFRONT_IRB_CODE_CELL].value:
		AnonName = study.frontsheet[study.XLSFRONT_IRB_CODE_CELL].value
	else:
		# This portion is old and may be deleted.
		# This takes the characters to the right of the last '\\' in the path
		# and makes it the default anonymised pt name 
		# eg if rootDir = 'c:\mydicim\ptZERO' then AnonName becomes 'ptZERO'
		# The slicing /could/ be made more readable...
		AnonName = rootDir[ -rootDir[-1::-1].find('\\') : ] 

	AnonID = 'RESEARCH'  # not stricty necessary- is redefined later.
	
	dir_count = 0
	file_count = 0
	valid_DCM_file = 0
	copyOK = 0
	copyfailed = 0
	anonok = 0
	anonfailed = 0
	
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
	
	for dirName, subdirList, fileList in os.walk(rootDir):
		dir_count  += len( subdirList )
		file_count += len( fileList )
	
		dirNameAnon = rootDir + '-anon' + dirName[ len(rootDir): ]
	
		# Create the directories as we come across them.
		create_dir( dirNameAnon, verbose=True )
		dir_count += 1  # assumed created OK (error raised if not)

		for fname in fileList:
			testfilename = f'{dirName}\\{fname}'
			savefilename = f'{dirNameAnon}\\{fname}'

			print(f'\t{fname}', end='',flush=True)

			# --------------- Check file before processing
			# File in skip list?
			if fname in study.SKIP_LIST:
				skipped_dcm_filenames.append( fname )
				print(' -on skiplist-')
				continue


			# Check 'fourcc' (bytes from 128 to 132) = "DICM"
			DICOM = check_DICOM_fourCC( testfilename )
			if not DICOM:
				print('\tfourcc says not DICOM -skipping file-')
				not_DCM_filenames.append(f'{fname}: fourcc failed- non-dicom')
				continue

			# ----------- Try to open with pydicom
			try:
				study.DCM = pydicom.filereader.dcmread( testfilename, force=True)
				# Blank the preamble.
				study.DCM.preamble = b'\x00' * 128
				
				load_warning = ''
				
				for tag in study.DCM_TAG_CHECKLIST:
					# There may be a beter way->  if tag not in study.DCM:
					if study.try_dcm_attrib( tag, '-blank-') == '-blank-':
						load_warning += (tag + ' ')

				if load_warning != '':
					tag_warning.append( f'{filename} : {load_warning}' )

			except:  # If exception on loading the file is prob non-DICOM
				print('\t-pydicom load failed -skipping file-')
				not_DCM_filenames.append(f'{fname}: pydicom load failed- non-dicom')
				continue

			else:  # Do this if the file is DICOM
				valid_DCM_file += 1
				print('\t-DICOM- De-identify', end='')

				# this returns False if there is no StudyInstanceUID tag
				study.test_study_UID = study.get_DCM_StudyInstanceUID( )

				if not study.test_study_UID:
					skipped_dcm_filenames.append(f'{fname} -No studyUID')
					print(' -No StudyInstanceUID tag  -skipped file-')
					continue

				# Check if StudyInstanceUID has match in cache
				if study.test_study_UID in study.xls_UID_lookup:
					# retrieve the previous studyID linked to the UID
					AnonID = study.get_old_study_attrib_from_UID(
						study.XLSDATA_STUDYIDS,
						study.test_study_UID
						)
					print(f' - Known UID, using {AnonID}')
				else:
					# If UNIQUE study UID ie. not in cache
					AnonID = study.assign_next_free_studyID( )
					print(f' - Unique UID - Assigning {AnonID}')
					
				# Perform deidentification on loaded DICOM data
				study.deidentifyDICOM(AnonName, AnonID )

				# Write de-identified DICOM to disc
				study.DCM.save_as(savefilename, write_like_original=True)

	# Stats on exit
	all_dir_count += dir_count
	all_file_count += file_count
	all_valid_DCM_file += valid_DCM_file
	all_copyOK += copyOK
	all_copyfailed += copyfailed
	all_anonok += anonok
	all_anonfailed += anonfailed


	#print('Found ' + str(valid_DCM_file) + ' valid DICOM files')
	#print('New pt name is\t\'' + AnonName + '\'' )
	#print('New pt ID is:\t\'' + AnonID + '\'' )
	
	print(f'Anonymised: {rootDir}')
	print(f'DICOMs Anonymised:\t{anonok} OK, {anonfailed} failed' )
	print(f'Non-DICOMs Copied:\t{copyOK} OK, {copyfailed} failed' )


if all_dir_count > 1:
	print('\nFinished Batch Job.')
else:
	print('\nFinished Job.')

print(f'all_dir_count \t{all_dir_count}')
print(f'all_file_count \t{all_file_count}')
print(f'all_valid_DCM_file \t{all_valid_DCM_file}')
print(f'all_copyOK \t{all_copyOK}')
print(f'all_copyfailed \t{all_copyfailed}')
print(f'all_anonok \t{all_anonok}')
print(f'all_anonfailed \t{all_anonfailed}')

print(f'\nskipped: ')
if len(skipped_dcm_filenames) > 0:
	for line in skipped_dcm_filenames:
		print(f'\t{line}')
else:
		print('\tNone')

print(f'\npresumed non-DICOM:')
if len(not_DCM_filenames) > 0:
	for line in not_DCM_filenames:
		print(f'\t{line}')
else:
	print('\tNone')

print(f'\n\n{len(tag_warning)} tag warnings:')
if len(tag_warning) > 0:
	for line in tag_warning:
		print(f'\t{line}')
else:
	print('\tNone')

study.log( f'Completed. Deidentified {all_anonok}, failed {all_anonfailed}', study.LOGLEVEL_NORMAL )

#studytools.write_xls_to_disc( study.XLS, study.xls_filename )
study.write_xls_to_disc( study.xls_filename )




#-----------------------> Helper Functions <-----------------------------------

def create_dir( dir_name, verbose=True ):
	try: 
		os.makedirs( dir_name )
	except OSError:
		if not os.path.isdir( dir_name ):
			print(f'Fatal Error: Failed to create dir: {dir_name}')
			raise
	else:
		if verbose:
			print(f'\n\t{dirNameAnon} created OK')
		return True

def check_DICOM_fourCC( filename ):
	with open( filename, "r", encoding="Latin-1") as file:
		file.seek(128,0)
		line = file.read(4)
	if line == "DICM":
		return True
	else:
		print('\tfourcc says not DICOM -skipping file-')
		return False



def show_zeropath_warning():
	print('No cmd line arguments found.')
	print('\nSyntax:')
	print('\tBatch-Deidentifier <dir1> [<dir2> <dir3>...]')
	print('\n\twhere <dir_> is the base directory of DICOM files')
	print('Batch-Deidentifier will change the patient name to the IRB code.')
	print('e.g. BatchAnonymiser c:\\myfiles\\patient-zero')
	print('\n\t will:')
	print('\t\t-Duplicate the directory tree into c:\\myfiles\\patient-zero-anon')
	print('\t\t\texcluding non-DICOM files but including empty directories')
	print('\t\t-Deidentify all DICOM files according to the study XLSX file')
	print('\t\t-Change the patient name in all DICOM files to the IRB Code')
	print('\t\t\tstrip out patient identifiers and partial identifiers,')
	print('\t\t\tand more in a fairly aggressive manner.')
	print('\t\t\tand then apply a pre-generated (random) studyID')
