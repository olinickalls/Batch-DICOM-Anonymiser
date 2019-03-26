'''
*****************************
By Oliver Nickalls Jan 2019

Enter 1 or more directories as cmd line arguments to create duplicate directories, containing copies of original non-DICOM files too.


This expands on the previous version 'recurseDIR.py' that only takes a single directory as an argument.

Much borrowed from the pyDICOM anonymiser example from the userguide
# https://pydicom.github.io/pydicom/dev/auto_examples/metadata_processing/plot_anonymize.html
PyDICOM Version 1.2.1

=====================
Planned enhancements:
=====================
-Logging with variable on-screen verbosity
-Support taking IDs/Name from an external list to allow reversible anonymisation
	the user may or may not be blinded to the process
-?encrypt / scramble log output?


'''

import os         # for os.walk() primarily
import sys        # cmd line arguments
import pydicom    # DICOM - obviously...
import shutil     # used for just file copying.
import openpyxl   # For excel file access

#from BAModules import *     # Not the cleanest way of doing this- future name change needed

import study_modules     # Class re-write of BA Modules.py and studytools.py


# ---------------------------------------------------------------------------
#    Initialise the main class

study = study_modules.Study_Class()

# ---------------------------------------------------------------------------


print( os.path.basename(__file__) )

##
## Work In Progress:
##    Need to convert this to argparse.
##    Include cmd line options such as xlsfilename, log level...
##


xls_filename = 'test_file.xlsx'

print('Formatting input files...')




file_paths = sys.argv[1:]  # the first argument is the script itself

if len( file_paths ) < 1:
	file_paths = [ 'C:\\Users\\oliver\\Documents\\pycode\\Batch-DICOM-Anonymiser\\sample_1' ]



if len(file_paths) == 0:
	print('No input found. Defaulting to test string.')
	#file_paths.append( 'C:\\Users\\oliver\\Documents\\pycode\\dropscript\\DVD 6- Volunteer 60' )
	print('No cmd line arguments found.\n\nSyntax:\n\tBatch-Anonymiser <dir1> [<dir2> <dir3>...]')
	print('\n\twhere <dir_> is the base directory of DICOM files')
	print('BatchAnonymiser will change the patient name to the \'base\' directory name.')
	print('e.g. BatchAnonymiser c:\\myfiles\\patient-zero')
	print('\n\t will:')
	print('\t\t-Duplicate the directory tree into c:\\myfiles\\patient-zero-anon (including non-DICOM files and empty directories)')
	print('\t\t-Anonymise all DICOM files')
	print('\t\t-Change the patient name in all DICOM files to \'patient-zero\'.')
	exit()

study.log_message( '\n' + str(len(file_paths)) + ' line(s) received from cmd line', study.loglevel_high) # print no. of lines received

# Iterate through all lines received from the cmd line and print them to screen
line_count = 1
for p in file_paths:
	print( str(line_count) + '\t' + p)
	line_count += 1

#print('File List complete.')

print('\n')


study.xls_filename = xls_filename

#--------------------> Open XLSX to read/write

# studytools.load_study_xls( study.xls_filename )

#class method for loading XLS file
study.load_xls( study.xls_filename )


if study.XLS == False:
	print(f'Fatal Error: Unable to open file {study.xls_filename}')
	exit()


print(f'Loaded XLS. Found {len( study.xls_UID_lookup )} previously deidentified studie(s).')

# Create genertor object for next_log_row
#study.next_log_row_gen = studytools.next_log_row_generator( study.XLS )

try:
	study.XLS.save( study.xls_filename )
except:
	print(f'{study.xls_filename} save permission denied. Is the file open in excel?.\nPlease unlock and try again.')
	#raise

#--------------------> Log start of new session

study.log_message( f'Launched: Examining {str(file_paths)}', study.loglevel_normal )


#--------------------> Process multiple directories

# Count some dir and file stats
all_dir_count = 0
all_file_count = 0
all_valid_DCM_file = 0
all_copyOK = 0
all_copyfailed = 0
all_anonok = 0
all_anonfailed = 0

skipped_dcm_filenames = []
not_DCM_filenames     = []
tag_warning           = []


#loop through all the folders/files in file_paths[] 

for rootDir in file_paths:
	
	print(f'rootDir = {rootDir}')
	
	if study.frontsheet[ study.xlsFront_IRB_code_cell ].value:
		AnonName = study.frontsheet[ study.xlsFront_IRB_code_cell ].value
	else:
		# This portion is old and may be deleted.
		# This takes the characters to the right of the last '\\' in the path
		#  and makes it the default anonymised pt name 
		#  e.g. if rootDir = 'c:\stuff\mydicim\ptZERO' then AnonName becomes 'ptZERO' 
		AnonName = rootDir[ -rootDir[-1::-1].find('\\') : ] 


	AnonID = 'RESEARCH'
	
	
	
	# Count some dir and file stats
	dir_count      = 0
	file_count     = 0
	valid_DCM_file = 0
	copyOK         = 0
	copyfailed     = 0
	anonok         = 0
	anonfailed     = 0
	
	
	#small bit of code to strip the deepest dir tree from rootDir
	# then append with '-anon'
	#
	# e.g. from C:\mystuff\sub\dcmfiles
	#      to   C:\mystuff\sub\dcmfiles_anon
	#
	#  needs to work within the os.walk() loop below.
	# 1- strip the rootDir from the left of the string
	# 2- insert the anonymised root in that space   
	# This can only work because the final \ is not present at the end of the paths presented by os.walk 
	
	
	for dirName, subdirList, fileList in os.walk(rootDir):
		dir_count  += len( subdirList )
		file_count += len( fileList )
	
		dirNameAnon = rootDir + '-anon' + dirName[ len(rootDir): ]
	
		# Create the directories as we come across them.
		# I am not going to check if empty, just blindly re-create the same dir structure
	
		try: 
			os.makedirs( dirNameAnon )
		except OSError:
			if not os.path.isdir( dirNameAnon ):
				print(f'Fatal Error: Failed to create directory: {dirNameAnon}')
				raise
		else:
			print(f'\t{dirNameAnon} created OK')
			dir_count += 1

			
		#    print('Found directory: %s' % dirName)
		for fname in fileList:
			testfilename = dirName + '\\' + fname
			savefilename = dirNameAnon + '\\' + fname


			# print each file namejust  before testing - end='' to prevent the \n & flush to push to screen
			print( f'\t{fname}', end='', flush=True )

			# Skip certain files based on filename. skip_list[] contains the list.  Do not copy. Do no try to read.
			if fname in study.skip_list:
				skipped_dcm_filenames.append( fname )
				continue

			# Try to open each file with pydicom to validate it.
			# print '--OK--' if successful, '--FAILED--' if not then move on.

			try:  # Try opening each file as a DICOM file with pyDICOM
				# testdcmobj = pydicom.filereader.dcmread( testfilename, force=True)
				study.DCM = pydicom.filereader.dcmread( testfilename, force=True)
				
				# Mini-test to check major DICOM tags are present on loading.
				# Run test against the list study.dcm_tag_checklist
				load_warning = ''
				
				for tag in study.dcm_tag_checklist:
					if study.try_dcm_attrib( tag, '-blank-') == '-blank-':
						load_warning += ( tag + ' ' )

				if load_warning != '':
					#print(f'Load Warning: \'{fname}\' is missing tags: {load_warning}')
					tag_warning.append( f'{filename} : {load_warning}' )
					#print(f'**************TAG WARNING********* count = {len(tag_warning)}')


			except:  # If it fails (ie raises an exception) count it as non-DICOM
				print('\t-NonDICOM  -skipping file-')
				not_DCM_filenames.append( fname + ': failed to load- assumed non-dicom & was skipped')
				continue

				# Insert ability to copy non-DICOM files here
				# This is not automatically desirable.


			else:  # Do this if the file is DICOM
				valid_DCM_file += 1
				print('\t-DICOM- De-identify', end='')

				# this returns False if there is no StudyInstanceUID tag
				study.test_study_UID = study.get_DCM_StudyInstanceUID( ) 

				if not study.test_study_UID:
					#print(f'\n\t\tFailed to find StudyInstanceUID in DCM. Skipping file { fname }, study.test_study_UID = { study.test_study_UID }')
					skipped_dcm_filenames.append( fname + '-failed to find studyUID' )
					print(' -No StudyInstanceUID tag  -skipped file-')
					continue

				# step 1 - grab pt identifiers a see if match existing study UID
				#print(f'\nTry: deidentification loop')
				#print(f'study.test_study_UID = {study.test_study_UID}')
				#print(f'lookup dict = {study.xls_UID_lookup}')

				if study.test_study_UID in study.xls_UID_lookup:
					# ie. if the study UID is known and is in the UID cache (possible re-anonymisation)
					#AnonID = studytools.get_old_study_attrib( study.XLS, study.xls_UID_lookup, study.test_study_UID, study.xlsData_study_IDs )
					AnonID = study.get_old_study_attrib_from_UID( study.xlsData_study_IDs, study.test_study_UID )
					print(f' - Known UID, using {AnonID}')
					#print(f'AnonID = {AnonID}')
				else:
					# If UNIQUE study UID (needs new studyID) & add to dict_cache
					# AnonID = studytools.assign_next_free_studyID( study.XLS, study.DCM, study.test_study_UID )
					AnonID = study.assign_next_free_studyID( )
					print(f' - Unique UID - Assigning {AnonID}')
					
				
				
				
				#print(f'DeIdentify using name: { AnonName }\tID: { AnonID }')
				#deidentifyDICOM( study.DCM, AnonName, AnonID )   # deidentifyDICOM ( file-like object, name string, ID string )
				study.deidentifyDICOM( AnonName, AnonID )

				# print('-deidentifyDICOM- done')
				# testdcmobj.save_as( savefilename, write_like_original=True)
				study.DCM.save_as( savefilename, write_like_original=True)
				#print('study.DCM.save_as() done')


	

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

study.log_message( f'Completed. Deidentified {all_anonok}, failed {all_anonfailed}', study.loglevel_normal )

#studytools.write_xls_to_disc( study.XLS, study.xls_filename )
study.write_xls_to_disc( study.xls_filename )

pass