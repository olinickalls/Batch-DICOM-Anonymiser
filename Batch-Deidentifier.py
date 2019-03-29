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

import os         # for os.walk() primarily
import sys        # cmd line arguments
import pydicom    # DICOM - obviously...
import shutil     # used for just file copying.
import openpyxl   # For excel file access
import study_modules     # Class re-write of BA Modules.py and studytools.py

# ---------------------------------------------------------------------------
study = study_modules.Study_Class()

# ---------------------------------------------------------------------------
##    Work In Progress:
##    Need to convert this to argparse.
##    Include cmd line options such as xlsfilename, log level...

study.xls_filename = 'test_file.xlsx'  # Default


print('Formatting input files...')

file_paths = sys.argv[1:]  # the first argument is the script itself

if len( file_paths ) < 1:  # Default
	file_paths = [ 'C:\\Users\\oliver\\Documents\\pycode\\Batch-DICOM-Anonymiser\\sample_1' ]


if len(file_paths) == 0:
	print('No input found. Defaulting to test string.')
	print('No cmd line arguments found.\n\nSyntax:\n\tBatch-Anonymiser <dir1> [<dir2> <dir3>...]')
	print('\n\twhere <dir_> is the base directory of DICOM files')
	print('BatchAnonymiser will change the patient name to the \'base\' directory name.')
	print('e.g. BatchAnonymiser c:\\myfiles\\patient-zero')
	print('\n\t will:')
	print('\t\t-Duplicate the directory tree into c:\\myfiles\\patient-zero-anon (including non-DICOM files and empty directories)')
	print('\t\t-Anonymise all DICOM files')
	print('\t\t-Change the patient name in all DICOM files to \'patient-zero\'.')
	exit()

print('\n')

#--------------------> Open XLSX to read/write
study.load_xls( study.xls_filename )

if study.XLS == False:
	print(f'Fatal Error: Unable to open file {study.xls_filename}')
	exit()

print(f'Loaded XLS. Found {len( study.xls_UID_lookup )} previously deidentified studie(s).')

try:
	study.XLS.save( study.xls_filename )
except:
	print(f'{study.xls_filename} save permission denied. Is the file open in excel?.\nPlease unlock and try again.')
	raise

#--------------------> Log start of new session
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
for rootDir in file_paths:
	
	print(f'rootDir = {rootDir}')
	
	if study.frontsheet[study.XLSFRONT_IRB_CODE_CELL].value:
		AnonName = study.frontsheet[study.XLSFRONT_IRB_CODE_CELL].value
	else:
		# This portion is old and may be deleted.
		# This takes the characters to the right of the last '\\' in the path
		# and makes it the default anonymised pt name 
		# eg if rootDir = 'c:\mydicim\ptZERO' then AnonName becomes 'ptZERO'
		# The slicing /could/ be made more readable...
		AnonName = rootDir[ -rootDir[-1::-1].find('\\') : ] 

	AnonID = 'RESEARCH'
	
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
	
		try: 
			os.makedirs( dirNameAnon )
		except OSError:
			if not os.path.isdir( dirNameAnon ):
				print(f'Fatal Error: Failed to create dir: {dirNameAnon}')
				raise
		else:
			print(f'\t{dirNameAnon} created OK')
			dir_count += 1

		for fname in fileList:
			testfilename = f'{dirName}\\{fname}'
			savefilename = f'{dirNameAnon}\\{fname}'

			print(f'\t{fname}', end='',flush=True)

			if fname in study.SKIP_LIST:
				skipped_dcm_filenames.append( fname )
				continue

			# Try to open each file with pydicom to validate it.
			try:
				study.DCM = pydicom.filereader.dcmread( testfilename, force=True)
				
				load_warning = ''
				
				for tag in study.DCM_TAG_CHECKLIST:
					# There may be a beter way->  if tag not in study.DCM:
					if study.try_dcm_attrib( tag, '-blank-') == '-blank-':
						load_warning += (tag + ' ')

				if load_warning != '':
					tag_warning.append( f'{filename} : {load_warning}' )

			except:  # If exception on loading the file is prob non-DICOM
				print('\t-NonDICOM  -skipping file-')
				not_DCM_filenames.append(f'{fname}: load failed- non-dicom')
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

